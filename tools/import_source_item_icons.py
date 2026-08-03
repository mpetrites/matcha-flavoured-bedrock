#!/usr/bin/env python3
"""Import exact Java item textures for unresolved custom-item atlas entries."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from upstream import add_source_argument


ROOT = Path(__file__).resolve().parents[1]
ATLAS = ROOT / "resource_pack/textures/item_texture.json"
DESTINATION = ROOT / "resource_pack/textures/items/source_imports"
REPORT = ROOT / "docs/item-icon-audit.json"
BEDROCK_BASE_TEXTURES = {
    "textures/blocks/calcite",
    "textures/blocks/dripstone_block",
    "textures/blocks/glass",
    "textures/blocks/stone",
    "textures/blocks/stone_andesite",
    "textures/blocks/stone_granite",
    "textures/blocks/tuff",
    "textures/items/apple_golden",
    "textures/items/blaze_powder",
    "textures/items/book_writable",
    "textures/items/bundle_red",
    "textures/items/charcoal",
    "textures/items/chorus_fruit",
    "textures/items/clownfish_raw",
    "textures/items/dye_powder_blue",
    "textures/items/fish_pufferfish_raw",
    "textures/items/fish_raw",
    "textures/items/glow_berries",
    "textures/items/melon",
    "textures/items/snowball",
    "textures/items/trident",
}

# Generators use Java item/model names, while the checked-in Bedrock proxy
# textures use Bedrock's legacy filenames. These are fallbacks only: a matching
# Java texture must always win, even when an older generated or proxy texture is
# already present locally.
VANILLA_PROXY_BY_IDENTIFIER = {
    "matcha:baked_pumpkin": "breeze_rod",
    "matcha:blessing_hell_bound_book": "book_enchanted",
    "matcha:carbon_rich_iron": "spawn_egg_piglin_brute",
    "matcha:cooked_beef": "beef_cooked",
    "matcha:cooked_chicken": "chicken_cooked",
    "matcha:cooked_mutton": "mutton_cooked",
    "matcha:cooked_porkchop": "porkchop_cooked",
    "matcha:copper_compass": "compass_item",
    "matcha:crafting_chicken_noodle_soup": "rabbit_stew",
    "matcha:crafting_golden_pie": "pumpkin_pie",
    "matcha:crafting_morsel_stew": "rabbit_stew",
    "matcha:crafting_squid_ink_pasta": "rabbit_stew",
    "matcha:dried_kelp": "dried_kelp",
    "matcha:flour_bag": "spawn_egg_magma_cube",
    "matcha:golden_compass": "compass_item",
    "matcha:popped_chorus_fruit": "chorus_fruit_popped",
    "matcha:uncooked_curry": "spawn_egg_strider",
    "matcha:uncooked_green_curry": "spawn_egg_zombified_piglin",
    "matcha:uncooked_paneer_makhani": "spawn_egg_zoglin",
    "matcha:uncooked_ramen": "spawn_egg_wither_skeleton",
    "matcha:wooden_axe": "wood_axe",
    "matcha:wooden_hoe": "wood_hoe",
    "matcha:wooden_pickaxe": "wood_pickaxe",
    "matcha:wooden_shovel": "wood_shovel",
    "matcha:wooden_sword": "wood_sword",
}


def used_icons() -> dict[str, dict[str, str]]:
    icons = {}
    for path in (ROOT / "behavior_pack/items").rglob("*.json"):
        body = json.loads(path.read_text(encoding="utf-8")).get("minecraft:item", {})
        identifier = body.get("description", {}).get("identifier")
        icon = body.get("components", {}).get("minecraft:icon", {})
        key = icon.get("textures", {}).get("default") if isinstance(icon, dict) else icon
        if identifier and key:
            icons[key] = {"identifier": identifier, "definition": str(path.relative_to(ROOT))}
    return icons


def main() -> None:
    parser = argparse.ArgumentParser()
    add_source_argument(parser)
    args = parser.parse_args()
    source = args.source.resolve()
    if not (source / "assets/minecraft/textures/item").is_dir():
        raise SystemExit(f"Missing Java item textures: {source}")
    source_items = source / "assets/minecraft/textures/item"
    atlas = json.loads(ATLAS.read_text(encoding="utf-8"))
    texture_data = atlas["texture_data"]
    destination_root = ROOT / "resource_pack"
    DESTINATION.mkdir(parents=True, exist_ok=True)

    imported = []
    base_pack = []
    unresolved = []
    for key, details in sorted(used_icons().items()):
        entry = texture_data.get(key)
        texture = entry.get("textures") if isinstance(entry, dict) else entry
        if not isinstance(texture, str):
            continue

        # Resolve by the custom-item identifier first. Atlas paths can point at
        # stale Bedrock proxies from an earlier build, whereas the identifier's
        # stem is stable and matches Java's custom texture naming convention.
        identifier_stem = details["identifier"].split(":", 1)[-1]
        source_candidates = [source_items / f"{identifier_stem}.png"]
        texture_candidate = source_items / f"{Path(texture).name}.png"
        if texture_candidate not in source_candidates:
            source_candidates.append(texture_candidate)
        source_texture = next((candidate for candidate in source_candidates if candidate.is_file()), None)
        if source_texture is not None:
            destination = DESTINATION / f"{identifier_stem}.png"
            shutil.copyfile(source_texture, destination)
            texture_data[key] = {"textures": f"textures/items/source_imports/{destination.stem}"}
            imported.append({**details, "atlas_key": key, "source": str(source_texture.relative_to(source))})
            continue

        local_texture = destination_root / f"{texture}.png"
        if local_texture.is_file():
            if texture.startswith("textures/items/source_imports/"):
                imported.append({**details, "atlas_key": key, "source": texture})
            continue
        proxy_stem = VANILLA_PROXY_BY_IDENTIFIER.get(details["identifier"])
        proxy_texture = ROOT / f"resource_pack/textures/items/vanilla_proxy/{proxy_stem}.png"
        if proxy_stem and proxy_texture.is_file():
            texture_data[key] = {"textures": f"textures/items/vanilla_proxy/{proxy_stem}"}
            imported.append({**details, "atlas_key": key, "source": str(proxy_texture.relative_to(ROOT))})
            continue
        if texture in BEDROCK_BASE_TEXTURES:
            base_pack.append({**details, "atlas_key": key, "texture": texture})
            continue

        unresolved.append({**details, "atlas_key": key, "texture": texture})

    ATLAS.write_text(json.dumps(atlas, indent=2) + "\n", encoding="utf-8")
    report = {
        "used_custom_item_icons": len(used_icons()),
        "exact_source_imports": len(imported),
        "bedrock_base_references": len(base_pack),
        "unresolved_icons": len(unresolved),
        "imported": imported,
        "base_pack": base_pack,
        "unresolved": unresolved,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if not isinstance(value, list)}))


if __name__ == "__main__":
    main()
