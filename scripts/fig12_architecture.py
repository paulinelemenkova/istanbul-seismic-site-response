#!/usr/bin/env python3
import glob
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties, findfont, fontManager
from matplotlib.patches import (Ellipse, FancyArrowPatch, FancyBboxPatch,
                                Rectangle)

URW_DIRS = ("/usr/share/fonts/opentype/urw-base35",
            "/usr/share/fonts/type1/urw-base35",
            "/usr/local/share/fonts/urw-base35",
            "/opt/homebrew/share/fonts", "/Library/Fonts")

def ensure_nimbus():
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
    "font.sans-serif": ["Nimbus Sans", "Helvetica"],
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

FS_TITLE = 11.0
FS_HEAD = 9.0
FS_ITEM = 8.0

BLUE_F, BLUE_E = "#dceaf5", "#4a7fa8"
GREEN, RED = "#1a7a55", "#b34a44"
NAVY = "#2c3e56"
PURPLE = "#7a4fa3"
AMBER_F, AMBER_E = "#fbeed6", "#c8871a"

FEATURES = [("$V_{s30}$", "site stiffness"),
            ("$h_{sed}$", "sediment thickness"),
            ("$R_{fault}$", "distance to fault"),
            ("$T_0$", "fundamental period"),
            ("$H$", "building height"),
            ("$S_a(T_0)$", "spectral acceleration")]

CM = 1 / 2.54
YMIN, YMAX = 0.0, 100.0
FIG_W, FIG_H = 17.5 * CM, 8.4 * CM

fig = plt.figure(figsize=(FIG_W, FIG_H))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100)
ax.set_ylim(YMIN, YMAX)
ax.axis("off")
fig.canvas.draw()
renderer = fig.canvas.get_renderer()

ASPECT = (FIG_W / 100.0) / (FIG_H / (YMAX - YMIN))

def node(x, y, r=1.15, **kw):
    return Ellipse((x, y), width=2 * r, height=2 * r * ASPECT, **kw)

AGG_C, APP_C = 80.45, 94.45
FX, FW = 0.8, 23.5
VX, VW = 25.8, 9.0
EX, EW = 36.6, 35.0
AX_, AW = 73.2, 14.5
PX, PW = 89.1, 10.7

ax.text(50, 98.0,
        "Architecture of the resist/collapse surrogate:\n"
        "feature inputs \u2192 tree ensemble \u2192 aggregation "
        "\u2192 binary prediction",
        ha="center", va="top", fontsize=FS_TITLE, weight="bold",
        color=NAVY, linespacing=1.30)

for x, lab, col in [(12.5, "Input features", BLUE_E),
                    (30.3, "Feature vector", NAVY),
                    (54.1, "Classifier", GREEN),
                    (AGG_C, "Prediction", "#6a4a10"),
                    (APP_C, "Application", PURPLE)]:
    ax.text(x, 79.0, lab, ha="center", va="center", fontsize=FS_HEAD,
            weight="bold", color=col)

feat_texts = []
ys = [70.0, 59.0, 48.0, 37.0, 26.0, 15.0]
for y, (sym, desc) in zip(ys, FEATURES):
    ax.add_patch(FancyBboxPatch((FX, y - 4.4), FW, 8.8,
                                boxstyle="round,pad=0,rounding_size=1.3",
                                fc=BLUE_F, ec=BLUE_E, lw=0.8))
    a = ax.text(FX + 1.6, y, sym, ha="left", va="center", fontsize=FS_HEAD,
                color="#1a2a3a")
    b = ax.text(FX + FW - 1.4, y, desc, ha="right", va="center",
                fontsize=FS_ITEM, color="#3a4a5a")
    feat_texts.append((a, b, y))
    ax.add_patch(FancyArrowPatch((FX + FW + 0.3, y), (FX + FW + 1.3, y),
                                 arrowstyle="-|>", mutation_scale=6, lw=0.8,
                                 color="#3a4a5e"))

ax.add_patch(FancyBboxPatch((VX, 10.0), VW, 65.0,
                            boxstyle="round,pad=0,rounding_size=1.3",
                            fc="#e4e7ec", ec=NAVY, lw=1.0))
ax.text(VX + VW / 2, 42.5, "Feature\nvector\n$\\mathbf{x}\\in\\mathsf{R}^{6}$",
        ha="center", va="center", fontsize=FS_HEAD, weight="bold", color=NAVY,
        linespacing=1.55)
ax.add_patch(FancyArrowPatch((VX + VW + 0.25, 42.5), (EX - 0.25, 42.5),
                             arrowstyle="-|>", mutation_scale=8, lw=1.1,
                             color="#3a4a5e"))

ax.add_patch(FancyBboxPatch((EX, 10.0), EW, 65.0,
                            boxstyle="round,pad=0,rounding_size=1.3",
                            fc="#f2f4f6", ec="#b8c0c8", lw=0.9))
ax.text(EX + EW / 2, 70.5,
        "Ensemble of decision trees\n(random forest / XGBoost)",
        ha="center", va="center", fontsize=FS_HEAD, weight="bold", color=GREEN)

