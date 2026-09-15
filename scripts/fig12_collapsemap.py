#!/usr/bin/env python3
# ============================================================================
# fig12_collapsemap — predicted spatial distribution of collapse potential
#                     across the Istanbul-Marmara area, overlaid on the
#                     site-amplification field.
# ----------------------------------------------------------------------------
# Layers:  collapse probability P(collapse)  -> filled colour raster (YlOrRd)
#          site-amplification factor AF       -> thin grey contour overlay
#          high-risk clusters (P >= 0.70)     -> bold contour outline
#          named districts, coastline, Sea of Marmara, graticule, scale, N-arrow
#
# Engine: Python 3 (Matplotlib 3.10.x, NumPy 2.x, SciPy, pyshp/shapely).
#         Coastline = Natural Earth 10m land (vector), clipped to the window.
#
# REQUIRED INPUT (the script fails without them; it will not synthesise)
#   score.nc      surrogate collapse-screening score on the analysis grid, 0..1,
#                 exported from the fitted XGBoost classifier for ALL cells.
#   amp.nc        site-amplification factor F = (760/Vs30)^m on this window,
#                 the same field as Figure 12.
#
# The previous version drew BOTH fields from a seeded synthetic construction
# (a coastal band plus five Gaussians on the named districts) that reproduced
# the manuscript's narrative rather than the model's output, and its
# amplification was incompatible with Figure 12: 1.0-1.8 concentrated in one
# lobe, against 0.94-1.66 distributed across the window on the real Vs30 grid.
#
#   Natural Earth land shapefile (place next to this script, or edit NE_PATH):
#     ne_10m_land.{shp,shx,dbf} from
#     https://github.com/nvkelso/natural-earth-vector/tree/master/10m_physical
# ============================================================================
import os, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, FuncFormatter
from matplotlib.colors import Normalize
from matplotlib.patches import Polygon as MplPolygon, FancyArrow
from matplotlib.collections import PatchCollection
from scipy.ndimage import gaussian_filter
import shapefile                       # pyshp
from shapely.geometry import shape, box
from shapely.ops import unary_union

# ---- study window (lon/lat) ------------------------------------------------
W, E, S, N = 27.80, 30.00, 40.55, 41.30   # identical to Figure 12
NE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ne_10m_land.shp")
if not os.path.exists(NE_PATH):
    raise SystemExit("ne_10m_land.shp not found next to this script. Download the "
                     "three files ne_10m_land.{shp,shx,dbf} from "
                     "https://github.com/nvkelso/natural-earth-vector/tree/master/10m_physical")

# ---- land / sea mask from Natural Earth ------------------------------------
sf = shapefile.Reader(NE_PATH)
win = box(W, S, E, N)
land = unary_union([shape(sr.shape.__geo_interface__).intersection(win)
                    for sr in sf.shapeRecords()
                    if shape(sr.shape.__geo_interface__).intersects(win)])

# ---- named places (annotation only; not model input) -----------------------
DISTRICTS = {
    "Esenyurt":      (28.673, 41.029),
    "Avc\u0131lar":  (28.721, 40.979),
    "K\u00fc\u00e7\u00fck\u00e7ekmece": (28.780, 40.997),
    "Bak\u0131rk\u00f6y": (28.872, 40.981),
    "Zeytinburnu":   (28.905, 40.992),
}
CONTEXT = {
    "Fatih":   (28.949, 41.048),
    "Kad\u0131k\u00f6y": (29.028, 40.990),
    "\u00dcsk\u00fcdar": (29.020, 41.026),
}

# ---- real input grids ------------------------------------------------------
# LAYOUT_CHECK=1 draws the furniture without the score raster, so labelling can
# be verified before the classifier output is to hand. It is a diagnostic mode;
# its output is not the figure.
LAYOUT_CHECK = os.environ.get("LAYOUT_CHECK", "0") == "1"
import xarray as xr

def load(path, what):
    if not os.path.exists(path):
        raise SystemExit(f"ERROR: {path} missing - {what}. This script does not "
                         "substitute a synthetic field.")
    da = xr.open_dataarray(path)
    ln = da[da.dims[1]].values
    la = da[da.dims[0]].values
    return ln, la, da.values

# amplification: the Figure 12 field, so the two maps agree by construction
lon_a, lat_a, AF_in = load("amp.nc", "site-amplification grid from Figure 12")

if LAYOUT_CHECK:
    lon, lat = lon_a, lat_a
    LON, LAT = np.meshgrid(lon, lat)
    P_COLLAPSE = np.full(LON.shape, np.nan)
    AF = AF_in
else:
    lon, lat, P_COLLAPSE = load("score.nc", "surrogate collapse-screening score "
                                "from the fitted classifier")
    LON, LAT = np.meshgrid(lon, lat)
    # resample the amplification field onto the score grid if their postings differ
    if AF_in.shape != P_COLLAPSE.shape:
        AF = (xr.open_dataarray("amp.nc")
                .interp({AF_in.dims if False else "lat": lat, "lon": lon})
                .values) if False else np.array(
              xr.open_dataarray("amp.nc").interp(
                  **{xr.open_dataarray("amp.nc").dims[0]: lat,
                     xr.open_dataarray("amp.nc").dims[1]: lon}).values)
    else:
        AF = AF_in
    print(f"score.nc {P_COLLAPSE.shape}  range {np.nanmin(P_COLLAPSE):.3f}"
          f"-{np.nanmax(P_COLLAPSE):.3f}")

