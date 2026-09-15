#!/usr/bin/env python3
import sys

import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
from matplotlib.patheffects import withStroke

import glob, os
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

FS_TAG, FS_LAB, FS_TICK = 11.0, 9.5, 8.5

LW_MAIN, LW_SERIES = 2.0, 1.2

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Nimbus Sans", "Helvetica"],
    "font.size": FS_LAB,
    "axes.labelsize": FS_LAB,
    "xtick.labelsize": FS_TICK,
    "ytick.labelsize": FS_TICK,
    "legend.fontsize": FS_LAB,
    "axes.labelpad": 2,
    "axes.titlepad": 3,
    "axes.linewidth": 0.8,
    "mathtext.fontset": "custom",
    "mathtext.rm": "Nimbus Sans", "mathtext.it": "Nimbus Sans:italic",
    "mathtext.bf": "Nimbus Sans:bold", "mathtext.sf": "Nimbus Sans",
    "mathtext.cal": "Nimbus Sans:italic", "mathtext.tt": "Nimbus Sans",
    "pdf.fonttype": 42, "ps.fonttype": 42,
})
_fp = FontProperties(); _fp.set_family("sans-serif")
if "DejaVu" in findfont(_fp):
    raise RuntimeError("resolved to DejaVu Sans, which is forbidden.")

HALO = [withStroke(linewidth=1.8, foreground="white")]

G = 9.80665

def Sa_ec8(T, ag, S, TB, TC, TD):
    T = np.asarray(T, float)
    out = np.empty_like(T)
    b1 = T < TB
    b2 = (T >= TB) & (T < TC)
    b3 = (T >= TC) & (T < TD)
    b4 = T >= TD
    out[b1] = ag * S * (1 + 1.5 * T[b1] / TB)
    out[b2] = ag * S * 2.5
    out[b3] = ag * S * 2.5 * (TC / T[b3])
    out[b4] = ag * S * 2.5 * (TC * TD / T[b4] ** 2)
    return out

CLASSES = {
    "A": (1.00, 0.15, 0.40, 2.00),
    "B": (1.20, 0.15, 0.50, 2.00),
    "C": (1.15, 0.20, 0.60, 2.00),
    "D": (1.35, 0.20, 0.80, 2.00),
    "E": (1.40, 0.15, 0.50, 2.00),
}
DESC = {"A": "rock", "B": "stiff", "C": "medium",
        "D": "soft", "E": "soft over rock"}
ag = 0.40

SET1 = {"red": "#e41a1c", "blue": "#377eb8", "green": "#4daf4a",
        "purple": "#984ea3", "orange": "#ff7f00", "brown": "#a65628"}
COL = {"B": SET1["blue"], "C": SET1["green"], "D": SET1["orange"], "E": SET1["red"]}
MRK = {"B": "o", "C": "s", "D": "^", "E": "D"}
LS = {"B": (0, (1, 1.4)), "C": (0, (5, 1.6)), "D": (0, (6, 1.6, 1.4, 1.6)),
      "E": "solid"}

T = np.linspace(1e-3, 4.0, 1400)

CM = 1 / 2.54
fig, (axA, axD) = plt.subplots(1, 2, figsize=(17.5 * CM, 8.0 * CM))

fig.subplots_adjust(left=0.070, right=0.988, bottom=0.135, top=0.975, wspace=0.155)

def style(ax, xmaj, xmin, ymaj, ymin):
    ax.set_xlim(0, 4)
    ax.xaxis.set_major_locator(MultipleLocator(xmaj))
    ax.xaxis.set_minor_locator(AutoMinorLocator(xmin))
    ax.yaxis.set_major_locator(MultipleLocator(ymaj))
    ax.yaxis.set_minor_locator(AutoMinorLocator(ymin))
    ax.tick_params(which="both", direction="in", top=True, right=True, pad=2)
    ax.tick_params(which="major", length=4.2, width=0.8)
    ax.tick_params(which="minor", length=2.4, width=0.6)
    ax.grid(which="major", lw=0.5, color="0.85")
    ax.grid(which="minor", lw=0.3, color="0.92")
    ax.set_axisbelow(True)

