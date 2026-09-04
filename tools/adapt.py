"""One-shot: turn rsi-list's index.html into the Embodied Expertise List template.
Every replacement asserts its target occurs exactly once, so a template drift fails loudly."""
import re, sys, io
src = io.open(sys.argv[1], encoding="utf-8").read()
out = src

def rep(old, new, count=1, regex=False):
    global out
    n = len(re.findall(old, out, flags=re.S)) if regex else out.count(old)
    assert n == count, f"expected {count} of {old[:60]!r}, found {n}"
    out = re.sub(old, lambda m: new, out, flags=re.S) if regex else out.replace(old, new)

rep("<title>RSI List — The recursive self-improvement landscape</title>",
    "<title>Embodied Expertise List — The deployability landscape</title>")
rep(r"<!-- Vercel Web Analytics\..*?insights/script\.js\"></script>\n", "", regex=True)
rep('<span class="brand" aria-label="RSI List">', '<span class="brand" aria-label="Embodied Expertise List">')
rep('<span class="tava"><i>R</i></span><span class="tava"><i>S</i></span><span class="tava"><i>I</i></span>',
    '<span class="tava"><i>E</i></span><span class="tava"><i>E</i></span>')
rep('<span class="hl" style="--d:.12s">The recursive self-improvement landscape</span>',
    '<span class="hl" style="--d:.12s">The embodied expertise landscape</span>')
rep(r'<p class="tk-sub">Recursive self-improvement, or RSI.*?</p>\n\s*<p class="tk-sub">This directory lists.*?</p>',
    '<p class="tk-sub">Embodied expertise is physical know-how: what an experienced welder, surgeon or maintenance technician does that the manual leaves out. Robots today learn short, general actions from large datasets. Turning that into expertise that works reliably at a real site is a different problem. Observe the human, practice from sparse feedback, deploy on whatever hardware the site already has, and keep improving after deployment.</p>\n'
    '        <p class="tk-sub">This directory lists the organizations building that loop, from whichever layer they start: robot foundation models, human-data capture, deployment runtimes and silicon, the robots themselves, and the labs everyone is measured against. Each entry is graded on the deployment evidence it has shown, not on what it says. The taxonomy follows the Affordance Inc. deck that prompted the list: OBSERVE → PRACTICE → DEPLOY → IMPROVE.</p>',
    regex=True)
rep('<option value="rank">Sort: RSI rank</option>', '<option value="rank">Sort: Deployability rank</option>')
rep(r'<p class="mono">RSI LIST · 2026</p>.*?</p>',
    '<p class="mono">EMBODIED EXPERTISE LIST · 2026</p>\n'
    '    <p class="mono contrib">CONTRIBUTORS ·\n'
    '      <a href="https://github.com/yurekami" target="_blank" rel="noopener">Daniel Kang</a> ·\n'
    '      taxonomy from the <a href="https://github.com/yurekami/embodied-expertise-list" target="_blank" rel="noopener">Affordance Inc. deck</a> ·\n'
    '      format and code forked from <a href="https://rsi-list.com" target="_blank" rel="noopener">RSI List</a> (MIT)\n'
    '    </p>', regex=True)

# ---- data blocks become build markers ----
rep(r"const DATA = \[.*?(?=const SEGS = )", "/*@DATA*/\n", regex=True)
rep(r"const FIELD_EVENTS = \[.*?\n\];\n", "/*@EVENTS*/\n", regex=True)

# ---- segments, tiers, tags ----
rep('const SEGS = [["all","All"],["pure","Pure-play"],["lab","Frontier labs"],["infra","Infrastructure"],["research","Research"],["radar","Radar"]];',
    'const SEGS = [["all","All"],["pure","Deployability infra"],["body","Robot makers"],["lab","Frontier labs"],["research","Research"],["radar","Radar"]];')
rep('const SEGNAME = {pure:"PURE-PLAY", lab:"FRONTIER LAB", infra:"INFRA", research:"RESEARCH"};',
    'const SEGNAME = {pure:"INFRA", body:"ROBOT MAKER", lab:"FRONTIER LAB", research:"RESEARCH"};')
rep('const TIERNAME = {core:"RSI", self:"AUTO RESEARCH", enable:"SELF-IMPROVEMENT"};',
    'const TIERNAME = {gen:"GENERAL TASKS", site:"SITE-BOUNDED", open:"OPEN-WORLD", layer:"ENABLING LAYER"};\n'
    'const LVLNAME = ["research","demo","pilot","paid deployment","fleet"];\n'
    'const LVLTIP = ["L0 research / pre-product: papers, no robot at a customer site","L1 demo: lab or staged demos, videos, benchmarks","L2 pilot: robots working at a customer site, pilots or pilot fees","L3 paid deployment: recurring paid deployments at multiple sites","L4 fleet: hundreds of units in production, learning from deployment data"];')
rep(r"const TIERTIP = \{.*?\};",
    'const TIERTIP = {\n'
    '  gen:"General physical tasks: one policy for many objects and sites, the robot-foundation-model bet",\n'
    '  site:"Site-bounded expertise: the know-how of one plant, one clinic, one warehouse, made reliable there",\n'
    '  open:"Open-world expertise: field, outdoor and construction work where the environment keeps changing",\n'
    '  layer:"An enabling layer under the loop: data capture, deployment runtime, silicon, tooling"\n'
    '};', regex=True)
