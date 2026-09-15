#!/usr/bin/env python3
"""
fig07_catalog.py -- six-panel overview of the Sea of Marmara earthquake
catalogue, both rows drawn from the REAL KOERI/EarthScope IEB catalogues.

  TOP ROW    (a,b,c) -- longer instrumental record, 1973-2025
                        (IEB_3000_Marmara.csv, ~3.5k events)
  BOTTOM ROW (d,e,f) -- homogeneous digital network, 1994-2025
                        (IEB_Marmara.csv, ~2k events)

For each row: (magnitude-time with the completeness magnitude Mc; the
Gutenberg-Richter frequency-magnitude distribution with a maximum-likelihood
b-value; and the timeline of M>=5 events). Mc (maximum-curvature + 0.2) and
b (Aki-Utsu) are computed here from the data -- no values are hard-coded and
no synthetic catalogue is used.

Inputs (place under ../data or alongside this script):
    IEB_3000_Marmara.csv   IEB_Marmara.csv
Both are CSVs with columns Year, Month, Day, Time, Lat, Lon, Depth, Mag,
Region, Timestamp.

Outputs: fig07_catalog.pdf, fig07_catalog.png
"""
import os, csv, glob, warnings
from pathlib import Path
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator, LogLocator
from matplotlib.patheffects import withStroke
from matplotlib.font_manager import FontProperties, findfont, fontManager

# ----------------------------------------------------------------------
# House style: prefer Nimbus Sans (fonts-urw-base35); warn, do not crash.
# ----------------------------------------------------------------------
for _d in ("/usr/share/fonts/opentype/urw-base35", "/usr/share/fonts/type1/urw-base35",
           "/usr/local/share/fonts/urw-base35", "/opt/homebrew/share/fonts", "/Library/Fonts"):
    for _f in glob.glob(os.path.join(_d, "NimbusSans-*.otf")):
        try: fontManager.addfont(_f)
        except Exception: pass
_have_nimbus = bool({"Nimbus Sans", "Helvetica"} & {f.name for f in fontManager.ttflist})
if not _have_nimbus:
    warnings.warn("Nimbus Sans not found; falling back to the default sans-serif. "
                  "Install fonts-urw-base35 to match the house style.")
LW_MAIN, LW_SERIES, LW_GUIDE, LW_ARROW = 2.0, 1.2, 0.7, 1.0
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": (["Nimbus Sans", "Helvetica"] if _have_nimbus else []) + ["DejaVu Sans"],
    "mathtext.default": "regular",
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "font.size": 8.5, "axes.titlesize": 9.5, "axes.labelsize": 8.5,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.0,
    "axes.labelpad": 2, "axes.titlepad": 3, "axes.linewidth": 0.8,
})
HALO = [withStroke(linewidth=1.7, foreground="white")]
BLUE, ORANGE, GREEN, RED = "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"

# named large events (name only; magnitude read from the catalogue)
NAMED = {1999: "1999 İzmit", 2025: "2025 Silivri"}


def find(fn):
    here = Path(__file__).resolve().parent
    for c in (here.parent / "data" / fn, here / "data" / fn, here / fn,
              Path(fn), Path("/mnt/user-data/uploads") / fn):
        if c.exists():
            return str(c)
    raise FileNotFoundError(f"{fn} not found (looked in ../data, ./data, ., uploads)")


