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

        local_texture = destination_root / f"{texture}.png"
        if local_texture.is_file():
            if texture.startswith("textures/items/source_imports/"):
                imported.append({**details, "atlas_key": key, "source": texture})
            continue
        if texture in BEDROCK_BASE_TEXTURES:
            base_pack.append({**details, "atlas_key": key, "texture": texture})
            continue

        source_texture = source_items / f"{Path(texture).name}.png"
        if source_texture.is_file():
            destination = DESTINATION / source_texture.name
            shutil.copyfile(source_texture, destination)
            texture_data[key] = {"textures": f"textures/items/source_imports/{destination.stem}"}
            imported.append({**details, "atlas_key": key, "source": str(source_texture.relative_to(source))})
        else:
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