for k, cx in enumerate([EX + 6.4, EX + 17.5, EX + 28.6]):
    ax.plot([cx, cx - 2.8], [59.0, 45.0], color="#8a949e", lw=0.8, zorder=1)
    ax.plot([cx, cx + 2.8], [59.0, 45.0], color="#8a949e", lw=0.8, zorder=1)
    for px in (cx - 2.8, cx + 2.8):
        ax.plot([px, px - 1.4], [45.0, 31.0], color="#8a949e", lw=0.8, zorder=1)
        ax.plot([px, px + 1.4], [45.0, 31.0], color="#8a949e", lw=0.8, zorder=1)
    for px, py in [(cx, 59.0), (cx - 2.8, 45.0), (cx + 2.8, 45.0)]:
        ax.add_patch(node(px, py, fc="white", ec="#5a646e", lw=0.9, zorder=2))
    cols = [GREEN, RED, RED, GREEN] if k != 1 else [RED, GREEN, GREEN, RED]
    for lx, c in zip([cx - 4.2, cx - 1.4, cx + 1.4, cx + 4.2], cols):
        ax.add_patch(Rectangle((lx - 0.95, 26.5), 1.9, 4.6, fc=c, ec=c,
                               zorder=2))
    ax.text(cx, 20.0, "Tree %s" % ["1", "2", "$T$"][k], ha="center",
            va="center", fontsize=FS_ITEM, color="#3a4a5a")

ax.add_patch(FancyArrowPatch((EX + EW + 0.25, 42.5), (AX_ - 0.25, 42.5),
                             arrowstyle="-|>", mutation_scale=8, lw=1.1,
                             color="#3a4a5e"))

ax.add_patch(FancyBboxPatch((AX_, 30.0), AW, 25.0,
                            boxstyle="round,pad=0,rounding_size=1.3",
                            fc=AMBER_F, ec=AMBER_E, lw=1.0))
ax.text(AX_ + AW / 2, 48.5, "Aggregation", ha="center", va="center",
        fontsize=FS_HEAD, weight="bold", color="#6a4a10")
ax.text(AX_ + AW / 2, 37.5, "majority vote /\nadditive update",
        ha="center", va="center", fontsize=FS_ITEM, color="#6a4a10",
        linespacing=1.45)

for y, lab, col in [(68.5, "RESIST", GREEN), (16.5, "COLLAPSE", RED)]:
    ax.add_patch(FancyBboxPatch((AX_, y - 6.5), AW, 13.0,
                                boxstyle="round,pad=0,rounding_size=1.3",
                                fc=col, ec=col))
    ax.text(AX_ + AW / 2, y, lab, ha="center", va="center", fontsize=FS_HEAD,
            weight="bold", color="white")
ax.add_patch(FancyArrowPatch((AGG_C, 55.4), (AGG_C, 61.6), arrowstyle="-|>",
                             mutation_scale=7, lw=1.0, color="#3a4a5e"))
ax.add_patch(FancyArrowPatch((AGG_C, 29.6), (AGG_C, 23.4), arrowstyle="-|>",
                             mutation_scale=7, lw=1.0, color="#3a4a5e"))

ax.add_patch(FancyBboxPatch((PX, 10.0), PW, 65.0,
                            boxstyle="round,pad=0,rounding_size=1.3",
                            fc="#ece4f5", ec=PURPLE, lw=1.1))
ax.text(PX + PW / 2, 42.5, "Screen\nIstanbul\nbuilding\nstock",
        ha="center", va="center", fontsize=FS_HEAD, weight="bold",
        color="#4a2a70", linespacing=1.55)
for y in (68.5, 16.5):
    ax.add_patch(FancyArrowPatch((AX_ + AW + 0.3, y), (PX - 0.4, y),
                                 arrowstyle="-|>", mutation_scale=7, lw=1.0,
                                 color=PURPLE))

ax.text(50, 4.5,
        "Single output: the binary resist/collapse decision of the drift "
        "limit-state rule; $S_a(T_0)$ enters as an input feature.",
        ha="center", va="center", fontsize=FS_ITEM, style="italic",
        color="#5a646e")

fig.canvas.draw()
renderer = fig.canvas.get_renderer()
bad = []
for a, b, y in feat_texts:
    ba = a.get_window_extent(renderer=renderer)
    bb = b.get_window_extent(renderer=renderer)
    if ba.x1 > bb.x0 - 2.0:
        bad.append(("feature row y=%.0f" % y, ba.x1 - bb.x0))
    box_x1 = ax.transData.transform((FX + FW - 0.6, 0))[0]
    if bb.x1 > box_x1 + 0.5:
        bad.append(("descriptor overflows box, y=%.0f" % y, bb.x1 - box_x1))
if EX + EW > AX_:
    bad.append(("ensemble panel overlaps aggregation block", EX + EW - AX_))
if bad:
    for what, amt in bad:
        print("  COLLISION: %-42s by %.1f" % (what, amt))
    raise SystemExit("rule 1 violated: %d collision(s)." % len(bad))
print("rule 1 check: %d feature rows clear, panels clear" % len(feat_texts))

outdir = sys.argv[1] if len(sys.argv) > 1 else "figures"
os.makedirs(outdir, exist_ok=True)
for ext, kw in (("pdf", {}), ("png", {"dpi": 600})):
    fig.savefig(os.path.join(outdir, "fig12_architecture." + ext),
                bbox_inches="tight", pad_inches=0.02, facecolor="white", **kw)

try:
    from PIL import Image
    _p = os.path.join(outdir, "fig12_architecture.png")
    _im = Image.open(_p).convert("RGBA")
    _bg = Image.new("RGB", _im.size, (255, 255, 255))
    _bg.paste(_im, mask=_im.split()[3])
    _bg.save(_p, dpi=(600, 600))
except ImportError:
    print("note: Pillow not available; PNG left with an alpha channel")

print("wrote fig12_architecture.pdf / .png in %s" % outdir)
print("font resolved to: %s" % FONT_RESOLVED)
print("verify embedding: pdffonts %s/fig12_architecture.pdf | "
      "grep -i -e nimbus -e dejavu" % outdir)
