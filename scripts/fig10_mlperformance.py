#!/usr/bin/env python3

import os
import glob
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.text import Text
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
from matplotlib.legend_handler import HandlerTuple
from matplotlib.ticker import AutoMinorLocator, MultipleLocator
from sklearn.metrics import (roc_curve, auc, precision_recall_curve,
                             average_precision_score, confusion_matrix,
                             accuracy_score, precision_score, recall_score,
                             f1_score)

NAME = "fig10_mlperformance"
OUTDIR = "."

for _d in ("/usr/share/fonts/opentype/urw-base35",
           "/usr/share/fonts/type1/urw-base35",
           "/usr/local/share/fonts/urw-base35",
           "/opt/homebrew/share/fonts", "/Library/Fonts",
           os.path.expanduser("~/Library/Fonts")):
    for _f in glob.glob(os.path.join(_d, "NimbusSans-*.otf")) + \
              glob.glob(os.path.join(_d, "NimbusSans-*.ttf")):
        try:
            font_manager.fontManager.addfont(_f)
        except Exception:
            pass
if not {"Nimbus Sans", "Helvetica"} & {f.name for f in font_manager.fontManager.ttflist}:
    raise RuntimeError("Nimbus Sans not installed: `apt-get install fonts-urw-base35` "
                       "(Debian/Ubuntu) or `brew install --cask font-urw-base35`.")

PT_TAG, PT_TEXT, PT_TICK = 10.0, 9.0, 8.2
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Nimbus Sans", "Helvetica"],
    "font.size": PT_TEXT,
    "axes.titlesize": PT_TAG, "axes.titleweight": "bold",
    "axes.labelsize": PT_TEXT, "legend.fontsize": PT_TEXT,
    "xtick.labelsize": PT_TICK, "ytick.labelsize": PT_TICK,
    "axes.labelpad": 2, "axes.titlepad": 3.5, "axes.linewidth": 0.8,
    "axes.edgecolor": "#333333", "mathtext.default": "regular",
    "legend.framealpha": 0.92, "legend.edgecolor": "0.6",
    "legend.borderpad": 0.42, "legend.handletextpad": 0.55,
    "legend.labelspacing": 0.38, "legend.borderaxespad": 0.4,
    "savefig.dpi": 600, "figure.dpi": 130,

    "pdf.fonttype": 42, "ps.fonttype": 42,
})

QUAL_MIXED_12 = ["#B6CEE5", "#5884B3",
                 "#E5B5C5", "#CC6686",
                 "#F2CEC1", "#E87B70",
                 "#F9EBAA", "#E5CF6C",
                 "#CCE5B5", "#91BE64",
                 "#B6E3D1", "#5BBE94"]
QUAL_LIGHT_06 = ["#B6CEE5", "#E5B5C5", "#F2CEC1",
                 "#F9EBAA", "#CEE5B5", "#B6E4D1"]

BLUE, BLUE_L = QUAL_MIXED_12[1], QUAL_LIGHT_06[0]
PINK, PINK_L = QUAL_MIXED_12[3], QUAL_LIGHT_06[1]
SALMON = QUAL_MIXED_12[5]
GOLD = QUAL_MIXED_12[7]
GREEN = QUAL_MIXED_12[9]
TEAL, TEAL_L = QUAL_MIXED_12[11], QUAL_LIGHT_06[5]
GREY, GRID = "#6E6E6E", "0.86"

def shade(hex_colour, f=0.74):
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02X%02X%02X" % tuple(min(255, max(0, round(v * f))) for v in (r, g, b))
FILL_ALPHA = 0.62

CM_RAMP = LinearSegmentedColormap.from_list(
    "ssz_pink_seq", ["#FFFFFF", PINK_L, PINK, "#8C4059"])

def _find_predictions():
    here = Path(__file__).resolve().parent
    for nm in ("ml_predictions.csv", "predictions.csv"):
        for c in (here.parent / "data" / nm, here / "data" / nm, here / nm, Path(nm)):
            if c.exists():
                return str(c)
    raise FileNotFoundError(
        "predictions CSV not found; provide data/ml_predictions.csv with columns "
        "y_true,y_score (0=resist, 1=collapse; predicted P(collapse))")

