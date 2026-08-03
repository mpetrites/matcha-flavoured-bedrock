#!/usr/bin/env python3
"""Inventory every pinned Java source surface and record its Bedrock handling."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from upstream import add_source_argument, baseline, validate_source


ROOT = Path(__file__).resolve().parents[1]

# Classification is intentionally exhaustive. A new upstream namespace/type
# fails this audit until its Bedrock ownership is explicitly decided.
ROUTES = {
    "data/blasting/recipe": ("converted", "recipe converter"),
    "data/blessings/recipe": ("converted", "blessing generator and scripted enchantments"),
    "data/crafting/recipe": ("converted", "recipe/component/equipment generators"),
    "data/custom_music/jukebox_song": ("classified", "presentation report; no obtainable source recipe"),
    "data/custom_music/recipe": ("converted", "recipe converter"),
    "data/endless_repairs/README.txt": ("classified", "source documentation"),
    "data/endless_repairs/advancement": ("converted", "advancement registry"),
    "data/endless_repairs/function": ("implemented", "scripted repair-state behavior"),
    "data/food/recipe": ("converted", "food and recipe converters"),
    "data/main/advancement": ("converted", "advancement registry"),
    "data/main/banner_pattern": ("engine-limited", "Java banner registry has no behavior-pack equivalent"),
    "data/main/enchantment": ("implemented", "blessings and scripted enchantments"),
    "data/main/function": ("implemented", "survival, mechanics, worldgen, villager, and interaction scripts"),
    "data/main/instrument": ("implemented", "Happy Ghast horn interaction"),
    "data/main/jukebox_song": ("implemented", "custom items and sound events"),
    "data/main/predicate": ("implemented", "script event/state adapters"),
    "data/main/tags": ("classified", "expanded or routed by generators/scripts"),
    "data/minecraft/dimension_type": ("engine-limited", "documented in worldgen report"),
    "data/minecraft/enchantment": ("implemented", "enchantment generator/script routing"),
    "data/minecraft/loot_table": ("converted", "loot converter"),
    "data/minecraft/predicate": ("implemented", "scripted environment adapter"),
    "data/minecraft/structure": ("converted", "mcstructure converter"),
    "data/minecraft/tags": ("classified", "expanded by converters or documented as engine-limited"),
    "data/minecraft/timeline": ("implemented", "extended day script"),
    "data/minecraft/trade_set": ("converted", "villager trade catalog"),
    "data/minecraft/villager_trade": ("converted", "villager trade catalog"),
    "data/minecraft/worldgen": ("converted", "client biomes, structures, and documented limits"),
    "data/potions/recipe": ("converted", "food/component converter"),
    "data/smelting/recipe": ("converted", "recipe converter"),
    "data/smithing_table/recipe": ("implemented", "state-preserving scripted smithing"),
    "data/smoking/recipe": ("converted", "recipe converter"),
    "data/stonecutting/recipe": ("converted", "recipe converter"),
    "assets/matcha/sounds": ("converted", "sound definitions"),
    "assets/minecraft/blockstates": ("classified", "textures ported; Java geometry documented"),
    "assets/minecraft/equipment": ("converted", "armor attachables and equipment generator"),
    "assets/minecraft/items": ("converted", "custom item definitions/icons"),
    "assets/minecraft/lang": ("converted", "English item and advancement names"),
    "assets/minecraft/models": ("classified", "icons/attachables ported; Java model semantics documented"),
    "assets/minecraft/sounds": ("converted", "bell overrides"),
    "assets/minecraft/sounds.json": ("converted", "sound definitions"),
    "assets/minecraft/texts": ("classified", "source credits preserved by project attribution"),
    "assets/minecraft/textures": ("converted", "presentation converter and source icon importer"),
}


def surface(path: Path, root: Path) -> str:
    relative = path.relative_to(root)
    parts = relative.parts
    return "/".join(parts[:2]) if len(parts) > 1 else parts[0]


parser = argparse.ArgumentParser(description=__doc__)
add_source_argument(parser)
source = validate_source(parser.parse_args().source)
counts: Counter[str] = Counter()
for root_name in ("data", "assets"):
    root = source / root_name
    for path in root.rglob("*"):
        if path.is_file():
            counts[f"{root_name}/{surface(path, root)}"] += 1

unclassified = sorted(set(counts) - set(ROUTES))
stale_routes = sorted(set(ROUTES) - set(counts))
surfaces = [
    {"surface": name, "files": count, "status": ROUTES[name][0], "handling": ROUTES[name][1]}
    for name, count in sorted(counts.items()) if name in ROUTES
]
status_counts = Counter(row["status"] for row in surfaces)
report = {
    "baseline": baseline(),
    "summary": {
        "source_files": sum(counts.values()),
        "surfaces": len(counts),
        "classified_surfaces": len(surfaces),
        "unclassified_surfaces": len(unclassified),
        "stale_routes": len(stale_routes),
        "status_counts": dict(sorted(status_counts.items())),
        "status": "pass" if not unclassified and not stale_routes else "fail",
    },
    "surfaces": surfaces,
    "unclassified": unclassified,
    "stale_routes": stale_routes,
}
(ROOT / "docs/full-parity-audit.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report["summary"]))
raise SystemExit(bool(unclassified or stale_routes))
