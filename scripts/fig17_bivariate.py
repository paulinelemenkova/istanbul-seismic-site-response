#!/usr/bin/env python3
# ============================================================================
# fig17_bivariate — modelled heavy-damage ratio AGAINST pre-1980 building share
#                   by neighbourhood (959 mahalle), Istanbul
# ----------------------------------------------------------------------------
# WHY THIS FIGURE
#
# The manuscript states that construction age alone explains little of the
# modelled damage (r = 0.38 across the 959 neighbourhoods) and that Beylikdüzü
# and Büyükçekmece reach high damage ratios with almost no pre-code stock. Those
# are claims about the JOINT distribution of two variables, which no single-
# variable choropleth can show. In the top damage DECILE the split is stark:
# 34 neighbourhoods have mostly pre-1980 stock (>70%), 32 of them in Fatih,
# while 22 have almost none (<30%) - Küçükçekmece 7, Beylikdüzü 3, Tuzla 3,
# Bahçelievler 2. An old-stock historic core and a new-stock western periphery
# reach comparable damage ratios by different routes. The map classifies by
# TERCILES rather than deciles so that every neighbourhood is placed; in the top
# damage tercile the corresponding counts are 43 and 177.
#
# CLASSIFICATION. Both variables are cut at their terciles, giving a 3x3 scheme.
# Breaks: damage ratio 0.0133 / 0.0429; pre-1980 share 0.045 / 0.340.
#
# COLOUR. nipy_spectral, as requested. cpt_tools.assess reports it "unsuitable"
# for encoding a continuous variable - lightness runs L* 0-93 with six
# reversals - but that objection applies to a continuous ramp. Here it is used
# CATEGORICALLY: nine well-separated samples for nine discrete classes, decoded
# through the 3x3 key rather than by reading a gradient. The residual cost is
# that a 1-D ramp cannot make the two axes separately readable, so the key does
# all the decoding work; BIVAR=classic switches to a conventional two-dimensional
# palette in which hue carries damage and saturation carries age.
#
# INPUT: mahalle_inventory_scenario_joined.csv, mahalle_with_coords.csv,
#        mahalle_fixed.geojson, ne_10m_land.{shp,shx,dbf}
# PANEL (b) LIFELINE DAMAGE. The İBB scenario reports pipe damage for three
# networks separately: gas (356 breaks), potable water (461) and wastewater
# (1042), 1859 in total. They are NOT mapped as three panels because they are
# nearly the same field - pairwise correlations across the 959 neighbourhoods
# are 0.84 (gas-water), 0.80 (gas-wastewater) and 0.83 (water-wastewater) - so
# three panels would repeat one pattern three times. The combined count is
# mapped instead and the three totals are given in the caption.
#
# Output: fig17_bivariate.pdf / .png
# ============================================================================
import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator, FuncFormatter
from matplotlib.patches import Polygon as MplPolygon, FancyArrow, Rectangle
from matplotlib.collections import PatchCollection
import shapefile
from shapely.geometry import shape, box, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

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


# ---- data ------------------------------------------------------------------
dmg = pd.read_csv(need(os.path.join(HERE, "mahalle_inventory_scenario_joined.csv"),
                       "İBB inventory joined to scenario damage"))
xy = pd.read_csv(need(os.path.join(HERE, "mahalle_with_coords.csv"), "centroids"))
dmg["pre80"] = dmg["1980_oncesi"] / dmg.n_bldg
dmg["pipes"] = (dmg.dogalgaz_boru_hasari + dmg.icme_suyu_boru_hasari
                + dmg.atik_su_boru_hasari)
tab = xy.merge(dmg[["mahalle_uavt", "n_bldg", "heavy_ratio", "pre80", "pipes",
                    "dogalgaz_boru_hasari", "icme_suyu_boru_hasari",
                    "atik_su_boru_hasari"]], on="mahalle_uavt", how="left")

qd = tab.heavy_ratio.quantile([1/3, 2/3]).values
qa = tab.pre80.quantile([1/3, 2/3]).values
tab["di"] = np.digitize(tab.heavy_ratio, qd)      # 0 low .. 2 high damage
tab["ai"] = np.digitize(tab.pre80, qa)            # 0 new .. 2 old stock

# ---- 3x3 palette -----------------------------------------------------------
SCHEME = os.environ.get("BIVAR", "nipy_spectral")
if SCHEME == "classic":
    # hue = damage, saturation = age; decodes on both axes independently
    GRID = [["#e8e8e8", "#ace4e4", "#5ac8c8"],
            ["#dfb0d6", "#a5add3", "#5698b9"],
            ["#be64ac", "#8c62aa", "#3b4994"]]
else:
    cm = plt.get_cmap(SCHEME)
    # nine evenly spaced samples, avoiding the black and white extremes
    sm = [cm(x) for x in np.linspace(0.06, 0.94, 9)]
    GRID = [[sm[0], sm[1], sm[2]], [sm[3], sm[4], sm[5]], [sm[6], sm[7], sm[8]]]

