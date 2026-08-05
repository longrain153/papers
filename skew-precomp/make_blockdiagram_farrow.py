#!/usr/bin/env python3
"""Traditional 2nd-order Farrow (2 programmable multipliers, Horner form)
for |skew| <= 1 ps — comparison diagram to the multiplierless version."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

fig, ax = plt.subplots(figsize=(12, 6))
ax.set_xlim(0, 12)
ax.set_ylim(0, 6)
ax.axis("off")

BLUE = dict(fc="#eef3fb", ec="#2b5aa0")
ORANGE = dict(fc="#fdf3e3", ec="#b07818")
GREEN = dict(fc="#e8f6e8", ec="#2c7a2c")
PURPLE = dict(fc="#f5e9f7", ec="#7a3d8a")


def box(x, y, w, h, text, fs=9, **kw):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06",
                                lw=1.3, **kw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def circ(x, y, text, kw):
    ax.add_patch(Circle((x, y), 0.26, fc=kw["fc"], ec=kw["ec"], lw=1.3))
    ax.text(x, y, text, ha="center", va="center", fontsize=9.5)


def arrow(p1, p2, label="", loff=(0, 0.13), fs=8.6, color="k", ls="-"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=11,
                                 lw=1.2, color=color, linestyle=ls))
    if label:
        ax.text((p1[0] + p2[0]) / 2 + loff[0], (p1[1] + p2[1]) / 2 + loff[1],
                label, ha="center", fontsize=fs, color="#1a3d6e")


# ---------------- main path ----------------
arrow((0.1, 5.2), (1.0, 5.2), "x[n]\n8bit", loff=(0, 0.18))
box(1.0, 4.85, 2.4, 0.7, "delay line\n13 taps", **BLUE)
arrow((3.4, 5.2), (9.3, 5.2), "center tap    8bit")
box(9.3, 4.85, 1.0, 0.7, "+", fs=13, **BLUE)
arrow((10.3, 5.2), (11.0, 5.2), "9bit")
box(11.0, 4.85, 0.85, 0.7, "rnd/\nsat", **BLUE)
arrow((11.85, 5.2), (11.95, 5.2))
ax.text(11.6, 4.55, "y[n]  8bit", fontsize=9, color="#1a3d6e")

# ---------------- cut + feed bus ----------------
arrow((2.1, 4.85), (2.1, 4.45), "outer taps ×12   8bit", loff=(1.25, -0.25))
box(1.75, 3.95, 0.7, 0.5, "cut", **ORANGE)
ax.plot([2.1, 2.1], [3.95, 3.62], color="k", lw=1.2)
ax.plot([0.5, 2.1], [3.62, 3.62], color="k", lw=1.2)
ax.plot([0.5, 0.5], [3.62, 1.8], color="k", lw=1.2)
ax.text(1.1, 3.7, "6bit", fontsize=8.6, color="#1a3d6e")
arrow((0.5, 3.0), (0.9, 3.0))
arrow((0.5, 1.8), (0.9, 1.8))

# ---------------- fixed subfilters ----------------
box(0.9, 2.65, 3.3, 0.7,
    "v₁ = Σₖ aₖ·(x[n−k] − x[n+k])\nk = 1..6,  fixed CSD  (antisym)",
    fs=8.4, **ORANGE)
box(0.9, 1.45, 3.3, 0.7,
    "v₂ = b₀·x[n] + Σₖ bₖ·(x[n−k] + x[n+k])\nk = 1..2,  fixed CSD  (sym)",
    fs=8.4, **ORANGE)

# ---------------- Horner chain: y = x + mu*(v1 + mu*v2) ----------------
circ(5.3, 1.8, "×", GREEN)
ax.text(5.3, 2.22, "mult 1", fontsize=8.2, color="#2c7a2c", ha="center")
arrow((4.2, 1.8), (5.04, 1.8), "v₂  9bit", loff=(-0.05, 0.14))
circ(6.6, 1.8, "+", GREEN)
arrow((5.56, 1.8), (6.34, 1.8), "9bit", loff=(0, 0.12))
# v1 routes over to the adder
ax.plot([4.2, 6.6], [3.0, 3.0], color="k", lw=1.2)
ax.text(5.4, 3.13, "v₁  9bit", fontsize=8.6, ha="center", color="#1a3d6e")
arrow((6.6, 3.0), (6.6, 2.06))
circ(7.9, 1.8, "×", GREEN)
ax.text(7.9, 2.22, "mult 2", fontsize=8.2, color="#2c7a2c", ha="center")
arrow((6.86, 1.8), (7.64, 1.8), "10bit", loff=(0, 0.12))
arrow((8.16, 1.8), (9.8, 1.8), "c = μ·v₁ + μ²·v₂\n8bit (rnd)",
      loff=(0, 0.2))
ax.plot([9.8, 9.8], [1.8, 4.85], color="k", lw=1.2)
arrow((9.8, 4.7), (9.8, 4.85))

# ---------------- mu register (software-written) ----------------
ax.add_patch(FancyBboxPatch((5.0, 0.3), 3.4, 0.75,
                            boxstyle="round,pad=0.06", fc="none",
                            ec="#7a3d8a", lw=1.2, linestyle=(0, (5, 3))))
ax.text(5.12, 0.62, "software:\nwrite μ per\ncalibration", fontsize=8,
        color="#7a3d8a", style="italic", va="center")
box(6.5, 0.4, 1.6, 0.5, "μ register  8bit", fs=8.6, **PURPLE)
ax.add_patch(FancyArrowPatch((6.5, 0.75), (5.3, 1.54), arrowstyle="-|>",
                             mutation_scale=10, lw=1.0, color="#7a3d8a",
                             linestyle=(0, (4, 3))))
ax.add_patch(FancyArrowPatch((8.1, 0.75), (7.9, 1.54), arrowstyle="-|>",
                             mutation_scale=10, lw=1.0, color="#7a3d8a",
                             linestyle=(0, (4, 3))))
ax.text(8.35, 1.15, "same μ to both\n(quasi-static)", fontsize=7.8,
        color="#7a3d8a")

ax.text(0.15, 0.05,
        "Horner form:  y = x + μ·(v₁ + μ·v₂)  ≡  x + μ·v₁ + μ²·v₂"
        "   ·   the 2 multipliers are the only programmable elements",
        fontsize=8, color="#555")
ax.set_title("Traditional 2nd-order Farrow, |skew| ≤ 1 ps: "
             "2 programmable multipliers · worst-case MSE −27.2 dB "
             "(d 6bit)", fontsize=10.5)
fig.tight_layout()
fig.savefig("blockdiagram_farrow_1ps.png", dpi=170)
print("saved blockdiagram_farrow_1ps.png")
