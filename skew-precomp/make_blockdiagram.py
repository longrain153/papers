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
labels = ("d₁", "d₂", "d₃")
for i, sx in enumerate((1.2, 2.5, 3.8)):
    box(sx, 2.9, 0.9, 0.6, f"−\n{labels[i]}", fs=9, **ORANGE)
    if i:
        arrow((sx + 0.45, 3.6), (sx + 0.45, 3.5))
    arrow((sx + 0.45, 2.9), (sx + 0.45, 2.55))
ax.text(4.4, 2.62, "6bit ×3", fontsize=9, color="#1a3d6e")
ax.plot([2.1, 4.25], [3.6, 3.6], color="k", lw=1.2)
ax.plot([2.1, 2.1], [3.95, 3.6], color="k", lw=1.2)

# ---------- hardwired shift-add ----------
box(1.2, 1.85, 3.5, 0.7,
    "v = d₁ − (d₂≫1) + (d₂≫4) + (d₃≫2)"
    "\nhardwired shifts", fs=8.8, **ORANGE)
arrow((4.7, 2.2), (5.6, 2.2), "v  8bit", loff=(0, 0.16))

# ---------- programmable shifts ----------
box(5.6, 2.75, 1.9, 0.65, "prog shift A\n5:1 mux  ≫{4..7}/off",
    fs=8.5, **GREEN)
box(5.6, 1.25, 1.9, 0.65, "prog shift B\n5:1 mux  ≫{4..7}/off",
    fs=8.5, **GREEN)
ax.plot([5.5, 5.5], [1.55, 3.05], color="k", lw=1.2)
arrow((5.5, 3.05), (5.6, 3.05))
arrow((5.5, 1.55), (5.6, 1.55))
arrow((7.5, 3.05), (8.4, 2.5), "6bit", loff=(-0.15, 0.14))
arrow((7.5, 1.55), (8.4, 2.1), "6bit", loff=(-0.15, -0.3))
box(8.4, 1.95, 1.3, 0.65, "± combine", fs=9, **GREEN)
arrow((9.7, 2.3), (9.8, 2.3))
ax.plot([9.8, 9.8], [2.3, 4.85], color="k", lw=1.2)
arrow((9.8, 4.7), (9.8, 4.85))
ax.text(10.1, 3.5, "c  7bit", fontsize=9.5, color="#1a3d6e")

# ---------- config ----------
box(1.2, 0.25, 1.6, 0.6, "μ register\n8bit", fs=8.8, **PURPLE)
arrow((2.8, 0.55), (3.6, 0.55))
box(3.6, 0.25, 2.1, 0.6, "firmware\nSPT lookup", fs=8.8, **PURPLE)
arrow((5.7, 0.55), (6.5, 0.55))
box(6.5, 0.25, 2.3, 0.6, "config regs  8bit\n2×(sign+select)", fs=8.8,
    **PURPLE)
for tgt in ((6.6, 1.25), (6.6, 2.75), (9.05, 1.95)):
    ax.add_patch(FancyArrowPatch((7.65, 0.85), tgt, arrowstyle="-|>",
                                 mutation_scale=10, lw=1.0, color="#7a3d8a",
                                 linestyle=(0, (4, 3))))
ax.text(8.9, 1.05, "static selects", fontsize=8.5, color="#7a3d8a")

ax.set_title("Tunable skew pre-compensator (|skew| ≤ 0.35 ps): "
             "0 multipliers · worst-case MSE −28.4 dB", fontsize=11)
fig.tight_layout()
fig.savefig("blockdiagram.png", dpi=170)
print("saved blockdiagram.png")
