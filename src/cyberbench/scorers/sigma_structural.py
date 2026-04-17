"""SIGMA rule structural scorer. Validates YAML structure and expected fields."""

from __future__ import annotations

import re

import yaml

from ..tasks import Task


# Points: 0.3 parse, 0.3 required top-level fields, 0.2 detection structure, 0.2 domain match
WEIGHTS = {
    "parse": 0.3,
    "required_fields": 0.3,
    "detection_structure": 0.2,
    "domain_match": 0.2,
}


def _extract_yaml_block(text: str) -> str:
    # Extract content from ```yaml ... ``` fences if present; otherwise take whole text.
    m = re.search(r"```(?:yaml)?\s*\n(.+?)```", text, re.DOTALL)
    return m.group(1) if m else text


def score(task: Task, response: str) -> tuple[float, dict]:
    req = task.requirements or {}
    # `condition` in SIGMA is always nested under `detection`; when it appears in
    # must_have_fields we check for it inside the detection block, not at the top level.
    must_have_raw = req.get("must_have_fields") or ["title", "detection", "logsource"]
    must_have_top = [f for f in must_have_raw if f != "condition"]
    condition_required = "condition" in must_have_raw
    detection_keys_any = req.get("detection_keys_should_include") or []
    expected_product = req.get("expected_logsource_product")

    detail: dict = {"parse_ok": False, "missing_fields": [], "detection_keys": []}
    earned = 0.0

    raw = _extract_yaml_block(response)
    try:
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            return 0.0, {**detail, "error": "top-level is not a mapping"}
        detail["parse_ok"] = True
        earned += WEIGHTS["parse"]
    except yaml.YAMLError as e:
        return 0.0, {**detail, "error": f"yaml parse error: {e}"}

    detection = data.get("detection")
    missing = [f for f in must_have_top if f not in data]
    if condition_required and not (
        isinstance(detection, dict) and "condition" in detection
    ):
        missing.append("condition")
    detail["missing_fields"] = missing
    total_req = len(must_have_top) + (1 if condition_required else 0)
    if total_req > 0:
        if not missing:
            earned += WEIGHTS["required_fields"]
        else:
            earned += WEIGHTS["required_fields"] * (1 - len(missing) / total_req)

    # detection structure
    if isinstance(detection, dict):
        # collect all leaf keys (e.g., EventID, Image) from nested selection blocks
        found_keys = _collect_detection_keys(detection)
        detail["detection_keys"] = sorted(found_keys)
        if detection_keys_any:
            if any(k in found_keys for k in detection_keys_any):
                earned += WEIGHTS["detection_structure"]
        else:
            # no specific requirement — reward having any keys + a condition
            if found_keys and "condition" in detection:
                earned += WEIGHTS["detection_structure"]

    # domain/product match
    logsource = data.get("logsource") or {}
    if expected_product:
        if isinstance(logsource, dict) and logsource.get("product") == expected_product:
            earned += WEIGHTS["domain_match"]
            detail["logsource_product_matched"] = True
        else:
            detail["logsource_product_matched"] = False
    else:
        earned += WEIGHTS["domain_match"]  # no requirement = full credit

    return min(earned, 1.0), detail


def _collect_detection_keys(block) -> set[str]:
    keys: set[str] = set()
    if isinstance(block, dict):
        for k, v in block.items():
            if k == "condition":
                continue
            if isinstance(v, dict):
                keys |= _collect_detection_keys(v)
            else:
                keys.add(k)
    elif isinstance(block, list):
        for item in block:
            keys |= _collect_detection_keys(item)
    return keys