_pred = np.genfromtxt(_find_predictions(), delimiter=",", names=True)
y_true = _pred["y_true"].astype(int)
y_score = _pred["y_score"].astype(float)
PREV = float(y_true.mean())

_ts = np.unique(y_score)
_f1 = np.array([f1_score(y_true, (y_score >= t).astype(int)) for t in _ts])
THR = float(_ts[int(np.argmax(_f1))])

fpr, tpr, _ = roc_curve(y_true, y_score)
ROC_AUC = auc(fpr, tpr)
prec_c, rec_c, _ = precision_recall_curve(y_true, y_score)
AP = average_precision_score(y_true, y_score)

y_hat = (y_score >= THR).astype(int)
ACC = accuracy_score(y_true, y_hat)
PRE = precision_score(y_true, y_hat)
REC = recall_score(y_true, y_hat)
F1 = f1_score(y_true, y_hat)
CM = confusion_matrix(y_true, y_hat)
op_fpr, op_tpr = CM[0, 1] / CM[0].sum(), REC

def style(ax, xlabel=None, ylabel=None, tag=None, grid="both",
          minor_x=True, minor_y=True):
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if tag:
        ax.set_title(tag, loc="left")
    ax.tick_params(which="both", direction="in", top=True, right=True, pad=2.5)
    ax.tick_params(which="major", length=4.0, width=0.8)
    ax.tick_params(which="minor", length=2.2, width=0.6)
    if minor_x:
        ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    if minor_y:
        ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    if grid:
        ax.grid(which="major", axis=("both" if grid is True else grid),
                lw=0.5, color=GRID)
        ax.set_axisbelow(True)
    return ax

def covers_data(bb, ax):
    hits = 0

    def c(xy):
        p = ax.transData.transform(np.asarray(xy, float))
        return int(((p[:, 0] >= bb.x0) & (p[:, 0] <= bb.x1) &
                    (p[:, 1] >= bb.y0) & (p[:, 1] <= bb.y1)).sum())

    for ln in ax.get_lines():
        d = np.column_stack(ln.get_data())
        if d.shape[0] > 2:
            hits += c(d)
    for col in ax.collections:
        off = col.get_offsets()
        if len(off):
            hits += c(off)
        for pth in col.get_paths():
            if len(pth.vertices):
                hits += c(pth.vertices)
    for pch in ax.patches:
        vs = pch.get_path().transformed(pch.get_patch_transform()).vertices
        if len(vs):
            hits += c(vs)
    return hits

fig, ax = plt.subplots(2, 2, figsize=(6.9, 6.5), constrained_layout=True)
fig.set_constrained_layout_pads(w_pad=0.02, h_pad=0.02, wspace=0.03, hspace=0.04)

ANN = dict(fontsize=PT_TEXT, ha="center", va="center")
ARROW = dict(arrowstyle="->", lw=0.9, color=shade(PINK), shrinkA=1, shrinkB=4)

a = ax[0, 0]
_u = np.linspace(0, 1, 200)
a.plot(_u, _u, ls=(0, (4, 3)), lw=1.0, color=GREY, zorder=2)
a.fill_between(fpr, tpr, 0, color=BLUE_L, alpha=FILL_ALPHA, lw=0, zorder=1)
a.plot(fpr, tpr, color=BLUE, lw=2.0, solid_capstyle="round", zorder=3)
a.scatter([op_fpr], [op_tpr], s=95, marker="*", color=PINK, edgecolor="black",
          lw=0.6, zorder=5)
a.set_xlim(0, 1); a.set_ylim(0, 1)
a.xaxis.set_major_locator(MultipleLocator(0.2))
a.yaxis.set_major_locator(MultipleLocator(0.2))
style(a, "False positive rate (\u2013)", "True positive rate (\u2013)",
      "(a) Receiver operating characteristic", grid="both")
