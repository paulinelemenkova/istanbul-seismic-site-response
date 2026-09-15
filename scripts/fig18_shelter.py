#!/usr/bin/env python3
# ============================================================================
import os, sys, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, FuncFormatter
from matplotlib.colors import Normalize, LogNorm
from matplotlib.patches import Polygon as MplPolygon, FancyArrow
from matplotlib.collections import PatchCollection
import shapefile
from shapely.geometry import shape, box, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

sys.path.insert(0, "/mnt/skills/user/scientific-plotting/scripts")
from cpt_tools import load_cpt

HERE = os.path.dirname(os.path.abspath(__file__))
W, E, S, N = 27.80, 30.00, 40.55, 41.50

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
LW_MAIN, LW_STRUCT, LW_LEAD = 1.0, 0.8, 1.0
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


def need(p, what):
    if not os.path.exists(p):
        raise SystemExit(f"ERROR: {os.path.basename(p)} missing - {what}.")
    return p


CPT_A = os.environ.get("CPT_A", "indigo-orange.cpt")  # also supplied: gold, gem-256, cmy
REVERSE_A = os.environ.get("REVERSE_A", "1") == "1"
CMAP_A = load_cpt(need(os.path.join(HERE, CPT_A), "cpt-city palette for panel (a)"),
                  name=CPT_A[:-4])
if REVERSE_A:
    CMAP_A = CMAP_A.reversed()
CPT_B = os.environ.get("CPT_B", "aquamarinemermaid.cpt")  # also: girlcat, autumnrose
REVERSE_B = os.environ.get("REVERSE_B", "0") == "1"   # purple low, gold high
# CLIP_B takes a sub-range of the ramp. rc/aquamarinemermaid is symmetric: both
# ends are the same dark purple (102,42,112), so used whole it would give the
# smallest and largest neighbourhoods identical colours. Only that dark purple
# is trimmed (0.12-0.82), keeping rose, gold and blue: the ends become
# (137,68,123) and (75,104,185), distinct in hue. The clipped ramp is still
# DIVERGING, L* 40-81 with its light centre on gold, so the two ends match in
# lightness and separate by hue alone - see the note on panel (b) below.
CLIP_B = tuple(float(x) for x in os.environ.get("CLIP_B", "0.12,0.82").split(","))
from matplotlib.colors import LinearSegmentedColormap
_raw = load_cpt(need(os.path.join(HERE, CPT_B), "cpt-city palette for panel (b)"),
                name=CPT_B[:-4])
CMAP_B = (LinearSegmentedColormap.from_list(CPT_B[:-4] + "_clip",
          _raw(np.linspace(CLIP_B[0], CLIP_B[1], 256)))
          if CLIP_B != (0.0, 1.0) else _raw)
if REVERSE_B:
    CMAP_B = CMAP_B.reversed()

# ---- data ------------------------------------------------------------------
dmg = pd.read_csv(need(os.path.join(HERE, "mahalle_inventory_scenario_joined.csv"),
                       "İBB inventory joined to scenario damage"))
xy = pd.read_csv(need(os.path.join(HERE, "mahalle_with_coords.csv"), "centroids"))
tab = xy.merge(dmg[["mahalle_uavt", "n_bldg", "heavy", "heavy_ratio",
                    "gecici_barinma"]], on="mahalle_uavt", how="left")
if "area_km2" not in tab.columns:                       # fall back to the vs30 table
    ar = pd.read_csv(need(os.path.join(HERE, "mahalle_vs30.csv"),
                          "neighbourhood areas"))[["mahalle_uavt", "area_km2"]]
    tab = tab.merge(ar, on="mahalle_uavt", how="left")
tab["shelter_km2"] = tab.gecici_barinma / tab.area_km2

# ---- geometry and spatial join --------------------------------------------
gj = json.load(open(need(os.path.join(HERE, "mahalle_fixed.geojson"), "polygons")))
polys = [shape(f["geometry"]) for f in gj["features"]]
tree = STRtree(polys)
shel = np.full(len(polys), np.nan)
for lon_, lat_, v in zip(tab.lon, tab.lat, tab.shelter_km2):
    if not (np.isfinite(lon_) and np.isfinite(lat_) and np.isfinite(v)):
        continue
    p = Point(lon_, lat_)
    for i in tree.query(p):
        if polys[i].contains(p):
            shel[i] = v
            break
