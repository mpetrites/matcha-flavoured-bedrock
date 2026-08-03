#!/usr/bin/env python3
"""Reject duplicate custom-item definitions and recipe-derived catalog aliases."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "behavior_pack/items"
REPORT = ROOT / "docs/item-duplicate-check-report.json"

lang = {}
for line in (ROOT / "resource_pack/texts/en_US.lang").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        key, value = line.split("=", 1)
        lang[key] = value


def canonical_stem(stem: str) -> str:
    """Remove acquisition-method suffixes that must not create new items."""
    stem = re.sub(r"_from_.+$", "", stem)
    return re.sub(r"_campfire$", "", stem)


definitions: dict[str, list[str]] = defaultdict(list)
generated: dict[str, list[tuple[str, str]]] = defaultdict(list)

for path in ITEMS.rglob("*.json"):
    body = json.loads(path.read_text(encoding="utf-8")).get("minecraft:item", {})
    identifier = body.get("description", {}).get("identifier")
    if not identifier:
        continue
    relative = str(path.relative_to(ROOT))
    definitions[identifier].append(relative)
    if path.parent.name in {"generated_foods", "generated_components"}:
        generated[canonical_stem(path.stem)].append((identifier, relative))

problems = []
for identifier, paths in sorted(definitions.items()):
    if len(paths) > 1:
        problems.append({
            "problem": "duplicate item identifier",
            "item": identifier,
            "definitions": paths,
        })

for stem, entries in sorted(generated.items()):
    identifiers = sorted({identifier for identifier, _ in entries})
    if len(identifiers) > 1:
        problems.append({
            "problem": "recipe variants generated separate catalog items",
            "canonical_stem": stem,
            "items": identifiers,
            "definitions": [path for _, path in entries],
        })

for path in sorted((ITEMS / "generated_foods").glob("*.json")):
    body = json.loads(path.read_text(encoding="utf-8")).get("minecraft:item", {})
    display = body.get("components", {}).get("minecraft:display_name", {})
    key = display.get("value") if isinstance(display, dict) else None
    name = lang.get(key, "")
    if "_from_" not in path.stem and " From " in name:
        problems.append({
            "problem": "canonical item inherited an alternate acquisition-recipe name",
            "item": body.get("description", {}).get("identifier"),
            "definition": str(path.relative_to(ROOT)),
            "display_name": name,
        })

report = {
    "custom_item_definitions": sum(len(paths) for paths in definitions.values()),
    "unique_item_identifiers": len(definitions),
    "problems": problems,
    "status": "pass" if not problems else "fail",
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "custom_item_definitions": report["custom_item_definitions"],
    "unique_item_identifiers": report["unique_item_identifiers"],
    "problems": len(problems),
    "status": report["status"],
}))
if problems:
    raise SystemExit(1)
