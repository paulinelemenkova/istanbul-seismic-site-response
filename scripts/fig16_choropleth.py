#!/usr/bin/env python3
# ============================================================================
# fig16_collapsemap — İBB scenario heavy-damage ratio by neighbourhood
#                     (959 mahalle), Istanbul metropolitan area
# ============================================================================
import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.ticker import AutoMinorLocator, FuncFormatter
from matplotlib.colors import Normalize
from matplotlib.patches import Polygon as MplPolygon, FancyArrow, Patch
from matplotlib.collections import PatchCollection
from matplotlib.lines import Line2D
import shapefile
from shapely.geometry import shape, box, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))

# Figure 12's longitudes; north edge extended to 41.50 so the 22 neighbourhoods
# above 41.30 N are not clipped.
W, E, S, N = 27.80, 30.00, 40.55, 41.50

# ---- Nimbus Sans; DejaVu Sans is forbidden by the house style --------------
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

# Rule 2: two content weights, structural ink below both.
# LW_MAIN  cluster / top-decile boundary (the emphasised element)
# LW_SERIES amplification contours, if the overlay is reinstated
LW_MAIN, LW_SERIES, LW_STRUCT, LW_LEAD = 1.0, 1.0, 0.8, 1.0

plt.rcParams.update({
    "font.size": 9.5, "font.family": "sans-serif",
    "font.sans-serif": ["Nimbus Sans", "Helvetica"],
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

SEA, LANDBG, COAST, NODATA = "#d8ecf5", "#f2f2f0", "#3a3a3a", "#cfcfcf"


def need(path, what):
    if not os.path.exists(path):
        raise SystemExit(f"ERROR: {os.path.basename(path)} missing - {what}.")
    return path


# ---- data ------------------------------------------------------------------
dmg = pd.read_csv(need(os.path.join(HERE, "mahalle_inventory_scenario_joined.csv"),
                       "İBB inventory joined to scenario damage"))
xy = pd.read_csv(need(os.path.join(HERE, "mahalle_with_coords.csv"),
                      "neighbourhood centroids"))
tab = xy.merge(dmg[["mahalle_uavt", "n_bldg", "heavy", "heavy_ratio"]],
               on="mahalle_uavt", how="left")

gj = json.load(open(need(os.path.join(HERE, "mahalle_fixed.geojson"),
                         "neighbourhood polygons")))
polys = [shape(f["geometry"]) for f in gj["features"]]

tree = STRtree(polys)
val = np.full(len(polys), np.nan)
for lon_, lat_, r in zip(tab.lon, tab.lat, tab.heavy_ratio):
    if not (np.isfinite(lon_) and np.isfinite(lat_) and np.isfinite(r)):
        continue
    p = Point(lon_, lat_)
    for i in tree.query(p):
        if polys[i].contains(p):
            val[i] = r if not np.isfinite(val[i]) else max(val[i], r)
            break
n_mapped = int(np.isfinite(val).sum())

NE = need(os.path.join(HERE, "ne_10m_land.shp"),
          "Natural Earth land; get ne_10m_land.{shp,shx,dbf} from "
          "github.com/nvkelso/natural-earth-vector/tree/master/10m_physical")
sf = shapefile.Reader(NE)
win = box(W, S, E, N)
land = unary_union([shape(sr.shape.__geo_interface__).intersection(win)
                    for sr in sf.shapeRecords()
                    if shape(sr.shape.__geo_interface__).intersects(win)])
land_parts = land.geoms if land.geom_type == "MultiPolygon" else [land]

# ---- figure ----------------------------------------------------------------
# Panel (a) damage, panel (b) the site-amplification field, on an identical
# window so the two can be read against each other directly.
import xarray as xr
ampda = xr.open_dataarray(need(os.path.join(HERE, "amp_panel.nc"),
                               "amplification field on this window"))
ALON = ampda[ampda.dims[1]].values
ALAT = ampda[ampda.dims[0]].values
AMP = ampda.values

fig, (ax, axb) = plt.subplots(2, 1, figsize=(8.4, 9.4))
for a_ in (ax, axb):
    a_.set_facecolor(SEA)
    a_.set_xlim(W, E); a_.set_ylim(S, N)
    a_.set_aspect(1 / np.cos(np.deg2rad(0.5 * (S + N))))

for poly in land_parts:
    ax.add_patch(MplPolygon(np.asarray(poly.exterior.coords), closed=True,
                            fc=LANDBG, ec="none", zorder=1))

norm = Normalize(0.0, float(np.nanmax(val)))
# Colour scales. Different variables, so different ramps by design; the same
# variable must never be split across two ramps (see Figure 12, which shares
# panel (b)'s quantity).
#   batlow  sequential, lightness monotonic L* 12-87 -- ordered damage ratio
#   roma    diverging, light centre. Legitimate here only because the scale
#           spans F = 0.94-1.66, whose midpoint is 1.299: the pale centre lands
#           on F = 1.3, the rock/intermediate class boundary of the Results and
#           the level contoured below. Rescale the limits and that coincidence
#           is lost, at which point roma should be replaced by a sequential map.
try:                       # optional: only needed for the Crameri names
    import cmcrameri.cm as cmc
    CM = {"batlow": cmc.batlow, "roma": cmc.roma, "vik": cmc.vik,
          "lipari": cmc.lipari, "oslo": cmc.oslo}
except ImportError:
    CM = {}
_get = lambda n: CM.get(n) or plt.get_cmap(n)
CMAP_A = os.environ.get("CMAP_A", "turbo")       # panel (a): damage ratio
CMAP_B = os.environ.get("CMAP_B", "gist_ncar")   # panel (b): amplification
cmap = _get(CMAP_A)


def parts(g):
    return g.geoms if g.geom_type == "MultiPolygon" else [g]


shown, cols, blank = [], [], []
for g_, v in zip(polys, val):
    for part in parts(g_):
        poly = MplPolygon(np.asarray(part.exterior.coords), closed=True)
        if np.isfinite(v):
            shown.append(poly); cols.append(cmap(norm(v)))
        else:
            blank.append(poly)
ax.add_collection(PatchCollection(blank, facecolor=NODATA, edgecolor="white",
                                  linewidths=0.25, zorder=2))
ax.add_collection(PatchCollection(shown, facecolor=cols, edgecolor="white",
                                  linewidths=0.25, zorder=3))

thr = float(np.nanpercentile(val, 90))
top_union = unary_union([g_ for g_, v in zip(polys, val)
                         if np.isfinite(v) and v >= thr])
for part in parts(top_union):
    ax.plot(*np.asarray(part.exterior.coords).T, color="black",
            lw=LW_MAIN, solid_joinstyle="round", zorder=4)

for poly in land_parts:
    ax.plot(*np.asarray(poly.exterior.coords).T, color=COAST, lw=LW_STRUCT, zorder=5)
    for ring in poly.interiors:
        ax.plot(*np.asarray(ring.coords).T, color=COAST, lw=LW_STRUCT, zorder=5)

# ---- named districts and water ---------------------------------------------
DISTRICTS = {"Esenyurt": (28.673, 41.029), "Avc\u0131lar": (28.721, 40.979),
             "K\u00fc\u00e7\u00fck\u00e7ekmece": (28.780, 40.997),
             "Bak\u0131rk\u00f6y": (28.872, 40.981), "Zeytinburnu": (28.905, 40.992)}
LABELPOS = {"Esenyurt": (28.290, 41.190, "right"), "Avc\u0131lar": (28.290, 41.100, "right"),
            "K\u00fc\u00e7\u00fck\u00e7ekmece": (28.520, 41.300, "center"),
            "Bak\u0131rk\u00f6y": (28.930, 40.830, "center"),
            "Zeytinburnu": (29.280, 40.900, "left")}
for name, (lo_, la_) in DISTRICTS.items():
    tlo, tla, ha = LABELPOS[name]
    ax.plot([lo_, tlo], [la_, tla], color="#111111", lw=LW_LEAD, zorder=6)
    ax.plot(lo_, la_, "o", ms=4.4, mfc="#111111", mec="white", mew=0.6, zorder=7)
    ax.annotate(name, (tlo, tla), fontsize=7.3, fontweight="bold", color="#111111",
                ha=ha, va="center", zorder=8,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))

ax.text(28.45, 40.70, "Sea of Marmara", fontsize=10, style="italic",
        color="#1f6f93", ha="center", zorder=6)
ax.text(29.62, 41.22, "Black Sea", fontsize=9, style="italic",
        color="#1f6f93", ha="center", zorder=6)

# ---- frame furniture -------------------------------------------------------
for a_ in (ax, axb):
    a_.xaxis.set_major_locator(plt.MultipleLocator(0.5))
    a_.yaxis.set_major_locator(plt.MultipleLocator(0.2))
    a_.xaxis.set_minor_locator(AutoMinorLocator())
    a_.yaxis.set_minor_locator(AutoMinorLocator())
    a_.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.1f}\u00b0E"))
    a_.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.1f}\u00b0N"))
    a_.grid(which="major", lw=0.3, color="#9fb9c6", alpha=0.6, zorder=0)
    a_.tick_params(labelsize=8)

