#!/usr/bin/env python3
"""Generate Bedrock custom foods, recipes, textures, and scripted effects."""

from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
from pathlib import Path

from convert_recipes import convert, safe_name


EXISTING_ITEMS = {
    "matcha:baked_apple",
    "matcha:charred_fish",
    "matcha:charred_meat",
    "matcha:charred_potato",
    "matcha:fried_egg",
}

LANG_START = "## BEGIN GENERATED MATCHA FOODS"
LANG_END = "## END GENERATED MATCHA FOODS"


def strip_namespace(value: str) -> str:
    return value.split(":", 1)[-1]


def source_stem(path: Path) -> str:
    return re.sub(r"_campfire$", "", path.stem)


def visual_key(recipe: dict, path: Path) -> str:
    components = recipe["result"]["components"]
    model = components.get("minecraft:item_model")
    if isinstance(model, str):
        return strip_namespace(model)
    custom_model = components.get("minecraft:custom_model_data", {})
    strings = custom_model.get("strings", [])
    if strings:
        return strip_namespace(strings[0])
    return source_stem(path)


def custom_item_id(recipe: dict, path: Path) -> str:
    key = safe_name(visual_key(recipe, path))
    namespace = path.parent.parent.name
    if namespace != "food":
        key = safe_name(f"{namespace}_{key}")
    return f"matcha:{key}"


