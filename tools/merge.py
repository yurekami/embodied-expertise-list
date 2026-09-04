"""Merge the research batches (research/[A-E].json) into data/orgs.json under one curation table.

Every researched name must appear in CURATE, DROP or MERGE, so nothing slips in unreviewed.
Curation keys: rank (int), radar (bool), tier (gen|site|open|layer), tags (list), plus any field override.
"""
import glob, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RESEARCH = os.path.join(HERE, "..", "..", "research")
OUT = os.path.join(HERE, "..", "data", "orgs.json")

DROP = {
    "Manus",                # 2019 round, mocap gloves: weak fit
    "Angel Robotics",       # rehab exoskeletons, not embodied expertise
    "Physical Superintelligence",  # physics-sim lab for data-center optimization, not embodied (launched 2026-09-01)
}
FUNDING_EVENT = re.compile(r"^(series [a-z]|seed|raises|in talks|\$|\d+(\.\d+)?M|out of stealth with \$|emerges from stealth with \$)", re.I)
RENAME = {
    "Meta Reality Labs (Project Aria / Ego4D)": "Meta",
    "Meta FAIR": "Meta",
    "Apple (EgoDex)": "Apple",
    "AgiBot (Zhiyuan Robotics)": "AgiBot",
    "AgiBot (智元机器人)": "AgiBot",
    "Open X-Embodiment (Google DeepMind + 33 labs)": "Open X-Embodiment",
    "Stanford UMI (REAL Lab / Shuran Song)": "Stanford REAL Lab (UMI)",
    "1X": "1X Technologies",
    "Galbot (银河通用)": "Galbot",
    "Tesla (Optimus)": "Tesla",
    "Boston Dynamics (Hyundai)": "Boston Dynamics",
}
# name -> curation / overrides
CURATE = {
    # ---- frontier labs (shown apart) ----
    "Google DeepMind": dict(tier="gen", tags=["Practice", "Deploy"]),
    "Toyota Research Institute": dict(tier="gen", tags=["Practice"]),
    "Meta": dict(tier="gen", tags=["Observe", "Practice"], oss=True),
    "OpenAI": dict(tier="gen", tags=["Observe", "Practice"]),
    "Amazon": dict(tier="site", tags=["Deploy", "Practice", "Body"]),
    "NVIDIA": dict(tier="layer", tags=["Practice", "Deploy", "Silicon"]),
    "Intrinsic": dict(tier="site", tags=["Deploy", "Practice"]),
    "Qualcomm": dict(tier="layer", tags=["Deploy", "Silicon"]),
    "Scale AI": dict(tier="layer", tags=["Observe"]),
    "Apple": dict(tier="layer", tags=["Observe"]),
    "Tesla": dict(tier="gen", tags=["Body", "Practice", "Silicon"], head="", raisedD="–", valD="–"),
    # ---- enabling layers, n/r ----
    "Encord": dict(tier="layer", tags=["Observe"]),
    "General Intuition": dict(tier="gen", tags=["Observe", "Practice"]),
    "XDOF": dict(tier="layer", tags=["Observe"]),
    "Build AI": dict(tier="layer", tags=["Observe"], rounds=[]),
    "Config": dict(tier="layer", tags=["Observe"]),
    "Viam": dict(tier="layer", tags=["Deploy", "Improve"], stage="Series C+"),
    "Foxglove": dict(tier="layer", tags=["Observe", "Deploy"]),
    "Rerun": dict(tier="layer", tags=["Observe"]),
    "Rebellions": dict(tier="layer", tags=["Silicon"]),
    "DEEPX": dict(tier="layer", tags=["Silicon", "Deploy"]),
    "SiMa.ai": dict(tier="layer", tags=["Silicon", "Deploy"]),
    "Innatera": dict(tier="layer", tags=["Silicon", "Improve"]),
    "Ineffable Intelligence": dict(seg="infra", tier="gen", tags=["Practice", "Improve"], stage="Seed",
                                   raised=1100, raisedD="$1.1B", raisedC="hi", val=5.1, valD="$5.1B", valC="hi"),
    "Core Automation": dict(seg="infra", tier="gen", tags=["Practice", "Improve"], stage="Seed",
                            raised=532, raisedD="~$532M", raisedC="hi", val=3.62, valD="$3.62B", valC="med",
                            sources=[["SEC Form D · 2026-07", "https://app.edgar.tools/filing/2148145/0002148145-26-000001/formd"],
                                     ["Forge financing history", "https://forgeglobal.com/core-automation_ipo/"],
                                     ["Ex-OpenAI researcher Jerry Tworek launches Core Automation · The Decoder", "https://the-decoder.com/ex-openai-researcher-jerry-tworek-launches-core-automation-to-build-the-most-automated-ai-lab-in-the-world/"]],
                            url="https://the-decoder.com/ex-openai-researcher-jerry-tworek-launches-core-automation-to-build-the-most-automated-ai-lab-in-the-world/",
                            rounds=[{"date": "2026-04", "amountM": 100, "label": "First round", "src": 1},
                                    {"date": "2026-07", "amountM": 432, "label": "$432M raise at $3.62B (SEC filing)", "src": 0}],
                            events=[{"date": "2026-01", "label": "Jerry Tworek leaves OpenAI to found Core Automation", "src": 2}]),
    "Naver Labs": dict(tier="site", tags=["Practice", "Deploy", "Body"]),
    # ---- research ----
    "Open X-Embodiment": dict(seg="academic", tier="layer", tags=["Observe", "Practice"], head="", hq="Mountain View, USA"),
    "Stanford REAL Lab (UMI)": dict(seg="academic", tier="layer", tags=["Observe"], head="", founded=2024),
    # ---- robot makers, n/r ----
    "Sanctuary AI": dict(tier="gen", tags=["Body", "Observe", "Practice"]),
    "AgiBot": dict(tier="gen", tags=["Body", "Observe", "Practice"], oss=True, headC="lo",
                   raised=84, raisedD="$84M+ (most rounds undisclosed)", raisedC="med", val=2.1, valD="$2.1B (2025-03)", valC="hi"),
    "Figure AI": dict(tier="gen", tags=["Body", "Practice", "Observe"]),
    "1X Technologies": dict(tier="gen", tags=["Body", "Practice", "Improve"], oss=True, headC="lo",
                            raised=136.5, raisedD="$136.5M (confirmed)", raisedC="hi", val=0.82, valD="$820M (2024-01)", valC="hi",
                            skip_rounds=["Series C (reported"]),
    "Apptronik": dict(tier="gen", tags=["Body", "Observe", "Deploy"], val=5.4, valD="~$5.4B", valC="med", raisedD="~$963M"),
    "Agility Robotics": dict(tier="site", tags=["Body", "Deploy", "Improve"]),
    "Boston Dynamics": dict(tier="gen", tags=["Body", "Deploy", "Practice"], raisedD="$917M", valD="$1.1B (2020)"),
    "Unitree": dict(tier="gen", tags=["Body", "Practice"], oss=True, raisedD="~$1.1B", val=53, valD="$53B (mkt cap)", valC="med"),
    "Galbot": dict(tier="site", tags=["Body", "Practice", "Deploy"]),
    "UBTech": dict(tier="site", tags=["Body", "Deploy"], lvl=3, raisedD="$1.34B (pre-IPO)", val=5.1, valD="$5.1B (mkt cap)", valC="med"),
    "The Bot Company": dict(tier="gen", tags=["Body", "Practice"], val=2.0, valD="$2B (2025-03)", valC="hi", raisedD="$300M", headC="lo"),
    "Sunday Robotics": dict(tier="gen", tags=["Body", "Observe", "Practice"], head="", hq="San Francisco, USA"),
    "Rainbow Robotics": dict(tier="gen", tags=["Body"]),
    "Doosan Robotics": dict(tier="site", tags=["Body"]),
    "WIRobotics": dict(tier="gen", tags=["Body"]),
    # ---- the index (deployability infra, ranked) and the radar ----
    "Physical Intelligence": dict(rank=1, tier="gen", tags=["Practice", "Deploy"]),
    "Skild AI": dict(rank=2, tier="gen", tags=["Practice", "Deploy"]),
    "Sereact": dict(rank=3, tier="site", tags=["Practice", "Deploy", "Improve"]),
    "Generalist AI": dict(rank=4, tier="gen", tags=["Practice", "Observe"]),
    "Field AI": dict(rank=5, tier="open", tags=["Practice", "Deploy", "Improve"]),
    "Covariant": dict(rank=6, tier="site", tags=["Practice", "Deploy", "Improve"], acq=True),
    "Dyna Robotics": dict(rank=7, tier="site", tags=["Practice", "Deploy", "Improve"]),
    "Micropsi Industries": dict(rank=8, tier="site", tags=["Observe", "Practice", "Deploy"]),
    "Genesis AI": dict(rank=9, tier="gen", tags=["Observe", "Practice"], hq="Paris, France + Palo Alto, USA"),
    "Mimic Robotics": dict(rank=10, tier="gen", tags=["Practice", "Observe"]),
    "CarbonSix": dict(rank=11, tier="site", tags=["Practice", "Improve", "Deploy"]),
    "RLWRLD": dict(rank=12, tier="site", tags=["Practice", "Improve"]),
    "Robai": dict(radar=True, tier="gen", tags=["Practice", "Improve"], rounds=[]),
    "Affordance Inc.": dict(radar=True, tier="site", tags=["Observe", "Practice", "Deploy", "Improve"],
                            url="https://arxiv.org/abs/2604.28197",
                            sources=[["OmniRobotHome · arXiv 2604.28197 · 2026-04", "https://arxiv.org/abs/2604.28197"]],
                            events=[{"date": "2026-04", "label": "OmniRobotHome preprint (arXiv 2604.28197)", "src": 0}],
                            note="Paid pilots reported: $10k closed and >$200k milestone-based under negotiation; top-5 finalist in the AMD-backed agentic chip-design contest (results 2026-09-09). Angel round of $1.1M targeted as a six-month bridge to seed. All figures self-reported from the company deck (v13), not independently verified."),
}
DATE = re.compile(r"^\d{4}-\d{2}$")