seg = 20.0 / (111.32 * np.cos(np.deg2rad(0.5 * (S + N))))
x0, y0 = W + 0.10, S + 0.07
ax.plot([x0, x0 + seg], [y0, y0], color="#111111", lw=3, solid_capstyle="butt", zorder=8)
for xx in (x0, x0 + seg):
    ax.plot([xx, xx], [y0 - 0.012, y0 + 0.012], color="#111111", lw=1, zorder=8)
ax.text(x0 + seg / 2, y0 + 0.022, "20 km", ha="center", va="bottom",
        fontsize=7.2, fontweight="bold", zorder=8)

nax, nay = W + 0.085, S + 0.30
ax.add_patch(FancyArrow(nax, nay - 0.10, 0, 0.13, width=0.0, head_width=0.045,
                        head_length=0.05, length_includes_head=True,
                        color="#111111", zorder=8))
ax.text(nax, nay + 0.055, "N", ha="center", va="bottom", fontsize=9,
        fontweight="bold", zorder=8)

# ===================== panel (b): site amplification ========================
for poly in land_parts:
    axb.add_patch(MplPolygon(np.asarray(poly.exterior.coords), closed=True,
                             fc=LANDBG, ec="none", zorder=1))
ANORM = Normalize(float(np.nanmin(AMP)), float(np.nanmax(AMP)))
imb = axb.pcolormesh(ALON, ALAT, AMP, cmap=_get(CMAP_B), norm=ANORM,
                     shading="auto", zorder=2, rasterized=True)
