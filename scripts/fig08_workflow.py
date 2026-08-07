#!/usr/bin/env python3
"""
fig08_workflow.py -- Figure 8 of the Istanbul soil-amplification manuscript:
the methodology workflow, from raw data through GMT dataset construction and
feature engineering to a trained resist/collapse surrogate and screening maps.

House style (scientific-plotting skill):
  * Nimbus Sans everywhere; DejaVu Sans is forbidden, and the script raises if
    matplotlib would fall back to it.
  * Built at the final double-column width (17.5 cm), not drawn large and shrunk.
  * Exactly three text sizes, all inside the mandatory 8-12 pt band:
    11 pt bold (in-figure title), 9 pt bold (stage headers), 8 pt (stage items).
  * Rule 1 (nothing readable may overlap anything else) is *verified, not
    assumed*: every item label is measured in display space after rendering and
    asserted to sit inside its own stage box.
  * Two line weights only (rule 2): the primary stage-to-stage flow is the
    emphasised path at 2.0 pt, the feedback loop is an ordinary 1.2 pt, and
    structural ink (box outlines) sits at 0.8 pt so it cannot be mistaken for
    the flow.
  * The loop caption is a direct label placed against the arc it names, not a
    detached string (rule 3).
  * Exported as vector PDF plus 600 dpi PNG, named figNN_*.

Colour: qual-mixed-12 (Statistik Stadt Zurich / Interactive Things, 2015;
cpt-city ssz/qual-mixed-12.cpt, CC BY-SA 4.0). A genuinely *qualitative* scale
of twelve colours built as six light/dark pairs -- blue, pink, red, yellow,
green, teal -- which is exactly the structure this figure needs: the dark member
of a pair fills the stage header and the light member of the same pair fills the
body beneath it, so no tint has to be synthesised. Five of the six pairs are
used; red is dropped because it is the nearest neighbour of pink (the retained
five have a minimum pairwise CIELAB separation of 29.4).

Header labels take a darkened ink of the pair's own hue rather than white: none
of the six dark members reaches 4.5:1 against white text (the best is 3.9:1), so
white would fail on every header and outright on the yellow.

Font: apt-get install fonts-urw-base35    (Debian/Ubuntu)
      brew install --cask font-urw-base35 (macOS)

Usage:  python3 fig08_workflow.py [outdir]
"""
import glob
import re
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, findfont, fontManager
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# --------------------------------------------------------------------------- #
# 1. Font: Nimbus Sans, with Helvetica as the only permitted fallback.         #
# --------------------------------------------------------------------------- #
URW_DIRS = ("/usr/share/fonts/opentype/urw-base35",
            "/usr/share/fonts/type1/urw-base35",
            "/usr/local/share/fonts/urw-base35",
            "/opt/homebrew/share/fonts", "/Library/Fonts")


def ensure_nimbus():
    """Register Nimbus Sans; raise rather than let DejaVu Sans through."""
    for d in URW_DIRS:
        for f in glob.glob(os.path.join(d, "NimbusSans-*.otf")):
            try:
                fontManager.addfont(f)
            except Exception:
                pass
    if not ({"Nimbus Sans", "Helvetica"} & {f.name for f in fontManager.ttflist}):
        raise RuntimeError("Nimbus Sans not found. Install fonts-urw-base35; "
                           "DejaVu Sans is forbidden by the house style.")


ensure_nimbus()
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Nimbus Sans", "Helvetica"],      # never DejaVu
    "mathtext.fontset": "custom",
    "mathtext.rm": "Nimbus Sans", "mathtext.it": "Nimbus Sans:italic",
    "mathtext.bf": "Nimbus Sans:bold", "mathtext.sf": "Nimbus Sans",
    "mathtext.cal": "Nimbus Sans:italic", "mathtext.tt": "Nimbus Sans",
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

_fp = FontProperties()
_fp.set_family("sans-serif")
FONT_RESOLVED = findfont(_fp)
if "DejaVu" in FONT_RESOLVED:
    raise RuntimeError("resolved to %s: DejaVu Sans is forbidden." % FONT_RESOLVED)

# --------------------------------------------------------------------------- #
# 2. Sizes: three only, all inside the 8-12 pt band.                           #
# --------------------------------------------------------------------------- #
FS_TITLE = 11.0      # level 1: in-figure title  (bold)
FS_HEAD = 9.0        # level 2: stage headers    (bold)
FS_ITEM = 8.0        # level 4: stage items, loop caption

# Rule 2: two weights for content. The stage-to-stage flow is what the figure is
# about, so it takes the emphasised weight; the feedback loop is secondary.
# Structural ink (box outlines) stays below both so it never reads as flow.
LW_MAIN, LW_SERIES, LW_STRUCT = 2.0, 1.2, 0.8

