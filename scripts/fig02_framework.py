#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fig02_framework -- Research-framework schematic.
Lemenkova & Zulfikar, Sea of Marmara seismic-response study.

Font: apt-get install fonts-urw-base35 / brew install --cask font-urw-base35
Usage: python3 fig02_framework.py [outdir]
"""
import glob
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, findfont, fontManager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

# --------------------------------------------------------------------------- #
# Font                                                                         #
# --------------------------------------------------------------------------- #
URW = ("/usr/share/fonts/opentype/urw-base35", "/usr/share/fonts/type1/urw-base35",
       "/usr/local/share/fonts/urw-base35", "/opt/homebrew/share/fonts",
       "/Library/Fonts")
for d in URW:
    for f in glob.glob(os.path.join(d, "NimbusSans-*.otf")):
        try:
            fontManager.addfont(f)
        except Exception:
            pass
if not ({"Nimbus Sans", "Helvetica"} & {f.name for f in fontManager.ttflist}):
    raise RuntimeError("Nimbus Sans not found; install fonts-urw-base35. "
                       "DejaVu Sans is forbidden by the house style.")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Nimbus Sans", "Helvetica"],      # never DejaVu
    "mathtext.fontset": "custom",
    "mathtext.rm": "Nimbus Sans", "mathtext.it": "Nimbus Sans:italic",
    "mathtext.bf": "Nimbus Sans:bold", "mathtext.sf": "Nimbus Sans",
    "mathtext.cal": "Nimbus Sans:italic", "mathtext.tt": "Nimbus Sans",
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
})
_fp = FontProperties(); _fp.set_family("sans-serif")
RESOLVED = findfont(_fp)
if "DejaVu" in RESOLVED:
    raise RuntimeError("resolved to %s: DejaVu Sans is forbidden." % RESOLVED)

# --------------------------------------------------------------------------- #
# Sizes and colours                                                            #
# --------------------------------------------------------------------------- #
FS_TITLE, FS_HEAD, FS_ITEM = 11.0, 9.0, 8.0

C = {"lim_dark": "#B4504A", "lim_tint": "#F3DFDC", "lim_panel": "#FBF1F0",
     "gmt_dark": "#2C6E9B", "gmt_tint": "#DCE9F2",
     "ml_dark": "#1F7A5C", "ml_tint": "#DBEEE5",
     "slate": "#33455E", "s2_panel": "#F1F4F7",
     "amb_dark": "#C58A1A", "amb_tint": "#F6EAD0", "amb_panel": "#FBF6EA",
     "ink": "#222222", "arrow": "#4A4A4A", "panel_edge": "#D8D8D8"}

CM = 1 / 2.54
FIG_W_IN, FIG_H_IN = 17.5 * CM, 11.2 * CM     # journal double-column width
XMAX = 132.0
YMAX = XMAX * FIG_H_IN / FIG_W_IN

fig = plt.figure(figsize=(FIG_W_IN, FIG_H_IN))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, XMAX); ax.set_ylim(0, YMAX)
ax.set_aspect("equal"); ax.axis("off")
fig.canvas.draw()
REND = fig.canvas.get_renderer()

CHECKS = []          # (Text, x_left, x_right) verified after rendering


def box(x0, y0, x1, y1, *, fc, ec, lw=1.0, rounding=1.3, z=2):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0,
                 boxstyle="round,pad=0,rounding_size=%s" % rounding,
                 linewidth=lw, edgecolor=ec, facecolor=fc, zorder=z,
                 mutation_aspect=1.0))


def label(x, y, s, *, color=C["ink"], size=FS_ITEM, weight="normal",
          z=5, style="normal"):
    return ax.text(x, y, s, color=color, fontsize=size, fontweight=weight,
                   ha="center", va="center", zorder=z, fontstyle=style,
                   linespacing=1.30)


def header(x0, x1, yc, s, *, fc):
    box(x0, yc - 3.4, x1, yc + 3.4, fc=fc, ec=fc, lw=0, rounding=1.3, z=3)
    t = label((x0 + x1) / 2, yc, s, color="white", size=FS_HEAD, weight="bold", z=6)
    CHECKS.append((t, x0, x1))          # headers are checked too


def item(x0, x1, yc, s, *, tint, edge, h=5.9):
    box(x0, yc - h, x1, yc + h, fc=tint, ec=edge, lw=0.9, rounding=1.1, z=2)
    t = label((x0 + x1) / 2, yc, s, size=FS_ITEM)
    CHECKS.append((t, x0, x1))


def big_arrow(x0, x1, yc):
    ax.add_patch(FancyArrowPatch((x0, yc), (x1, yc),
                 arrowstyle="simple,head_length=3.2,head_width=5.0,tail_width=2.0",
                 color=C["arrow"], lw=0, zorder=6, mutation_scale=1.0))


def thin_arrow(x0, y0, x1, y1, color=C["arrow"], lw=1.1, rad=0.0):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                 mutation_scale=9, color=color, lw=lw,
                 connectionstyle="arc3,rad=%s" % rad, zorder=4,
                 shrinkA=0, shrinkB=0))


# --------------------------------------------------------------------------- #
# Layout                                                                       #
# --------------------------------------------------------------------------- #
# Panel spans chosen so that the inter-stage gaps are ~10 units wide,
# which is what the connector labels need to sit clear of the panels.
C1, C2, C3 = (1.9, 30.9), (45.0, 87.0), (101.1, 130.1)
HDR_Y = YMAX - 12.0
PANEL_TOP, PANEL_BOT = YMAX - 6.5, 2.5

for (x0, x1), pf in ((C1, C["lim_panel"]), (C2, C["s2_panel"]), (C3, C["amb_panel"])):
    box(x0 - 1.4, PANEL_BOT, x1 + 1.4, PANEL_TOP, fc=pf, ec=C["panel_edge"],
        lw=0.9, rounding=2.0, z=1)

label(XMAX / 2, YMAX - 3.0,
      "Research framework: coupling GMT geophysical mapping with supervised\n"
      "machine learning for seismic-risk screening of Istanbul",
      size=FS_TITLE, weight="bold", color=C["slate"])

# ---- stage 1 ----
header(*C1, HDR_Y, "1  \u00b7  Current limitations", fc=C["lim_dark"])
label((C1[0] + C1[1]) / 2, HDR_Y - 7.0, "The research gap",
      size=FS_ITEM, weight="bold", color=C["lim_dark"], style="italic")
lim_items = ["Seismic source\nassessed in isolation\nfrom site and\nstructural response",
             "Site amplification\nand structural\nvulnerability treated\nseparately",
             "Hazard mapping\ndecoupled from data-\ndriven classification",
             "Script-based Marmara\nmapping rarely\ncoupled with\nmachine learning"]
y = HDR_Y - 16.5
for s in lim_items:
    item(C1[0] + 1.5, C1[1] - 1.5, y, s, tint=C["lim_tint"], edge=C["lim_dark"])
    y -= 13.6

# ---- stage 2 ----
header(*C2, HDR_Y, "2  \u00b7  Proposed GMT + ML framework", fc=C["slate"])
xL0, xL1, xR0, xR1 = 46.0, 65.4, 66.6, 86.0
label((xL0 + xL1) / 2, HDR_Y - 7.4, "GMT geophysical\nmapping",
      size=FS_ITEM, weight="bold", color=C["gmt_dark"])
label((xR0 + xR1) / 2, HDR_Y - 7.4, "Python supervised\nlearning",
      size=FS_ITEM, weight="bold", color=C["ml_dark"])
gmt_items = ["Earthquake\ncatalogue &\nfocal mechanisms",
             "Topography\u2013\nbathymetry,\n$V_{s30}$ classes",
             "Reproducible\ncommand-line\nmaps"]
ml_items = ["Site & structural\ndescriptors",
            "Resist vs. collapse\nclassifier\n(tree ensemble)",
            "Predicted ground-\nshaking level"]
y = HDR_Y - 17.5
for sg, sm in zip(gmt_items, ml_items):
    item(xL0, xL1, y, sg, tint=C["gmt_tint"], edge=C["gmt_dark"])
    item(xR0, xR1, y, sm, tint=C["ml_tint"], edge=C["ml_dark"])
    last_y = y - 5.9
    y -= 13.6
for sx0, sx1 in ((xL0, xL1), (xR0, xR1)):
    xc = (sx0 + sx1) / 2
    for ya in (HDR_Y - 23.4, HDR_Y - 37.0):
        thin_arrow(xc, ya, xc, ya - 2.8)
int_y0, int_y1 = 3.5, 12.5
box(xL0, int_y0, xR1, int_y1, fc=C["slate"], ec=C["slate"], lw=0, rounding=1.4, z=3)
_t2 = label((xL0 + xR1) / 2, (int_y0 + int_y1) / 2,
            "Integrated, reproducible screening of\nIstanbul soils and buildings",
            color="white", size=FS_ITEM, weight="bold", z=6)
CHECKS.append((_t2, xL0, xR1))
thin_arrow((xL0 + xL1) / 2, last_y - 0.3, (xL0 + xL1) / 2 + 4.0, int_y1 + 0.2,
           color=C["gmt_dark"], lw=1.2, rad=-0.18)
thin_arrow((xR0 + xR1) / 2, last_y - 0.3, (xR0 + xR1) / 2 - 4.0, int_y1 + 0.2,
           color=C["ml_dark"], lw=1.2, rad=0.18)

# ---- stage 3 ----
header(*C3, HDR_Y, "3  \u00b7  Contributions", fc=C["amb_dark"])
con_items = ["(i) Reproducible GMT\nmapping of seismicity\nand physiography\nframing the demand",
             "(ii) Workflow that\nseparates resistance\nfrom collapse and\npredicts shaking",
             "(iii) Interpretation\nvia site-response and\nstructural dynamics"]
y = HDR_Y - 16.5
for s in con_items:
    item(C3[0] + 1.5, C3[1] - 1.5, y, s, tint=C["amb_tint"], edge=C["amb_dark"])
    y -= 13.6
box(C3[0] + 1.5, int_y0, C3[1] - 1.5, int_y1, fc=C["ml_dark"], ec=C["ml_dark"],
    lw=0, rounding=1.4, z=3)
_t3 = label((C3[0] + C3[1]) / 2, (int_y0 + int_y1) / 2,
            "Reproducible screening\nfor fault-proximal\nmegacities",
            color="white", size=FS_ITEM, weight="bold", z=6)
CHECKS.append((_t3, C3[0] + 1.5, C3[1] - 1.5))

# ---- inter-stage arrows ----
# The inter-stage arrow and its caption are derived from the gap between the
# panel outlines, not hardcoded, so both stay centred if the panels move.
PANEL_PAD = 1.4                       # panels are drawn at C +/- PANEL_PAD
GAPS = [((C1[1] + PANEL_PAD), (C2[0] - PANEL_PAD), "addressed\nby"),
        ((C2[1] + PANEL_PAD), (C3[0] - PANEL_PAD), "delivers")]
mid = (int_y1 + HDR_Y - 16.5) / 2

for gx0, gx1, caption in GAPS:
    xc = (gx0 + gx1) / 2.0            # centre of the empty space
    half = (gx1 - gx0) * 0.32         # arrow spans ~64 % of the gap
    big_arrow(xc - half, xc + half, mid)
    t = label(xc, mid + 7.4, caption, size=FS_ITEM, style="italic",
              color=C["arrow"])
    CHECKS.append((t, gx0, gx1))      # the caption must fit the gap too

# --------------------------------------------------------------------------- #
# Rule 1 check: every item label must sit inside its box                       #
# --------------------------------------------------------------------------- #
fig.canvas.draw()
REND = fig.canvas.get_renderer()
bad = []
for t, x0, x1 in CHECKS:
    bb = t.get_window_extent(renderer=REND)
    a = ax.transData.transform((x0 + 0.6, 0))[0]
    b = ax.transData.transform((x1 - 0.6, 0))[0]
    if bb.x0 < a - 0.5 or bb.x1 > b + 0.5:
        bad.append((t.get_text().split("\n")[0], (bb.x1 - b) / (b - a) * 100))
if bad:
    for line, over in bad:
        print("  OVERFLOW: %-32s %+.1f%% past its box" % (line, over))
    raise SystemExit("rule 1 violated: %d label(s) overflow; shorten the wrap."
                     % len(bad))
print("rule 1 check: all %d item labels inside their boxes" % len(CHECKS))

# --------------------------------------------------------------------------- #
# Export                                                                       #
# --------------------------------------------------------------------------- #
outdir = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(outdir, exist_ok=True)
stem = os.path.join(outdir, "fig02_framework")
fig.savefig(stem + ".pdf", bbox_inches="tight", pad_inches=0.04,
            facecolor="white")
fig.savefig(stem + ".png", dpi=600, bbox_inches="tight", pad_inches=0.04,
            facecolor="white")
try:
    from PIL import Image
    im = Image.open(stem + ".png").convert("RGBA")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bg.paste(im, mask=im.split()[3])
    bg.save(stem + ".png", dpi=(600, 600))
except ImportError:
    pass
print("wrote %s.pdf and %s.png" % (stem, stem))
print("font resolved to: %s" % RESOLVED)
