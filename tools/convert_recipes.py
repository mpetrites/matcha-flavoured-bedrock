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


def options(value: str | list[str]) -> list[str]:
    values = value if isinstance(value, list) else [value]
    return [PROXY_ITEM_MAP.get(namespaced(value), namespaced(value)) for value in values]


def safe_name(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")


def result_for(recipe: dict) -> dict:
    source = recipe["result"]
    result = {"item": namespaced(source["id"])}
    if source.get("count", 1) != 1:
        result["count"] = source["count"]
    return result


def identifier(namespace: str, stem: str, variant: int, total: int) -> str:
    base = safe_name(f"{namespace}_{stem}")
    suffix = f"_v{variant + 1}" if total > 1 else ""
    return f"matcha_port:{base}{suffix}"


def description(recipe_id: str) -> dict:
    return {"identifier": recipe_id}


def convert_shaped(recipe: dict, namespace: str, stem: str) -> list[dict]:
    symbols = list(recipe["key"])
    choices = [options(recipe["key"][symbol]) for symbol in symbols]
    variants = list(itertools.product(*choices))
    converted = []
    for number, selected in enumerate(variants):
        key = {
            symbol: {"item": item}
            for symbol, item in zip(symbols, selected)
        }
        recipe_id = identifier(namespace, stem, number, len(variants))
        converted.append(
            {
                "format_version": "1.21.100",
                "minecraft:recipe_shaped": {
                    "description": description(recipe_id),
                    "tags": ["crafting_table"],
                    "pattern": recipe["pattern"],
                    "key": key,
                    "result": result_for(recipe),
                },
            }
        )
    return converted


def convert_shapeless(recipe: dict, namespace: str, stem: str) -> list[dict]:
    choices = [options(ingredient) for ingredient in recipe["ingredients"]]
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
                    "ingredients": [{"item": item} for item in selected],
                    "result": result_for(recipe),
                },
            }
        )
    return converted


def convert_single_input(
    recipe: dict, namespace: str, stem: str, kind: str
) -> list[dict]:
    inputs = options(recipe["ingredient"])
    converted = []
    for number, item in enumerate(inputs):
        recipe_id = identifier(namespace, stem, number, len(inputs))
        if kind == "stonecutting":
            body = {
                "description": description(recipe_id),
                "tags": ["stonecutter"],
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


def convert_smithing(recipe: dict, namespace: str, stem: str) -> list[dict]:
    fields = ["template", "base", "addition"]
    choices = [options(recipe[field]) for field in fields]
    variants = list(itertools.product(*choices))
    converted = []
    for number, selected in enumerate(variants):
        recipe_id = identifier(namespace, stem, number, len(variants))
        body = {
            "description": description(recipe_id),
            "tags": ["smithing_table"],
            **dict(zip(fields, selected)),
            "result": result_for(recipe)["item"],
        }
        converted.append(
            {
                "format_version": "1.21.100",
                "minecraft:recipe_smithing_transform": body,
            }
        )
    return converted


def convert(recipe: dict, namespace: str, stem: str) -> list[dict]:
    kind = TYPE_MAP[recipe["type"]]
    if kind == "shaped":
        return convert_shaped(recipe, namespace, stem)
    if kind == "shapeless":
        return convert_shapeless(recipe, namespace, stem)
    if kind == "smithing":
        return convert_smithing(recipe, namespace, stem)
    return convert_single_input(recipe, namespace, stem, kind)


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
