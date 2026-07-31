#!/usr/bin/env python3
"""Import vanilla proxy icons used by Matcha recipe items."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "resource_pack/textures/item_texture.json"
DESTINATION = ROOT / "resource_pack/textures/items/vanilla_proxy"

# Matcha item identifier -> path within the official Bedrock resource pack.
SOURCES = {
    "matcha:baked_pumpkin": "textures/items/breeze_rod.png",
    "matcha:bedrock_buster": "textures/items/spawn_eggs/spawn_egg_chicken.png",
    "matcha:benzene": "textures/items/spawn_eggs/spawn_egg_endermite.png",
    "matcha:blessing_hell_bound_book": "textures/items/book_enchanted.png",
    "matcha:carbon_rich_iron": "textures/items/spawn_eggs/spawn_egg_piglin_brute.png",
    "matcha:cheese": "textures/items/cookie.png",
    "matcha:cooked_beef": "textures/items/beef_cooked.png",
    "matcha:cooked_chicken": "textures/items/chicken_cooked.png",
    "matcha:cooked_mutton": "textures/items/mutton_cooked.png",
    "matcha:cooked_porkchop": "textures/items/porkchop_cooked.png",
    "matcha:copper_compass": "textures/items/compass_item.png",
    "matcha:crafting_chicken_noodle_soup": "textures/items/rabbit_stew.png",
    "matcha:crafting_golden_pie": "textures/items/pumpkin_pie.png",
    "matcha:crafting_morsel_stew": "textures/items/rabbit_stew.png",
    "matcha:crafting_squid_ink_pasta": "textures/items/rabbit_stew.png",
    "matcha:crafting_stuffed_mushrooms": "textures/items/potato_baked.png",
    "matcha:dried_kelp": "textures/items/dried_kelp.png",
    "matcha:dried_kelp_from_dried_kelp_block": "textures/items/dried_kelp.png",
    "matcha:estus_ash": "textures/items/glowstone_dust.png",
    "matcha:flour_bag": "textures/items/spawn_eggs/spawn_egg_magma_cube.png",
    "matcha:golden_compass": "textures/items/compass_item.png",
    "matcha:milk_bottle": "textures/items/beetroot_soup.png",
    "matcha:popped_chorus_fruit": "textures/items/chorus_fruit_popped.png",
    "matcha:potions_estus_flask": "textures/items/potion_bottle_drinkable.png",
    "matcha:uncooked_curry": "textures/items/spawn_eggs/spawn_egg_strider.png",
    "matcha:uncooked_green_curry": "textures/items/spawn_eggs/spawn_egg_zombified_piglin.png",
    "matcha:uncooked_paneer_makhani": "textures/items/spawn_eggs/spawn_egg_zoglin.png",
    "matcha:uncooked_ramen": "textures/items/spawn_eggs/spawn_egg_wither_skeleton.png",
    "matcha:wooden_axe": "textures/items/wood_axe.png",
    "matcha:wooden_hoe": "textures/items/wood_hoe.png",
    "matcha:wooden_pickaxe": "textures/items/wood_pickaxe.png",
    "matcha:wooden_shovel": "textures/items/wood_shovel.png",
    "matcha:wooden_sword": "textures/items/wood_sword.png",
}


def item_icons() -> dict[str, str]:
    icons = {}
    for path in (ROOT / "behavior_pack/items").rglob("*.json"):
        body = json.loads(path.read_text(encoding="utf-8")).get("minecraft:item", {})
        identifier = body.get("description", {}).get("identifier")
        icon = body.get("components", {}).get("minecraft:icon", {})
        textures = icon.get("textures", {}) if isinstance(icon, dict) else {}
        if identifier and isinstance(textures, dict) and textures.get("default"):
            icons[identifier] = textures["default"]
    return icons


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path, help="Official Bedrock resource_pack directory")
    args = parser.parse_args()
    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    texture_data = atlas["texture_data"]
    texture_data["matcha_component_flour"] = {
        "textures": "textures/items/generated_components/flour"
    }
    texture_data["matcha_component_dough"] = {
        "textures": "textures/items/generated_components/dough"
    }
    texture_data["matcha_component_warding_shield"] = {
        "textures": "textures/items/generated_components/warding_shield"
    }
    icons = item_icons()
    DESTINATION.mkdir(parents=True, exist_ok=True)

    copied = set()
    for identifier, relative_source in SOURCES.items():
        source = args.source / relative_source
        if not source.is_file():
            raise SystemExit(f"Missing official texture: {source}")
        output_name = source.name
        destination = DESTINATION / output_name
        if destination not in copied:
            shutil.copyfile(source, destination)
            copied.add(destination)
        texture_data[icons[identifier]] = {
            "textures": f"textures/items/vanilla_proxy/{destination.stem}"
        }

    ATLAS.write_text(json.dumps(atlas, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"items_fixed": len(SOURCES), "textures_copied": len(copied)}))


if __name__ == "__main__":
    main()
