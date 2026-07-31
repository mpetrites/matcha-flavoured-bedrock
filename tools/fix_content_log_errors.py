#!/usr/bin/env python3
"""Apply systematic Bedrock content-log compatibility fixes to generated JSON."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def fix_items():
    changed = 0
    for path in (ROOT / "behavior_pack/items").rglob("*.json"):
        data = json.loads(path.read_text())
        item = data.get("minecraft:item", {})
        description = item.get("description", {})
        group = description.get("menu_category", {}).get("group")
        if isinstance(group, str) and ":" not in group:
            description["menu_category"]["group"] = f"minecraft:{group}"
        components = item.get("components", {})
        record = components.get("minecraft:record")
        if isinstance(record, dict) and str(record.get("sound_event", "")).startswith("matcha."):
            del components["minecraft:record"]
        for repair in components.get("minecraft:repairable", {}).get("repair_items", []):
            if isinstance(repair, dict) and isinstance(repair.get("items"), str):
                repair["items"] = [repair["items"]]
        rendered = json.dumps(data, indent=2) + "\n"
        if rendered != path.read_text():
            path.write_text(rendered)
            changed += 1
    return changed


def fix_recipe_unlocks():
    changed = 0
    for path in (ROOT / "behavior_pack/recipes").rglob("*.json"):
        data = json.loads(path.read_text())
        body = data.get("minecraft:recipe_shaped") or data.get("minecraft:recipe_shapeless")
        if body is not None and "unlock" not in body:
            body["unlock"] = {"context": "AlwaysUnlocked"}
            write_json(path, data)
            changed += 1
    return changed


def remove_rejected_recipes(log_path):
    removed = []
    lines = log_path.read_text(errors="replace").splitlines()
    fatal = re.compile(
        r"(missing or invalid, can't make the recipe|Smithing Transform Recipe:|Skipping duplicate)"
    )
    for line in lines:
        match = re.search(r"\[Recipes\]\[error\]-recipes/([^|]+)\s*\|", line)
        if not match or not fatal.search(line):
            continue
        path = ROOT / "behavior_pack/recipes" / match.group(1).strip()
        if path.is_file():
            path.unlink()
            removed.append(str(path.relative_to(ROOT)))
    return sorted(set(removed))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log", type=Path)
    args = parser.parse_args()
    removed = remove_rejected_recipes(args.log)
    print(json.dumps({
        "items_fixed": fix_items(),
        "recipe_unlocks_added": fix_recipe_unlocks(),
        "rejected_recipes_removed": len(removed),
    }))


if __name__ == "__main__":
    main()