def mark_dot(ax, T, y, cls):
    idx = np.linspace(60, len(T) - 60, 6).astype(int)
    ax.plot(T[idx], y[idx], MRK[cls], ms=3.4, mfc=COL[cls], mec="white",
            mew=0.5, ls="none", zorder=5)

SaA = Sa_ec8(T, ag, *CLASSES["A"])
for cls in ("E", "D", "C", "B"):
    y = Sa_ec8(T, ag, *CLASSES[cls])
    axA.plot(T, y, color=COL[cls], lw=LW_SERIES, ls=LS[cls], zorder=4,
             label=f"Type {cls} ({DESC[cls]})")
    mark_dot(axA, T, y, cls)
axA.plot(T, SaA, color="k", lw=LW_MAIN, ls=(0, (6, 2)), zorder=6,
         label="Type A (rock) \u2014 design ref.")
style(axA, 1.0, 5, 0.5, 5)
axA.set_ylim(0, 1.98)
axA.set_xlabel("Period $T$ (s)")
axA.set_ylabel("Pseudo-acceleration $S_a$ ($g$)")

sp = [(0.15, "low-rise"),
      (0.70, "mid-rise"),
      (2.00, "isolated")]
for (Tp, lab), ytxt in zip(sp, (0.04, 0.155, 0.04)):
    axA.axvline(Tp, color="0.45", lw=0.7, ls=":", zorder=2)
    axA.text(Tp + 0.04, ytxt, lab, fontsize=FS_TICK, va="bottom", ha="left",
             color="0.30", path_effects=HALO, zorder=7)

axA.annotate("seismic\nisolation",
             xy=(2.05, Sa_ec8(np.array([2.05]), ag, *CLASSES["E"])[0]),
             xytext=(2.72, 0.72), fontsize=FS_TICK,
             color=SET1["purple"], ha="left", va="center",
             path_effects=HALO, zorder=7,
             arrowprops=dict(arrowstyle="-|>", color=SET1["purple"], lw=1.0,
                             connectionstyle="arc3,rad=0.25",
                             shrinkA=2, shrinkB=1))

axA.text(0.018, 0.96, "(a)", transform=axA.transAxes, fontsize=FS_TAG,
         fontweight="bold", va="top", ha="left",
         bbox=dict(boxstyle="square,pad=0.18", fc="white", ec="0.4", lw=0.5))
legA = axA.legend(loc="upper right", framealpha=0.93, edgecolor="0.6",
                  borderpad=0.5, labelspacing=0.35, handlelength=2.2,
                  bbox_to_anchor=(0.995, 0.995))
legA.get_frame().set_linewidth(0.5)

def Sd_cm(T, *p):
    return Sa_ec8(T, *p) * G * (T / (2 * np.pi)) ** 2 * 100.0

SdA = Sd_cm(T, ag, *CLASSES["A"])
for cls in ("E", "D", "C", "B"):
    y = Sd_cm(T, ag, *CLASSES[cls])
    axD.plot(T, y, color=COL[cls], lw=LW_SERIES, ls=LS[cls], zorder=4,
             label=f"Type {cls}")
    mark_dot(axD, T, y, cls)
axD.plot(T, SdA, color="k", lw=LW_MAIN, ls=(0, (6, 2)), zorder=6, label="Type A (rock)")
style(axD, 1.0, 5, 20, 4)
axD.set_ylim(0, 82)
axD.set_xlabel("Period $T$ (s)")
axD.set_ylabel("Spectral displacement $S_d$ (cm)")
axD.text(0.018, 0.96, "(b)", transform=axD.transAxes, fontsize=FS_TAG,
         fontweight="bold", va="top", ha="left",
         bbox=dict(boxstyle="square,pad=0.18", fc="white", ec="0.4", lw=0.5))

axD.annotate("soft sites: large\nlong-period\ndisplacement demand",
             xy=(2.10, Sd_cm(np.array([2.10]), ag, *CLASSES["D"])[0]),
             xytext=(1.05, 79.0), fontsize=FS_TICK, ha="left", va="top", color="0.25",
             path_effects=HALO,
             arrowprops=dict(arrowstyle="->", color="0.4", lw=0.8,
                             connectionstyle="arc3,rad=0.25"))

LABEL_AT = {"D": (3.30, 6), "E": (3.30, 7), "C": (2.60, -13), "B": (3.30, -13),
            "A": (3.30, -13)}
