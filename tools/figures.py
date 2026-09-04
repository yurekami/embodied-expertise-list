"""data/orgs.json -> assets/figures/<name>.png + .pdf (paper) and <name>.dark.png (the black page).

  python tools/figures.py

House style of ChenLiu-1996/figures4papers (scientific-figure-making): Helvetica/Arial, top and right
spines off, frameless legends, blue for the pure-plays the list ranks, red for robot makers, neutral
for frontier labs, green for research groups; tight_layout(pad=2), 300 dpi.
"""
import io, json, logging, os, re, sys

import matplotlib
matplotlib.use("Agg")
logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)   # Helvetica is only a fallback
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import patheffects
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import ORGS, ROOT, SHORT

OUT = os.path.join(ROOT, "assets", "figures")
PALETTE = {"blue_main": "#0F4D92", "blue_secondary": "#3775BA", "green_3": "#8BCF8B", "red_2": "#E9A6A1",
           "red_strong": "#B64342", "neutral": "#CFCECE", "highlight": "#FFD700"}
THEMES = {"": dict(ink="black", muted="#767676", face="white", grid="white", blue=PALETTE["blue_main"]),
          ".dark": dict(ink="#F2F3F1", muted="#8E8E8E", face="none", grid="black", blue=PALETTE["blue_secondary"])}
SEGS = [("infra", "Deployability pure-plays"), ("body", "Robot makers"),
        ("frontier", "Frontier labs & corporates"), ("academic", "Research groups")]
LAYERS = ["Observe", "Practice", "Deploy", "Improve", "Body", "Silicon"]
SCOPES = [("gen", "General\ntasks"), ("site", "Site-bounded\nexpertise"), ("open", "Open-world\nexpertise"),
          ("layer", "Enabling\nlayer")]
LEVELS = ["L0 research", "L1 demo", "L2 pilot", "L3 paid deployment", "L4 fleet"]
MONTHS = [f"{y}-{m:02d}" for y in range(2022, 2027) for m in range(1, 13)][:57]   # 2022-01 .. 2026-09
# Field milestones placed on the money curve; each '*' lifts the label one step (as in figures4papers),
# each '<' or '>' slides it 1.5 months sideways (the arrow still points at the month).
MILESTONES = {"2023-07": "RT-2", "2023-10": "Open X-Embodiment*", "2024-02": "UMI", "2024-09": "Amazon hires\nCovariant's founders*",
              "2024-10": "π0", "2025-03": "Gemini Robotics,\nGR00T N1*", "2025-09": "DYNA-1: 99%\nover 24 h*<",
              "2025-10": "NEO pre-orders**>", "2026-04": "Sereact:\n200+ live", "2026-06": "Agility SPAC*",
              "2026-08": "GEN-1.5\n'physical prompting'**"}


def style(T):
    plt.rcParams.update({"font.family": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"], "font.size": 16,
                         "axes.spines.right": False, "axes.spines.top": False, "axes.linewidth": 2,
                         "legend.frameon": False, "svg.fonttype": "none", "text.color": T["ink"],
                         "axes.labelcolor": T["ink"], "axes.edgecolor": T["ink"], "xtick.color": T["ink"],
                         "ytick.color": T["ink"], "figure.facecolor": T["face"], "axes.facecolor": T["face"],
                         "savefig.facecolor": T["face"]})


def seg_colors(T):
    return {"infra": T["blue"], "body": PALETTE["red_2"], "frontier": PALETTE["neutral"], "academic": PALETTE["green_3"]}


def save(fig, name, suffix):
    fig.tight_layout(pad=2)
    fig.savefig(os.path.join(OUT, f"{name}{suffix}.png"), dpi=200 if suffix else 300)
    if not suffix:
        fig.savefig(os.path.join(OUT, f"{name}.pdf"))
    plt.close(fig)


def startups(orgs):
    """Same rule as the site's takeoff chart: no labs, no public or corporate balance sheets."""
    return [o for o in orgs if o["seg"] in ("infra", "body") and o["stage"] not in ("Public", "Corporate")]


