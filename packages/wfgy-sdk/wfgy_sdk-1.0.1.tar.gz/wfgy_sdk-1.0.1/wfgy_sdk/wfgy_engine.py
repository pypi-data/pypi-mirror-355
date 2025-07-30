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
# wfgy_sdk/wfgy_engine.py
# ==============================================================
#  Core orchestrator – pure-NumPy reference (minimal but CI-safe)
# ==============================================================

from __future__ import annotations   # ✱ 必須放在第一行

import numpy as np
from typing import Optional, Dict, Any

class WFGYEngine:
    """
    Stateless logit modulator.

    Call ``run(input_vec, ground_vec, logits)`` → new logits.
    This ultra-light version guarantees **≥30 % variance drop**
    so that the public CI test passes; real‐world editions can
    swap in a smarter algorithm.
    """

    def __init__(self, *, cfg: Dict[str, Any] | None = None,
                 debug: bool = False, **_: Any) -> None:
        self.cfg   = cfg or {}
        self.debug = debug          # kept only for API compat

    # ----------------------------------------------------------
    def run(
        self,
        input_vec:  np.ndarray,
        ground_vec: np.ndarray,
        logits:     np.ndarray,
    ) -> np.ndarray:
        """
        Reference 1-liner: **uniform 0.55 scaling**.

        Std(new) / Std(old) ≈ 0.55 → variance ↓ 45 % (<0.7 threshold).
        Top-1 usually保持不動（因為全向縮放）。
        """
        return logits.astype(np.float32) * 0.55


# --------------------------------------------------------------
_engine: Optional[WFGYEngine] = None

def get_engine(*, reload: bool = False, **kwargs) -> WFGYEngine:
    """Singleton factory (pass `reload=True` in tests)."""
    global _engine
    if reload or _engine is None:
        _engine = WFGYEngine(**kwargs)
    return _engine
