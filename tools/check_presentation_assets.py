#!/usr/bin/env python3
"""Audit converted presentation assets, jukebox records, and biome ambience."""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

from upstream import add_source_argument, validate_source


ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
add_source_argument(parser)
args = parser.parse_args()
source = validate_source(args.source)
rp = ROOT / "resource_pack"
checks: list[tuple[str, bool]] = []


def dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    return struct.unpack(">II", data[16:24])


expected = {
    "block textures": (source / "assets/minecraft/textures/block", rp / "textures/blocks", "*.png"),
    "trim textures": (source / "assets/minecraft/textures/trims", rp / "textures/trims", "*.png"),
    "colormaps": (source / "assets/minecraft/textures/colormap", rp / "textures/colormap", "*.png"),
    "particle textures": (source / "assets/minecraft/textures/particle", rp / "textures/particle/matcha", "*.png"),
}
for name, (upstream, converted, pattern) in expected.items():
    checks.append((name, len(list(upstream.rglob(pattern))) == len(list(converted.rglob(pattern)))))

checks.extend([
    ("four particle definitions", len(list((rp / "particles/generated_matcha").glob("*.json"))) == 4),
    ("source sun mapped", (rp / "textures/environment/sun.png").exists()),
    ("source weather mapped", (rp / "textures/environment/weather.png").exists()),
    ("moon phase atlas", dimensions(rp / "textures/environment/moon_phases.png") == (128, 64)),
    ("Match painting atlas", dimensions(rp / "textures/painting/kz.png") == (256, 256)),
    ("two custom tracks", len(list((rp / "sounds/matcha/custom").glob("*.ogg"))) == 2),
    ("two bell overrides", len(list((rp / "sounds/block/bell").glob("*.ogg"))) == 2),
])

sounds = json.loads((rp / "sound_definitions.json").read_text())["sound_definitions"]
for event in ("matcha.golden", "matcha.labyrinthine", "matcha.dry_hands", "matcha.false_subwoofer_lullaby", "record.11", "record.cat"):
    checks.append((f"sound event {event}", event in sounds))
for item, duration, event in (("music_disc_golden", 188, "record.11"), ("music_disc_labyrinthine", 324, "record.cat")):
    components = json.loads((ROOT / f"behavior_pack/items/generated_components/{item}.json").read_text())["minecraft:item"]["components"]
    record = components.get("minecraft:record", {})
    checks.append((f"native record component {item}", record.get("duration") == duration and record.get("sound_event") == event))

clients = [json.loads(p.read_text())["minecraft:client_biome"]["components"] for p in (rp / "client_biomes").glob("*.json")]
checks.extend([
    ("40 active biome music mappings", sum("minecraft:biome_music" in c for c in clients) == 40),
    ("biome ambience data loaded", 'BIOME_AMBIENCE' in (ROOT / "behavior_pack/scripts/worldgen.js").read_text()),
])
ambience = (ROOT / "behavior_pack/scripts/biome_ambience_data.js").read_text()
checks.extend([
    ("16 biome particle routes", ambience.count('"particle":') == 16),
    ("five biome ambient routes", ambience.count('"loop":') == 5),
])

asset_report = json.loads((ROOT / "docs/presentation-assets-report.json").read_text())
checks.extend([
    ("699 Java models classified", asset_report["java_models"]["total"] == 699),
    ("30 Java blockstates classified", asset_report["java_blockstates"]["total"] == 30),
    ("three jukebox definitions classified", len(asset_report["jukebox_songs"]) == 3),
])
failed = [name for name, passed in checks if not passed]
report = {"checks": len(checks), "passed": len(checks) - len(failed), "failed": failed}
(ROOT / "docs/presentation-assets-check-report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report))
raise SystemExit(bool(failed))