def item_signature(recipe: dict) -> str:
    """Identity of the custom stack, excluding recipe-specific details."""
    result = recipe["result"]
    return json.dumps(
        [result["id"], result.get("components", {})],
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_recipe(entries: list[tuple[Path, dict]]) -> tuple[Path, dict]:
    return min(
        entries,
        key=lambda entry: (
            "_from_" in entry[0].stem,
            entry[0].stem.endswith("_campfire"),
            len(entry[0].stem),
            entry[0].stem,
        ),
    )


def display_name(recipe: dict, path: Path, lang: dict[str, str]) -> str:
    components = recipe["result"]["components"]
    item_name = components.get("minecraft:item_name") or components.get("minecraft:custom_name")
    if isinstance(item_name, str):
        return item_name
    if isinstance(item_name, dict):
        if "text" in item_name:
            return item_name["text"]
        if "translate" in item_name:
            translated = lang.get(item_name["translate"], "")
            if translated and not translated.startswith(("item.", "tile.", "entity.", "%")):
                return translated
    return source_stem(path).replace("_", " ").title()


def saturation_modifier(food: dict) -> float:
    nutrition = food.get("nutrition", 0)
    saturation = food.get("saturation", 0)
    if not nutrition:
        return 0.0
    return round(saturation / (nutrition * 2), 6)


def remainder(components: dict) -> str | None:
    value = components.get("minecraft:use_remainder")
    if not value:
        return None
    item = value.get("id")
    if not item:
        return None
    return item if ":" in item else f"minecraft:{item}"


def item_definition(item_id: str, recipe: dict, texture_key: str) -> dict:
    components = recipe["result"]["components"]
    food = components.get("minecraft:food", {})
    consumable = components.get("minecraft:consumable", {})
    is_splash = recipe["result"]["id"] == "minecraft:splash_potion"
    food_component = {
        "can_always_eat": food.get("can_always_eat", True),
        "nutrition": food.get("nutrition", 0),
        "saturation_modifier": saturation_modifier(food),
    }
    use_remainder = remainder(components)
    if not use_remainder and recipe["result"]["id"] in {"minecraft:potion", "minecraft:honey_bottle"}:
        use_remainder = "minecraft:glass_bottle"
    if use_remainder:
        food_component["using_converts_to"] = use_remainder

    sound = consumable.get("sound", "")
    use_animation = consumable.get("animation")
    if use_animation not in {"drink", "eat"}:
        use_animation = (
            "drink"
            if "drink" in sound or use_remainder == "minecraft:glass_bottle"
            or recipe["result"]["id"] in {"minecraft:potion","minecraft:splash_potion"}
            else "eat"
        )
    item_components = {
        "minecraft:display_name": {"value": f"item.{item_id}.name"},
        "minecraft:icon": {"textures": {"default": texture_key}},
        "minecraft:max_stack_size": components.get("minecraft:max_stack_size", 64),
    }
    if is_splash:
        # Script API supplies the aimed area impact. Keeping this out of the
        # food component prevents the former drink-to-apply approximation.
        item_components.update({
            "minecraft:interact_button": "Throw",
            "minecraft:use_animation": "bow",
            "minecraft:use_modifiers": {
                "use_duration": 0.1,
                "movement_modifier": 1.0,
            },
            "minecraft:cooldown": {
                "category": "matcha_splash_food",
                "duration": 0.25,
            },
        })
    else:
        item_components.update({
            "minecraft:food": food_component,
            "minecraft:use_modifiers": {
                "use_duration": consumable.get("consume_seconds", 1.6),
                "movement_modifier": 0.35,
            },
            "minecraft:use_animation": use_animation,
        })
    return {
        "format_version": "1.21.100",
        "minecraft:item": {
            "description": {
                "identifier": item_id,
                "menu_category": {
                    "category": "items",
                    "group": "minecraft:itemGroup.name.cookedFood",
                },
            },
            "components": item_components,
        },
    }


def effect_actions(recipe: dict) -> list[dict]:
    consumable = recipe["result"]["components"].get("minecraft:consumable", {})
    actions = []
    for action in consumable.get("on_consume_effects", []):
        action_type = strip_namespace(action["type"])
        converted = {"type": action_type}
        if "probability" in action:
            converted["probability"] = action["probability"]
        if action_type == "apply_effects":
            converted["effects"] = [
                {
                    "id": strip_namespace(effect["id"]),
                    "duration": effect.get("duration", 1),
                    "amplifier": effect.get("amplifier", 0),
                    "showParticles": effect.get("show_particles", True),
                }
                for effect in action.get("effects", [])
            ]
        elif action_type == "remove_effects":
            converted["effects"] = [
                strip_namespace(effect) for effect in action.get("effects", [])
            ]
        actions.append(converted)
    potion_effects = recipe["result"]["components"].get("minecraft:potion_contents", {}).get("custom_effects", [])
    if potion_effects:
        actions.append({
            "type": "apply_effects",
            "effects": [{
                "id": strip_namespace(effect["id"]),
                "duration": effect.get("duration", 1),
                "amplifier": effect.get("amplifier", 0),
                "showParticles": effect.get("show_particles", True),
            } for effect in potion_effects],
        })
    return actions


def find_texture(java_root: Path, key: str, recipe: dict) -> Path | None:
    candidates = [key]
    model = recipe["result"]["components"].get("minecraft:item_model")
    if isinstance(model, str):
        candidates.append(strip_namespace(model))
    for candidate in candidates:
        path = java_root / "assets/minecraft/textures/item" / f"{candidate}.png"
        if path.exists():
            return path
    return None


def replace_generated_lang(path: Path, entries: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    if LANG_START in text:
        before = text.split(LANG_START, 1)[0].rstrip()
        after = text.split(LANG_END, 1)[1].lstrip()
        text = before + "\n"
        if after:
            text += after
    block = "\n".join([LANG_START, *entries, LANG_END])
    path.write_text(text.rstrip() + "\n\n" + block + "\n", encoding="utf-8")


def write_effect_module(path: Path, effects: dict[str, list[dict]]) -> None:
    payload = json.dumps(effects, indent=2, ensure_ascii=False)
    path.write_text(
        "// Generated by tools/convert_foods.py. Do not edit by hand.\n"
        f"export const FOOD_EFFECTS = {payload};\n",
        encoding="utf-8",
    )


def write_interaction_module(path: Path, splashes: dict[str, list[dict]]) -> None:
    payload = json.dumps(splashes, indent=2, ensure_ascii=False)
    path.write_text(
        "// Generated by tools/convert_foods.py. Do not edit by hand.\n"
        f"export const SPLASH_FOODS = {payload};\n",
        encoding="utf-8",
    )


def clear_json_files(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.glob("*.json"):
        child.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("java_root", type=Path)
    parser.add_argument("behavior_pack", type=Path)
    parser.add_argument("resource_pack", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()

    java_data = args.java_root / "data"
    lang = json.loads(
        (args.java_root / "assets/minecraft/lang/en_us.json").read_text(
            encoding="utf-8"
        )
    )
    item_dir = args.behavior_pack / "items/generated_foods"
    recipe_dir = args.behavior_pack / "recipes/generated_foods"
    texture_dir = args.resource_pack / "textures/items/generated_foods"
    clear_json_files(item_dir)
    clear_json_files(recipe_dir)
    texture_dir.mkdir(parents=True, exist_ok=True)
    for texture in texture_dir.glob("*.png"):
        texture.unlink()

    recipes = []
    for path in sorted(java_data.glob("*/recipe/*.json")):
        recipe = json.loads(path.read_text(encoding="utf-8"))
        components = recipe.get("result", {}).get("components", {})
        if "minecraft:consumable" not in components and "minecraft:potion_contents" not in components:
            continue
        recipes.append((path, recipe))

    # Alternate recipes can yield the exact same component-bearing stack. All
    # such recipes must point at one Bedrock item definition.
    signature_groups: dict[str, list[tuple[Path, dict]]] = {}
    for entry in recipes:
        signature_groups.setdefault(item_signature(entry[1]), []).append(entry)
    item_id_by_signature = {}
    for signature, entries in signature_groups.items():
        canonical_path, canonical_data = canonical_recipe(entries)
        item_id_by_signature[signature] = custom_item_id(canonical_data, canonical_path)
    if len(set(item_id_by_signature.values())) != len(item_id_by_signature):
        raise SystemExit("Distinct food item signatures resolved to duplicate item identifiers")

    def resolved_item_id(recipe: dict) -> str:
        return item_id_by_signature[item_signature(recipe)]

    canonical: dict[str, tuple[Path, dict]] = {}
    effects: dict[str, list[dict]] = {}
    splashes: dict[str, list[dict]] = {}
    names: dict[str, str] = {}
    textures: dict[str, str] = {}
    conflicts = []

    for path, recipe in recipes:
        item_id = resolved_item_id(recipe)
        actions = effect_actions(recipe)
        if item_id in effects and effects[item_id] != actions:
            conflicts.append(
                {
                    "item": item_id,
                    "first": str(canonical[item_id][0]),
                    "second": str(path),
                }
            )
            continue
        if item_id in canonical:
            canonical[item_id] = canonical_recipe([canonical[item_id], (path, recipe)])
        else:
            canonical[item_id] = (path, recipe)
        effects[item_id] = actions
        if recipe["result"]["id"] == "minecraft:splash_potion":
            splashes[item_id] = actions

    if conflicts:
        raise SystemExit(
            "Conflicting food definitions:\n" + json.dumps(conflicts, indent=2)
        )

    # Alternate acquisition recipes (for example *_from_* and *_campfire)
    # share one item and must not rename it in the creative catalog.
    names = {
        item_id: display_name(recipe, path, lang)
        for item_id, (path, recipe) in canonical.items()
    }

    atlas_path = args.resource_pack / "textures/item_texture.json"
    atlas = json.loads(atlas_path.read_text(encoding="utf-8"))
    atlas["texture_data"] = {
        key: value
        for key, value in atlas["texture_data"].items()
        if not key.startswith("matcha_food_")
    }

    for item_id, (path, recipe) in sorted(canonical.items()):
        key = safe_name(visual_key(recipe, path))
        texture_key = f"matcha_food_{key}"
        source_texture = find_texture(args.java_root, key, recipe)
        if source_texture:
            destination = texture_dir / f"{key}.png"
            shutil.copyfile(source_texture, destination)
            texture_path = f"textures/items/generated_foods/{key}"
        else:
            texture_path = strip_namespace(recipe["result"]["id"])
        atlas["texture_data"][texture_key] = {"textures": texture_path}
        textures[item_id] = texture_path

        if item_id not in EXISTING_ITEMS:
            output = item_definition(item_id, recipe, texture_key)
            item_file = safe_name(strip_namespace(item_id)) + ".json"
            (item_dir / item_file).write_text(
                json.dumps(output, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    generated_recipe_count = 0
    for path, recipe in recipes:
        item_id = resolved_item_id(recipe)
        if item_id in EXISTING_ITEMS:
            continue
        recipe_copy = copy.deepcopy(recipe)
        count = recipe_copy["result"].get("count", 1)
        recipe_copy["result"] = {"id": item_id, "count": count}
        if path.stem == "estus_flask":
            recipe_copy["ingredients"] = [
                "minecraft:glass_bottle",
                "matcha:estus_ash",
                "matcha:estus_ash",
            ]
        converted = convert(
            recipe_copy, path.parent.parent.name, f"food_{path.stem}"
        )
        for number, output in enumerate(converted):
            suffix = f"_v{number + 1}" if len(converted) > 1 else ""
            output_path = recipe_dir / (
                safe_name(f"{path.parent.parent.name}_food_{path.stem}{suffix}")
                + ".json"
            )
            output_path.write_text(
                json.dumps(output, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            generated_recipe_count += 1

    atlas_path.write_text(
        json.dumps(atlas, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    replace_generated_lang(
        args.resource_pack / "texts/en_US.lang",
        [f"item.{item_id}.name={name}" for item_id, name in sorted(names.items())],
    )
    write_effect_module(args.behavior_pack / "scripts/food_effects.js", effects)
    write_interaction_module(
        args.behavior_pack / "scripts/food_interaction_data.js", splashes
    )
    (args.behavior_pack / "functions/matcha_consumables_test.mcfunction").write_text(
        "# Generated consumables test kit\n"
        + "\n".join(f"give @s {item_id} 1" for item_id in sorted(effects))
        + "\n",
        encoding="utf-8",
    )

    report = {
        "source_food_recipes": len(recipes),
        "custom_food_items": len(canonical),
        "existing_items_reused": len(EXISTING_ITEMS & canonical.keys()),
        "new_item_definitions": len(canonical.keys() - EXISTING_ITEMS),
        "bedrock_recipe_variants": generated_recipe_count,
        "scripted_food_effects": len(effects),
        "scripted_splash_foods": len(splashes),
        "textures": textures,
        "conflicts": conflicts,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "textures"}))


if __name__ == "__main__":
    main()
