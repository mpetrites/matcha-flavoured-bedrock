#!/usr/bin/env python3
"""Port directly usable Matcha presentation assets and catalogue Java-only ones."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import struct
import zlib
from pathlib import Path

from upstream import add_source_argument, baseline, validate_source


ROOT = Path(__file__).resolve().parents[1]


def reset(path: Path, pattern: str = "*") -> None:
    path.mkdir(parents=True, exist_ok=True)
    for old in path.glob(pattern):
        if old.is_dir():
            shutil.rmtree(old)
        else:
            old.unlink()


def copy_tree(source: Path, destination: Path) -> int:
    if not source.exists():
        return 0
    count = 0
    for path in source.rglob("*"):
        if not path.is_file():
            continue
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        count += 1
    return count


def safe(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")


def read_png(path: Path) -> tuple[int, int, list[bytearray]]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    offset, width, height, color_type, packed = 8, 0, 0, 0, bytearray()
    while offset < len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", payload)
            if depth != 8 or interlace != 0 or color_type not in (2, 6):
                raise ValueError(f"unsupported PNG layout: {path}")
        elif kind == b"IDAT":
            packed.extend(payload)
        elif kind == b"IEND":
            break
    channels = 3 if color_type == 2 else 4
    raw = zlib.decompress(bytes(packed)); stride = width * channels
    rows, previous, cursor = [], bytearray(stride), 0
    for _ in range(height):
        mode = raw[cursor]; cursor += 1
        encoded = raw[cursor:cursor + stride]; cursor += stride
        row = bytearray(stride)
        for index, value in enumerate(encoded):
            left = row[index - channels] if index >= channels else 0
            up = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if mode == 0: predictor = 0
            elif mode == 1: predictor = left
            elif mode == 2: predictor = up
            elif mode == 3: predictor = (left + up) // 2
            elif mode == 4:
                estimate = left + up - upper_left
                distances = (abs(estimate - left), abs(estimate - up), abs(estimate - upper_left))
                predictor = (left, up, upper_left)[distances.index(min(distances))]
            else: raise ValueError(f"unsupported PNG filter {mode}: {path}")
            row[index] = (value + predictor) & 255
        rgba = bytearray()
        for index in range(0, stride, channels):
            rgba.extend(row[index:index + 3]); rgba.append(row[index + 3] if channels == 4 else 255)
        rows.append(rgba); previous = row
    return width, height, rows


def write_png(path: Path, width: int, height: int, rows: list[bytearray]) -> None:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    raw = b"".join(b"\0" + bytes(row) for row in rows)
    payload = b"\x89PNG\r\n\x1a\n"
    payload += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    payload += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    path.write_bytes(payload)


def merge_match_painting(atlas: Path, match: Path, output: Path) -> bool:
    if not atlas.exists():
        return False
    width, height, rows = read_png(atlas)
    match_width, match_height, match_rows = read_png(match)
    if width < 32 or height < 160 or (match_width, match_height) != (32, 32):
        raise ValueError("unexpected Match painting atlas dimensions")
    for y in range(32):
        rows[128 + y][0:32 * 4] = match_rows[y]
    write_png(output, width, height, rows)
    return True


def build_moon_atlas(source: Path, output: Path) -> None:
    phases = [
        "full_moon", "waning_gibbous", "third_quarter", "waning_crescent",
        "new_moon", "waxing_crescent", "first_quarter", "waxing_gibbous",
    ]
    canvas = [bytearray(128 * 4) for _ in range(64)]
    for index, phase in enumerate(phases):
        width, height, rows = read_png(source / f"{phase}.png")
        if (width, height) != (32, 32):
            raise ValueError(f"unexpected moon phase dimensions: {phase}")
        x, y = (index % 4) * 32, (index // 4) * 32
        for row in range(32):
            canvas[y + row][x * 4:(x + 32) * 4] = rows[row]
    write_png(output, 128, 64, canvas)


def main() -> None:
    parser = argparse.ArgumentParser()
    add_source_argument(parser)
    parser.add_argument("--painting-atlas", type=Path, default=Path("/private/tmp/bedrock_kz.png"))
    args = parser.parse_args()
    source = validate_source(args.source)
    assets = source / "assets/minecraft"
    rp = ROOT / "resource_pack"

    counts = {}
    block_target = rp / "textures/blocks"
    reset(block_target)
    counts["block_textures"] = copy_tree(assets / "textures/block", block_target)

    trim_target = rp / "textures/trims"
    reset(trim_target)
    counts["trim_textures"] = copy_tree(assets / "textures/trims", trim_target)

    colormap_target = rp / "textures/colormap"
    reset(colormap_target)
    for path in (assets / "textures/colormap").glob("*.png"):
        name = path.name.lower().replace(" ", "_").replace("-_copy", "_copy")
        shutil.copy2(path, colormap_target / name)
    counts["colormaps"] = len(list(colormap_target.glob("*.png")))

    environment_target = rp / "textures/environment"
    reset(environment_target)
    counts["environment_files"] = copy_tree(assets / "textures/environment", environment_target)
    celestial = assets / "textures/environment/celestial"
    shutil.copy2(celestial / "sun.png", environment_target / "sun.png")
    shutil.copy2(assets / "textures/environment/rain.png", environment_target / "weather.png")
    build_moon_atlas(celestial / "moon", environment_target / "moon_phases.png")
    counts["bedrock_environment_mappings"] = 3

    painting_target = rp / "textures/painting"
    reset(painting_target)
    counts["painting_textures"] = copy_tree(assets / "textures/painting", painting_target)
    counts["painting_atlas_merged"] = int(merge_match_painting(
        args.painting_atlas, assets / "textures/painting/match.png", painting_target / "kz.png"
    ))

    particle_texture_target = rp / "textures/particle/matcha"
    reset(particle_texture_target)
    counts["particle_textures"] = copy_tree(assets / "textures/particle", particle_texture_target)
    particle_target = rp / "particles/generated_matcha"
    reset(particle_target)
    for texture in sorted(particle_texture_target.glob("*.png")):
        name = texture.stem
        texture_width, texture_height, _ = read_png(texture)
        definition = {
            "format_version": "1.10.0",
            "particle_effect": {
                "description": {
                    "identifier": f"matcha:{name}",
                    "basic_render_parameters": {
                        "material": "particles_alpha",
                        "texture": f"textures/particle/matcha/{name}",
                    },
                },
                "components": {
                    "minecraft:emitter_rate_instant": {"num_particles": 1},
                    "minecraft:emitter_lifetime_once": {"active_time": 0.1},
                    "minecraft:particle_lifetime_expression": {"max_lifetime": 0.55},
                    "minecraft:particle_motion_dynamic": {
                        "linear_acceleration": [0, -2.5, 0],
                        "linear_drag_coefficient": 1.5,
                    },
                    "minecraft:particle_appearance_billboard": {
                        "size": [0.18, 0.18],
                        "facing_camera_mode": "rotate_xyz",
                        "uv": {"texture_width": texture_width, "texture_height": texture_height, "uv": [0, 0], "uv_size": [texture_width, texture_height]},
                    },
                },
            },
        }
        (particle_target / f"{name}.json").write_text(json.dumps(definition, indent=2) + "\n")
    counts["particle_definitions"] = len(list(particle_target.glob("*.json")))

    sounds_target = rp / "sounds/matcha/custom"
    reset(sounds_target)
    counts["custom_sounds"] = copy_tree(source / "assets/matcha/sounds/custom", sounds_target)
    bell_target = rp / "sounds/block/bell"
    reset(bell_target)
    counts["bell_sounds"] = copy_tree(assets / "sounds/block/bell", bell_target)
    sound_definitions = {
        "format_version": "1.20.20",
        "sound_definitions": {
            "matcha.golden": {"category": "record", "sounds": [{"name": "sounds/matcha/custom/golden_demo", "stream": True}]},
            "record.11": {"category": "record", "sounds": [{"name": "sounds/matcha/custom/golden_demo", "stream": True}]},
            "matcha.false_subwoofer_lullaby": {"category": "music", "sounds": [{"name": "sounds/matcha/custom/false_subwoofer_lullaby", "stream": True}]},
            "matcha.labyrinthine": {"category": "record", "sounds": [{"name": "sounds/music/game/swamp/labyrinthine", "stream": True}]},
            "record.cat": {"category": "record", "sounds": [{"name": "sounds/music/game/swamp/labyrinthine", "stream": True}]},
            "matcha.dry_hands": {"category": "record", "sounds": [{"name": "sounds/music/game/dry_hands", "stream": True}]},
        },
    }
    (rp / "sound_definitions.json").write_text(json.dumps(sound_definitions, indent=2) + "\n")

    model_files = sorted((assets / "models").rglob("*.json"))
    blockstates = sorted((assets / "blockstates").glob("*.json"))
    model_parents = {}
    texture_refs = set()
    for path in model_files:
        data = json.loads(path.read_text())
        model_parents[data.get("parent", "<root>")] = model_parents.get(data.get("parent", "<root>"), 0) + 1
        texture_refs.update(v for v in data.get("textures", {}).values() if isinstance(v, str) and not v.startswith("#"))
    jukebox = {}
    for path in sorted((source / "data/main/jukebox_song").glob("*.json")):
        jukebox[f"main:{path.stem}"] = json.loads(path.read_text())

    report = {
        "baseline": baseline(),
        "copied": counts,
        "java_models": {
            "total": len(model_files),
            "item": sum("/item/" in str(p) for p in model_files),
            "block": sum("/block/" in str(p) for p in model_files),
            "parents": dict(sorted(model_parents.items())),
            "texture_references": len(texture_refs),
            "bedrock_handling": "item outputs use generated icons/attachables; block texture layers are copied, while Java parent/override geometry is not a Bedrock model format",
        },
        "java_blockstates": {
            "total": len(blockstates),
            "files": [p.name for p in blockstates],
            "bedrock_handling": "all referenced block texture assets are installed; Java variants/multipart JSON cannot override vanilla Bedrock block permutations",
        },
        "jukebox_songs": jukebox,
        "painting_handling": "match.png and back.png are installed; Match is an atlas entry on legacy Bedrock clients and requires in-game target-version verification",
        "environment_handling": "source rain, sun, and individual lunar phases are installed; Bedrock clients that require moon_phases.png retain their engine atlas",
    }
    report_path = ROOT / "docs/presentation-assets-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