# ---- geometry and spatial join --------------------------------------------
gj = json.load(open(need(os.path.join(HERE, "mahalle_fixed.geojson"), "polygons")))
polys = [shape(f["geometry"]) for f in gj["features"]]
tree = STRtree(polys)
cls = np.full(len(polys), -1, int)
pipe = np.full(len(polys), np.nan)
for lon_, lat_, di, ai, hr, pv in zip(tab.lon, tab.lat, tab.di, tab.ai,
                                      tab.heavy_ratio, tab.pipes):
    if not (np.isfinite(lon_) and np.isfinite(lat_) and np.isfinite(hr)):
        continue
    p = Point(lon_, lat_)
    for i in tree.query(p):
        if polys[i].contains(p):
            cls[i] = int(di) * 3 + int(ai)
            pipe[i] = pv
            break
n_mapped = int((cls >= 0).sum())

NE = need(os.path.join(HERE, "ne_10m_land.shp"), "Natural Earth land")
sf = shapefile.Reader(NE)
win = box(W, S, E, N)
land = unary_union([shape(sr.shape.__geo_interface__).intersection(win)
                    for sr in sf.shapeRecords()
                    if shape(sr.shape.__geo_interface__).intersects(win)])
land_parts = land.geoms if land.geom_type == "MultiPolygon" else [land]


def parts(g):
    return g.geoms if g.geom_type == "MultiPolygon" else [g]


# ---- figure ----------------------------------------------------------------
fig, (ax, axb) = plt.subplots(2, 1, figsize=(8.4, 9.4))
for a_ in (ax, axb):
    a_.set_facecolor(SEA)
    a_.set_xlim(W, E); a_.set_ylim(S, N)
    a_.set_aspect(1 / np.cos(np.deg2rad(0.5 * (S + N))))
    for poly in land_parts:
        a_.add_patch(MplPolygon(np.asarray(poly.exterior.coords), closed=True,
                                fc=LANDBG, ec="none", zorder=1))

