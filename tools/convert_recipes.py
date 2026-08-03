#!/usr/bin/env python3
"""Convert component-free Matcha Flavoured Java recipes to Bedrock JSON."""

from __future__ import annotations

import argparse
import itertools
import json
import re
from collections import Counter
from pathlib import Path


TYPE_MAP = {
    "minecraft:crafting_shaped": "shaped",
    "minecraft:crafting_shapeless": "shapeless",
    "minecraft:stonecutting": "stonecutting",
    "minecraft:smithing_transform": "smithing",
    "minecraft:smelting": "furnace",
    "minecraft:blasting": "blast_furnace",
    "minecraft:smoking": "smoker",
    "minecraft:campfire_cooking": "campfire",
}
PROXY_ITEM_MAP = {
    "minecraft:enderman_spawn_egg": "matcha:flour",
    "minecraft:magma_cube_spawn_egg": "matcha:flour_bag",
    "minecraft:shulker_spawn_egg": "matcha:dough",
    "minecraft:strider_spawn_egg": "matcha:uncooked_curry",
    "minecraft:zombified_piglin_spawn_egg": "matcha:uncooked_green_curry",
    "minecraft:zoglin_spawn_egg": "matcha:uncooked_paneer_makhani",
    "minecraft:wither_skeleton_spawn_egg": "matcha:uncooked_ramen",
    "minecraft:endermite_spawn_egg": "matcha:benzene",
    # Java names which Bedrock still exposes under legacy runtime IDs.
    "minecraft:bricks": "minecraft:brick_block",
    "minecraft:dead_bush": "minecraft:deadbush",
    "minecraft:end_stone_bricks": "minecraft:end_bricks",
    "minecraft:light_gray_glazed_terracotta": "minecraft:silver_glazed_terracotta",
    "minecraft:magma_block": "minecraft:magma",
    "minecraft:nether_bricks": "minecraft:nether_brick",
    "minecraft:oak_button": "minecraft:wooden_button",
    "minecraft:oak_door": "minecraft:wooden_door",
    "minecraft:oak_fence_gate": "minecraft:fence_gate",
    "minecraft:oak_pressure_plate": "minecraft:wooden_pressure_plate",
    "minecraft:oak_trapdoor": "minecraft:trapdoor",
    "minecraft:powered_rail": "minecraft:golden_rail",
    "minecraft:red_nether_bricks": "minecraft:red_nether_brick",
    "minecraft:snow_block": "minecraft:snow",
    "minecraft:terracotta": "minecraft:hardened_clay",
    "minecraft:slime_block": "minecraft:slime",
    "minecraft:spectral_arrow": "minecraft:arrow",
    # Java `snow` is the thin layer; Bedrock reserves `snow` for the block.
    "minecraft:snow": "minecraft:snow_layer",
    "minecraft:waxed_copper_block": "minecraft:waxed_copper",
    "#minecraft:acacia_logs": "minecraft:acacia_log",
    "#minecraft:bamboo_blocks": "minecraft:bamboo_block",
    "#minecraft:birch_logs": "minecraft:birch_log",
    "#minecraft:cherry_logs": "minecraft:cherry_log",
    "#minecraft:coals": "minecraft:coal",
    "#minecraft:copper_tool_materials": "minecraft:copper_ingot",
    "#minecraft:crimson_stems": "minecraft:crimson_stem",
    "#minecraft:dark_oak_logs": "minecraft:dark_oak_log",
    "#minecraft:diamond_tool_materials": "minecraft:diamond",
    "#minecraft:eggs": "minecraft:egg",
    "#minecraft:gold_tool_materials": "minecraft:gold_ingot",
    "#minecraft:iron_tool_materials": "minecraft:iron_ingot",
    "#minecraft:jungle_logs": "minecraft:jungle_log",
    "#minecraft:logs": "minecraft:oak_log",
    "#minecraft:logs_that_burn": "minecraft:oak_log",
    "#minecraft:mangrove_logs": "minecraft:mangrove_log",
    "#minecraft:oak_logs": "minecraft:oak_log",
    "#minecraft:pale_oak_logs": "minecraft:pale_oak_log",
    "#minecraft:planks": "minecraft:oak_planks",
    "#minecraft:soul_fire_base_blocks": "minecraft:soul_sand",
    "#minecraft:spruce_logs": "minecraft:spruce_log",
    "#minecraft:stone_crafting_materials": "minecraft:cobblestone",
    "#minecraft:terracotta": "minecraft:hardened_clay",
    "#minecraft:warped_stems": "minecraft:warped_stem",
    "#minecraft:wooden_tool_materials": "minecraft:oak_planks",
    "#minecraft:wool": "minecraft:white_wool",
}

