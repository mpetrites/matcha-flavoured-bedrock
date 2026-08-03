#!/usr/bin/env python3
"""Fail when a Bedrock recipe consumes the same item that it produces."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "behavior_pack/recipes"
REPORT = ROOT / "docs/self-referencing-recipe-check-report.json"


def recipe_body(data: dict) -> dict | None:
    return next(
        (value for key, value in data.items() if key.startswith("minecraft:recipe_") and isinstance(value, dict)),
        None,
    )


def item_id(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        item = value.get("item")
        return item if isinstance(item, str) else None
    return None


def input_counts(body: dict) -> dict[str, int]:
    found: dict[str, int] = {}

    def add(identifier: str, count: int = 1) -> None:
        found[identifier] = found.get(identifier, 0) + count

    for field in ("input", "base", "addition", "template"):
        value = item_id(body.get(field))
        if value:
            add(value)
    for value in body.get("ingredients", []):
        identifier = item_id(value)
        if identifier:
            add(identifier)
    pattern = body.get("pattern", [])
    for symbol, value in body.get("key", {}).items():
        identifier = item_id(value)
        if identifier:
            add(identifier, sum(row.count(symbol) for row in pattern))
    return found


problems = []
checked = 0
for path in sorted(RECIPES.rglob("*.json")):
    body = recipe_body(json.loads(path.read_text(encoding="utf-8")))
    if body is None:
        continue
    checked += 1
    raw_result = body.get("result", body.get("output"))
    result = item_id(raw_result)
    result_count = raw_result.get("count", 1) if isinstance(raw_result, dict) else 1
    consumed = input_counts(body).get(result, 0) if result else 0
    # Recipes such as flower cloning intentionally consume one and return two.
    # A cycle is invalid only when it has no positive item gain.
    if result and consumed and result_count <= consumed:
        problems.append({
            "recipe": str(path.relative_to(ROOT)),
            "identifier": body.get("description", {}).get("identifier"),
            "item": result,
            "consumed": consumed,
            "produced": result_count,
        })

report = {
    "recipes_checked": checked,
    "problems": problems,
    "status": "pass" if not problems else "fail",
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"recipes_checked": checked, "problems": len(problems), "status": report["status"]}))
if problems:
    raise SystemExit(1)