# Contours at 1.1, 1.3 and 1.5. Smoothing is reduced from sigma = 2.0 to 0.5
# cells (about 250 m) because the heavier smoothing capped the field at 1.43 and
# erased the 1.5 level entirely. At sigma = 0.5 the levels enclose 90.7%, 25.7%
# and 0.3% of land respectively: 1.1 traces little more than the coast and 1.5
# survives only as a few isolated patches, so 1.3 is the one that divides the
# field and is the only level labelled inline.
from scipy.ndimage import gaussian_filter
_f = np.where(np.isfinite(AMP), AMP, np.nanmean(AMP))
_sm = gaussian_filter(_f, 0.5)
LEVELS = [1.1, 1.3, 1.5]
csb = axb.contour(ALON, ALAT, _sm, levels=LEVELS, colors="black",
                  linewidths=[LW_SERIES * 0.8, LW_SERIES, LW_SERIES * 0.8],
                  zorder=4)
# Label only a few selected segments per level. clabel by default annotates
# every segment, which on this fragmented field repeats "1.3" dozens of times.
# allsegs gives the polylines per level directly (matplotlib >= 3.8 no longer
# exposes .collections); the longest well-separated ones are labelled.
WANT = {1.1: 3, 1.3: 5, 1.5: 1}
spots = []
for lv, segs in zip(csb.levels, csb.allsegs):
    chosen = []
    for seg in sorted((x for x in segs if len(x) > 15), key=len, reverse=True):
        m = seg[len(seg) // 2]
        if all(np.hypot(m[0] - c[0], m[1] - c[1]) > 0.30 for c in chosen + spots):
            chosen.append(m)
        if len(chosen) == WANT.get(round(lv, 1), 1):
            break
    spots += chosen
if spots:
    lab = axb.clabel(csb, fmt="%.1f", fontsize=7.0, inline=True,
                     inline_spacing=3, manual=spots)
    for t in lab:
        t.set_path_effects([pe.withStroke(linewidth=2.0, foreground="white", alpha=0.95)])
print(f"contour labels placed: {len(spots)}")

for poly in land_parts:
    axb.plot(*np.asarray(poly.exterior.coords).T, color=COAST, lw=LW_STRUCT, zorder=5)
    for ring in poly.interiors:
        axb.plot(*np.asarray(ring.coords).T, color=COAST, lw=LW_STRUCT, zorder=5)
for name, (lo_, la_) in DISTRICTS.items():
    axb.plot(lo_, la_, "o", ms=3.6, mfc="#111111", mec="white", mew=0.6, zorder=7)
axb.text(28.45, 40.70, "Sea of Marmara", fontsize=10, style="italic",
         color="#1f6f93", ha="center", zorder=6)

cbb = fig.colorbar(imb, ax=axb, fraction=0.030, pad=0.02)
cbb.set_label("Site-amplification factor\n$F=(760/V_{s30})^{m}$", fontsize=8.5)
cbb.ax.tick_params(labelsize=7.5)
for _lv in LEVELS:
    cbb.ax.axhline(_lv, color="black",
                   lw=LW_SERIES if _lv == 1.3 else LW_SERIES * 0.8)
axb.legend([Line2D([0], [0], color="black", lw=LW_SERIES)],
           ["$F$ = 1.1, 1.3, 1.5 (250 m smoothing)"], loc="upper right", fontsize=6.8,
           framealpha=0.92, edgecolor="#cccccc").set_zorder(9)

for a_, tag in ((ax, "(a)"), (axb, "(b)")):
    a_.text(0.012, 0.975, tag, transform=a_.transAxes, fontsize=10.5,
            fontweight="bold", va="top", ha="left", zorder=10,
            bbox=dict(boxstyle="square,pad=0.18", fc="white", ec="0.4", lw=0.5))

sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap); sm.set_array([])
cb = fig.colorbar(sm, ax=ax, fraction=0.030, pad=0.02)
cb.set_label("Modelled heavy-damage ratio\n(heavy or very heavy / total stock)",
             fontsize=8.5)
