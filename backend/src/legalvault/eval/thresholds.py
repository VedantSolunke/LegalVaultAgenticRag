from __future__ import annotations

import json
from pathlib import Path

from legalvault.eval.models import EvalThresholds

DEFAULT_THRESHOLDS_PATH = Path(__file__).resolve().parents[3] / "eval" / "thresholds.json"


def load_thresholds(path: Path | None = None) -> EvalThresholds:
    thresholds_path = path or DEFAULT_THRESHOLDS_PATH
    raw = json.loads(thresholds_path.read_text(encoding="utf-8"))
    invite_gate = raw.get("invite_gate") or raw
    return EvalThresholds(
        min_overall_pass_rate=float(invite_gate["min_overall_pass_rate"]),
        section_lookup_min_pass_rate=float(
            invite_gate["section_lookup_min_pass_rate"]
        ),
        ipc_mapping_min_pass_rate=float(invite_gate["ipc_mapping_min_pass_rate"]),
        fact_pattern_min_pass_rate=float(invite_gate["fact_pattern_min_pass_rate"]),
    )