rep(r'const TAGS = \[\n.*?\n\];',
    'const TAGS = [\n'
    '  ["Observe",  "Observe",  "Capturing human physical expertise as robot-learnable data"],\n'
    '  ["Practice", "Practice", "Policy learning, simulation, RL, autoresearch on the deployed algorithm"],\n'
    '  ["Deploy",   "Deploy",   "Edge runtime, hardware bridging, compilers, fleet tooling"],\n'
    '  ["Improve",  "Improve",  "Memory and continual learning from feedback after deployment"],\n'
    '  ["Body",     "Body",     "Builds the robot hardware itself"],\n'
    '  ["Silicon",  "Silicon",  "Chips and FPGAs for robots"],\n'
    '];', regex=True)
rep('.b-tier.core{background:var(--accent-soft); color:var(--accent-ink); border:1px solid rgba(232,168,124,.4)}\n'
    '  .b-tier.self{border:1px solid rgba(232,168,124,.3); color:#D9B295; background:transparent}\n'
    '  .b-tier.enable{background:var(--chip); color:var(--muted); border:1px dashed var(--line)}',
    '.b-tier.site{background:var(--accent-soft); color:var(--accent-ink); border:1px solid rgba(232,168,124,.4)}\n'
    '  .b-tier.gen{border:1px solid rgba(232,168,124,.3); color:#D9B295; background:transparent}\n'
    '  .b-tier.open{border:1px solid rgba(211,180,94,.45); color:#D3B45E; background:transparent}\n'
    '  .b-tier.layer{background:var(--chip); color:var(--muted); border:1px dashed var(--line)}\n'
    '  .lvlcell{font-family:"IBM Plex Mono",monospace; font-size:11.5px; white-space:nowrap; cursor:help}\n'
    '  .lvlcell b{color:var(--accent-ink); font-weight:500} .lvlcell span{color:var(--faint)}')
rep("const CONF = {hi:['●','conf-hi','confirmed'], med:['◐','conf-med','reported'], lo:['–','conf-lo','unknown']};",
    "const CONF = {hi:['●','conf-hi','confirmed'], med:['◐','conf-med','reported'], lo:['–','conf-lo','unknown']};\n"
    "DATA.forEach(d=>{ d.strict = d.tier || \"layer\"; });\n"
    "function lvlCell(d){ const l=d.lvl??0, t=d.target??l; return `<span class=\"lvlcell\" title=\"${esc(LVLTIP[l])}${t>l?' · aims: '+esc(LVLTIP[t]):''}\"><b>L${l}</b> ${esc(LVLNAME[l])}${t>l?` <span>→ L${t}</span>`:''}</span>`; }")
rep('title="Radar: meets the RSI bar, not yet the index bar"', 'title="Radar: early-stage, below the index bar"')
rep('  const LAB_ORDER = {"Google DeepMind":0, "OpenAI":1, "Anthropic":2};   /* evidence order, matches the rank note */\n', '')
rep('      if(a.seg==="lab" && b.seg==="lab") return (LAB_ORDER[a.name]??9)-(LAB_ORDER[b.name]??9);',
    '      if(a.seg==="lab" && b.seg==="lab") return (b.lvl-a.lvl) || a.name.localeCompare(b.name);')
rep(r'  if\(state\.sort==="rank"\)\{\n    /\* curated placements.*?\n  \}\n  return rows;', '  return rows;', regex=True)
rep('const GROUPS = ["Frontier labs \\u2014 outside the ranking", "The index", "Tooling & nonprofits \\u2014 n/r", "The radar \\u25ce"];',
    'const GROUPS = ["Frontier labs \\u2014 outside the ranking", "The index \\u2014 deployability infra", "Robot makers, corporates & research \\u2014 n/r", "The radar \\u25ce"];')
rep('<tr class="group"><td colspan="9">', '<tr class="group"><td colspan="10">')
rep('<th>Tag</th><th>Stage</th>', '<th>Tag</th><th>Evidence</th><th>Stage</th>')
rep('    <td>${tagCell(d)}</td>\n', '    <td>${tagCell(d)}</td>\n    <td>${lvlCell(d)}</td>\n')
rep('<div><h4>Verifier</h4><p>${esc(verOf(d).join(", ")||"–")}</p></div>', '<div><h4>Evidence</h4><p>${lvlCell(d)}</p></div>')
rep('      ${fact("Verifier", esc(verOf(d).join(", ")||"–"))}\n', '      ${fact("Evidence", lvlCell(d))}\n')
rep('const VERIFIERS = ["Jinyan","Jiabing","Yu"];', 'const VERIFIERS = [];')
rep('"rsi-verifiers"', '"ee-verifiers"', count=2)
rep('<div class="org-sec"><h3>Their mission</h3>', '<div class="org-sec"><h3>What they build</h3>')
# tags: fixed data on the entry, no server, no snapshot fetch
rep(r"/\* ---------- company tags \(Model.*?\nlet viewSlug = null;",
    "/* ---------- tags: fixed data on each entry (Observe / Practice / Deploy / Improve / Body / Silicon) */\n"
    "function tagsOf(d){ return d.tags||[]; }\n"
    "function tagCell(d){\n"
    "  const cur = tagsOf(d);\n"
    "  return `<div class=\"tag-chips\">${\n"
    "    TAGS.map(([v,label,tip])=>`<span class=\"tagchip${cur.includes(v)?\"\":\" off\"}\" title=\"${esc(tip)}\">${esc(label)}</span>`).join(\"\")\n"
    "  }</div>`;\n"
    "}\n"
    "function bootTags(){}\n\n"
    "let viewSlug = null;", regex=True)
