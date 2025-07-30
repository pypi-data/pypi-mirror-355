"""
╭──────────────────────────────────────────────────────────╮
│  WFGY SDK · Self-Healing Variance Gate for Any LLM       │
│----------------------------------------------------------│
│ 💌  Contact : hello@onestardao.com  /  TG @PSBigBig       │
│ 🌐  Docs    : https://onestardao.com/papers               │
│ 🐙  GitHub  : https://github.com/onestardao/WFGY          │
│                                                          │
│ ★ Star WFGY 1.0 → Unlock 2.0                             │
│   10k ⭐ by **Aug 1st** = next-gen AI alchemy             │
│   Your click = our quantum leap                          │
│                                                          │
│ 🔍  Official PDF of WFGY 1.0 (Zenodo DOI):               │
│     https://doi.org/10.5281/zenodo.15630969              │
│     (Hosted on Zenodo – trusted international archive)   │
│                                                          │
│ 🧬  WFGY BigBang Prompt Pack (v1.0):                     │
│     https://doi.org/10.5281/zenodo.15657016              │
│     (Prompts to trigger the gate; multilingual updates coming) │
│                                                          │
│ 🧠  Hidden folder inside repo: /I_am_not_lizardman        │
│     (X secret papers, wild prompts, and Einstein drama) │
│                                                          │
│ ⚠  GPT-2 demo is just the appetizer. With bigger LLMs,   │
│    WFGY activates variance-drop lasers and KL fireworks. │
│                                                          │
│ 🎮  Bonus: Honest Hero RPG Channel →                     │
│     https://www.youtube.com/@OneStarDao                  │
╰──────────────────────────────────────────────────────────╯
"""
# wfgy_sdk/reporter.py

import os, json
from .utils import RESULTS_DIR

def generate_report(fmt, output):
    entries = []
    for fn in os.listdir(RESULTS_DIR):
        if fn.endswith(".json"):
            data = json.load(open(os.path.join(RESULTS_DIR, fn)))
            entries.append((fn.replace(".json",""), data))
    if fmt == "html":
        with open(output, "w") as f:
            f.write("<html><body><h1>Report</h1>")
            for name,data in entries:
                f.write(f"<h2>{name}</h2><pre>{data}</pre>")
            f.write("</body></html>")
    else:
        with open(output, "w") as f:
            for name,data in entries:
                f.write(f"## {name}\n{data}\n\n")
    print(f"Report saved to {output}")