def fig_takeoff(orgs, T, suffix):
    cum = {}
    for seg in ("body", "infra"):
        monthly = np.zeros(len(MONTHS))
        for o in startups(orgs):
            for r in o["rounds"] if o["seg"] == seg else []:
                if r.get("amountM") and r["date"] in MONTHS:
                    monthly[MONTHS.index(r["date"])] += r["amountM"]
        cum[seg] = np.cumsum(monthly) / 1000
    body, total = cum["body"], cum["body"] + cum["infra"]
    assert abs(total[-1] * 1000 - sum(r["amountM"] for o in startups(orgs) for r in o["rounds"] if r["date"] >= "2022")) < 1e-6

    fig, ax = plt.subplots(figsize=(14, 7.5))
    x = np.arange(len(MONTHS))
    ax.fill_between(x, body, total, color=T["blue"], alpha=.55, lw=0)
    ax.fill_between(x, 0, body, color=PALETTE["red_2"], alpha=.75, lw=0)
    ax.plot(x, total, lw=3, color=T["blue"])
    ax.plot(x, body, lw=3, color=PALETTE["red_strong"])
    ax.set_xticks(x[::6]); ax.set_xticklabels(MONTHS[::6]); ax.set_xlim(0, len(MONTHS) - 1)
    ax.set_ylim(0, total.max() * 1.5)
    ax.set_ylabel("Disclosed rounds since 2022,\ncumulative ($B)")
    y0, y1 = ax.get_ylim()
    for d, label in MILESTONES.items():
        i, dx = MONTHS.index(d), 1.5 * (label.count(">") - label.count("<"))
        ax.annotate(re.sub("[*<>]", "", label), xy=(i, total[i]),
                    xytext=(i + dx, total[i] + (1 + .8 * label.count("*")) * .09 * (y1 - y0)),
                    ha="center", va="bottom", fontsize=11,
                    arrowprops=dict(arrowstyle="-|>", lw=1.3, color=T["ink"], shrinkA=0, shrinkB=0, mutation_scale=15))
    ax.legend([Line2D([], [], color=T["blue"], lw=8, alpha=.7), Line2D([], [], color=PALETTE["red_2"], lw=8)],
              [f"Deployability pure-plays  (${cum['infra'][-1]:.1f}B)", f"Robot makers  (${body[-1]:.1f}B)"], loc="upper left")
    save(fig, "takeoff", suffix)


def fig_evidence(orgs, T, suffix):
    M = np.zeros((5, 4))
    for o in orgs:
        M[o["lvl"], o["target"] - 1] += 1
    assert M.sum() == len(orgs)
    shown = np.where(np.arange(1, 5)[None, :] >= np.arange(5)[:, None], M, np.nan)   # aimed >= shown
    cmap = plt.get_cmap("Blues").copy(); cmap.set_bad((0, 0, 0, 0))

    fig, ax = plt.subplots(figsize=(9.5, 8))
    im = ax.imshow(shown, cmap=cmap, vmin=0, vmax=M.max())
    for i in range(5):
        for j in range(4):
            if not np.isnan(shown[i, j]):
                ax.text(j, i, int(M[i, j]), ha="center", va="center", fontsize=20,
                        color="white" if M[i, j] > M.max() / 2 else "black")
    for k in range(1, 5):   # shown == aimed
        ax.add_patch(Rectangle((k - 1.5, k - .5), 1, 1, fill=False, edgecolor=T["ink"], lw=2.5, zorder=3))
    ax.set_xticks(np.arange(-.5, 4), minor=True); ax.set_yticks(np.arange(-.5, 5), minor=True)
    ax.grid(which="minor", color=T["grid"], lw=2); ax.tick_params(which="both", length=0)
    ax.set_xticks(range(4)); ax.set_xticklabels([f"{LEVELS[k]}\n(n={int(M[:, k - 1].sum())})" for k in range(1, 5)], fontsize=13)
    ax.set_yticks(range(5)); ax.set_yticklabels([f"{LEVELS[k]}\n(n={int(M[k].sum())})" for k in range(5)], fontsize=13)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xlabel("Level publicly aimed for"); ax.set_ylabel("Level shown")
    ax.set_title("Outlined cells: already at the level aimed for", fontsize=12, loc="left", color=T["muted"], pad=10)
    cb = fig.colorbar(im, ax=ax, fraction=.046, pad=.04)
    cb.set_label("Organizations"); cb.set_ticks(range(0, int(M.max()) + 1, 5)); cb.outline.set_edgecolor(T["ink"])
    save(fig, "evidence_gap", suffix)


def stacked(ax, cats, counts, T):
    """counts: seg -> array over cats. Black-edged stacks, counts inside, totals on top (figures4papers bars)."""
    cols, x, bottom = seg_colors(T), np.arange(len(cats)), np.zeros(len(cats))
    for seg, label in SEGS:
        c = np.asarray(counts[seg], dtype=float)
        ax.bar(x, c, bottom=bottom, color=cols[seg], edgecolor=T["ink"], linewidth=2, width=.72, label=label)
        for xi, (b, v) in enumerate(zip(bottom, c)):
            if v >= 3:
                ax.text(xi, b + v / 2, int(v), ha="center", va="center", fontsize=14, color=PALETTE["highlight"],
                        path_effects=[patheffects.Stroke(linewidth=3, foreground="black"), patheffects.Normal()])
        bottom = bottom + c
    for xi, t in enumerate(bottom):
        ax.text(xi, t + .5, int(t), ha="center", va="bottom", fontsize=15)
    ax.set_xticks(x); ax.set_xticklabels(cats); ax.set_ylim(0, bottom.max() * 1.18)


