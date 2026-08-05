#!/usr/bin/env python3
"""Traditional 2nd-order Farrow (2 programmable multipliers, Horner form)
for |skew| <= 1 ps, with the v1/v2 CSD coefficients expanded.
Coefficient values verified in-loop: worst-case MSE -27.2 dB (d 6bit)."""

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
ax.plot([2.1, 2.1], [3.95, 3.75], color="k", lw=1.2)
ax.plot([0.5, 2.1], [3.75, 3.75], color="k", lw=1.2)
ax.plot([0.5, 0.5], [3.75, 1.7], color="k", lw=1.2)
ax.text(1.1, 3.83, "6bit", fontsize=8.6, color="#1a3d6e")
arrow((0.5, 3.05), (0.9, 3.05))
arrow((0.5, 1.7), (0.9, 1.7))

# ---------------- fixed subfilters with expanded CSD coefficients ------
box(0.9, 2.35, 3.6, 1.35,
    "v₁ = Σₖ aₖ·(x[n−k] − x[n+k]),  k = 1..6\n"
    "a₁ = 1−2⁻⁴+2⁻⁶ = 61/64\n"
    "a₂ = −2⁻¹+2⁻⁴ = −7/16\n"
    "a₃ = 2⁻²+2⁻⁶ = 17/64\n"
    "a₄ = −2⁻²+2⁻⁴+2⁻⁷ = −23/128\n"
    "a₅ = 2⁻³−2⁻⁸ = 31/256\n"
    "a₆ = −2⁻⁴−2⁻⁶−2⁻⁹ = −41/512",
    fs=7.0, **ORANGE)
ax.text(4.6, 3.78, "antisym, fixed CSD", fontsize=7.6, color="#b07818")
box(0.9, 0.95, 3.6, 1.1,
    "v₂ = b₀·x[n] + Σₖ bₖ·(x[n−k] + x[n+k]),  k = 1..2\n"
    "b₀ = −1−2⁻¹−2⁻⁵ = −49/32\n"
    "b₁ = 1−2⁻³+2⁻⁵ = 29/32\n"
    "b₂ = −2⁻²+2⁻⁴+2⁻⁶ = −11/64",
    fs=7.0, **ORANGE)
ax.text(4.6, 2.12, "sym, fixed CSD", fontsize=7.6, color="#b07818")

# ---------------- Horner chain: y = x + mu*(v1 + mu*v2) ----------------
circ(5.5, 1.55, "×", GREEN)
ax.text(5.5, 1.97, "mult 1", fontsize=8.2, color="#2c7a2c", ha="center")
arrow((4.5, 1.55), (5.24, 1.55), "v₂  9bit", loff=(-0.05, 0.14), fs=8)
circ(6.7, 1.55, "+", GREEN)
arrow((5.76, 1.55), (6.44, 1.55), "9bit", loff=(0, 0.12), fs=8)
ax.plot([4.5, 6.7], [3.02, 3.02], color="k", lw=1.2)
ax.text(5.6, 3.15, "v₁  9bit", fontsize=8.6, ha="center", color="#1a3d6e")
arrow((6.7, 3.02), (6.7, 1.81))
circ(7.9, 1.55, "×", GREEN)
ax.text(7.9, 1.97, "mult 2", fontsize=8.2, color="#2c7a2c", ha="center")
arrow((6.96, 1.55), (7.64, 1.55), "10bit", loff=(0, 0.12), fs=8)
arrow((8.16, 1.55), (9.8, 1.55), "c = μ·v₁ + μ²·v₂\n8bit (rnd)",
      loff=(0, 0.22), fs=8.4)
ax.plot([9.8, 9.8], [1.55, 4.85], color="k", lw=1.2)
arrow((9.8, 4.7), (9.8, 4.85))

# ---------------- mu register (software-written) ----------------
ax.add_patch(FancyBboxPatch((5.0, 0.28), 3.4, 0.66,
                            boxstyle="round,pad=0.06", fc="none",
                            ec="#7a3d8a", lw=1.2, linestyle=(0, (5, 3))))
ax.text(5.12, 0.6, "software:\nwrite μ per\ncalibration", fontsize=7.8,
        color="#7a3d8a", style="italic", va="center")
box(6.5, 0.36, 1.6, 0.5, "μ register  8bit", fs=8.6, **PURPLE)
ax.add_patch(FancyArrowPatch((6.5, 0.65), (5.5, 1.29), arrowstyle="-|>",
                             mutation_scale=10, lw=1.0, color="#7a3d8a",
                             linestyle=(0, (4, 3))))
ax.add_patch(FancyArrowPatch((8.1, 0.65), (7.9, 1.29), arrowstyle="-|>",
                             mutation_scale=10, lw=1.0, color="#7a3d8a",
                             linestyle=(0, (4, 3))))
ax.text(8.5, 0.95, "same μ to both\n(quasi-static)", fontsize=7.8,
        color="#7a3d8a")

ax.text(0.15, 0.05,
        "Horner form:  y = x + μ·(v₁ + μ·v₂)  ≡  x + μ·v₁ + μ²·v₂"
        "   ·   the 2 multipliers are the only programmable elements"
        "   ·   CSD coefficients verified: −27.2 dB worst case",
        fontsize=7.8, color="#555")
ax.set_title("Traditional 2nd-order Farrow, |skew| ≤ 1 ps: "
             "2 programmable multipliers · worst-case MSE −27.2 dB "
             "(d 6bit)", fontsize=10.5)
fig.tight_layout()
fig.savefig("blockdiagram_farrow_1ps.png", dpi=170)
print("saved blockdiagram_farrow_1ps.png")