n_mapped = int(np.isfinite(shel).sum())

NE = need(os.path.join(HERE, "ne_10m_land.shp"), "Natural Earth land")
sf = shapefile.Reader(NE)
land = unary_union([shape(sr.shape.__geo_interface__).intersection(box(W, S, E, N))
                    for sr in sf.shapeRecords()
                    if shape(sr.shape.__geo_interface__).intersects(box(W, S, E, N))])
land_parts = land.geoms if land.geom_type == "MultiPolygon" else [land]


def parts(g):
    return g.geoms if g.geom_type == "MultiPolygon" else [g]


fig, (ax, axb) = plt.subplots(2, 1, figsize=(8.4, 9.0))

# ===================== panel (a): shelter demand ============================
ax.set_facecolor(SEA)
ax.set_xlim(W, E); ax.set_ylim(S, N)
ax.set_aspect(1 / np.cos(np.deg2rad(0.5 * (S + N))))
for poly in land_parts:
    ax.add_patch(MplPolygon(np.asarray(poly.exterior.coords), closed=True,
                            fc=LANDBG, ec="none", zorder=1))
# Shelter density spans four orders of magnitude (p25 = 43, median 409,
# p95 = 5005, maximum 18,889 per km2), so a linear scale collapses the map into
# one colour. A logarithmic scale is used, bounded at the 25th and 95th
# percentiles rather than at the extremes: scaling to the full range left 28%
# of neighbourhoods inside the ramp's near-black lower quarter and the map read
# as a dark mass. Values outside the bounds take the end colours, marked by the
# arrows on the bar.
SLO, SHI = (float(np.nanpercentile(shel, 25)), float(np.nanpercentile(shel, 95)))
snorm = LogNorm(SLO, SHI)
shown, cols, blank = [], [], []
for g_, v in zip(polys, shel):
    for part in parts(g_):
        pg = MplPolygon(np.asarray(part.exterior.coords), closed=True)
        if np.isfinite(v):
            shown.append(pg); cols.append(CMAP_A(float(np.clip(snorm(max(v, SLO)), 0, 1))))
        else:
            blank.append(pg)
ax.add_collection(PatchCollection(blank, facecolor=NODATA, edgecolor="white",
                                  linewidths=0.25, zorder=2))
ax.add_collection(PatchCollection(shown, facecolor=cols, edgecolor="white",
                                  linewidths=0.25, zorder=3))
for poly in land_parts:
    ax.plot(*np.asarray(poly.exterior.coords).T, color=COAST, lw=LW_STRUCT, zorder=5)
    for ring in poly.interiors:
        ax.plot(*np.asarray(ring.coords).T, color=COAST, lw=LW_STRUCT, zorder=5)
ax.text(28.98, 40.700, "Sea of Marmara", fontsize=10, style="italic",
        color="#1f6f93", ha="center", zorder=6)
ax.text(29.62, 41.28, "Black Sea", fontsize=9, style="italic",
        color="#1f6f93", ha="center", zorder=6)
ax.xaxis.set_major_locator(plt.MultipleLocator(0.5))
ax.yaxis.set_major_locator(plt.MultipleLocator(0.2))
ax.xaxis.set_minor_locator(AutoMinorLocator())
ax.yaxis.set_minor_locator(AutoMinorLocator())
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.1f}\u00b0E"))
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f"{v:.1f}\u00b0N"))
ax.grid(which="major", lw=0.3, color="#9fb9c6", alpha=0.6, zorder=0)
ax.tick_params(labelsize=8)
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
sm = plt.cm.ScalarMappable(norm=snorm, cmap=CMAP_A); sm.set_array([])
cba = fig.colorbar(sm, ax=ax, fraction=0.030, pad=0.02, extend="both")
cba.set_label("Temporary-shelter demand\n(people per km$^2$, logarithmic)", fontsize=8.5)
cba.ax.tick_params(labelsize=7.5)
ax.set_title(f"Modelled temporary-shelter demand, \u0130BB $M_\\mathrm{{w}}$ 7.5 "
             f"scenario: {int(tab.gecici_barinma.sum()):,} people over "
             f"{n_mapped} of {len(tab)} mahalle",
             fontsize=9.5, fontweight="bold", loc="left", pad=6)