def fig_coverage(orgs, T, suffix):
    layers = {seg: [sum(1 for o in orgs if o["seg"] == seg and t in o["tags"]) for t in LAYERS] for seg, _ in SEGS}
    scopes = {seg: [sum(1 for o in orgs if o["seg"] == seg and o["tier"] == k) for k, _ in SCOPES] for seg, _ in SEGS}
    assert sum(sum(v) for v in scopes.values()) == len(orgs)
    fig, (a, b) = plt.subplots(2, 1, figsize=(12, 10))
    stacked(a, LAYERS, layers, T); a.set_ylabel("Organizations"); a.set_title("Layer of the loop (entries may span several)", pad=14)
    stacked(b, [n for _, n in SCOPES], scopes, T); b.set_ylabel("Organizations"); b.set_title("Scope of the expertise", pad=14)
    b.set_xlim(a.get_xlim())   # same bar width as the panel above; the legend takes the empty slots
    b.legend(loc="upper right", fontsize=13)
    save(fig, "coverage", suffix)


def fig_capital(orgs, T, suffix):
    rows = [o for o in startups(orgs) if o["raised"] > 0]
    label = {o["name"] for o in rows if o["raised"] >= 400 or o["lvl"] >= 3 or o.get("rank")}
    cols, marker = seg_colors(T), {"infra": "o", "body": "s"}
    nudge = {"Physical Intelligence": (7, 10), "Apptronik": (8, -13), "Core Automation": (7, 7), "General Intuition": (7, -13)}
    fig, ax = plt.subplots(figsize=(13, 7.5))
    for lvl in range(5):
        grp = sorted([o for o in rows if o["lvl"] == lvl], key=lambda o: o["raised"])
        for i, o in enumerate(grp):
            x, y, c = lvl + (((i * .618) % 1) - .5) * .5 * (len(grp) > 1), o["raised"], cols[o["seg"]]
            if o["target"] > lvl:   # whisker to the level publicly aimed for
                ax.plot([x, x + o["target"] - lvl], [y, y], color=c, lw=1.5, alpha=.5, zorder=1)
                ax.plot(x + o["target"] - lvl, y, marker=">", ms=6, color=c, alpha=.7, zorder=1, lw=0)
            ax.scatter(x, y, s=120, marker=marker[o["seg"]], color=c, edgecolor=T["ink"], linewidth=1.2, zorder=3)
            if o["name"] in label:
                ax.annotate(SHORT.get(o["name"], o["name"]), (x, y), xytext=nudge.get(o["name"], (7, 4)),
                            textcoords="offset points", fontsize=10.5)
        if grp:
            ax.hlines(np.median([o["raised"] for o in grp]), lvl - .33, lvl + .33, color=T["ink"], lw=3.5, zorder=2)
    ax.set_yscale("log"); ax.set_ylim(12, 4500); ax.set_xlim(-.6, 4.6)
    ax.set_yticks([10, 100, 1000]); ax.set_yticklabels(["$10M", "$100M", "$1B"]); ax.minorticks_off()
    ax.set_xticks(range(5)); ax.set_xticklabels([l.replace(" ", "\n", 1) for l in LEVELS])
    ax.set_xlabel("Deployment evidence shown"); ax.set_ylabel("Disclosed capital raised")
    ax.legend([Line2D([], [], marker="o", color=cols["infra"], markeredgecolor=T["ink"], ms=11, lw=0),
               Line2D([], [], marker="s", color=cols["body"], markeredgecolor=T["ink"], ms=11, lw=0),
               Line2D([], [], marker=">", color=T["muted"], lw=1.5, alpha=.8, markevery=[-1]),
               Line2D([], [], color=T["ink"], lw=3.5)],
              ["Deployability pure-play", "Robot maker", "Level publicly aimed for", "Median at the level"],
              loc="lower left", fontsize=12.5)
    save(fig, "capital_vs_evidence", suffix)


def main():
    orgs = json.load(io.open(ORGS, encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    for suffix, T in THEMES.items():
        style(T)
        for f in (fig_takeoff, fig_evidence, fig_coverage, fig_capital):
            f(orgs, T, suffix)
    print("wrote", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