for cls in ("D", "E", "C", "B", "A"):
    xl, dy = LABEL_AT[cls]
    yl = Sd_cm(np.array([xl]), ag, *CLASSES[cls])[0]
    axD.annotate(f"Type {cls}", xy=(xl, yl), xytext=(0, dy),
                 textcoords="offset points", ha="center",
                 va="bottom" if dy > 0 else "top",
                 fontsize=FS_TICK, color=COL.get(cls, "k"), fontweight="bold",
                 path_effects=HALO, zorder=8)

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
_stem = os.path.join(OUT, "fig13_spectra")
fig.savefig(_stem + ".pdf", bbox_inches="tight", pad_inches=0.02)
fig.savefig(_stem + ".png", dpi=600, bbox_inches="tight", pad_inches=0.02)
try:
    from PIL import Image
    _im = Image.open(_stem + ".png").convert("RGBA")
    _bg = Image.new("RGB", _im.size, (255, 255, 255))
    _bg.paste(_im, mask=_im.split()[3])
    _bg.save(_stem + ".png", dpi=(600, 600))
except ImportError:
    pass
print("plateau Sa: A=%.2f E=%.2f g" % (2.5 * ag * CLASSES["A"][0],
                                        2.5 * ag * CLASSES["E"][0]))
print("Sd@2s: A=%.1f D=%.1f cm" % (SdA[np.argmin(abs(T - 2))],
                                   Sd_cm(np.array([2.0]), ag, *CLASSES["D"])[0]))

from matplotlib.text import Annotation, Text

def _text_bbox(a, r):
    return Text.get_window_extent(a, renderer=r)

fig.canvas.draw()
_rend = fig.canvas.get_renderer()
_bad = 0

def _data_px(ax):
    _p = []
    for _ln in ax.get_lines():
        _xy = _ln.get_xydata()
        if len(_xy):
            _p.append(ax.transData.transform(_xy))
    return np.vstack(_p) if _p else np.empty((0, 2))

for _ax, _name in ((axA, "(a)"), (axD, "(b)")):
    _P = _data_px(_ax)
    _lg = _ax.get_legend()
    _boxes = ([("legend", _lg.get_frame().get_window_extent(_rend))] if _lg else [])
    for _c in _ax.texts:
        if _c.get_text().strip():
            _boxes.append((repr(_c.get_text())[:26], _text_bbox(_c, _rend)))
    for _lbl, _bb in _boxes:
        _hit = ((_P[:, 0] > _bb.x0) & (_P[:, 0] < _bb.x1) &
                (_P[:, 1] > _bb.y0) & (_P[:, 1] < _bb.y1)).sum() if len(_P) else 0
        if _hit:
            print("  OVERLAP in %s: %-28s %d data points" % (_name, _lbl, _hit))
            _bad += 1
    for _i in range(len(_boxes)):
        for _j in range(_i + 1, len(_boxes)):
            if _boxes[_i][1].overlaps(_boxes[_j][1]):
                print("  TEXT-TEXT in %s: %s / %s" % (_name, _boxes[_i][0], _boxes[_j][0]))
                _bad += 1
    for _a in _ax.texts:
        if isinstance(_a, Annotation) and getattr(_a, "arrow_patch", None) is not None:
            _head = _ax.transData.transform(np.asarray(_a.xy, float))
            _tail = _a.get_transform().transform(np.asarray(_a.get_position(), float))
            _hg = np.hypot(*(_P - _head).T).min() * 72.0 / fig.dpi if len(_P) else np.inf
            _tb = _text_bbox(_a, _rend)
            _tg = np.hypot(max(_tb.x0 - _tail[0], 0, _tail[0] - _tb.x1),
                           max(_tb.y0 - _tail[1], 0, _tail[1] - _tb.y1)) * 72.0 / fig.dpi
            _txt = _a.get_text().strip() or "(arrow with detached caption)"
            if _hg > 4.0 or _tg > 4.0:
                print("  ARROW in %s: %-24s head gap %.1f pt, tail gap %.1f pt"
                      % (_name, repr(_txt)[:24], _hg, _tg))
                _bad += 1
print("house checks: %s" % ("FAILED" if _bad else
                            "no text on data, no text on text, all arrows connect"))
print("saved %s.pdf / .png" % _stem)
