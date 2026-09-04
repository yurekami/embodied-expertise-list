"""Embed data/orgs.json into index.html.

  python tools/build.py            # data/orgs.json + template.html -> index.html

The JSON is the source of truth for entries, rounds and events; index.html is the whole site.
"""
import io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORGS = os.path.join(ROOT, "data", "orgs.json")
TEMPLATE = os.path.join(ROOT, "template.html")
OUT = os.path.join(ROOT, "index.html")

SEG = {"infra": "pure", "body": "body", "frontier": "lab", "academic": "research", "nonprofit": "research"}
TIERS = {"gen", "site", "open", "layer"}
TAGS = {"Observe", "Practice", "Deploy", "Improve", "Body", "Silicon"}
SHORT = {"Physical Intelligence": "Physical Int.", "Google DeepMind": "DeepMind", "Boston Dynamics": "Boston Dyn.",
         "Toyota Research Institute": "TRI", "Rainbow Robotics": "Rainbow", "Ineffable Intelligence": "Ineffable",
         "1X Technologies": "1X", "Agility Robotics": "Agility", "Skild AI": "Skild", "Generalist AI": "Generalist",
         "Dyna Robotics": "Dyna", "Genesis AI": "Genesis", "Affordance Inc.": "Affordance", "Sanctuary AI": "Sanctuary",
         "Core Automation": "Core Automation", "Physical Superintelligence": "Physical SI", "Doosan Robotics": "Doosan",
         "The Bot Company": "Bot Company", "Micropsi Industries": "Micropsi", "General Intuition": "Gen. Intuition",
         "Mimic Robotics": "Mimic", "Sunday Robotics": "Sunday", "Stanford REAL Lab (UMI)": "Stanford REAL",
         "Open X-Embodiment": "Open X-Emb."}
# (org, YYYY-MM) of the milestones that get a text label on the takeoff chart; every other event is a bare node
KEY_EVENTS = {("Google DeepMind", "2023-07"), ("Open X-Embodiment", "2023-10"), ("Stanford REAL Lab (UMI)", "2024-02"),
              ("Agility Robotics", "2024-06"), ("Amazon", "2024-09"), ("Physical Intelligence", "2024-10"),
              ("Covariant", "2024-03"), ("Google DeepMind", "2025-03"), ("NVIDIA", "2025-03"),
              ("Apple", "2025-05"), ("Meta", "2025-06"), ("Dyna Robotics", "2025-09"), ("1X Technologies", "2025-10"),
              ("Sunday Robotics", "2025-11"), ("Build AI", "2026-04"), ("Affordance Inc.", "2026-04"), ("Sereact", "2026-04"),
              ("XDOF", "2026-06"), ("Agility Robotics", "2026-06"), ("Generalist AI", "2026-08"), ("Unitree", "2026-08")}
DATA_KEYS = ["rank", "radar", "acq", "name", "country", "stage", "head", "headC", "url", "seg", "dom", "lvl", "target",
             "tier", "tags", "loop", "flagship", "people", "founded", "hq", "raised", "raisedD", "raisedC", "val", "valD",
             "valC", "oss", "note", "sources"]
DATE = re.compile(r"^\d{4}-\d{2}$")


def money(m):
    return f"${m/1000:.1f}B".replace(".0B", "B") if m >= 1000 else f"${m:g}M"


def check(orgs):
    names = [o["name"] for o in orgs]
    assert len(names) == len(set(names)), "duplicate names"
    for o in orgs:
        n = o["name"]
        assert o["seg"] in SEG, f"{n}: seg {o['seg']}"
        assert o["tier"] in TIERS, f"{n}: tier {o.get('tier')}"
        assert set(o.get("tags", [])) <= TAGS, f"{n}: tags {o.get('tags')}"
        assert 0 <= o["lvl"] <= 4 and o["lvl"] <= o["target"] <= 4, f"{n}: lvl/target"
        assert o["raisedC"] in ("hi", "med", "lo") and o["valC"] in ("hi", "med", "lo"), f"{n}: confidence"
        for r in o.get("rounds", []) + o.get("events", []):
            assert DATE.match(r["date"]), f"{n}: date {r['date']}"
            assert 0 <= r["src"] < len(o["sources"]), f"{n}: src {r['src']} out of range"
        if o.get("rank"):
            assert o["seg"] == "infra" and not o.get("radar"), f"{n}: only infra pure-plays are ranked"


def data_js(orgs):
    rows = []
    for o in orgs:
        d = {k: o[k] for k in DATA_KEYS if k in o}
        d["seg"] = SEG[o["seg"]]
        d["rank"] = o.get("rank") or None
        rows.append(json.dumps(d, ensure_ascii=False))
    return "const DATA = [\n" + ",\n".join(rows) + "\n];\n"


def timelines_js(orgs):
    t = {}
    for o in orgs:
        items = [[str(o["founded"]), "Founded", o["hq"]]]
        for r in o.get("rounds", []):
            amt = f" — {money(r['amountM'])}" if r.get("amountM") else ""
            items.append([r["date"], f"{r['label']}{amt}", o["sources"][r["src"]][0]])
        for e in o.get("events", []):
            items.append([e["date"], e["label"], o["sources"][e["src"]][0]])
        items.sort(key=lambda x: x[0])
        t[o["name"]] = items
    return "const TIMELINES = " + json.dumps(t, ensure_ascii=False, indent=0) + ";\n"


def events_js(orgs):
    ev = []
    for o in orgs:
        plotted = SEG[o["seg"]] != "lab" and o["stage"] not in ("Public", "Corporate")
        if plotted:
            for r in o.get("rounds", []):
                if r.get("amountM") and r["date"] >= "2022":   # the takeoff starts in 2022; older capital stays on the entry
                    ev.append({"d": r["date"], "co": o["name"], "kind": "cap", "amt": r["amountM"],
                               "t": f"{r['label']} — {money(r['amountM'])}", "sl": f"{r['label']} · {money(r['amountM'])}"})
        for e in o.get("events", []):
            kind = "org" if re.search(r"found|launch|stealth", e["label"], re.I) else "ev"
            sl = e["label"] if len(e["label"]) <= 30 else e["label"][:28].rstrip() + "…"
            ev.append({"d": e["date"], "co": o["name"], "kind": kind, "t": e["label"], "sl": sl,
                       **({"key": True} if (o["name"], e["date"]) in KEY_EVENTS else {})})
    caps = sorted([e for e in ev if e["kind"] == "cap"], key=lambda e: -e["amt"])[:7]
    for e in caps:
        e["lab"] = "b"
    ev.sort(key=lambda e: (e["d"], -e.get("amt", 0)))
    return "const FIELD_EVENTS = [\n" + ",\n".join(json.dumps(e, ensure_ascii=False) for e in ev) + "\n];\n"


def main():
    orgs = json.load(io.open(ORGS, encoding="utf-8"))
    check(orgs)
    html = io.open(TEMPLATE, encoding="utf-8").read()
    for marker, block in (("/*@DATA*/\n", data_js(orgs) + timelines_js(orgs)),
                          ("/*@EVENTS*/\n", events_js(orgs)),
                          ("/*@SHORT*/{}", json.dumps({k: v for k, v in SHORT.items() if any(o["name"] == k for o in orgs)}, ensure_ascii=False))):
        assert html.count(marker) == 1, marker
        html = html.replace(marker, block)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(html)
    ranked = sum(1 for o in orgs if o.get("rank"))
    print(f"wrote index.html: {len(orgs)} orgs, {ranked} ranked, {len(html)} bytes")


if __name__ == "__main__":
    main()
