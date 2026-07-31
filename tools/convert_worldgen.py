#!/usr/bin/env python3
"""Convert Matcha biome presentation and audit dimension/worldgen semantics."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

from upstream import add_source_argument, baseline, validate_source


def color(value: object) -> str | None:
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, int):
        return f"#{value & 0xFFFFFF:06x}"
    return None


def bedrock_sound(value: str) -> str:
    sound = value.removeprefix("minecraft:")
    if sound == "music.game":
        return "music.game"
    if sound == "music.creative":
        return "music.game.creative"
    if sound == "music.under_water":
        return "music.game.water"
    if sound.startswith("music.overworld."):
        return "music.game." + sound.rsplit(".", 1)[-1]
    if sound.startswith("music.nether."):
        return "music.game." + sound.rsplit(".", 1)[-1]
    return sound


def main() -> None:
    parser = argparse.ArgumentParser()
    add_source_argument(parser)
    parser.add_argument("--resource-pack", type=Path, default=Path("resource_pack"))
    parser.add_argument("--report", type=Path, default=Path("docs/worldgen-conversion-report.json"))
    args = parser.parse_args()
    source = validate_source(args.source)
    biome_source = source / "data/minecraft/worldgen/biome"
    output = args.resource_pack / "client_biomes"
    fog_output = args.resource_pack / "fogs/generated_matcha"
    output.mkdir(parents=True, exist_ok=True)
    fog_output.mkdir(parents=True, exist_ok=True)
    for directory in (output, fog_output):
        for old in directory.glob("*.json"):
            old.unlink()

    component_counts: Counter[str] = Counter()
    unsupported_counts: Counter[str] = Counter()
    scripted_counts: Counter[str] = Counter()
    biome_rows = []
    ambience_data = {}
    fogs = 0
    for path in sorted(biome_source.glob("*.json")):
        source_biome = json.loads(path.read_text(encoding="utf-8"))
        attributes = source_biome.get("attributes", {})
        effects = source_biome.get("effects", {})
        ambient_particle = attributes.get("minecraft:visual/ambient_particles")
        if isinstance(ambient_particle, list):
            ambient_particle = ambient_particle[0] if ambient_particle else None
        if isinstance(ambient_particle, dict) and "argument" in ambient_particle:
            ambient_particle = ambient_particle.get("argument", [None])[0]
        ambient_sounds = attributes.get("minecraft:audio/ambient_sounds", {})
        ambience = {}
        if isinstance(ambient_particle, dict):
            particle = ambient_particle.get("particle", {}).get("type")
            if particle:
                ambience["particle"] = particle.removeprefix("minecraft:")
                ambience["particleChance"] = ambient_particle.get("probability", 0)
        if isinstance(ambient_sounds, dict):
            if ambient_sounds.get("loop"):
                ambience["loop"] = str(ambient_sounds["loop"]).removeprefix("minecraft:")
            addition = ambient_sounds.get("additions")
            if isinstance(addition, dict) and addition.get("sound"):
                ambience["addition"] = str(addition["sound"]).removeprefix("minecraft:")
                ambience["additionChance"] = addition.get("tick_chance", 0)
            mood = ambient_sounds.get("mood")
            if isinstance(mood, dict) and mood.get("sound"):
                ambience["mood"] = str(mood["sound"]).removeprefix("minecraft:")
                ambience["moodDelay"] = mood.get("tick_delay", 6000)
        if ambience:
            ambience_data[f"minecraft:{path.stem}"] = ambience
            if "particle" in ambience:
                scripted_counts["minecraft:visual/ambient_particles"] += 1
            if any(key in ambience for key in ("loop", "addition", "mood")):
                scripted_counts["minecraft:audio/ambient_sounds"] += 1
        components: dict[str, dict] = {}

        sky = color(attributes.get("minecraft:visual/sky_color"))
        if sky:
            components["minecraft:sky_color"] = {"sky_color": sky}
        water = color(effects.get("water_color"))
        if water:
            components["minecraft:water_appearance"] = {"surface_color": water}
        grass = color(effects.get("grass_color"))
        if grass:
            components["minecraft:grass_appearance"] = {"color": grass}
        foliage = color(effects.get("foliage_color"))
        if foliage:
            components["minecraft:foliage_appearance"] = {"color": foliage}
        dry_foliage = color(effects.get("dry_foliage_color"))
        if dry_foliage:
            components["minecraft:dry_foliage_color"] = {"color": dry_foliage}

        music = attributes.get("minecraft:audio/background_music", {})
        if isinstance(music, dict) and isinstance(music.get("default"), dict):
            sound = music["default"].get("sound")
            if sound:
                components["minecraft:biome_music"] = {
                    "music_definition": bedrock_sound(sound),
                    "volume_multiplier": attributes.get("minecraft:audio/music_volume", 1.0),
                }

        fog_color = color(attributes.get("minecraft:visual/fog_color"))
        water_fog = color(attributes.get("minecraft:visual/water_fog_color"))
        if fog_color or water_fog:
            identifier = f"matcha:{path.stem}"
            components["minecraft:fog_appearance"] = {"fog_identifier": identifier}
            distance = {}
            if fog_color:
                distance["air"] = {
                    "fog_start": 0.8,
                    "fog_end": 1.0,
                    "fog_color": fog_color,
                    "render_distance_type": "render",
                }
            if water_fog:
                distance["water"] = {
                    "fog_start": 0.0,
                    "fog_end": attributes.get("minecraft:visual/water_fog_end_distance", 60.0),
                    "fog_color": water_fog,
                    "render_distance_type": "fixed",
                }
            fog = {
                "format_version": "1.21.90",
                "minecraft:fog_settings": {
                    "description": {"identifier": identifier},
                    "distance": distance,
                },
            }
            (fog_output / f"{path.stem}.json").write_text(
                json.dumps(fog, indent=2) + "\n", encoding="utf-8"
            )
            fogs += 1

        for key in components:
            component_counts[key] += 1
        for key in attributes:
            if key not in {
                "minecraft:visual/sky_color", "minecraft:visual/fog_color",
                "minecraft:visual/water_fog_color", "minecraft:visual/water_fog_end_distance",
                "minecraft:audio/background_music", "minecraft:audio/music_volume",
                "minecraft:audio/ambient_sounds", "minecraft:visual/ambient_particles",
            }:
                unsupported_counts[key] += 1

        client_biome = {
            "format_version": "1.21.130",
            "minecraft:client_biome": {
                "description": {"identifier": f"minecraft:{path.stem}"},
                "components": components,
            },
        }
        (output / f"{path.stem}.json").write_text(
            json.dumps(client_biome, indent=2) + "\n", encoding="utf-8"
        )
        biome_rows.append({
            "biome": f"minecraft:{path.stem}",
            "ported_components": sorted(components),
            "feature_stages": len(source_biome.get("features", [])),
            "spawn_categories": sum(bool(v) for v in source_biome.get("spawners", {}).values()),
        })

    dimension_rows = []
    for path in sorted((source / "data/minecraft/dimension_type").glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        dimension_rows.append({
            "dimension": f"minecraft:{path.stem}",
            "source": data,
            "classification": {
                "ported": ["the_nether.attributes.minecraft:gameplay/water_evaporates"] if path.stem == "the_nether" else [],
                "native_equivalent": ["height", "min_y", "coordinate_scale", "has_skylight", "has_ceiling"],
                "engine_limited": ["cloud height/color", "dimension ambient/sky lighting", "logical height", "timeline replacement"],
            },
        })

    report = {
        "baseline": baseline(),
        "source_biomes": len(biome_rows),
        "generated_client_biomes": len(biome_rows),
        "generated_fogs": fogs,
        "ported_component_counts": dict(sorted(component_counts.items())),
        "unmapped_attribute_counts": dict(sorted(unsupported_counts.items())),
        "scripted_attribute_counts": dict(sorted(scripted_counts.items())),
        "worldgen_classification": {
            "presentation": "ported through client_biome and fog definitions",
            "village_structures": "ported through native structures and deterministic scripted assembly",
            "features_and_carvers": "retain Bedrock terrain; Java configured-feature registries cannot replace vanilla Bedrock generation safely",
            "spawners": "partly covered by global spawn rules; weighted biome spawn tables have no equivalent vanilla-biome override",
            "ambient_particles": "16 source routes mapped through scripted stable Bedrock particle identifiers",
            "biome_music_and_ambient_audio": "40 active music definitions use client biomes; five ambient sets use scripted Bedrock sound events; Pale Garden retains its empty source entry",
        },
        "dimensions": dimension_rows,
        "biomes": biome_rows,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    ambience_path = args.resource_pack.parent / "behavior_pack/scripts/biome_ambience_data.js"
    ambience_path.write_text(
        "// Generated by tools/convert_worldgen.py. Do not edit by hand.\n"
        f"export const BIOME_AMBIENCE = {json.dumps(ambience_data, indent=2)};\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "source_biomes": len(biome_rows),
        "generated_client_biomes": len(biome_rows),
        "generated_fogs": fogs,
    }))


if __name__ == "__main__":
    main()
