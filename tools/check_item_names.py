#!/usr/bin/env python3
"""Verify that every craftable Matcha item has a readable localized name."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
lang = {}
for line in (ROOT / "resource_pack/texts/en_US.lang").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        key, value = line.split("=", 1)
        lang[key] = value

craftable = set()
def collect(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"item", "output"} and isinstance(child, str) and child.startswith("matcha:"):
                craftable.add(child)
            collect(child)
    elif isinstance(value, list):
        for child in value: collect(child)

for path in (ROOT / "behavior_pack/recipes").rglob("*.json"):
    collect(json.loads(path.read_text(encoding="utf-8")))

items = {}
for path in (ROOT / "behavior_pack/items").rglob("*.json"):
    body = json.loads(path.read_text(encoding="utf-8")).get("minecraft:item", {})
    identifier = body.get("description", {}).get("identifier")
    display = body.get("components", {}).get("minecraft:display_name", {})
    if identifier: items[identifier] = display.get("value") if isinstance(display, dict) else None

problems = []
for identifier in sorted(craftable):
    key = items.get(identifier)
    if not key:
        problems.append({"item": identifier, "problem": "missing item definition or display-name key"})
        continue
    value = lang.get(key)
    if not value:
        problems.append({"item": identifier, "problem": f"missing language entry {key}"})
    elif value.startswith(("item.", "tile.", "entity.", "%")):
        problems.append({"item": identifier, "problem": f"non-readable language value {value}"})

report = {"craftable_custom_items": len(craftable), "problems": problems, "status": "pass" if not problems else "fail"}
(ROOT / "docs/item-name-check-report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"craftable_custom_items": len(craftable), "problems": len(problems), "status": report["status"]}))
if problems: raise SystemExit(1)