def normalize(o):
    o["stage"] = {"Series C": "Series C+", "Series D": "Series C+", "Series E": "Series C+"}.get(o["stage"], o["stage"])
    if o.get("head", "").lower().startswith("n/a"):
        o["head"] = ""
    skip = tuple(o.pop("skip_rounds", []))
    for r in o.get("rounds", []) + o.get("events", []):
        if re.match(r"^\d{4}-\d{2}-\d{2}$", r["date"]):
            r["date"] = r["date"][:7]
    o["rounds"] = [r for r in o.get("rounds", []) if DATE.match(r["date"]) and not r["label"].startswith(skip)]
    o["events"] = [e for e in o.get("events", []) if DATE.match(e["date"]) and not FUNDING_EVENT.match(e["label"])]
    for k in ("raisedD", "valD"):            # table cells hold one figure; the story lives in note/timeline
        v = o.get(k, "–")
        if len(v) > 16 or v.lower().startswith(("n/a", "public", "–", "-")):
            m = re.match(r"^[~>]?\$[\d.,]+\s?[MBK]?\+?", v)
            o[k] = m.group(0) if m else ("undisclosed" if "undisclosed" in v else "–")
    o.setdefault("radar", False)
    o.setdefault("rank", None)
    o["dom"] = o["dom"][:3]
    return o