# ===================== panel (b): ratio against count =======================
ok = np.isfinite(tab.heavy) & np.isfinite(tab.heavy_ratio) & (tab.n_bldg > 0)
t = tab[ok]
sc = axb.scatter(t.heavy, 100 * t.heavy_ratio, c=t.n_bldg, cmap=CMAP_B,
                 norm=LogNorm(t.n_bldg.min(), t.n_bldg.max()),
                 s=16, lw=0.25, edgecolor="#333333", zorder=3)
# top ten by each measure: the disagreement between the two rankings
c10 = set(t.nlargest(10, "heavy").index)
r10 = set(t.nlargest(10, "heavy_ratio").index)
for idx, mk, lab in ((c10 - r10, "s", "top 10 by count only"),
                     (r10 - c10, "^", "top 10 by ratio only"),
                     (c10 & r10, "o", "top 10 by both")):
    q = t.loc[sorted(idx)]
    axb.scatter(q.heavy, 100 * q.heavy_ratio, marker=mk, s=64, facecolor="none",
                edgecolor="black", lw=LW_MAIN, zorder=4, label=f"{lab} ({len(q)})")
axb.set_xscale("log")
axb.set_xlabel("Heavily or very heavily damaged buildings per neighbourhood (count)")
axb.set_ylabel("Heavy-damage ratio (per cent of stock)")
axb.xaxis.set_minor_locator(AutoMinorLocator())
axb.yaxis.set_minor_locator(AutoMinorLocator())
axb.tick_params(which="both", direction="in", top=True, right=True, labelsize=8)
axb.grid(which="major", lw=0.5, color="0.85")
axb.set_axisbelow(True)
rho = t.heavy.corr(t.heavy_ratio, method="spearman")
axb.legend(loc="upper left", bbox_to_anchor=(0.008, 0.918), fontsize=7.2,
           framealpha=0.92, edgecolor="#cccccc",
           title=f"Spearman $\\rho$ = {rho:.2f}", title_fontsize=7.4)
cbb = fig.colorbar(sc, ax=axb, fraction=0.030, pad=0.02)
cbb.set_label("Total building stock\nper neighbourhood (logarithmic)", fontsize=8.5)
cbb.ax.tick_params(labelsize=7.5)
axb.set_title("Count-based against rate-based prioritisation: the two orderings "
              "agree broadly and diverge at the margin",
              fontsize=9.5, fontweight="bold", loc="left", pad=6)

for a_, tag in ((ax, "(a)"), (axb, "(b)")):
    a_.text(0.012, 0.975, tag, transform=a_.transAxes, fontsize=10.5,
            fontweight="bold", va="top", ha="left", zorder=10,
            bbox=dict(boxstyle="square,pad=0.18", fc="white", ec="0.4", lw=0.5))

# Panel (a) carries a fixed geographic aspect, so matplotlib shrinks its axes
# and the free scatter of (b) would otherwise be wider. Align (b) to (a) after
# the first draw.
fig.canvas.draw()
pa, pb = ax.get_position(), axb.get_position()
axb.set_position([pa.x0, pb.y0, pa.width, pb.height])
cba_pos, cbb_pos = cba.ax.get_position(), cbb.ax.get_position()
cbb.ax.set_position([cba_pos.x0, cbb_pos.y0, cba_pos.width, cbb_pos.height])

fig.savefig(os.path.join(HERE, "fig18_shelter.pdf"), bbox_inches="tight", pad_inches=0.02)
fig.savefig(os.path.join(HERE, "fig18_shelter.png"), dpi=600,
            bbox_inches="tight", pad_inches=0.02)
v = shel[np.isfinite(shel)]
print(f"mapped {n_mapped}/{len(tab)} mahalle | shelter/km2 {v.min():.0f}-{v.max():.0f} "
      f"median {np.median(v):.0f} | log scale spans {SLO:.0f}-{SHI:.0f} (p25-p95)")
print(f"Spearman(count, ratio) = {rho:.3f} | top-10 overlap {len(c10 & r10)}/10")
