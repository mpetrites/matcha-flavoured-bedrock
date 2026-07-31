#!/usr/bin/env python3
"""Resolve and validate the single pinned Matcha Java source baseline."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

BASELINE_PATH = Path(__file__).with_name("upstream_baseline.json")


def baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def add_source_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source", required=True, type=Path,
                        help="unpacked root of the pinned official Matcha Java release")


def validate_source(path: Path) -> Path:
    source = path.expanduser().resolve()
    required = (source / "pack.mcmeta", source / "data/crafting/recipe",
                source / "data/main/enchantment", source / "assets/minecraft/lang/en_us.json")
    missing = [str(item) for item in required if not item.exists()]
    if missing:
        raise SystemExit("invalid upstream source; missing: " + ", ".join(missing))
    expected = baseline()["inventory"]["recipes"]
    actual = len(list((source / "data").glob("*/recipe/*.json")))
    if actual != expected:
        raise SystemExit(f"upstream recipe inventory mismatch: expected {expected}, found {actual} in {source}")
    return source


def verify_archive(path: Path) -> None:
    metadata = baseline(); data = path.read_bytes(); failures = []
    if len(data) != metadata["size"]:
        failures.append(f"size expected {metadata['size']}, found {len(data)}")
    for algorithm in ("sha1", "sha512"):
        actual = hashlib.new(algorithm, data).hexdigest()
        if actual != metadata[algorithm]: failures.append(f"{algorithm} expected {metadata[algorithm]}, found {actual}")
    if failures: raise SystemExit("official archive verification failed: " + "; ".join(failures))
    print(f"verified Matcha {metadata['version']}: {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("archive", type=Path)
    verify_archive(parser.parse_args().archive)