# --------------------------------------------------------------------------- #
# 2b. Palette: qual-mixed-12 (see the module docstring).                       #
# --------------------------------------------------------------------------- #
CPT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "qual-mixed-12.cpt")


def read_cpt_discrete(path):
    """Read a discrete GMT .cpt as a list of RGB triples, one per slice."""
    out = []
    for line in open(path):
        line = line.strip()
        if not line or line[0] in "#BFN":
            continue
        f = line.split()
        if len(f) >= 4:
            out.append(tuple(int(v) / 255 for v in f[1].split("/")))
    return out


def _lum(rgb):
    a = np.asarray(rgb[:3], float)
    a = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2])


def contrast(rgb, other=(1, 1, 1)):
    """WCAG contrast ratio between two colours."""
    a, b = sorted((_lum(rgb), _lum(other)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def darken_to(rgb, target=4.5, ref=(1, 1, 1)):
    """Scale a colour toward black until it clears *target* against *ref*."""
    c = np.asarray(rgb[:3], float)
    for k in np.linspace(1.0, 0.0, 128):
        if contrast(c * k, ref) >= target:
            return tuple(c * k)
    return (0.0, 0.0, 0.0)


# The twelve entries are six (light, dark) pairs; keep five, dropping red as the
# nearest neighbour of pink.
_C = read_cpt_discrete(CPT)
PAIRS = [(_C[i], _C[i + 1]) for i in range(0, 12, 2)]      # blue pink red
KEEP = [0, 1, 3, 4, 5]                                     # yellow green teal

BOD = [PAIRS[i][0] for i in KEEP]                          # light member: body
HDR = [PAIRS[i][1] for i in KEEP]                          # dark member: header
STAGE = HDR
# Outlines and bullets sit on the pale body tint, not on white, so that is the
# reference they must be measured against.
INK = [darken_to(c, 4.5, ref=BOD[i]) for i, c in enumerate(HDR)]
# No dark member clears 4.5:1 against white text, so every header label is a
# darkened ink of its own hue, measured against that header rather than white.
HDR_TXT = [darken_to(c, 4.5, ref=c) for c in HDR]

TITLES = ["1 \u00b7 Input data",
          "2 \u00b7 GMT processing\n& mapping",
          "3 \u00b7 Feature set\n& labels",
          "4 \u00b7 Supervised\nlearning",
          "5 \u00b7 Evaluation\n& prediction"]

# Source strings are single-line; wrap_fit() below breaks them to the measured
# box width, so the wrap adapts automatically if the font, the point size or the
# box geometry ever changes.
ITEMS = [
    ["Earthquake catalogue",
     "Focal mechanisms",
     "SRTM15+ relief, $V_{s30}$",
     "Building inventory"],
    ["Command-line GMT",
     "Seismicity maps",
     "Amplification field",
     "Geospatial dataset"],
    ["Six tabular features",
     "Drift limit-state labels",
     "2800 cells; 2240/560",
     "Split 60/15/25"],
    ["Random forest",
     "XGBoost",
     "5-fold grid search",
     "Class weighting"],
    ["ROC-AUC, PR, $F_1$",
     "Spatial block CV",
     "Leave-one-district-out",
     "Surrogate screening maps"],
]


def wrap_fit(ax, renderer, text, max_px, **kw):
    """Greedy word wrap to a measured pixel width.

    Splits on spaces and, where a single token is still too wide, after internal
    hyphens (the hyphen stays at the end of the line). Width is measured with a
    throwaway Text artist so that mathtext runs such as $V_{s30}$ are sized
    correctly rather than by a character count.
    """
    def width(s):
        probe = ax.text(0, 0, s, **kw)
        w = probe.get_window_extent(renderer=renderer).width
        probe.remove()
        return w

    def atoms(word):
        if width(word) <= max_px or "-" not in word[1:]:
            return [word]
        parts, cur = [], ""
        for piece in re.split(r"(?<=-)", word):
            if cur and width(cur + piece) > max_px:
                parts.append(cur)
                cur = piece
            else:
                cur += piece
        if cur:
            parts.append(cur)
        return parts

    lines, cur = [], ""
    for word in text.split(" "):
        for atom in atoms(word):
            trial = (cur + " " + atom).strip() if not cur.endswith("-") else cur + atom
            if cur and width(trial) > max_px:
                lines.append(cur)
                cur = atom
            else:
                cur = trial
    if cur:
        lines.append(cur)
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# 3. Geometry, in a 0-100 schematic space mapped to the final printed size.    #
# --------------------------------------------------------------------------- #
CM = 1 / 2.54
FIG_W, FIG_H = 17.5 * CM, 7.8 * CM         # journal double-column width

W, GAP = 18.5, 1.85                        # stage box width / inter-box gap
X0 = (100 - (5 * W + 4 * GAP)) / 2.0
BOT, TOP = 2.0, 72.0                       # stage box vertical extent
HDR_H = 12.0                               # header band height
PAD_L, PAD_R = 2.4, 0.6                    # text inset from the box edges
ITEM_Y = [52.0, 37.5, 23.0, 8.5]          # item centres

fig = plt.figure(figsize=(FIG_W, FIG_H))
ax = fig.add_axes([0, 0, 1, 1])            # schematic uses the whole canvas
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")
fig.canvas.draw()                          # renderer needed to measure text
renderer = fig.canvas.get_renderer()

# Usable text width inside a stage box, in device pixels.
MAX_PX = (ax.transData.transform((W - PAD_L - PAD_R, 0))[0]
          - ax.transData.transform((0, 0))[0])

ax.text(50, 99.0,
        "Methodology workflow: from raw data through GMT dataset construction and "
        "feature\nengineering to a trained resist/collapse surrogate and screening "
        "maps for Istanbul",
        ha="center", va="top", fontsize=FS_TITLE, weight="bold",
        color="#243040", linespacing=1.30)

item_texts, head_texts = [], []            # (Text, stage index) for the checks
for i in range(5):
    x = X0 + i * (W + GAP)

    ax.add_patch(FancyBboxPatch((x, BOT), W, TOP - BOT,
                                boxstyle="round,pad=0,rounding_size=1.4",
                                fc=BOD[i], ec=INK[i], lw=LW_STRUCT, zorder=1))
    ax.add_patch(FancyBboxPatch((x, TOP - HDR_H), W, HDR_H,
                                boxstyle="round,pad=0,rounding_size=1.4",
                                fc=HDR[i], ec=INK[i], lw=LW_STRUCT, zorder=2))
    h_art = ax.text(x + W / 2, TOP - HDR_H / 2, TITLES[i], ha="center",
                    va="center", fontsize=FS_HEAD, weight="bold", color=HDR_TXT[i],
                    linespacing=1.25, zorder=3)
    head_texts.append((h_art, i))

    for y, raw in zip(ITEM_Y, ITEMS[i]):
        txt = wrap_fit(ax, renderer, raw, MAX_PX,
                       fontsize=FS_ITEM, ha="left", va="center")
        ax.text(x + 0.9, y, "\u2022", ha="left", va="center",
                fontsize=FS_ITEM, color=INK[i], zorder=3)
        t_art = ax.text(x + PAD_L, y, txt, ha="left", va="center",
                        fontsize=FS_ITEM, color="#243040",
                        linespacing=1.35, zorder=3)
        item_texts.append((t_art, i))
        if os.environ.get("DBG"): print("  stage %d: %d lines | %s" % (i+1, txt.count(chr(10))+1, txt.replace(chr(10)," / ")))

    if i < 4:                                          # inter-stage arrow
        ax.add_patch(FancyArrowPatch((x + W + 0.25, 40.0),
                                     (x + W + GAP - 0.25, 40.0),
                                     arrowstyle="-|>", mutation_scale=9,
                                     lw=LW_MAIN, color="#3a4a5e", zorder=4))

# Feedback loop: evaluation (5) back to supervised learning (4). Secondary to
# the main path, so LW_SERIES rather than LW_MAIN (rule 2).
LOOP = INK[3]                              # the hue of the stage it returns to
xa = X0 + 4 * (W + GAP) + W / 2
xb = X0 + 3 * (W + GAP) + W / 2
RAD = 0.22
loop_arc = FancyArrowPatch((xa, TOP + 0.5), (xb, TOP + 0.5),
                           connectionstyle="arc3,rad=%s" % RAD,
                           arrowstyle="-|>", mutation_scale=8,
                           lw=LW_SERIES, ls="--", color=LOOP, zorder=4)
ax.add_patch(loop_arc)
def arc_points(patch):
    """Densified display-space points along a FancyArrowPatch.

    `get_path()` returns DATA-space Bezier *control* points -- only 7 for this
    arc -- so testing those against a text box misses the curve between them.
    Transform first, then `to_polygons` to flatten the Beziers into segments.
    """
    tp = patch.get_transform().transform_path(patch.get_path())
    return np.vstack([np.asarray(q) for q in tp.to_polygons(closed_only=False)])


# Rule 3: the caption is a DIRECT label on the arc it names. Its height is taken
# from the *rendered* apex rather than from the nominal arc3 geometry, because
# `rad` is applied in display space and these axes are far from square, so the
# analytic apex is wrong in data units by a wide margin.
apex_y = ax.transData.inverted().transform(
    (0, arc_points(loop_arc)[:, 1].max()))[1]
loop_lbl = ax.annotate("cross-validated tuning", xy=((xa + xb) / 2, apex_y),
                       xytext=(0, 3), textcoords="offset points",
                       ha="center", va="bottom", fontsize=FS_ITEM,
                       style="italic", color=LOOP, zorder=5)

# --------------------------------------------------------------------------- #
# 4. Rule 1 check: verify by measurement that no label leaves its box and that #
#    consecutive items in a column do not collide vertically.                  #
# --------------------------------------------------------------------------- #
fig.canvas.draw()
renderer = fig.canvas.get_renderer()

bad_h, bad_v = [], []
boxes = {}
for t_art, i in head_texts + item_texts:
    bb = t_art.get_window_extent(renderer=renderer)
    x = X0 + i * (W + GAP)
    inset = PAD_L if (t_art, i) in item_texts else 0.6
    x0 = ax.transData.transform((x + inset, 0))[0]
    x1 = ax.transData.transform((x + W - PAD_R, 0))[0]
    if bb.x0 < x0 - 0.5 or bb.x1 > x1 + 0.5:
        bad_h.append((i + 1, t_art.get_text().split("\n")[0],
                      (bb.x1 - x1) / (x1 - x0) * 100.0))
    if (t_art, i) in item_texts:
        boxes.setdefault(i, []).append(bb)

for i, bbs in boxes.items():
    order = sorted(bbs, key=lambda b: -b.y0)
    for a, b in zip(order, order[1:]):
        if b.y1 > a.y0 - 2.0:
            bad_v.append((i + 1, a.y0 - b.y1))

if bad_h or bad_v:
    for stage, line, over in bad_h:
        print("  H-OVERFLOW stage %d: %-30s %+.1f%% past the box"
              % (stage, line, over))
    for stage, gap in bad_v:
        print("  V-COLLISION stage %d: items overlap by %.1f px" % (stage, -gap))
    raise SystemExit("rule 1 violated: %d horizontal, %d vertical."
                     % (len(bad_h), len(bad_v)))
# The title and the loop caption sit outside every stage box; check they clear
# the boxes and each other (rules 1 and 10).
free = [("loop caption", loop_lbl)]
free += [("title", t) for t in ax.texts if t.get_text().startswith("Methodology")]
box_top_px = ax.transData.transform((0, TOP))[1]
for name, art in free:
    bb = art.get_window_extent(renderer=renderer)
    if bb.y0 < box_top_px - 0.5:
        print("  CLASH: %s descends into the stage boxes" % name)
        raise SystemExit("rule 1 violated")
arc_px = arc_points(loop_arc)
lbb = loop_lbl.get_window_extent(renderer=renderer)
on_arc = ((arc_px[:, 0] > lbb.x0) & (arc_px[:, 0] < lbb.x1) &
          (arc_px[:, 1] > lbb.y0) & (arc_px[:, 1] < lbb.y1)).sum()
if on_arc:
    print("  CLASH: loop caption sits on its own arc (%d vertices)" % on_arc)
    raise SystemExit("rule 1 violated")

for a in range(len(free)):
    for b in range(a + 1, len(free)):
        if free[a][1].get_window_extent(renderer=renderer).overlaps(
                free[b][1].get_window_extent(renderer=renderer)):
            print("  CLASH: %s / %s" % (free[a][0], free[b][0]))
            raise SystemExit("rule 1 violated")
print("rule 1 check: %d labels, all inside their boxes, no vertical "
      "collisions; title and loop caption clear of the boxes and of each other"
      % (len(item_texts) + len(head_texts)))

# --------------------------------------------------------------------------- #
# 5. Export: vector PDF + 600 dpi PNG.                                         #
# --------------------------------------------------------------------------- #
outdir = sys.argv[1] if len(sys.argv) > 1 else "figures"
os.makedirs(outdir, exist_ok=True)
for ext, kw in (("pdf", {}), ("png", {"dpi": 600})):
    fig.savefig(os.path.join(outdir, "fig08_workflow." + ext),
                bbox_inches="tight", pad_inches=0.02, facecolor="white", **kw)

# Flatten the PNG onto white: journals reject figures with an alpha channel.
try:
    from PIL import Image
    _p = os.path.join(outdir, "fig08_workflow.png")
    _im = Image.open(_p).convert("RGBA")
    _bg = Image.new("RGB", _im.size, (255, 255, 255))
    _bg.paste(_im, mask=_im.split()[3])
    _bg.save(_p, dpi=(600, 600))
except ImportError:
    print("note: Pillow not available; PNG left with an alpha channel")

print("wrote fig08_workflow.pdf / .png in %s" % outdir)
print("font resolved to: %s" % FONT_RESOLVED)
print("verify embedding: pdffonts %s/fig08_workflow.pdf | "
      "grep -i -e nimbus -e dejavu" % outdir)
