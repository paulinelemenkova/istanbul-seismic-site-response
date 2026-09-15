#!/usr/bin/env python3
import argparse
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

FEATURES_FULL = ["vs30", "sed_thickness", "dist_fault", "T0", "bldg_height",
                 "Sa", "amp_factor"]
FEATURES_NOLEAK = ["vs30", "sed_thickness", "dist_fault", "T0", "bldg_height"]


# --------------------------------------------------------------------------- #
# Models: the two families reported in the revised Section 3.4.                #
# --------------------------------------------------------------------------- #
def make_models(seed, pos_weight, allow_fallback=False):
    rf = RandomForestClassifier(n_estimators=500, max_depth=20,
                                class_weight="balanced", random_state=seed,
                                n_jobs=-1)
    try:
        from xgboost import XGBClassifier
        gb = XGBClassifier(n_estimators=1000, learning_rate=0.05, max_depth=6,
                           subsample=0.8, colsample_bytree=0.8,
                           scale_pos_weight=pos_weight, eval_metric="logloss",
                           random_state=seed, n_jobs=-1, tree_method="hist")
        gb_name = "XGBoost"
    except ImportError:
        if not allow_fallback:
            sys.exit("xgboost is not installed, and the manuscript names "
                     "XGBoost as the selected model. Install it with "
                     "`pip install xgboost`, or re-run with --allow-fallback "
                     "AND rename the model in Tables 8 and 10 to whatever was "
                     "actually fitted. The script will not print rows labelled "
                     "XGBoost for a model that is not XGBoost.")
        from sklearn.ensemble import HistGradientBoostingClassifier
        gb = HistGradientBoostingClassifier(learning_rate=0.05, max_iter=1000,
                                            early_stopping=True,
                                            random_state=seed)
        gb_name = "HistGradientBoosting"
    return [("Random forest", rf), (gb_name, gb)]


def score(model, Xtr, ytr, Xte, yte):
    """Fit on one fold and return (accuracy, F1 on collapse, ROC-AUC)."""
    model.fit(Xtr, ytr)
    p = model.predict_proba(Xte)[:, 1]
    yhat = (p >= 0.5).astype(int)
    auc = roc_auc_score(yte, p) if len(np.unique(yte)) > 1 else np.nan
    return (accuracy_score(yte, yhat),
            f1_score(yte, yhat, pos_label=1, zero_division=0),
            auc)


def summarise(rows):
    """Mean and across-fold standard deviation of a list of metric triples."""
    a = np.array(rows, dtype=float)
    return np.nanmean(a, axis=0), np.nanstd(a, axis=0)


def cell(mean, sd):
    return "$%.3f \\pm %.3f$" % (mean, sd)


# --------------------------------------------------------------------------- #
# Fold designs                                                                 #
# --------------------------------------------------------------------------- #
def block_folds(df, block_m, n_folds, rng):
    """5 x 5 km contiguous blocks, assigned to folds in order of prevalence.

    Blocks are sorted by their collapse rate and dealt round-robin to the folds,
    so each fold carries a comparable prevalence while every cell of a block
    stays wholly inside one fold (Section 3.8 of the manuscript).
    """
    bx = np.floor(df["x"].to_numpy() / block_m).astype(int)
    by = np.floor(df["y"].to_numpy() / block_m).astype(int)
    block = pd.Series([f"{i}_{j}" for i, j in zip(bx, by)], index=df.index)

    rate = df.groupby(block)["label"].mean()
    order = rate.sample(frac=1.0, random_state=rng).sort_values().index
    assign = {b: k % n_folds for k, b in enumerate(order)}
    fold = block.map(assign).to_numpy()

    print("    %d blocks of %.0f m over %d cells; fold sizes %s"
          % (block.nunique(), block_m, len(df),
             np.bincount(fold, minlength=n_folds).tolist()))
    return fold


def district_folds(df):
    codes, names = pd.factorize(df["district"])
    print("    %d districts: %s" % (len(names), ", ".join(map(str, names[:8]))
                                    + (" ..." if len(names) > 8 else "")))
    return codes