cb.ax.tick_params(labelsize=7.5)
cb.ax.axhline(thr, color="black", lw=LW_MAIN)

ax.legend([Line2D([0], [0], color="black", lw=LW_MAIN),
           Patch(facecolor=NODATA, edgecolor="white")],
          [f"top decile ($\\geq$ {thr:.3f})", "no scenario data"],
          loc="upper right", fontsize=6.8, framealpha=0.92,
          edgecolor="#cccccc").set_zorder(9)

ax.set_title("Modelled heavy-damage ratio by neighbourhood, \u0130BB night-time "
             f"$M_\\mathrm{{w}}$ 7.5 Main Marmara Fault scenario "
             f"({n_mapped} of {len(tab)} mahalle)",
             fontsize=9.5, fontweight="bold", loc="left", pad=6)
axb.set_title("Site-amplification factor from the USGS hybrid $V_{s30}$ mosaic, "
              "same window", fontsize=9.5, fontweight="bold", loc="left", pad=6)

fig.tight_layout()
fig.savefig(os.path.join(HERE, "fig16_collapsemap.pdf"),
            bbox_inches="tight", pad_inches=0.02)
fig.savefig(os.path.join(HERE, "fig16_collapsemap.png"), dpi=600,
            bbox_inches="tight", pad_inches=0.02)

v = val[np.isfinite(val)]
print(f"mapped {n_mapped}/{len(tab)} mahalle | ratio {v.min():.4f}-{v.max():.4f} "
      f"mean {v.mean():.4f} | top-decile threshold {thr:.4f}")
print(f"stock-weighted heavy ratio {dmg.heavy.sum()/dmg.n_bldg.sum():.4f} "
      f"({dmg.heavy.sum():,} of {dmg.n_bldg.sum():,} buildings)")