# mask grid to land (sea cells -> NaN so they are not coloured)
from matplotlib.path import Path as MplPath
def land_mask(geom, LON, LAT):
    pts = np.column_stack([LON.ravel(), LAT.ravel()])
    inside = np.zeros(pts.shape[0], bool)
    polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    for poly in polys:
        ext = MplPath(np.asarray(poly.exterior.coords))
        ins = ext.contains_points(pts)
        for ring in poly.interiors:                       # subtract holes
            ins &= ~MplPath(np.asarray(ring.coords)).contains_points(pts)
        inside |= ins
    return inside.reshape(LON.shape)

MASK = land_mask(land, LON, LAT)
Pm  = np.where(MASK, P_COLLAPSE, np.nan)
AFm = np.where(MASK, AF, np.nan)

# ---- summary numbers (area-based, for the annotation box) ------------------
valid = Pm[~np.isnan(Pm)]
hi = (valid >= 0.70).mean() * 100
mid = ((valid >= 0.40) & (valid < 0.70)).mean() * 100
lo = (valid < 0.40).mean() * 100

# ---- house style -----------------------------------------------------------
# Nimbus Sans is mandatory; DejaVu Sans is forbidden by the house style.
import glob
from matplotlib.font_manager import FontProperties, findfont, fontManager
for _d in ("/usr/share/fonts/opentype/urw-base35", "/usr/share/fonts/type1/urw-base35",
           "/usr/local/share/fonts/urw-base35", "/opt/homebrew/share/fonts", "/Library/Fonts"):
    for _f in glob.glob(os.path.join(_d, "NimbusSans-*.otf")):
        try:
            fontManager.addfont(_f)
        except Exception:
            pass
if not ({"Nimbus Sans", "Helvetica"} & {f.name for f in fontManager.ttflist}):
    raise RuntimeError("Nimbus Sans not found; install fonts-urw-base35.")

# Rule 2: two line weights for content, with structural ink below both.
LW_MAIN, LW_SERIES, LW_STRUCT, LW_LEAD = 2.0, 1.2, 0.8, 1.0

plt.rcParams.update({"font.size": 9.5,
    "font.family": "sans-serif", "font.sans-serif": ["Nimbus Sans", "Helvetica"],
    "mathtext.fontset": "custom", "mathtext.rm": "Nimbus Sans",
    "mathtext.it": "Nimbus Sans:italic", "mathtext.bf": "Nimbus Sans:bold",
    "mathtext.sf": "Nimbus Sans", "mathtext.cal": "Nimbus Sans:italic",
    "mathtext.tt": "Nimbus Sans", "pdf.fonttype": 42, "ps.fonttype": 42,
    "axes.linewidth": 0.9, "axes.edgecolor": "#222222",
    "xtick.major.size": 4, "ytick.major.size": 4,
    "xtick.minor.size": 2.2, "ytick.minor.size": 2.2})
_fp = FontProperties(); _fp.set_family("sans-serif")
if "DejaVu" in findfont(_fp):
    raise RuntimeError("resolved to DejaVu Sans, which is forbidden.")
SEA   = "#d8ecf5"
COAST = "#3a3a3a"

fig, ax = plt.subplots(figsize=(8.4, 4.9))
ax.set_facecolor(SEA)                                     # sea colour
ax.set_xlim(W, E); ax.set_ylim(S, N)
ax.set_aspect(1 / np.cos(np.deg2rad(0.5 * (S + N))))      # Mercator-like aspect

# collapse-probability raster
norm = Normalize(0, 1)
im = ax.pcolormesh(lon, lat, Pm, cmap="YlOrRd", norm=norm, shading="auto",
                   zorder=2, rasterized=True)

# amplification field as contours (the field P is "overlaid on")
import matplotlib.patheffects as pe
clev = np.arange(1.2, 1.71, 0.2)
cs = ax.contour(LON, LAT, AFm, levels=clev, colors="#1b1b1b",
                linewidths=LW_SERIES, zorder=3)
cs.set_path_effects([pe.withStroke(linewidth=1.8, foreground="white", alpha=0.7)])
lbls = ax.clabel(cs, levels=clev, fmt="%.1f", fontsize=6.5, inline=True)
for t in lbls:
    t.set_path_effects([pe.withStroke(linewidth=1.8, foreground="white", alpha=0.85)])

# high-risk cluster outline (P = 0.70)
hr = ax.contour(LON, LAT, Pm, levels=[0.70], colors="#3d0a52",
                linewidths=LW_MAIN, zorder=4)

