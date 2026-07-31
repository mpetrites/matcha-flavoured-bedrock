#!/usr/bin/env python3
"""Recover rejected Java recipes as loadable Bedrock approximations."""
import json
import subprocess
from pathlib import Path

from convert_recipes import PROXY_ITEM_MAP

ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "behavior_pack/recipes"


def old_json(path):
    return json.loads(subprocess.check_output(
        ["git", "show", f"HEAD:{path.relative_to(ROOT)}"], text=True
    ))


def mapped(item):
    return PROXY_ITEM_MAP.get(item, item)


removed = subprocess.check_output(
    ["git", "diff", "--diff-filter=D", "--name-only", "--", "behavior_pack/recipes"],
    text=True,
).splitlines()
restored = 0
skipped_banners = 0
for relative in removed:
    path = ROOT / relative
    data = old_json(path)
    key = next(k for k in data if k.startswith("minecraft:recipe_"))
    body = data[key]
    result = body.get("result", {})
    result_id = result.get("item") if isinstance(result, dict) else result

    if result_id and result_id.endswith("_banner"):
        skipped_banners += 1
        continue

    if key == "minecraft:recipe_smithing_transform":
        ingredients = [mapped(body[field]) for field in ("template", "base", "addition")]
        body = {
            "description": body["description"],
            "tags": ["crafting_table"],
            "unlock": {"context": "AlwaysUnlocked"},
            "ingredients": [{"item": item} for item in ingredients],
            "result": {"item": mapped(result_id)},
        }
        data = {"format_version": "1.21.100", "minecraft:recipe_shapeless": body}
    else:
        if isinstance(result, dict) and result_id:
            result["item"] = mapped(result_id)
        if "output" in body:
            body["output"] = mapped(body["output"])
        if "input" in body:
            body["input"] = mapped(body["input"])
        if key in {"minecraft:recipe_shaped", "minecraft:recipe_shapeless"}:
            body.setdefault("unlock", {"context": "AlwaysUnlocked"})

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    restored += 1

print(json.dumps({"restored": restored, "colored_banners_skipped": skipped_banners}))