a.text(0.51, 0.88, f"ROC-AUC = {ROC_AUC:.3f}", color=shade(BLUE),
       fontweight="bold", **ANN)
a.text(0.85, 0.60, "Chance", color=GREY, **ANN)
a.annotate(f"Operating point\naccuracy = {ACC:.3f}", xy=(op_fpr, op_tpr),
           xytext=(0.60, 0.28), color=shade(PINK), arrowprops=ARROW,
           multialignment="center", **ANN)

b = ax[0, 1]
b.plot(_u, np.full_like(_u, PREV), ls=(0, (4, 3)), lw=1.0, color=GREY, zorder=2)
b.fill_between(rec_c, prec_c, 0, color=TEAL_L, alpha=FILL_ALPHA, lw=0, zorder=1)
b.plot(rec_c, prec_c, color=TEAL, lw=2.0, solid_capstyle="round", zorder=3)
b.scatter([REC], [PRE], s=95, marker="*", color=PINK, edgecolor="black",
          lw=0.6, zorder=5)
b.set_xlim(0, 1); b.set_ylim(0, 1)
b.xaxis.set_major_locator(MultipleLocator(0.2))
b.yaxis.set_major_locator(MultipleLocator(0.2))
style(b, "Recall (\u2013)", "Precision (\u2013)", "(b) Precision\u2013recall",
      grid="both")
b.text(0.34, 0.62, f"Average precision\n= {AP:.3f}", color=shade(TEAL),
       fontweight="bold", multialignment="center", **ANN)

b.text(0.035, 0.10, f"No skill (prevalence = {PREV:.2f})", color=GREY,
       **{**ANN, "ha": "left"})
b.annotate(f"Operating point\n$P$ = {PRE:.3f}, $R$ = {REC:.3f}",
           xy=(REC, PRE), xytext=(0.44, 0.33), color=shade(PINK), arrowprops=ARROW,
           multialignment="center", **ANN)

c = ax[1, 0]
CMN = CM / CM.sum(axis=1, keepdims=True)
im = c.imshow(CMN, cmap=CM_RAMP, vmin=0, vmax=1, aspect="auto")
lab = ["Resist", "Collapse"]
c.set_xticks([0, 1], lab); c.set_yticks([0, 1], lab)
c.set_xlabel("Predicted class"); c.set_ylabel("True class")
c.set_title("(c) Confusion matrix (row-normalised)", loc="left")
c.tick_params(which="major", direction="out", length=3.2, width=0.8, pad=2.5,
              top=False, right=False)
for i in range(2):
    for j in range(2):

        col = "white" if CMN[i, j] > 0.62 else "#3A1520"
        c.text(j, i, f"{CM[i, j]:d}\n({CMN[i, j] * 100:.1f}%)", ha="center",
               va="center", color=col, fontsize=PT_TEXT, fontweight="bold",
               linespacing=1.25)

c.set_xticks(np.arange(-0.5, 2, 1), minor=True)
c.set_yticks(np.arange(-0.5, 2, 1), minor=True)
c.grid(which="minor", color="white", lw=1.4)
c.tick_params(which="minor", length=0, top=False, right=False)
cb = fig.colorbar(im, ax=c, fraction=0.045, pad=0.02, ticks=[0, 0.25, 0.5, 0.75, 1])
cb.set_label("Share of true class (\u2013)", fontsize=PT_TEXT, labelpad=3)
cb.ax.tick_params(labelsize=PT_TICK, length=3.0, width=0.8, direction="in", pad=2)
cb.ax.minorticks_on()
cb.outline.set_linewidth(0.8)

d = ax[1, 1]

rows = sorted([("ROC-AUC", ROC_AUC, BLUE, "///"), ("Accuracy", ACC, PINK, ""),
               ("Precision", PRE, SALMON, ""), ("$F_1$", F1, GREEN, ""),
               ("Recall", REC, GOLD, "")], key=lambda r: r[1], reverse=True)
