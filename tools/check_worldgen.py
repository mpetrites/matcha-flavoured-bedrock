#!/usr/bin/env python3
"""Verify generated biome presentation and dimension approximations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from upstream import add_source_argument, validate_source


ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
add_source_argument(parser)
args = parser.parse_args()
source = validate_source(args.source)
source_biomes = sorted((source / "data/minecraft/worldgen/biome").glob("*.json"))
client_files = sorted((ROOT / "resource_pack/client_biomes").glob("*.json"))
fog_files = sorted((ROOT / "resource_pack/fogs/generated_matcha").glob("*.json"))

checks: list[tuple[str, bool]] = []
checks.append(("all source biomes converted", len(source_biomes) == len(client_files) == 65))
fog_ids = set()
for path in fog_files:
    fog = json.loads(path.read_text(encoding="utf-8"))
    fog_ids.add(fog["minecraft:fog_settings"]["description"]["identifier"])

components_seen = set()
for path in client_files:
    data = json.loads(path.read_text(encoding="utf-8"))["minecraft:client_biome"]
    checks.append((f"identifier {path.stem}", data["description"]["identifier"] == f"minecraft:{path.stem}"))
    components = data["components"]
    components_seen.update(components)
    fog = components.get("minecraft:fog_appearance", {}).get("fog_identifier")
    checks.append((f"fog reference {path.stem}", fog is None or fog in fog_ids))

checks.extend([
    ("all presentation component families present", {
        "minecraft:sky_color", "minecraft:water_appearance", "minecraft:grass_appearance",
        "minecraft:foliage_appearance", "minecraft:dry_foliage_color", "minecraft:fog_appearance",
    } <= components_seen),
    ("Nether water override loaded", 'import "./worldgen.js"' in (ROOT / "behavior_pack/scripts/main.js").read_text()),
    ("Nether water placement implemented", 'block.setType("minecraft:water")' in (ROOT / "behavior_pack/scripts/worldgen.js").read_text()),
])
failed = [name for name, passed in checks if not passed]
report = {
    "checks": len(checks), "passed": len(checks) - len(failed), "failed": failed,
    "source_biomes": len(source_biomes), "client_biomes": len(client_files), "fogs": len(fog_files),
}
(ROOT / "docs/worldgen-check-report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
raise SystemExit(bool(failed))
