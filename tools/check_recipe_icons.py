#!/usr/bin/env python3
"""Ensure every custom item shown by a recipe has a packaged icon."""

import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ATLAS = json.loads((ROOT / "resource_pack/textures/item_texture.json").read_text())["texture_data"]
ITEMS = {}
for path in (ROOT / "behavior_pack/items").rglob("*.json"):
    body = json.loads(path.read_text()).get("minecraft:item", {})
    identifier = body.get("description", {}).get("identifier")
    icon = body.get("components", {}).get("minecraft:icon", {})
    textures = icon.get("textures", {}) if isinstance(icon, dict) else {}
    if identifier:
        ITEMS[identifier] = textures.get("default") if isinstance(textures, dict) else None

used = set()
def visit(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"item", "input", "output", "base", "addition", "template"} and isinstance(child, str):
                used.add(child)
            visit(child)
    elif isinstance(value, list):
        for child in value:
            visit(child)

for path in (ROOT / "behavior_pack/recipes").rglob("*.json"):
    visit(json.loads(path.read_text()))

problems = []
required_dimensions = {"matcha:warding_shield": (16, 16)}
for identifier in sorted(item for item in used if item.startswith("matcha:")):
    key = ITEMS.get(identifier)
    if not key:
        problems.append({"item": identifier, "problem": "missing item definition or icon key"})
        continue
    entry = ATLAS.get(key)
    if not entry:
        problems.append({"item": identifier, "problem": f"missing atlas entry {key}"})
        continue
    paths = entry.get("textures") if isinstance(entry, dict) else entry
    paths = [paths] if isinstance(paths, str) else paths
    for texture in paths or []:
        files = [ROOT / "resource_pack" / f"{texture}{suffix}" for suffix in ("", ".png", ".tga")]
        existing = next((path for path in files if path.is_file()), None)
        if not existing:
            problems.append({"item": identifier, "problem": f"missing texture {texture}"})
        elif identifier in required_dimensions and existing.suffix.lower() == ".png":
            with existing.open("rb") as handle:
                header = handle.read(24)
            dimensions = struct.unpack(">II", header[16:24]) if header.startswith(b"\x89PNG\r\n\x1a\n") else None
            if dimensions != required_dimensions[identifier]:
                problems.append({"item": identifier, "problem": f"expected {required_dimensions[identifier]} icon, found {dimensions}"})

report = {"custom_recipe_items": sum(item.startswith("matcha:") for item in used), "problems": problems, "status": "pass" if not problems else "fail"}
(ROOT / "docs/recipe-icon-check-report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"custom_recipe_items": report["custom_recipe_items"], "problems": len(problems), "status": report["status"]}))
if problems:
    raise SystemExit(1)