shown, cols, blank = [], [], []
for g_, k in zip(polys, cls):
    for part in parts(g_):
        pg = MplPolygon(np.asarray(part.exterior.coords), closed=True)
        if k >= 0:
            shown.append(pg); cols.append(GRID[k // 3][k % 3])
        else:
            blank.append(pg)
ax.add_collection(PatchCollection(blank, facecolor=NODATA, edgecolor="white",
                                  linewidths=0.25, zorder=2))
ax.add_collection(PatchCollection(shown, facecolor=cols, edgecolor="white",
                                  linewidths=0.25, zorder=3))

# outline the two contrasting populations named in the text
for kk, col in ((6, "black"), (8, "black")):
    u = unary_union([g_ for g_, k in zip(polys, cls) if k == kk])
    if not u.is_empty:
        for pp in parts(u):
            ax.plot(*np.asarray(pp.exterior.coords).T, color=col, lw=LW_MAIN, zorder=4)

for poly in land_parts:
    ax.plot(*np.asarray(poly.exterior.coords).T, color=COAST, lw=LW_STRUCT, zorder=5)
    for ring in poly.interiors:
        ax.plot(*np.asarray(ring.coords).T, color=COAST, lw=LW_STRUCT, zorder=5)

MARK = {"Fatih": (28.949, 41.010), "K\u00fc\u00e7\u00fck\u00e7ekmece": (28.780, 40.997),
        "Beylikd\u00fcz\u00fc": (28.640, 40.995), "Tuzla": (29.300, 40.826),
        "Ba\u011fc\u0131lar": (28.855, 41.039)}
LAB = {"Fatih": (29.130, 41.135, "left"),
       "K\u00fc\u00e7\u00fck\u00e7ekmece": (28.470, 41.245, "center"),
       "Beylikd\u00fcz\u00fc": (28.190, 41.115, "right"),
       "Tuzla": (29.430, 40.775, "center"),
       "Ba\u011fc\u0131lar": (28.760, 41.235, "center")}
for name, (lo_, la_) in MARK.items():
    tlo, tla, ha = LAB[name]
    ax.plot([lo_, tlo], [la_, tla], color="#111111", lw=LW_LEAD, zorder=6)
    ax.plot(lo_, la_, "o", ms=4.0, mfc="#111111", mec="white", mew=0.6, zorder=7)
    ax.annotate(name, (tlo, tla), fontsize=7.3, fontweight="bold", color="#111111",
                ha=ha, va="center", zorder=8,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))

ax.text(28.98, 40.700, "Sea of Marmara", fontsize=10, style="italic",
        color="#1f6f93", ha="center", zorder=6)
ax.text(29.62, 41.28, "Black Sea", fontsize=9, style="italic",
        color="#1f6f93", ha="center", zorder=6)

# ===================== panel (b): lifeline damage ===========================
from matplotlib.colors import Normalize
CMAP_B = os.environ.get("CMAP_B", "plasma")
pmax = float(np.nanmax(pipe))
# 38% of neighbourhoods have no breaks and the median is 1, so a linear scale
# to the maximum (25) leaves nearly the whole map in the first colour. The
# scale is cut at the 95th percentile (7 breaks) with the tail shown as an
# over-range colour, which is stated on the bar.
pcut = float(np.nanpercentile(pipe, 95))
pnorm = Normalize(0, pcut)
pcm = plt.get_cmap(CMAP_B)
pshown, pcols, pblank = [], [], []
for g_, v in zip(polys, pipe):
    for part in parts(g_):
        pg = MplPolygon(np.asarray(part.exterior.coords), closed=True)
        if np.isfinite(v):
            pshown.append(pg); pcols.append(pcm(min(pnorm(v), 1.0)))
        else:
            pblank.append(pg)
axb.add_collection(PatchCollection(pblank, facecolor=NODATA, edgecolor="white",
                                   linewidths=0.25, zorder=2))
axb.add_collection(PatchCollection(pshown, facecolor=pcols, edgecolor="white",
                                   linewidths=0.25, zorder=3))
for poly in land_parts:
    axb.plot(*np.asarray(poly.exterior.coords).T, color=COAST, lw=LW_STRUCT, zorder=5)
    for ring in poly.interiors:
        axb.plot(*np.asarray(ring.coords).T, color=COAST, lw=LW_STRUCT, zorder=5)
for name, (lo_, la_) in MARK.items():
    axb.plot(lo_, la_, "o", ms=3.4, mfc="#111111", mec="white", mew=0.6, zorder=7)
axb.text(28.98, 40.700, "Sea of Marmara", fontsize=10, style="italic",
         color="#1f6f93", ha="center", zorder=6)
psm = plt.cm.ScalarMappable(norm=pnorm, cmap=pcm); psm.set_array([])
cbb = fig.colorbar(psm, ax=axb, fraction=0.030, pad=0.02, extend="max")
cbb.set_label("Modelled pipe breaks per neighbourhood\n(gas + water + wastewater; scale cut at the 95th percentile)", fontsize=8.5)
cbb.ax.tick_params(labelsize=7.5)

for a_, tag in ((ax, "(a)"), (axb, "(b)")):
    a_.text(0.012, 0.975, tag, transform=a_.transAxes, fontsize=10.5,
            fontweight="bold", va="top", ha="left", zorder=10,
            bbox=dict(boxstyle="square,pad=0.18", fc="white", ec="0.4", lw=0.5))
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

# ---- 3x3 key ---------------------------------------------------------------
kx = fig.add_axes([0.325, 0.556, 0.086, 0.098])
kx.set_xlim(0, 3); kx.set_ylim(0, 3); kx.set_xticks([]); kx.set_yticks([])
for r_ in range(3):
    for c_ in range(3):
        kx.add_patch(Rectangle((c_, r_), 1, 1, fc=GRID[r_][c_], ec="white", lw=0.6))
for sp in kx.spines.values():
    sp.set_visible(False)
kx.set_xlabel("pre-1980 share \u2192", fontsize=6.4, labelpad=1)
kx.set_ylabel("damage ratio \u2192", fontsize=6.4, labelpad=1)
kx.text(1.5, 3.20, "class key", fontsize=6.6, fontweight="bold", ha="center")

n_old = int(((tab.di == 2) & (tab.pre80 > 0.7)).sum())
n_new = int(((tab.di == 2) & (tab.pre80 < 0.3)).sum())
ax.set_title("Modelled heavy-damage ratio against pre-1980 building share; terciles at "
             f"{qd[0]:.3f}/{qd[1]:.3f} and {qa[0]:.2f}/{qa[1]:.2f}",
             fontsize=9.5, fontweight="bold", loc="left", pad=6)
_g, _w, _s = (int(tab.dogalgaz_boru_hasari.sum()), int(tab.icme_suyu_boru_hasari.sum()),
              int(tab.atik_su_boru_hasari.sum()))
axb.set_title(f"Modelled buried-pipe damage: gas {_g}, water {_w}, wastewater {_s} "
              f"({_g+_w+_s} breaks in total)",
              fontsize=9.5, fontweight="bold", loc="left", pad=6)

fig.savefig(os.path.join(HERE, "fig17_bivariate.pdf"), bbox_inches="tight", pad_inches=0.02)
fig.savefig(os.path.join(HERE, "fig17_bivariate.png"), dpi=600,
            bbox_inches="tight", pad_inches=0.02)

print(f"mapped {n_mapped}/{len(tab)} mahalle | scheme {SCHEME}")
q9 = tab.heavy_ratio.quantile(0.9)
d_old = int(((tab.heavy_ratio > q9) & (tab.pre80 > 0.7)).sum())
d_new = int(((tab.heavy_ratio > q9) & (tab.pre80 < 0.3)).sum())
print(f"top decile:  {d_old} mahalle >70% pre-1980, {d_new} <30%")
print(f"top tercile: {n_old} mahalle >70% pre-1980, {n_new} <30%")
print("class counts (rows damage low->high, cols age new->old):")
for r_ in range(3):
    print("   ", [int(((tab.di == r_) & (tab.ai == c_)).sum()) for c_ in range(3)])