# coastline on top of everything
polys = land.geoms if land.geom_type == "MultiPolygon" else [land]
patches = []
for poly in polys:
    ax.plot(*np.asarray(poly.exterior.coords).T, color=COAST, lw=LW_STRUCT, zorder=5)
    for ring in poly.interiors:
        ax.plot(*np.asarray(ring.coords).T, color=COAST, lw=LW_STRUCT, zorder=5)

# districts (with short leader lines so the dense cluster doesn't overlap)
LABELPOS = {   # name: (text_lon, text_lat, ha)
    "Esenyurt":      (28.330, 41.135, "right"),
    "Avc\u0131lar":  (28.330, 41.060, "right"),
    "K\u00fc\u00e7\u00fck\u00e7ekmece": (28.560, 41.215, "center"),
    "Bak\u0131rk\u00f6y": (28.930, 40.860, "center"),
    "Zeytinburnu":   (29.230, 40.930, "left"),
}
for name, (lo_, la_) in DISTRICTS.items():
    tlo, tla, ha = LABELPOS[name]
    ax.plot([lo_, tlo], [la_, tla], color="#111111", lw=LW_LEAD, zorder=6)
    ax.plot(lo_, la_, "o", ms=4.4, mfc="#111111", mec="white", mew=0.6, zorder=7)
    ax.annotate(name, (tlo, tla), fontsize=7.3, fontweight="bold", color="#111111",
                ha=ha, va="center", zorder=8,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8))
for name, (lo_, la_) in CONTEXT.items():
    ax.plot(lo_, la_, "s", ms=3.0, mfc="#555555", mec="white", mew=0.5, zorder=6)
    ax.annotate(name, (lo_, la_), textcoords="offset points", xytext=(4, 2.5),
                fontsize=6.4, color="#444444", style="italic", zorder=7)

# water labels
ax.text(28.45, 40.74, "Sea of Marmara", fontsize=10, style="italic",
        color="#1f6f93", ha="center", zorder=6)
ax.text(29.06, 41.115, "Bosphorus", fontsize=6.6, style="italic", rotation=72,
        color="#1f6f93", ha="center", va="center", zorder=6)

# graticule / ticks
ax.xaxis.set_major_locator(plt.MultipleLocator(0.5))
ax.yaxis.set_major_locator(plt.MultipleLocator(0.2))
ax.xaxis.set_minor_locator(AutoMinorLocator())
ax.yaxis.set_minor_locator(AutoMinorLocator())
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.1f}\u00b0E"))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.1f}\u00b0N"))
ax.grid(which="major", lw=0.3, color="#9fb9c6", alpha=0.6, zorder=1)
ax.tick_params(labelsize=8)

# scale bar (20 km) at lower-left
km_per_deg_lon = 111.32 * np.cos(np.deg2rad(0.5 * (S + N)))
seg = 20.0 / km_per_deg_lon                                # 20 km in deg-lon
x0, y0 = W + 0.10, S + 0.07
ax.plot([x0, x0 + seg], [y0, y0], color="#111111", lw=3, solid_capstyle="butt", zorder=8)
ax.plot([x0, x0], [y0 - 0.012, y0 + 0.012], color="#111111", lw=1, zorder=8)
ax.plot([x0 + seg, x0 + seg], [y0 - 0.012, y0 + 0.012], color="#111111", lw=1, zorder=8)
ax.text(x0 + seg / 2, y0 + 0.022, "20 km", ha="center", va="bottom",
        fontsize=7.2, fontweight="bold", zorder=8)

# north arrow upper-left
nax, nay = W + 0.085, N - 0.085
ax.add_patch(FancyArrow(nax, nay - 0.10, 0, 0.13, width=0.0, head_width=0.045,
                        head_length=0.05, length_includes_head=True,
                        color="#111111", zorder=8))
ax.text(nax, nay + 0.055, "N", ha="center", va="bottom", fontsize=9,
        fontweight="bold", zorder=8)

# colour bar
cb = fig.colorbar(im, ax=ax, fraction=0.030, pad=0.02)
cb.set_label("Surrogate collapse-screening score  $S$", fontsize=8.5)
cb.ax.tick_params(labelsize=7.5)
cb.ax.axhline(0.70, color="#3d0a52", lw=1.4)

# legend for the amplification contours
from matplotlib.lines import Line2D
leg = ax.legend([Line2D([0], [0], color="#3b3b3b", lw=LW_SERIES, alpha=0.7),
                 Line2D([0], [0], color="#3d0a52", lw=LW_MAIN)],
                ["site amplification factor", "high-risk cluster ($S$ = 0.70)"],
                loc="upper right", fontsize=6.8, framealpha=0.92,
                edgecolor="#cccccc")
leg.set_zorder(9)

ax.set_title("Predicted collapse potential across the Istanbul\u2013Marmara area\n"
             "(machine-learning model), overlaid on the site-amplification field",
             fontsize=10, fontweight="bold", loc="left", pad=8)

fig.tight_layout()
fig.savefig("fig12_collapsemap.pdf")
fig.savefig("fig12_collapsemap.png", dpi=600)
print(f"high={hi:.1f}% med={mid:.1f}% low={lo:.1f}% "
      f"Pmax={np.nanmax(Pm):.2f} AFmax={np.nanmax(AFm):.2f}")