def merge_meta(parts):
    base = next(p for p in parts if "V-JEPA" in p["loop"])
    aria = next(p for p in parts if p is not base)
    off = len(base["sources"])
    base["sources"] = base["sources"] + aria["sources"]
    for e in aria["events"]:
        base["events"].append({**e, "src": e["src"] + off})
    base["loop"] = base["loop"] + " " + aria["loop"]
    base["note"] = "One entry for Meta's two relevant programs: FAIR (V-JEPA world models, open weights) and Reality Labs (Project Aria glasses, Ego4D / Ego-Exo4D egocentric datasets). " + base["note"]
    base["dom"] = ["Data", "Manipulation", "Sim"]
    return base


def main():
    raw = []
    for f in sorted(glob.glob(os.path.join(RESEARCH, "[A-E].json"))):
        raw += json.load(io.open(f, encoding="utf-8"))
    by = {}
    for o in raw:
        o["name"] = RENAME.get(o["name"], o["name"])
        if o["name"] in DROP:
            continue
        by.setdefault(o["name"], []).append(o)
    orgs = []
    for name, parts in by.items():
        if name == "Meta" and len(parts) > 1:
            o = merge_meta(parts)
        elif len(parts) > 1:
            o = max(parts, key=lambda p: len(p.get("rounds", [])) * 10 + len(p["sources"]))
            for p in parts:
                if p is o:
                    continue
                off = len(o["sources"])
                o["sources"] += p["sources"]
                o["events"] += [{**e, "src": e["src"] + off} for e in p.get("events", []) if e["label"] not in {x["label"] for x in o["events"]}]
        else:
            o = parts[0]
        if name not in CURATE:
            sys.exit(f"uncurated: {name}")
        o.update(CURATE[name])
        orgs.append(normalize(o))
    missing = [n for n in CURATE if n not in by]
    if missing:
        print("curated but not researched:", ", ".join(missing))
    ranks = [o["rank"] for o in orgs if o["rank"]]
    assert len(ranks) == len(set(ranks)), "duplicate ranks"
    orgs.sort(key=lambda o: (o["rank"] or 99, o["name"]))
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(json.dumps(orgs, ensure_ascii=False, indent=1))
    print(f"wrote {len(orgs)} orgs, {len(ranks)} ranked, {sum(o['radar'] for o in orgs)} radar")


if __name__ == "__main__":
    main()
