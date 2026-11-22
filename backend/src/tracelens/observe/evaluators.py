import json
import re
from typing import Any


def run_regex_evaluator(output_text: str, pattern: str) -> tuple[float, dict[str, object]]:
    matched = bool(re.search(pattern, output_text, re.IGNORECASE))
    return (1.0 if matched else 0.0), {"matched": matched, "pattern": pattern}


def run_json_schema_evaluator(
    output_text: str, schema: dict[str, Any]
) -> tuple[float, dict[str, object]]:
    try:
        data = json.loads(output_text)
    except json.JSONDecodeError:
        return 0.0, {"error": "invalid_json"}

    required = schema.get("required", [])
    properties = schema.get("properties", {})
    if not isinstance(data, dict):
        return 0.0, {"error": "not_object"}

    missing = [key for key in required if key not in data]
    if missing:
        return 0.0, {"missing": missing}

    type_ok = True
    for key, rule in properties.items():
        if key not in data or not isinstance(rule, dict):
            continue
        expected = rule.get("type")
        if expected == "string" and not isinstance(data[key], str):
            type_ok = False
        if expected == "number" and not isinstance(data[key], (int, float)):
            type_ok = False

    score = 1.0 if type_ok and not missing else 0.5 if not missing else 0.0
    return score, {"type_ok": type_ok, "missing": missing}


def evaluate_output(
    kind: str, config: dict[str, object], output_text: str
) -> tuple[float, dict[str, object]]:
    if kind == "regex":
        pattern = str(config.get("pattern", ""))
        return run_regex_evaluator(output_text, pattern)
    if kind == "json_schema":
        raw_schema = config.get("schema", {})
        schema = dict(raw_schema) if isinstance(raw_schema, dict) else {}
        return run_json_schema_evaluator(output_text, schema)
    return 0.0, {"error": "unsupported_evaluator"}