# Generated singleton replacements extend the hand-maintained proxy list.  This
# file is deliberately optional so the converter can still bootstrap a clean
# checkout before the replacement audit has run.
_replacement_file = Path(__file__).with_name("vanilla_replacements.json")
if _replacement_file.exists():
    PROXY_ITEM_MAP.update(
        json.loads(_replacement_file.read_text(encoding="utf-8")).get(
            "replacements", {}
        )
    )


def namespaced(value: str) -> str:
    return value if ":" in value else f"minecraft:{value}"


def options(value: str | list[str], preserve_inputs: frozenset[str] = frozenset()) -> list[str]:
    values = value if isinstance(value, list) else [value]
    return [
        namespaced(value)
        if namespaced(value) in preserve_inputs
        else PROXY_ITEM_MAP.get(value, PROXY_ITEM_MAP.get(namespaced(value), namespaced(value)))
        for value in values
    ]


def safe_name(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")


def result_for(recipe: dict) -> dict:
    source = recipe["result"]
    source_id = namespaced(source["id"])
    result = {"item": PROXY_ITEM_MAP.get(source_id, source_id)}
    if source.get("count", 1) != 1:
        result["count"] = source["count"]
    return result


def identifier(namespace: str, stem: str, variant: int, total: int) -> str:
    base = safe_name(f"{namespace}_{stem}")
    suffix = f"_v{variant + 1}" if total > 1 else ""
    return f"matcha:{base}{suffix}"


def description(recipe_id: str) -> dict:
    return {"identifier": recipe_id}


def convert_shaped(recipe: dict, namespace: str, stem: str, preserve_inputs: frozenset[str]) -> list[dict]:
    symbols = list(recipe["key"])
    # Bedrock counts UTF-8 bytes rather than Unicode code points when it
    # validates pattern width. Normalize Java's arbitrary key symbols to
    # single-byte ASCII so a 2x2 recipe cannot be misread as 4x2.
    ascii_symbols = iter("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
    symbol_map = {symbol: next(ascii_symbols) for symbol in symbols}
    choices = [options(recipe["key"][symbol], preserve_inputs) for symbol in symbols]
    variants = list(itertools.product(*choices))
    converted = []
    for number, selected in enumerate(variants):
        key = {
            symbol_map[symbol]: {"item": item}
            for symbol, item in zip(symbols, selected)
        }
        recipe_id = identifier(namespace, stem, number, len(variants))
        converted.append(
            {
                "format_version": "1.21.100",
                "minecraft:recipe_shaped": {
                    "description": description(recipe_id),
                    "tags": ["crafting_table"],
                    "unlock": {"context": "AlwaysUnlocked"},
                    "pattern": [
                        "".join(symbol_map.get(symbol, symbol) for symbol in row)
                        for row in recipe["pattern"]
                    ],
                    "key": key,
                    "result": result_for(recipe),
                },
            }
        )
    return converted


def convert_shapeless(recipe: dict, namespace: str, stem: str, preserve_inputs: frozenset[str]) -> list[dict]:
    choices = [options(ingredient, preserve_inputs) for ingredient in recipe["ingredients"]]
    variants = list(itertools.product(*choices))
    converted = []
    for number, selected in enumerate(variants):
        recipe_id = identifier(namespace, stem, number, len(variants))
        converted.append(
            {
                "format_version": "1.21.100",
                "minecraft:recipe_shapeless": {
                    "description": description(recipe_id),
                    "tags": ["crafting_table"],
                    "unlock": {"context": "AlwaysUnlocked"},
                    "ingredients": [{"item": item} for item in selected],
                    "result": result_for(recipe),
                },
            }
        )
    return converted


def convert_single_input(
    recipe: dict, namespace: str, stem: str, kind: str, preserve_inputs: frozenset[str]
) -> list[dict]:
    inputs = options(recipe["ingredient"], preserve_inputs)
    converted = []
    for number, item in enumerate(inputs):
        recipe_id = identifier(namespace, stem, number, len(inputs))
        if kind == "stonecutting":
            body = {
                "description": description(recipe_id),
                "tags": ["stonecutter"],
                "unlock": {"context": "AlwaysUnlocked"},
                "ingredients": [{"item": item}],
                "result": result_for(recipe),
            }
            converted.append(
                {
                    "format_version": "1.21.100",
                    "minecraft:recipe_shapeless": body,
                }
            )
        else:
            body = {
                "description": description(recipe_id),
                "tags": [kind],
                "input": item,
                "output": result_for(recipe)["item"],
            }
            converted.append(
                {
                    "format_version": "1.21.100",
                    "minecraft:recipe_furnace": body,
                }
            )
    return converted


def convert_smithing(recipe: dict, namespace: str, stem: str, preserve_inputs: frozenset[str]) -> list[dict]:
    fields = ["template", "base", "addition"]
    choices = [options(recipe[field], preserve_inputs) for field in fields]
    variants = list(itertools.product(*choices))
    converted = []
    for number, selected in enumerate(variants):
        recipe_id = identifier(namespace, stem, number, len(variants))
        # Bedrock smithing transforms only accept the Netherite upgrade
        # material/template slots. Preserve custom progression as ordinary
        # crafting; this intentionally creates a fresh result item.
        body = {
            "description": description(recipe_id),
            "tags": ["crafting_table"],
            "unlock": {"context": "AlwaysUnlocked"},
            "ingredients": [{"item": item} for item in selected],
            "result": result_for(recipe),
        }
        converted.append(
            {
                "format_version": "1.21.100",
                "minecraft:recipe_shapeless": body,
            }
        )
    return converted


def convert(
    recipe: dict,
    namespace: str,
    stem: str,
    preserve_inputs: frozenset[str] = frozenset(),
) -> list[dict]:
    kind = TYPE_MAP[recipe["type"]]
    if kind == "shaped":
        return convert_shaped(recipe, namespace, stem, preserve_inputs)
    if kind == "shapeless":
        return convert_shapeless(recipe, namespace, stem, preserve_inputs)
    if kind == "smithing":
        return convert_smithing(recipe, namespace, stem, preserve_inputs)
    return convert_single_input(recipe, namespace, stem, kind, preserve_inputs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("java_data", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    source_files = sorted(args.java_data.glob("*/recipe/*.json"))
    counts: Counter[str] = Counter()
    skipped = []
    generated = []

    for source_file in source_files:
        namespace = source_file.parent.parent.name
        recipe = json.loads(source_file.read_text(encoding="utf-8"))
        recipe_type = recipe.get("type")
        if namespace == "crafting" and source_file.stem == "bronze_alloy":
            skipped.append(
                {"source": str(source_file.relative_to(args.java_data.parent)), "reason": "replaced by native matcha:bronze_alloy recipe"}
            )
            counts["skipped_native_replacements"] += 1
            continue
        if recipe_type not in TYPE_MAP:
            skipped.append(
                {"source": str(source_file.relative_to(args.java_data.parent)), "reason": f"unsupported type {recipe_type}"}
            )
            continue
        if recipe.get("result", {}).get("components"):
            skipped.append(
                {
                    "source": str(source_file.relative_to(args.java_data.parent)),
                    "reason": "Java-only result components require a custom Bedrock item",
                }
            )
            counts["skipped_component_results"] += 1
            continue

        converted = convert(recipe, namespace, source_file.stem)
        counts["source_recipes_converted"] += 1
        counts["bedrock_recipes_generated"] += len(converted)
        counts[recipe_type] += 1
        for number, output in enumerate(converted):
            suffix = f"_v{number + 1}" if len(converted) > 1 else ""
            output_name = safe_name(f"{namespace}_{source_file.stem}{suffix}") + ".json"
            output_path = args.output / output_name
            output_path.write_text(
                json.dumps(output, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            generated.append(str(output_path))

    report = {
        "source_recipe_count": len(source_files),
        "counts": dict(sorted(counts.items())),
        "generated_files": len(generated),
        "skipped_count": len(skipped),
        "skipped": skipped,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items() if key != "skipped"}))


if __name__ == "__main__":
    main()
