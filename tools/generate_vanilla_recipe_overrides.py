#!/usr/bin/env python3
"""Shadow vanilla recipes whose outputs are replaced by Matcha items."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "behavior_pack/recipes"
OUTPUT = RECIPES / "generated_vanilla_overrides"
CONFIG = json.loads(
    (ROOT / "tools/vanilla_replacements.json").read_text(encoding="utf-8")
)
# Singleton replacements also need recipe shadows. Recipe-only overrides cover
# ambiguous proxy items whose vanilla forms must remain valid smithing inputs.
REPLACEMENTS = CONFIG["replacements"] | CONFIG.get("recipe_overrides", {})
SOURCE_OVERRIDES = CONFIG.get("recipe_override_sources", {})


def recipe_body(data: dict) -> dict | None:
    for key, value in data.items():
        if key.startswith("minecraft:recipe_") and isinstance(value, dict):
            return value
    return None


def result_id(body: dict) -> str | None:
    result = body.get("result", body.get("output"))
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        return result.get("item")
    return None


def main() -> None:
    candidates: dict[str, list[Path]] = {}
    for path in sorted(RECIPES.rglob("*.json")):
        if OUTPUT in path.parents:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        body = recipe_body(data)
        if body is not None:
            candidates.setdefault(result_id(body), []).append(path)

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)

    generated = []
    missing = []
    for vanilla_id, matcha_id in sorted(REPLACEMENTS.items()):
        choices = candidates.get(matcha_id, [])
        if not choices:
            missing.append(vanilla_id)
            continue

        # A deterministic representative shadows the built-in recipe. Other
        # ways to craft the same Matcha item remain available under matcha IDs.
        source = choices[0]
        data = json.loads(source.read_text(encoding="utf-8"))
        body = recipe_body(data)
        body["description"]["identifier"] = vanilla_id
        output = OUTPUT / f"{vanilla_id.split(':', 1)[1]}.json"
        output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        generated.append(
            {"vanilla_identifier": vanilla_id, "matcha_recipe": str(source.relative_to(ROOT))}
        )

    for vanilla_id, relative_source in sorted(SOURCE_OVERRIDES.items()):
        source = RECIPES / relative_source
        if not source.is_file():
            missing.append(vanilla_id)
            continue
        data = json.loads(source.read_text(encoding="utf-8"))
        body = recipe_body(data)
        body["description"]["identifier"] = vanilla_id
        output = OUTPUT / f"{vanilla_id.split(':', 1)[1]}.json"
        output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        generated.append(
            {"vanilla_identifier": vanilla_id, "matcha_recipe": str(source.relative_to(ROOT))}
        )

    report = {
        "generated_count": len(generated),
        "generated": generated,
        "replacement_items_without_recipe": missing,
    }
    (ROOT / "docs/vanilla-recipe-override-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"generated": len(generated), "without_recipe": len(missing)}))


if __name__ == "__main__":
    main()
