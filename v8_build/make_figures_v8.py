# -*- coding: utf-8 -*-
"""
Figures for Applied Sciences v8.

Figure 1 - component-level support (promoted to Figure 1: it is the primary finding)
Figure 2 - five-state field recoverability, with corrected denominators
Figure 3 - audit-to-design traceability, each requirement labelled by provenance

Outputs svg / png(600 dpi) / pdf into 03_figures/
"""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Patch

OUT = Path(__file__).resolve().parent.parent / "03_figures"
OUT.mkdir(parents=True, exist_ok=True)

INK = "#1F1F1F"
MUTED = "#5A5A5A"
GRID = "#D8D8D8"

# provenance palette (Figure 3)
C_OBS = "#CFE3D6"; E_OBS = "#2F6B45"     # observed
C_PAR = "#FBE7C6"; E_PAR = "#9A6510"     # partly observed
C_DES = "#E4E0F0"; E_DES = "#4B3F72"     # author design assumption
C_STD = "#DCE6F2"; E_STD = "#2C5282"     # standard

# ---------------------------------------------------------------- Figure 1 ---
COMPONENTS = [
    ("Exposure", "unit", 50, 50),
    ("Exposure", "eligibility", 23, 23),
    ("Exposure", "time origin", 16, 16),
    ("Exposure", "coverage", 15, 18),
    ("Follow-up", "calendar interval", 12, 17),
    ("Follow-up", "exposure-qualified\nobservation", 13, 16),
    ("Follow-up", "trace coverage", 3, 3),
    ("Follow-up", "owner", 20, 20),
    ("Closure", "scope", 21, 21),
    ("Closure", "evidence basis", 13, 14),
    ("Closure", "date", 5, 5),
    ("Closure", "owner", 19, 20),
    ("Closure", "uncertainty", 5, 5),
    ("Closure", "reopening rule", 0, 0),
]
FIELD_SHADE = {"Exposure": "#BDD3EE", "Follow-up": "#F2C9A0", "Closure": "#C9DCC0"}


def fig1() -> None:
    fig, ax = plt.subplots(figsize=(8.6, 5.2), dpi=600)
    labels = [f"{c[1]}" for c in COMPONENTS]
    y = list(range(len(COMPONENTS)))
    prim = [c[2] for c in COMPONENTS]
    bound = [c[3] for c in COMPONENTS]
    colors = [FIELD_SHADE[c[0]] for c in COMPONENTS]

    ax.barh(y, prim, color=colors, edgecolor=INK, linewidth=0.6, height=0.62,
            label="Primary")
    for i, (p, b) in enumerate(zip(prim, bound)):
        if b > p:
            ax.barh(i, b - p, left=p, color=colors[i], edgecolor=INK, linewidth=0.6,
                    height=0.62, hatch="///", alpha=0.85)
    ax.invert_yaxis()
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8.6, color=INK)
    ax.set_xlabel("Supported component decisions (n of 100 rows)", fontsize=9.5, color=INK)
    ax.set_xlim(0, 56)
    ax.set_xticks(range(0, 56, 10))
    ax.tick_params(axis="x", labelsize=8.6, colors=INK)
    ax.grid(axis="x", color=GRID, linewidth=0.5, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(INK)

    for i, (p, b) in enumerate(zip(prim, bound)):
        ax.text(b + 1.2, i, str(b), va="center", fontsize=8.2, color=INK)

    # field group headers above each block
    ylim = ax.get_ylim()          # (bottom, top) inverted: bottom > top
    for name in ("Exposure", "Follow-up", "Closure"):
        idx = [i for i, c in enumerate(COMPONENTS) if c[0] == name]
        top = min(idx)            # smallest y index = highest on screen after invert
        ax.text(-0.55, top - 0.62, name.upper(), ha="left", va="center",
                fontsize=8.2, fontweight="bold", color=INK, clip_on=False)
        ax.plot([0.0, 54], [top - 0.44, top - 0.44],
                color=FIELD_SHADE[name], linewidth=2.2, clip_on=False)
    ax.set_ylim(14.9, -1.9)

    ax.legend(handles=[
        Patch(facecolor="#BDD3EE", edgecolor=INK, label="Primary"),
        Patch(facecolor="#BDD3EE", edgecolor=INK, hatch="///", label="Boundary-inclusive addition"),
    ], loc="lower right", fontsize=8.2, frameon=False)
    ax.text(0.0, 14.2, "215 of 1,400 decisions supported (15.4%); 228 (16.3%) boundary-inclusive.",
            fontsize=8.2, color=MUTED, clip_on=False)
    fig.tight_layout()
    save(fig, "Figure1_v8_component_level_support")


# ---------------------------------------------------------------- Figure 2 ---
def fig2() -> None:
    fields = ["Exposure\nopportunity", "Follow-up\nwindow", "Closure\nbasis"]
    data = {  # complete, partial, not recovered, unclear, not applicable
        "Exposure\nopportunity": [4, 46, 44, 5, 1],
        "Follow-up\nwindow": [0, 29, 65, 5, 1],
        "Closure\nbasis": [0, 21, 73, 5, 1],
    }
    colors = ["#2F6B45", "#8FBFA3", "#DCDCDC", "#B0A8C8", "#8C8C8C"]
    labels = ["Complete support", "Partial support", "Not recovered", "Unclear", "Not applicable"]

    fig, ax = plt.subplots(figsize=(7.6, 3.9), dpi=600)
    left = [0.0, 0.0, 0.0]
    for k, (col, lab) in enumerate(zip(colors, labels)):
        vals = [data[f][k] for f in fields]
        ax.barh(fields, vals, left=left, color=col, edgecolor="white",
                linewidth=0.8, height=0.58, label=lab)
        for i, (v, l) in enumerate(zip(vals, left)):
            if v >= 4:
                ax.text(l + v / 2, i, str(v), ha="center", va="center",
                        fontsize=8.6, color="white" if k < 2 else INK,
                        fontweight="bold" if k < 2 else "normal")
        left = [l + v for l, v in zip(left, vals)]
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Retained record rows (N = 100)", fontsize=9.5, color=INK)
    ax.tick_params(axis="both", labelsize=9.0, colors=INK)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(INK)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=5,
              fontsize=8.2, frameon=False)
    fig.text(0.5, 0.965,
             "Applicable N = 99; decision-relevant N = 94 (excludes 5 unclear and 1 not applicable).",
             ha="center", fontsize=8.2, color=MUTED)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    save(fig, "Figure2_v8_field_states")


