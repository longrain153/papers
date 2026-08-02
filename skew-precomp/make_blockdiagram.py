#!/usr/bin/env python3
"""Simplified block diagram: bit widths only (verified by sim_fixedpoint.py)."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(12, 6))
ax.set_xlim(0, 12)
ax.set_ylim(0, 6)
ax.axis("off")

BLUE = dict(fc="#eef3fb", ec="#2b5aa0")
ORANGE = dict(fc="#fdf3e3", ec="#b07818")
GREEN = dict(fc="#e8f6e8", ec="#2c7a2c")
PURPLE = dict(fc="#f5e9f7", ec="#7a3d8a")


def box(x, y, w, h, text, fs=9.5, **kw):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                lw=1.3, **kw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(p1, p2, label="", loff=(0, 0.13), fs=9, color="k", ls="-"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=11,
                                 lw=1.2, color=color, linestyle=ls))
    if label:
        ax.text((p1[0] + p2[0]) / 2 + loff[0], (p1[1] + p2[1]) / 2 + loff[1],
                label, ha="center", fontsize=fs, color="#1a3d6e")


# ---------- main path ----------
arrow((0.1, 5.2), (1.0, 5.2), "x[n]\n8bit", loff=(0, 0.18))
box(1.0, 4.85, 2.2, 0.7, "delay line\n7 taps", **BLUE)
arrow((3.2, 5.2), (9.3, 5.2), "center tap    8bit")
box(9.3, 4.85, 1.0, 0.7, "+", fs=13, **BLUE)
arrow((10.3, 5.2), (11.0, 5.2), "9bit")
box(11.0, 4.85, 0.85, 0.7, "rnd/\nsat", **BLUE)
arrow((11.9, 5.2), (11.98, 5.2))
ax.text(11.75, 4.55, "y[n]  8bit", fontsize=9.5, color="#1a3d6e")

# ---------- cut ----------
arrow((2.1, 4.85), (2.1, 4.45), "outer taps ×6   8bit", loff=(1.15, -0.25))
box(1.75, 3.95, 0.7, 0.5, "cut", **ORANGE)
ax.text(2.28, 3.72, "5bit", fontsize=9, color="#1a3d6e")

# ---------- subtractors ----------
labels = ("d₁ = x[n−1]−x[n+1]", "d₂ = x[n−2]−x[n+2]", "d₃ = x[n−3]−x[n+3]")
for i, sx in enumerate((0.85, 2.32, 3.79)):
    box(sx, 2.9, 1.3, 0.6, f"−\n{labels[i]}", fs=7.4, **ORANGE)
    if i:
        arrow((sx + 0.65, 3.6), (sx + 0.65, 3.5))
    arrow((sx + 0.65, 2.9), (sx + 0.65, 2.55))
ax.text(4.62, 2.68, "6bit ×3", fontsize=8.5, color="#1a3d6e")
ax.plot([2.1, 4.44], [3.6, 3.6], color="k", lw=1.2)
ax.plot([2.1, 2.1], [3.95, 3.6], color="k", lw=1.2)

# ---------- hardwired shift-add ----------
box(0.85, 1.85, 4.25, 0.7,
    "v = d₁ − (d₂≫1) + (d₂≫4) + (d₃≫2)"
    "\nhardwired shifts", fs=8.8, **ORANGE)
arrow((5.1, 2.2), (6.18, 2.2), "v  8bit", loff=(-0.1, 0.14), fs=8.5)

# ---------- programmable shifts: explicit 5:1 muxes ----------
from matplotlib.patches import Polygon


def mux(x, y, h, name):
    """Trapezoid 5:1 mux; returns (input ys, output point, sel point)."""
    w = 0.5
    ax.add_patch(Polygon([(x, y), (x, y + h), (x + w, y + h - 0.22),
                          (x + w, y + 0.22)], closed=True,
                         fc=GREEN["fc"], ec=GREEN["ec"], lw=1.3))
    ax.text(x + w / 2, y + h / 2, "5:1", fontsize=8, ha="center",
            va="center")
    ax.text(x + w / 2, y + h + 0.1, name, fontsize=8.8, ha="center",
            color="#2c7a2c")
    ys = [y + h - 0.18 - i * (h - 0.36) / 4 for i in range(5)]
    return ys, (x + w, y + h / 2), (x + w / 2, y)


VBUS = 6.2
ax.plot([VBUS, VBUS], [1.30, 3.72], color="k", lw=1.2)
ax.plot(VBUS, 2.2, "ko", ms=3.5)

for name, ybot in (("MUX A", 2.85), ("MUX B", 1.15)):
    ys, out, sel = mux(6.9, ybot, 1.25, name)
    ax.text(6.66, ys[0], "0", fontsize=7.8, ha="right", va="center",
            color="#1a3d6e")
    ax.plot([6.72, 6.9], [ys[0], ys[0]], color="k", lw=1.0)
    for i, sh in enumerate(("≫4", "≫5", "≫6", "≫7"), start=1):
        ax.plot([VBUS, 6.9], [ys[i], ys[i]], color="k", lw=1.0)
        ax.text(6.55, ys[i] + 0.03, f"v{sh}", fontsize=7.4, ha="center",
                color="#1a3d6e")
    if name == "MUX A":
        arrow(out, (8.2, 3.05), "tA  6bit", loff=(0.15, 0.18), fs=8)
    else:
        arrow(out, (8.2, 2.7), "tB  6bit", loff=(0.15, -0.34), fs=8)

box(8.2, 2.55, 1.4, 0.7, "± combine\n(static add/sub)", fs=8.2, **GREEN)
arrow((9.6, 2.9), (9.8, 2.9))
ax.plot([9.8, 9.8], [2.9, 4.85], color="k", lw=1.2)
arrow((9.8, 4.7), (9.8, 4.85))
ax.text(9.95, 3.7, "c = μ̂·v\n7bit", fontsize=8.8, color="#1a3d6e")

# ---------- config ----------
ax.add_patch(FancyBboxPatch((1.0, 0.12), 7.95, 0.92,
                            boxstyle="round,pad=0.06", fc="none",
                            ec="#7a3d8a", lw=1.2, linestyle=(0, (5, 3))))
ax.text(1.15, 0.94, "software (per calibration only)", fontsize=8.8,
        color="#7a3d8a", style="italic")
box(1.2, 0.25, 1.6, 0.6, "μ register\n8bit", fs=8.8, **PURPLE)
arrow((2.8, 0.55), (3.6, 0.55))
box(3.6, 0.25, 2.1, 0.6, "SPT lookup\nμ̂=(±2ᵖ±2^q)/256", fs=8.4, **PURPLE)
arrow((5.9, 0.55), (6.5, 0.55))
box(6.5, 0.25, 2.3, 0.6, "config regs  8bit\n2×(sign+select)", fs=8.8,
    **PURPLE)
ax.text(9.25, 0.5, "hardware datapath:\neverything above\n(per sample)",
        fontsize=8.2, color="#555", style="italic")
for src, tgt in (((7.15, 0.85), (7.15, 1.15)),
                 ((7.95, 0.85), (7.34, 2.85)),
                 ((8.5, 0.85), (8.9, 2.55))):
    ax.add_patch(FancyArrowPatch(src, tgt, arrowstyle="-|>",
                                 mutation_scale=10, lw=1.0, color="#7a3d8a",
                                 linestyle=(0, (4, 3))))
ax.text(8.75, 1.55, "static selects\nsel 3bit ×2, sign ×2", fontsize=8,
        color="#7a3d8a")

ax.set_title("Tunable skew pre-compensator (|skew| ≤ 0.35 ps): "
             "0 multipliers · worst-case MSE −28.4 dB", fontsize=11)
fig.tight_layout()
fig.savefig("blockdiagram.png", dpi=170)
print("saved blockdiagram.png")
