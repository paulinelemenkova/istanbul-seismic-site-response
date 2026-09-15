#!/usr/bin/env python3
import os, csv, glob, warnings
from pathlib import Path
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, MultipleLocator
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib.font_manager import fontManager

for _d in ("/usr/share/fonts/opentype/urw-base35", "/usr/share/fonts/type1/urw-base35",
           "/usr/local/share/fonts/urw-base35", "/opt/homebrew/share/fonts",
           "/Library/Fonts", os.path.expanduser("~/Library/Fonts")):
    for _f in glob.glob(os.path.join(_d, "NimbusSans-*.otf")) + glob.glob(os.path.join(_d, "NimbusSans-*.ttf")):
        try: fontManager.addfont(_f)
        except Exception: pass
_have = bool({"Nimbus Sans", "Helvetica"} & {f.name for f in fontManager.ttflist})
if not _have:
    warnings.warn("Nimbus Sans not found; falling back to the default sans-serif "
                  "(install fonts-urw-base35 to match the house style).")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": (["Nimbus Sans", "Helvetica"] if _have else []) + ["DejaVu Sans"],
    "mathtext.default": "regular", "pdf.fonttype": 42, "ps.fonttype": 42,
    "font.size": 9, "axes.labelsize": 10, "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5, "legend.fontsize": 9, "axes.linewidth": 0.8})

REF_LON = REF_LAT = STRIKE_DEG = None
CSV = "IEB_3000_Marmara.csv"


def find(fn):
    here = Path(__file__).resolve().parent
    for c in (here.parent / "data" / fn, here / "data" / fn, here / fn, Path(fn)):
        if c.exists():
            return str(c)
    raise FileNotFoundError(f"{fn} not found (looked in ../data, ./data, .)")


