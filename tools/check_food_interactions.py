#!/usr/bin/env python3
"""Audit Bedrock food carriers and scripted special interactions."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "behavior_pack"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


checks: list[tuple[str, bool]] = []
for name in ("pickled_crimson_fungus", "pickled_red_mushrooms"):
    components = load(BP / "items/generated_foods" / f"{name}.json")["minecraft:item"]["components"]
    checks.extend([
        (f"{name} is not drinkable food", "minecraft:food" not in components),
        (f"{name} exposes throw interaction", components.get("minecraft:interact_button") == "Throw"),
    ])

mead = load(BP / "items/generated_foods/mead.json")["minecraft:item"]["components"]
milk = load(BP / "items/generated_foods/milk_bottle.json")["minecraft:item"]["components"]
checks.extend([
    ("mead is a drink", mead.get("minecraft:use_animation") == "drink"),
    ("mead returns glass bottle", mead.get("minecraft:food", {}).get("using_converts_to") == "minecraft:glass_bottle"),
    ("milk bottle is a drink", milk.get("minecraft:use_animation") == "drink"),
    ("milk bottle returns glass bottle", milk.get("minecraft:food", {}).get("using_converts_to") == "minecraft:glass_bottle"),
])

script = (BP / "scripts/food_interactions.js").read_text(encoding="utf-8")
data = (BP / "scripts/food_interaction_data.js").read_text(encoding="utf-8")
main = (BP / "scripts/main.js").read_text(encoding="utf-8")
checks.extend([
    ("splash script is loaded", 'import "./food_interactions.js"' in main),
    ("poison splash is routed", '"matcha:pickled_red_mushrooms"' in data and '"poison"' in data),
    ("weakness splash is routed", '"matcha:pickled_crimson_fungus"' in data and '"weakness"' in data),
    ("splash duration scales by distance", "1 - distance / SPLASH_RADIUS" in script),
    ("cake bites restore health", 'block.typeId !== "minecraft:cake"' in script and 'addEffect("regeneration", 24' in script),
    ("cake healing requires a changed bite state", 'getState("bite_counter")' in script and "const successful =" in script),
])

failed = [name for name, passed in checks if not passed]
report = {
    "checks": len(checks),
    "passed": len(checks) - len(failed),
    "failed": failed,
    "splash_foods": 2,
    "drink_interactions": ["matcha:mead", "matcha:milk_bottle"],
    "placed_food_interactions": ["minecraft:cake"],
}
(ROOT / "docs/food-interactions-check-report.json").write_text(
    json.dumps(report, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(report))
raise SystemExit(bool(failed))