rep('document.title = d.name + " — RSI List";', 'document.title = d.name + " — Embodied Expertise List";')
rep('document.title = "RSI List";', 'document.title = "Embodied Expertise List";')

# ---- takeoff chart ----
rep('  const CATN = {rsi:"RSI", auto:"Auto research", self:"Self-improvement"};\n'
    '  const catOf = co => CAT_RSI.includes(co) ? "rsi" : CAT_AUTO.includes(co) ? "auto" : "self";\n',
    '  const CATN = {gen:"General tasks", site:"Site-bounded expertise", open:"Open-world expertise", layer:"Enabling layer"};\n'
    '  const catOf = co => (DATA.find(d=>d.name===co)||{}).tier || "layer";\n')
rep(r'  const SHORT = \{"Ineffable Intelligence".*?\};\n', '  const SHORT = /*@SHORT*/{};\n', regex=True)
rep('  const xa=2023.05, xb=NOW+.08;',
    '  const yr0 = Math.min(2023, ...caps.map(e=>+e.d.slice(0,4)));\n  const xa=yr0+.05, xb=NOW+.08;')
rep('  for(let yr=2024; yr<=Math.floor(xb); yr++){', '  for(let yr=yr0+1; yr<=Math.floor(xb); yr++){')
rep('  g += `<text x="${PL+4}" y="${base+17}" font-size="11" fill="${MUT}">2023</text>`;',
    '  g += `<text x="${PL+4}" y="${base+17}" font-size="11" fill="${MUT}">${yr0}</text>`;')
rep('  const yMax = Math.ceil(total/1000)*1000 + 300;',
    '  const GRID = total > 8000 ? 2000 : 1000;\n  const yMax = Math.ceil(total/GRID)*GRID + GRID*.3;')
rep('  for(let v=1000; v<yMax; v+=1000){', '  for(let v=GRID; v<yMax; v+=GRID){')
rep('aria-label="Disclosed funding in the RSI field as a running total from 2023 to now, with the field\'s milestones — shipped results and company launches — annotated along the curve"',
    'aria-label="Disclosed funding across the embodied-expertise field as a running total, with shipped results and company launches annotated along the curve"')
rep(r'  document\.getElementById\("tk-sub"\)\.innerHTML =\n.*?`;\n',
    '  document.getElementById("tk-sub").innerHTML =\n'
    '    `The chart above lays the field\'s milestones over its money. <b>${startups.length} startups</b> are in the directory, <b>${since25}</b> of them founded since 2025. <b>${fmtM(total)}</b> in disclosed rounds are plotted, <b>${pct26}%</b> of it in 2026. ● marks a shipped result, ○ a company launch, ◆ a named round. Hover a step or a label for the detail, click to open the entry.`;\n', regex=True)
rep(r'  document\.getElementById\("tk-foot"\)\.textContent =\n.*?`;\n',
    '  const undated = startups.filter(d=>d.raised>0 && !caps.some(e=>e.co===d.name)).map(d=>d.name);\n'
    '  document.getElementById("tk-foot").textContent =\n'
    '    `Only dated, disclosed rounds from the directory\'s own entries are plotted: ${fmtM(total)} of the ${fmtM(Math.round(siteTotal/100)*100)} in cumulative funding it records. ${undated.length?`${undated.length} entries disclosed a total but never a round date (${undated.join(", ")}), so they stay off the curve along with everything else undated. `:""}Frontier-lab, public-company and corporate capital is left out so startups share one scale. Lab results are kept in, because those are the results the startups get measured against. Category (general tasks, site-bounded, open-world, enabling layer) shows in the tooltip and on each entry\'s page.`;\n', regex=True)

# only key milestones get a text label; the rest stay as hoverable nodes on the curve
rep('    const i = marks.push({...e, cat:catOf(e.co), x, y, hit:[x-12, y-12, 24, 24]}) - 1;\n'
    '    annos.push({m:marks[i], i, x, y, l:`${nm(e.co)} · ${e.sl}`});',
    '    const i = marks.push({...e, cat:catOf(e.co), x, y, hit:[x-12, y-12, 24, 24]}) - 1;\n'
    '    if(e.key) annos.push({m:marks[i], i, x, y, l:`${nm(e.co)} · ${e.sl}`});')

io.open(sys.argv[2], "w", encoding="utf-8", newline="\n").write(out)
print("ok", len(src), "->", len(out))
