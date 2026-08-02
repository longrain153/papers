#!/usr/bin/env python3
"""Block diagram of the final power-optimized skew compensator with
node bit-widths (verified bit-exact by sim_fixedpoint.py)."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(13.5, 7.2))
ax.set_xlim(0, 13.5)
ax.set_ylim(0, 7.2)
ax.axis("off")


def box(x, y, w, h, text, fc="#eef3fb", ec="#2b5aa0", fs=8.6, style="round"):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"{style},pad=0.06",
                                fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs)


def arrow(x1, y1, x2, y2, label="", dy=0.14, fs=8, color="k", ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                 arrowstyle="-|>", mutation_scale=11,
                                 lw=1.2, color=color, linestyle=ls))
    if label:
        ax.text((x1 + x2) / 2, max(y1, y2) + dy, label, ha="center",
                fontsize=fs, color="#1a3d6e")


# ---------------- main path (top) ----------------
arrow(0.1, 6.3, 1.0, 6.3, "x[n]  s8\nLSB=FS/128", dy=0.18)
box(1.0, 5.9, 2.6, 0.8, "delay line\n7 taps × s8  (z⁻¹ ×6)")
arrow(3.6, 6.3, 10.6, 6.3, "center tap x[n−3]   s8", dy=0.12)
box(10.6, 5.9, 1.4, 0.8, "+\noutput adder")
arrow(12.0, 6.3, 12.7, 6.3)
box(12.7, 5.9, 0.7, 0.8, "rnd\nsat")
ax.text(13.05, 5.6, "y[n]  s8", ha="center", fontsize=8.6, color="#1a3d6e")
ax.add_patch(FancyArrowPatch((13.05, 5.9), (13.05, 5.35),
                             arrowstyle="-|>", mutation_scale=11, lw=1.2))

# ---------------- correction path ----------------
box(1.0, 4.7, 2.6, 0.7,
    "drop 3 LSBs (6 taps)\n→ s5, LSB = FS/16", fc="#fdf3e3", ec="#b07818")
arrow(2.3, 5.9, 2.3, 5.4, "outer taps ±1, ±2, ±3   6 × s8")

sub_x = [0.7, 2.05, 3.4]
for i, (sx, lbl) in enumerate(zip(sub_x, ("d₁ = x[−1]−x[+1]",
                                          "d₂ = x[−2]−x[+2]",
                                          "d₃ = x[−3]−x[+3]"))):
    box(sx, 3.6, 1.25, 0.7, f"-\n{lbl}", fc="#fdf3e3", ec="#b07818", fs=7.6)
    arrow(sx + 0.62, 4.7, sx + 0.62, 4.3, "s5×2")
    arrow(sx + 0.62, 3.6, sx + 0.62, 3.15,
          "s6\nLSB=FS/16", dy=-0.62, fs=7.3)

box(0.7, 2.35, 3.95, 0.8,
    "hardwired shift-add  (no mux)\n"
    "v = d₁ − (d₂≫1) + (d₂≫4) + (d₃≫2)",
    fc="#fdf3e3", ec="#b07818")
arrow(4.65, 2.75, 5.7, 2.75, "v  s8\nLSB=FS/32", dy=0.18)

# two programmable shifters
box(5.7, 3.0, 2.0, 0.75,
    "prog shift A\n5:1 mux {off,≫4,≫5,≫6,≫7}", fc="#e8f6e8", ec="#2c7a2c",
    fs=7.8)
box(5.7, 1.7, 2.0, 0.75,
    "prog shift B\n5:1 mux {off,≫4,≫5,≫6,≫7}", fc="#e8f6e8", ec="#2c7a2c",
    fs=7.8)
arrow(5.6, 2.75, 5.7, 3.35)
arrow(5.6, 2.75, 5.7, 2.1)
arrow(7.7, 3.37, 8.7, 3.0, "tA  s6, LSB=FS/128", fs=7.3)
arrow(7.7, 2.1, 8.7, 2.6, "tB  s6, LSB=FS/128", dy=-0.35, fs=7.3)

box(8.7, 2.5, 1.5, 0.75, "± combine\n(static add/sub)",
    fc="#e8f6e8", ec="#2c7a2c", fs=7.8)
arrow(10.2, 2.9, 11.3, 2.9, "c = μ̂·v   s7\nLSB=FS/128", dy=0.16, fs=7.6)
ax.add_patch(FancyArrowPatch((11.3, 2.9), (11.3, 5.9),
                             arrowstyle="-|>", mutation_scale=11, lw=1.2))
ax.text(11.55, 4.4, "s7", fontsize=7.6, color="#1a3d6e")
ax.text(11.15, 6.05, "s9 → rnd/sat", fontsize=7.2, ha="right",
        color="#1a3d6e")

# ---------------- config / firmware (bottom) ----------------
box(0.7, 0.35, 1.7, 0.7, "μ register\ns8 (step 1/256)\n|code| ≤ 24",
    fc="#f5e9f7", ec="#7a3d8a", fs=7.4)
arrow(2.4, 0.7, 3.3, 0.7)
box(3.3, 0.35, 2.6, 0.7,
    "firmware SPT LUT (49 entries)\nμ̂ = (±2ᵖ ± 2^q)/256, p,q∈{0..4}",
    fc="#f5e9f7", ec="#7a3d8a", fs=7.4)
arrow(5.9, 0.7, 6.9, 0.7)
box(6.9, 0.35, 2.9, 0.7,
    "config regs (double-buffered)\n2 × (sign 1b + select 3b) = 8 bit",
    fc="#f5e9f7", ec="#7a3d8a", fs=7.4)
for tx, ty in ((6.7, 1.7), (6.7, 3.0), (9.45, 2.5)):
    ax.add_patch(FancyArrowPatch((8.35, 1.05), (tx, ty),
                                 arrowstyle="-|>", mutation_scale=10,
                                 lw=1.0, color="#7a3d8a",
                                 linestyle=(0, (4, 3))))
ax.text(8.6, 1.35, "static select lines (no toggling)", fontsize=7.4,
        color="#7a3d8a")

ax.text(0.15, 0.05,
        "s N = N-bit signed two's complement · FS = full-scale amplitude of"
        " x · main path assumed s8 · bit-exact worst-case MSE = −28.35 dB"
        " (sim_fixedpoint.py)",
        fontsize=7.6, color="#555")
ax.set_title("Online-tunable skew pre-compensator, |skew| ≤ 0.35 ps "
             "@ 265.5 GSa/s — multiplierless, power-optimized "
             "(one parallel lane shown)", fontsize=10.5)
fig.tight_layout()
fig.savefig("blockdiagram.png", dpi=170)
print("saved blockdiagram.png")