def load(fn):
    lon, lat, dep, mag = [], [], [], []
    with open(find(fn), newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                la, lo, dp, mg = float(r["Lat"]), float(r["Lon"]), float(r["Depth"]), float(r["Mag"])
            except (KeyError, ValueError, TypeError):
                continue
            if np.isfinite(dp) and np.isfinite(mg):
                lon.append(lo); lat.append(la); dep.append(dp); mag.append(mg)
    return (np.array(lon), np.array(lat), np.array(dep), np.array(mag))


lon, lat, depth, M = load(CSV)

lat0 = float(np.mean(lat)) if REF_LAT is None else REF_LAT
lon0 = float(np.mean(lon)) if REF_LON is None else REF_LON
x = (lon - lon0) * 111.320 * np.cos(np.radians(lat0))
yv = (lat - lat0) * 110.574
pts = np.column_stack([x, yv])
if STRIKE_DEG is None:
    w, V = np.linalg.eigh(np.cov(pts.T))
    strike = V[:, int(np.argmax(w))]
else:
    a = np.radians(STRIKE_DEG); strike = np.array([np.sin(a), np.cos(a)])
normal = np.array([-strike[1], strike[0]])
if normal[0] < 0:
    normal = -normal
dist = pts @ normal
strike_az = (np.degrees(np.arctan2(strike[0], strike[1])) + 180) % 180

mean_depth = float(depth.mean())
frac_core = float(np.mean((depth >= 5) & (depth <= 15)))
N = depth.size
MMIN, MMAX = float(np.floor(M.min())), float(np.ceil(M.max()))
size = 4.0 + 90.0 * ((M - MMIN) / (MMAX - MMIN)) ** 1.6

BINW = 2.0
ymax = float(min(40.0, np.ceil((depth.max() + 2) / 2) * 2))
bins = np.arange(0, ymax + 0.001, BINW)
cnt, _ = np.histogram(depth, bins=bins)
xabs = float(np.ceil(np.percentile(np.abs(dist), 99) / 5) * 5)
XLIM, YLIM, NLIM = (-xabs, xabs), (0, ymax), (0, float(np.ceil(cnt.max() / 50) * 50))

BAND, INK, FAULT, GREY = "#ECECEC", "#1A1A1A", "#B2182B", "#5A5A5A"
_SKY18 = np.array([[251,238,84],[239,225,113],[228,211,142],[216,198,171],[205,185,200],
                   [193,171,229],[180,164,233],[167,157,233],[154,150,234],[141,143,234],
                   [128,136,235],[115,129,235],[102,122,235],[94,116,225],[85,110,216],
                   [76,104,206],[68,98,197],[59,92,187]]) / 255.0
CMAP = ListedColormap(_SKY18, name="sky_18")
_SKY20 = LinearSegmentedColormap.from_list("sky_20", [
    (0.0, np.array([255,253,212])/255.0), (0.300049, np.array([255,242,112])/255.0),
    (0.649902, np.array([251,198,86])/255.0), (1.0, np.array([227,181,95])/255.0)])
def sky20_fill(v, vmax, lo=0.20):
    v = np.asarray(v, float)
    return _SKY20(lo + (1.0 - lo) * np.clip(v / vmax, 0.0, 1.0))

fig = plt.figure(figsize=(6.89, 4.15))
ax_a = fig.add_axes([0.062, 0.310, 0.560, 0.615])
ax_b = fig.add_axes([0.640, 0.310, 0.142, 0.615], sharey=ax_a)
cax = fig.add_axes([0.062, 0.088, 0.392, 0.026])
kax = fig.add_axes([0.545, 0.020, 0.250, 0.120])

ax_a.set_xlim(*XLIM); ax_a.set_ylim(*YLIM); ax_a.invert_yaxis(); ax_a.set_axisbelow(True)
ax_a.axhspan(5, 15, color=BAND, lw=0, zorder=0)
ax_a.grid(which="major", lw=0.5, color="0.86", zorder=0.5)
o = np.argsort(M)
sc = ax_a.scatter(dist[o], depth[o], s=size[o], c=M[o], cmap=CMAP, vmin=MMIN, vmax=MMAX,
                  linewidths=0.18, edgecolors="#3C3C3C", alpha=0.85, zorder=3)
ax_a.axvline(0, color=FAULT, lw=1.2, ls=(0, (5, 2.5)), zorder=2.6)
ax_a.axhline(mean_depth, color=INK, lw=1.1, ls=(0, (5.5, 2.5)), zorder=2.6)
ax_a.axhline(20, color=GREY, lw=0.9, ls=(0, (2.5, 2.5)), zorder=2.6)
for yy in (5, 15):
    ax_a.axhline(yy, color="#BDBDBD", lw=0.6, zorder=0.6)
ax_a.set_xlabel("Distance perpendicular to the Main Marmara Fault (km)")
ax_a.set_ylabel("Focal depth (km)")
ax_a.xaxis.set_major_locator(MultipleLocator(20)); ax_a.xaxis.set_minor_locator(AutoMinorLocator(2))
ax_a.yaxis.set_major_locator(MultipleLocator(5)); ax_a.yaxis.set_minor_locator(AutoMinorLocator(5))
ax_a.tick_params(which="both", direction="in", top=True, right=True, pad=2.5)
ax_a.tick_params(which="major", length=4.0, width=0.8); ax_a.tick_params(which="minor", length=2.2, width=0.5)

ax_b.set_xlim(*NLIM); ax_b.set_axisbelow(True)
ax_b.axhspan(5, 15, color=BAND, lw=0, zorder=0)
ax_b.grid(which="major", axis="x", lw=0.5, color="0.86", zorder=0.5)
nz = cnt > 0
ax_b.barh((bins[:-1] + BINW / 2)[nz], cnt[nz], height=BINW * 0.92,
          color=sky20_fill(cnt[nz], cnt.max()), edgecolor="#3C3C3C", linewidth=0.35, zorder=3)
ax_b.axhline(mean_depth, color=INK, lw=1.1, ls=(0, (5.5, 2.5)), zorder=4)
ax_b.axhline(20, color=GREY, lw=0.9, ls=(0, (2.5, 2.5)), zorder=4)
ax_b.set_xlabel(f"Events per {BINW:g} km bin")
ax_b.xaxis.set_minor_locator(AutoMinorLocator(2))
ax_b.tick_params(which="both", direction="in", top=True, right=True, pad=2.5)
ax_b.tick_params(which="major", length=4.0, width=0.8); ax_b.tick_params(which="minor", length=2.2, width=0.5)
ax_b.tick_params(axis="y", labelleft=False)

ax_a.text(0.012, 0.988, "(a)", transform=ax_a.transAxes, ha="left", va="top",
          fontsize=10, fontweight="bold", color=INK)
ax_b.text(0.055, 0.988, "(b)", transform=ax_b.transAxes, ha="left", va="top",
          fontsize=10, fontweight="bold", color=INK)
ax_a.text(XLIM[0] * 0.8, 1.1, "NW", ha="left", va="center", fontsize=9, style="italic", color=GREY)
ax_a.text(XLIM[1] * 0.95, 1.1, "SE", ha="right", va="center", fontsize=9, style="italic", color=GREY)
for yy, txt, col in ((mean_depth, f"mean depth\n{mean_depth:.1f} km", INK),
                     (20.0, "base of the\nseismogenic zone\n(\u224820 km)", GREY)):
    ax_b.annotate(txt, xy=(1.0, yy), xycoords=("axes fraction", "data"),
                  xytext=(11, 0), textcoords="offset points", ha="left", va="center",
                  fontsize=9, color=col,
                  arrowprops=dict(arrowstyle="-", lw=0.7, color=col, shrinkA=1.5, shrinkB=1.5))
fig.text(0.062, 0.975, "Depth cross-section of instrumental seismicity, Main Marmara Fault",
         ha="left", va="top", fontsize=9, fontweight="bold", color=FAULT)
fig.text(0.062, 0.190, f"Shaded band: {frac_core*100:.0f}\u2009% of the {N} events lie between "
         "5 and 15 km depth.", ha="left", va="top", fontsize=8, color="#4F4F4F")

cb = fig.colorbar(sc, cax=cax, orientation="horizontal")
cb.set_label("Magnitude $M$", fontsize=9, labelpad=2)
cb.ax.tick_params(labelsize=8.5, direction="out", length=2.5, width=0.6, pad=1.5)
cb.outline.set_linewidth(0.6)
kax.set_axis_off(); kax.set_xlim(0, 1); kax.set_ylim(0, 1)
for xk, mk in zip((0.18, 0.5, 0.82), (MMIN + 0.2 * (MMAX - MMIN), MMIN + 0.55 * (MMAX - MMIN), MMAX)):
    kax.scatter([xk], [0.45], s=4.0 + 90.0 * ((mk - MMIN) / (MMAX - MMIN)) ** 1.6,
                color=CMAP((mk - MMIN) / (MMAX - MMIN)), linewidths=0.3, edgecolors="#3C3C3C")
    kax.text(xk, 0.03, f"{mk:.0f}", ha="center", va="bottom", fontsize=8.5)
kax.text(0.5, 0.96, "symbol area scales with $M$", ha="center", va="top", fontsize=9)

for ext in ("pdf", "png"):
    fig.savefig(f"fig11_crosssection.{ext}", dpi=300, bbox_inches="tight", pad_inches=0.02)
print(f"strike azimuth (data-derived) = {strike_az:.0f} deg;  ref = {lon0:.3f}E {lat0:.3f}N")
print(f"N={N}  depth {depth.min():.1f}-{depth.max():.1f} km  mean {mean_depth:.2f} +/- {depth.std(ddof=1):.2f}  "
      f"5-15 km {frac_core*100:.1f}%  <=20 km {100*np.mean(depth<=20):.1f}%  >20 km off-band {100*np.mean(depth>20):.1f}%")
print("saved fig11_crosssection.pdf / .png")