# ---------------------------------------------------------------- Figure 3 ---
ROWS = [
    ("Component-addressable\nassertions + evidence status",
     "0/99 complete follow-up or closure support", "observed", "T01; T08"),
    ("Closure and reopening as\nappend-only events",
     "reopening rule recovered 0/100 (absence observed;\nappend-only modelling is a design choice)",
     "partly", "T06; T07"),
    ("Conflict coexistence\n(disputes, supersession)",
     "counter-evidence not separately recovered 100/100", "design", "T02"),
    ("Source state separated\nfrom assertion history",
     "23/100 rows with inaccessible URLs", "partly", "T05; T08"),
    ("Withdrawable relations",
     "no withdrawal or retraction recovered", "design", "T04"),
    ("Typed cross-record relations",
     "100 rows to 91 inherited clusters (co-reference\nobserved; type vocabulary author-defined)",
     "partly", "T03"),
    ("Provenance and derivation tracing",
     "PROV-O [11]", "standard", "T08"),
    ("Downstream impact traversal\nafter source invalidation",
     "no corpus observation; task-level test", "design", "T09"),
    ("Historical state restoration",
     "no corpus observation; task-level test", "design", "T10"),
    ("Closure evidence-gap reporting",
     "no corpus observation; task-level test", "design", "T11"),
]
PROV = {
    "observed": (C_OBS, E_OBS, "Observed in audit"),
    "partly": (C_PAR, E_PAR, "Partly observed"),
    "design": (C_DES, E_DES, "Author design assumption"),
    "standard": (C_STD, E_STD, "Standard"),
}


def fig3() -> None:
    fig = plt.figure(figsize=(10.4, 6.9), dpi=600)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1040); ax.set_ylim(706, 0)
    ax.axis("off")

    # header
    for x, t in ((130, "AUDIT BASIS"), (470, "DESIGN REQUIREMENT"), (880, "TEST")):
        ax.text(x, 26, t, ha="center", fontsize=9.2, fontweight="bold", color=MUTED)

    y0 = 52
    h = 54
    gap = 5
    for i, (req, basis, prov, tests) in enumerate(ROWS):
        y = y0 + i * (h + gap)
        fc, ec, plabel = PROV[prov]
        # requirement
        ax.add_patch(FancyBboxPatch((300, y), 340, h, boxstyle="round,pad=3,rounding_size=6",
                                    facecolor=fc, edgecolor=ec, linewidth=1.3, zorder=2))
        ax.text(470, y + h / 2, req, ha="center", va="center", fontsize=8.3,
                color=INK, zorder=3)
        # basis
        ax.text(130, y + h / 2, basis, ha="center", va="center", fontsize=7.7,
                color=INK, zorder=3)
        # test
        ax.text(880, y + h / 2, tests, ha="center", va="center", fontsize=8.4,
                color=INK, zorder=3)
        # arrows
        ax.add_patch(FancyArrowPatch((282, y + h / 2), (298, y + h / 2),
                                     arrowstyle="-|>", mutation_scale=11,
                                     color=ec, linewidth=1.1, zorder=1))
        ax.add_patch(FancyArrowPatch((642, y + h / 2), (838, y + h / 2),
                                     arrowstyle="-|>", mutation_scale=11,
                                     color=MUTED, linewidth=1.0, zorder=1))
        # provenance tag
        ax.text(300, y + h + 0.5, plabel, ha="left", va="bottom", fontsize=6.8,
                color=ec, fontstyle="italic", zorder=3)

    ax.legend(handles=[Patch(facecolor=v[0], edgecolor=v[1], label=v[2]) for v in PROV.values()],
              loc="upper left", fontsize=8.2, frameon=False, ncol=4,
              bbox_to_anchor=(0.02, 0.965))
    ax.text(1030, 690,
            "Tests show representational feasibility on a frozen synthetic payload only; "
            "no accuracy, efficiency or comparative claim is made.",
            ha="right", fontsize=7.4, color=MUTED, fontstyle="italic")
    save(fig, "Figure3_v8_traceability_provenance")


def save(fig, base: str) -> None:
    plt.rcParams["svg.fonttype"] = "none"
    for ext in ("svg", "png", "pdf"):
        fig.savefig(OUT / f"{base}.{ext}", format=ext, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print("wrote", base)


if __name__ == "__main__":
    fig1(); fig2(); fig3()
    for p in sorted(OUT.iterdir()):
        print("  ", p.name, p.stat().st_size)