def run_grouped(df, feats, folds, seed, allow_fallback=False):
    """Fit and score each model once per fold, holding out one group."""
    X, y = df[feats].to_numpy(float), df["label"].to_numpy(int)
    pos_w = (y == 0).sum() / max((y == 1).sum(), 1)
    out = {}
    for name, model in make_models(seed, pos_w, allow_fallback):
        rows = []
        for f in np.unique(folds):
            tr, te = folds != f, folds == f
            if len(np.unique(y[tr])) < 2 or te.sum() == 0:
                continue
            rows.append(score(model, X[tr], y[tr], X[te], y[te]))
        out[name] = summarise(rows)
    return out


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--block-km", type=float, default=5.0)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--allow-fallback", action="store_true",
                    help="permit a non-XGBoost booster; the printed rows then "
                         "carry its real name, which you must also change in "
                         "Tables 8 and 10")
    a = ap.parse_args()

    df = pd.read_csv(a.csv)
    missing = [c for c in FEATURES_FULL + ["x", "y", "district", "label"]
               if c not in df.columns]
    if missing:
        sys.exit("missing column(s): %s" % ", ".join(missing))

    n1 = int(df["label"].sum())
    print("dataset: %d cells, %d resist / %d collapse (prevalence %.3f)"
          % (len(df), len(df) - n1, n1, n1 / len(df)))
    if len(df) != 2800:
        print("  NOTE: the manuscript states N = 2800; this file has %d. "
              "Reconcile before pasting." % len(df))

    # ---- Table 9: leakage-controlled row, same random 25 % hold-out -------- #
    print("\n[1/3] leakage-controlled ablation (random 25 % hold-out)")
    tr, te = train_test_split(df, test_size=0.25, stratify=df["label"],
                              random_state=a.seed)
    y_tr, y_te = tr["label"].to_numpy(int), te["label"].to_numpy(int)
    pos_w = (y_tr == 0).sum() / max((y_tr == 1).sum(), 1)
    gb_name, gb = make_models(a.seed, pos_w, a.allow_fallback)[1]

    full = score(gb, tr[FEATURES_FULL].to_numpy(float), y_tr,
                 te[FEATURES_FULL].to_numpy(float), y_te)
    _, gb2 = make_models(a.seed, pos_w, a.allow_fallback)[1]
    noleak = score(gb2, tr[FEATURES_NOLEAK].to_numpy(float), y_tr,
                   te[FEATURES_NOLEAK].to_numpy(float), y_te)
    print("    full   acc=%.3f  AUC=%.3f   (compare with the 0.896 / 0.930 "
          "already in Table 8)" % (full[0], full[2]))
    print("    no F, no Sa   acc=%.3f  AUC=%.3f" % (noleak[0], noleak[2]))

    # ---- Table 10: the two spatially independent designs ------------------ #
    print("\n[2/3] spatial block cross-validation")
    blk = run_grouped(df, FEATURES_FULL,
                      block_folds(df, a.block_km * 1000.0, a.folds, a.seed),
                      a.seed, a.allow_fallback)
    print("\n[3/3] leave-one-district-out")
    lodo = run_grouped(df, FEATURES_FULL, district_folds(df), a.seed,
                       a.allow_fallback)

    # ---- emit the LaTeX rows --------------------------------------------- #
    print("\n" + "=" * 74)
    print("Table 9 (tab:ablation) -- replace the [VALUE] row at line 809:")
    print("=" * 74)
    print("\\textcolor{blue}{Leakage-controlled (no $F$, no $S_a(T_0)$)} & "
          "\\textcolor{blue}{%.3f} & \\textcolor{blue}{%.3f} & "
          "\\textcolor{blue}{%+.3f} \\\\"
          % (noleak[0], noleak[2], noleak[2] - 0.930))

    print("\n" + "=" * 74)
    print("Table 10 (tab:spatialcv) -- replace the [VALUE] rows at 826-830:")
    print("=" * 74)
    for design, res in (("Spatial block CV ($5\\times5$\\,km)", blk),
                        ("Leave-one-district-out", lodo)):
        for name, (m, s) in res.items():
            short = name          # the real fitted model, never a guess
            print("\\textcolor{blue}{%s} & \\textcolor{blue}{%s} & "
                  "\\textcolor{blue}{%s} & \\textcolor{blue}{%s} & "
                  "\\textcolor{blue}{%s} \\\\"
                  % (design, short, cell(m[0], s[0]), cell(m[1], s[1]),
                     cell(m[2], s[2])))
        print("\\midrule")

    print("\nModels actually fitted: Random forest and %s." % gb_name)
    if gb_name != "XGBoost":
        print("WARNING: the boosting rows above are %s, not XGBoost. Rename "
              "the model in Tables 8 and 10 to match." % gb_name)
    print("After pasting, confirm nothing is left:  "
          "grep -n '\\[VALUE\\]' article_06082026.tex")


if __name__ == "__main__":
    main()