names = [r[0] for r in rows]
vals = np.array([r[1] for r in rows])
ypos = np.arange(len(rows))[::-1]
plt.rcParams["hatch.linewidth"] = 0.7
for yy, v, (_, _, col, htc) in zip(ypos, vals, rows):
    d.barh(yy, v, height=0.62, color=col, hatch=htc, edgecolor="black",
           lw=0.6, zorder=3)
for yy, v in zip(ypos, vals):
    d.text(v + 0.015, yy, f"{v:.3f}", va="center", ha="left",
           fontsize=PT_TEXT, fontweight="bold", color="#1A1A1A", zorder=4)
d.set_yticks(ypos, names)
d.set_xlim(0, 1.12); d.set_ylim(-0.62, len(rows) - 0.38)
d.xaxis.set_major_locator(MultipleLocator(0.25))
style(d, "Score (\u2013)", None, "(d) Summary metrics", grid="x", minor_y=False)
d.tick_params(axis="y", which="major", length=0, right=False)

h_free = Patch(facecolor=BLUE, edgecolor="black", lw=0.6, hatch="///")
h_op = tuple(Patch(facecolor=c, edgecolor="black", lw=0.6)
             for c in (PINK, SALMON, GREEN, GOLD))
key = d.legend(handles=[h_free, h_op],
               labels=["Threshold-free", "At the operating point"],
               handler_map={tuple: HandlerTuple(ndivide=None, pad=0.25)},
               loc="upper center", bbox_to_anchor=(0.5, -0.135), ncol=2,
               frameon=False, handlelength=2.2, handletextpad=0.5, columnspacing=1.6)

fig.canvas.draw()
r = fig.canvas.get_renderer()
checks = {"key (d)": (key.get_window_extent(r), d)}
for pan, axx in (("(a)", a), ("(b)", b), ("(c)", c), ("(d)", d)):
    checks[f"tag {pan}"] = (Text.get_window_extent(axx.title, renderer=r), axx)
for pan, axx in (("(a)", a), ("(b)", b), ("(d)", d)):

    for t in axx.texts:
        lbl = t.get_text().splitlines()[0][:22]
        checks[f"{pan} '{lbl}'"] = (Text.get_window_extent(t, renderer=r), axx)
bad = {k: covers_data(bb, axx) for k, (bb, axx) in checks.items()
       if covers_data(bb, axx) > 0}
print("rule 1/7 covers_data:", "clean (0 hits everywhere)" if not bad else bad)

out = {}
for k, (bb, axx) in checks.items():
    if k.startswith(("key", "tag")):
        continue
    ab = axx.get_window_extent()
    if bb.x0 < ab.x0 + 2 or bb.x1 > ab.x1 - 2 or bb.y0 < ab.y0 + 2 or bb.y1 > ab.y1 - 2:
        out[k] = "outside the axes"
print("in-axes containment:", "clean" if not out else out)

from matplotlib.font_manager import findfont, FontProperties
_fp = FontProperties(); _fp.set_family("sans-serif")
assert "DejaVu" not in findfont(_fp), "DejaVu Sans resolved -- forbidden by house style"

os.makedirs(OUTDIR, exist_ok=True)
for ext in ("pdf", "png"):
    fig.savefig(os.path.join(OUTDIR, f"{NAME}.{ext}"),
                bbox_inches="tight", pad_inches=0.02,
                **({"dpi": 600} if ext == "png" else {}))
print(f"AUC={ROC_AUC:.3f} ACC={ACC:.3f} PRE={PRE:.3f} REC={REC:.3f} "
      f"F1={F1:.3f} AP={AP:.3f} thr={THR:.4f}")
print("confusion matrix (rows = true resist/collapse):\n", CM)
import sklearn
print(f"versions: Python {os.sys.version.split()[0]}, Matplotlib "
      f"{matplotlib.__version__}, NumPy {np.__version__}, "
      f"scikit-learn {sklearn.__version__}, font {findfont(_fp)}")
