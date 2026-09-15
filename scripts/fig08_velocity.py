#!/usr/bin/env python3
import os, glob, warnings
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import label
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
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
    "font.size": 11, "axes.linewidth": 0.9})

TIF = "vs30_istanbul.tif"
WATER_VALUE = 600.0
VMIN, VMAX = 180.0, 760.0
IST = (28.979, 41.013)


def find(fn):
    here = Path(__file__).resolve().parent
    for c in (here.parent / "data" / fn, here / "data" / fn, here / fn, Path(fn)):
        if c.exists():
            return str(c)
    raise FileNotFoundError(f"{fn} not found (looked in ../data, ./data, .)")


r = rasterio.open(find(TIF))
z = r.read(1).astype(float)
W, S, E, N = r.bounds.left, r.bounds.bottom, r.bounds.right, r.bounds.top
ny, nx = z.shape
lon = np.linspace(W, E, nx)
lat = np.linspace(N, S, ny)
Lon, Lat = np.meshgrid(lon, lat)

cand = ~np.isfinite(z) | (np.round(z) == WATER_VALUE)
lbl, _ = label(cand)
edge = set(lbl[0, :]) | set(lbl[-1, :]) | set(lbl[:, 0]) | set(lbl[:, -1])
edge.discard(0)
water = np.isin(lbl, list(edge))

zmask = np.ma.masked_where(water, z)

lat0 = 0.5 * (S + N)
fig = plt.figure(figsize=(11.0, 5.6))
ax = fig.add_axes([0.055, 0.095, 0.86, 0.86])
ax.set_facecolor("0.85")
cmap = plt.get_cmap("jet").copy()
im = ax.imshow(zmask, extent=[W, E, S, N], origin="upper", cmap=cmap,
               vmin=VMIN, vmax=VMAX, interpolation="nearest",
               aspect=1.0 / np.cos(np.radians(lat0)))
ax.contour(Lon, Lat, water.astype(float), levels=[0.5], colors="black", linewidths=0.5)

ax.plot(*IST, marker="*", ms=17, mfc="white", mec="black", mew=1.2, zorder=6)
ax.annotate("Istanbul", IST, xytext=(7, 2), textcoords="offset points",
            fontsize=13, fontweight="bold", zorder=6)

def lon_fmt(x, _):
    d = int(abs(x)); m = int(round((abs(x) - d) * 60))
    return f"{d}\u00b0{m:02d}'E"
def lat_fmt(y, _):
    d = int(abs(y)); m = int(round((abs(y) - d) * 60))
    return f"{d}\u00b0{m:02d}'N"
xt = np.arange(np.ceil(W * 2) / 2, E + 1e-6, 0.5)
yt = np.arange(np.ceil(S * 2) / 2, N + 1e-6, 0.5)
ax.set_xticks(xt); ax.set_yticks(yt)
ax.xaxis.set_major_formatter(plt.FuncFormatter(lon_fmt))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lat_fmt))
ax.set_xlim(W, E); ax.set_ylim(S, N)
ax.grid(True, which="major", color="white", ls=(0, (6, 4)), lw=0.8, alpha=0.9)
ax.tick_params(direction="out", length=4, width=0.9, labelsize=11)

cax = fig.add_axes([0.925, 0.095, 0.018, 0.86])
cb = fig.colorbar(im, cax=cax, extend="max")
cb.set_label("$V_{s30}$  (m s$^{-1}$)", fontsize=12, labelpad=6)
cb.ax.tick_params(labelsize=10)

for ext in ("pdf", "png"):
    fig.savefig(f"fig08_velocity.{ext}", dpi=300, bbox_inches="tight", pad_inches=0.02)
print(f"grid {nx}x{ny}  extent {W:.3f}-{E:.3f}E {S:.3f}-{N:.3f}N  "
      f"Vs30 {np.nanmin(z):.0f}-{np.nanmax(z):.0f}  water%={100*water.mean():.0f}")
print("saved fig08_velocity.pdf / .png")