def load_catalogue(fn):
    """Return decimal-year and magnitude arrays from an IEB CSV."""
    yr, mag = [], []
    with open(find(fn), newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                Y, Mo, D = int(r["Year"]), int(r["Month"]), int(r["Day"])
                m = float(r["Mag"])
            except (KeyError, ValueError, TypeError):
                continue
            doy = (np.datetime64(f"{Y:04d}-{Mo:02d}-{D:02d}") - np.datetime64(f"{Y:04d}-01-01")) / np.timedelta64(1, "D")
            yr.append(Y + doy / 365.25); mag.append(m)
    return np.array(yr), np.array(mag)


def gr_stats(mag, dM=0.1):
    """Maximum-curvature Mc (+0.2) and Aki-Utsu b with 68% uncertainty."""
    edges = np.arange(np.floor(mag.min() * 10) / 10, mag.max() + dM, dM)
    left = np.round(edges[:-1], 2)
    inc, _ = np.histogram(mag, bins=edges)
    cum = np.array([(mag >= c - 1e-9).sum() for c in left])
    Mc = round(left[np.argmax(inc)] + 0.2, 1)
    sel = mag >= Mc - 1e-9
    mbar = mag[sel].mean(); n = int(sel.sum())
    b = np.log10(np.e) / (mbar - (Mc - dM / 2))
    sig = 2.3 * b**2 * np.sqrt(((mag[sel] - mbar)**2).sum() / (n * (n - 1)))
    a = np.log10(n) + b * Mc
    return dict(left=left, inc=inc, cum=cum, Mc=Mc, b=b, sig=sig, a=a, n=n)


def base(ax):
    ax.tick_params(which="both", direction="in", top=True, right=True, pad=2)
    ax.tick_params(which="major", length=4.0, width=0.8)
    ax.tick_params(which="minor", length=2.2, width=0.5)
    ax.grid(which="major", lw=0.5, color="0.85")
    ax.grid(which="minor", lw=0.3, color="0.92")
    ax.set_axisbelow(True)


def plot_row(axMT, axFMD, axTL, yr, mag, tags, period, fig, xmaj):
    g = gr_stats(mag)
    Mc, b, sig, a = g["Mc"], g["b"], g["sig"], g["a"]
    print(f"[{period}] N={mag.size}  Mc={Mc}  b={b:.2f}+/-{sig:.2f}  N(>=Mc)={g['n']}  "
          f"Mmax={mag.max():.1f}  M>=5:{int((mag>=5).sum())}")

    # (MT) magnitude vs time
    big = mag >= 6.0
    axMT.scatter(yr[~big], mag[~big], s=6, c=BLUE, alpha=0.45, lw=0, zorder=3)
    axMT.scatter(yr[big], mag[big], s=70, marker="*", c=RED, edgecolor="black", lw=0.5, zorder=5)
    axMT.axhline(Mc, color=ORANGE, lw=LW_MAIN, ls="--", zorder=4)
    axMT.axhspan(1.5, Mc, color="0.85", alpha=0.5, zorder=1)
    axMT.text(yr.min() + 0.4, Mc + 0.12, f"$M_c={Mc}$", color=ORANGE, fontsize=8,
              va="bottom", ha="left", path_effects=HALO, zorder=6)
    axMT.set_xlim(yr.min() - 0.5, yr.max() + 0.5); axMT.set_ylim(1.5, 8.0)
    axMT.xaxis.set_major_locator(MultipleLocator(xmaj)); axMT.xaxis.set_minor_locator(AutoMinorLocator(5))
    axMT.yaxis.set_major_locator(MultipleLocator(1)); axMT.yaxis.set_minor_locator(AutoMinorLocator(4))
    axMT.set_xlabel("Year"); axMT.set_ylabel("Magnitude $M$"); base(axMT)
    axMT.set_title(f"({tags[0]}) Magnitude vs time\n({period})", loc="left")

    # (FMD) frequency-magnitude
    left, inc, cum = g["left"], g["inc"], g["cum"]
    mp = cum > 0; ip = inc > 0
    axFMD.scatter(left[mp], cum[mp], s=14, facecolor=BLUE, edgecolor="none", zorder=4,
                  label=r"cumulative $N(\geq M)$")
    axFMD.scatter(left[ip], inc[ip], s=16, facecolor="none", edgecolor=GREEN, lw=0.8, zorder=3,
                  label="incremental")
    mm = np.linspace(Mc, mag.max(), 50)
    axFMD.plot(mm, 10**(a - b * mm), color=RED, lw=LW_MAIN, zorder=5,
               label=f"GR fit:\n$b={b:.2f}\\pm{sig:.2f}$")
    axFMD.axvline(Mc, color=ORANGE, lw=LW_GUIDE, ls="--", zorder=2)
    axFMD.set_yscale("log"); axFMD.set_xlim(mag.min() - 0.2, mag.max() + 0.3)
    axFMD.set_ylim(0.7, max(cum) * 30)
    axFMD.xaxis.set_major_locator(MultipleLocator(1)); axFMD.xaxis.set_minor_locator(AutoMinorLocator(5))
    axFMD.yaxis.set_major_locator(LogLocator(base=10))
    axFMD.yaxis.set_minor_locator(LogLocator(base=10, subs=np.arange(2, 10) * 0.1, numticks=12))
    axFMD.set_xlabel("Magnitude $M$"); axFMD.set_ylabel("Number of events"); base(axFMD)
    axFMD.text(Mc + 0.12, 1.2, f"$M_c={Mc}$", color=ORANGE, fontsize=8, ha="left", va="bottom",
               path_effects=HALO, zorder=6)
    leg = axFMD.legend(loc="upper right", framealpha=0.92, edgecolor="0.6", handletextpad=0.4,
                       borderpad=0.5, labelspacing=0.6, bbox_to_anchor=(0.995, 0.995))
    leg.get_frame().set_linewidth(0.5)
    axFMD.set_title(f"({tags[1]}) Frequency\u2013magnitude", loc="left")

    # (TL) timeline of M>=5
    m5 = mag >= 5.0; y5, mg5 = yr[m5], mag[m5]
    o = np.argsort(y5); y5, mg5 = y5[o], mg5[o]
    axTL.vlines(y5, 5.0, mg5, color="0.55", lw=LW_SERIES, zorder=2)
    sc = axTL.scatter(y5, mg5, s=22 + (mg5 - 5) * 40, c=mg5, cmap="viridis",
                      vmin=5, vmax=7.5, edgecolor="black", lw=0.4, zorder=4)
    axTL.set_xlim(yr.min() - 0.5, yr.max() + 0.5); axTL.set_ylim(4.8, 8.0)
    axTL.xaxis.set_major_locator(MultipleLocator(xmaj)); axTL.xaxis.set_minor_locator(AutoMinorLocator(5))
    axTL.yaxis.set_major_locator(MultipleLocator(1)); axTL.yaxis.set_minor_locator(AutoMinorLocator(4))
    axTL.set_xlabel("Year"); axTL.set_ylabel("Magnitude $M$"); base(axTL)
    axTL.set_title(f"({tags[2]}) Timeline, $M\\geq5$", loc="left")
    for yy, mm_ in zip(y5, mg5):
        if mm_ >= 6.0:
            name = NAMED.get(int(yy))
            txt = (name + f"\n$M${mm_:.1f}") if name else f"$M${mm_:.1f}"
            dx = -7 if yy > (yr.min() + yr.max()) / 2 else 6
            ha = "right" if dx < 0 else "left"
            axTL.annotate(txt, xy=(yy, mm_), xytext=(yy + dx, mm_ - 0.05), fontsize=7.0, ha=ha,
                          va="top", arrowprops=dict(arrowstyle="->", lw=LW_ARROW, color="0.3"),
                          path_effects=HALO, zorder=6)
    cb = fig.colorbar(sc, ax=axTL, fraction=0.046, pad=0.02)
    cb.set_label("$M$", fontsize=8); cb.ax.tick_params(labelsize=7.5)
    cb.ax.yaxis.set_minor_locator(AutoMinorLocator())


# ---- assemble the 2 x 3 plate --------------------------------------------
yr_top, mag_top = load_catalogue("IEB_3000_Marmara.csv")   # 1973-2025
yr_bot, mag_bot = load_catalogue("IEB_Marmara.csv")        # 1994-2025

fig = plt.figure(figsize=(7.4, 5.7), constrained_layout=True)
gs = fig.add_gridspec(2, 3, width_ratios=[1.05, 1.0, 1.05])
ax = [[fig.add_subplot(gs[r, c]) for c in range(3)] for r in range(2)]

plot_row(ax[0][0], ax[0][1], ax[0][2], yr_top, mag_top, ("a", "b", "c"),
         "1973\u20132025, instrumental record", fig, xmaj=10)
plot_row(ax[1][0], ax[1][1], ax[1][2], yr_bot, mag_bot, ("d", "e", "f"),
         "1994\u20132025, digital network", fig, xmaj=10)

fig.savefig("fig07_catalog.png", dpi=300, bbox_inches="tight", pad_inches=0.02)
fig.savefig("fig07_catalog.pdf", bbox_inches="tight", pad_inches=0.02)
print("saved fig07_catalog.png / .pdf")
