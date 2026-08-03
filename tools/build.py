#!/usr/bin/env python3
"""Build, audit, and package the complete Matcha Bedrock add-on."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from upstream import add_source_argument, validate_source


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_source_argument(parser)
    parser.add_argument(
        "--dry-run", action="store_true", help="print the ordered stages without running them"
    )
    args = parser.parse_args()
    source = validate_source(args.source)

    python = sys.executable
    tool = lambda name, *arguments: [python, str(TOOLS / name), *map(str, arguments)]
    stages = [
        ("upstream inventory", tool("check_upstream.py", "--source", source)),
        ("source parity", tool("check_parity_1_03.py", "--source", source)),
        (
            "base recipes",
            tool(
                "convert_recipes.py",
                source / "data",
                ROOT / "behavior_pack/recipes/generated",
                ROOT / "docs/recipe-conversion-report.json",
            ),
        ),
        ("equipment", tool("generate_equipment.py", "--source", source)),
        (
            "foods",
            tool(
                "convert_foods.py",
                source,
                ROOT / "behavior_pack",
                ROOT / "resource_pack",
                ROOT / "docs/food-conversion-report.json",
            ),
        ),
        ("component items", tool("convert_component_items.py", "--source", source)),
        ("blessing items", tool("generate_enchantments.py", "--source", source)),
        ("villager trade items", tool("generate_villager_trades.py", "--source", source)),
        ("loot items", tool("convert_loot.py", "--source", source)),
        ("source item icons", tool("import_source_item_icons.py", "--source", source)),
        ("vanilla replacements", tool("generate_vanilla_replacements.py", source, ROOT)),
        ("replacement recipe inputs", tool("sync_vanilla_recipe_inputs.py")),
        ("vanilla recipe overrides", tool("generate_vanilla_recipe_overrides.py")),
        ("equipment audit", tool("check_equipment.py")),
        ("smithing audit", tool("check_smithing.py")),
        ("component parity", tool("check_parity_1_4.py", "--source", source)),
        ("Estus audit", tool("check_estus.py")),
        ("enchantment audit", tool("check_enchantments.py", "--source", source)),
        ("survival audit", tool("check_survival_milestone.py", "--source", source)),
        ("villager trade audit", tool("check_villager_trades.py", "--source", source)),
        ("structures", tool("convert_structures.py", "--source", source)),
        ("loot and structure audit", tool("check_loot_structures.py", "--source", source)),
        ("advancements", tool("generate_advancements.py", "--source", source)),
        ("advancement audit", tool("check_advancements.py", "--source", source)),
        ("global mechanics audit", tool("check_global_mechanics.py", "--source", source)),
        ("food interaction audit", tool("check_food_interactions.py")),
        ("world generation", tool("convert_worldgen.py", "--source", source)),
        ("world generation audit", tool("check_worldgen.py", "--source", source)),
        ("presentation assets", tool("convert_presentation_assets.py", "--source", source)),
        ("presentation audit", tool("check_presentation_assets.py", "--source", source)),
        ("recipe icon audit", tool("check_recipe_icons.py")),
        ("item name audit", tool("check_item_names.py")),
        ("vanilla replacement audit", tool("check_vanilla_replacements.py")),
        ("full source surface audit", tool("check_full_parity.py", "--source", source)),
        ("package add-on", ["/bin/sh", str(ROOT / "scripts/package.sh")]),
    ]

    environment = os.environ.copy()
    dependency_path = "/tmp/matcha_pydeps"
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (dependency_path, environment.get("PYTHONPATH")) if part
    )

    for number, (name, arguments) in enumerate(stages, 1):
        command = arguments
        print(f"[{number}/{len(stages)}] {name}", flush=True)
        if args.dry_run:
            print("  " + " ".join(command), flush=True)
            continue
        subprocess.run(command, cwd=ROOT, check=True, env=environment)


if __name__ == "__main__":
    main()
