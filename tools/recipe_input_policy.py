"""Intentional vanilla recipe inputs that must survive replacement syncing."""

from __future__ import annotations

# These recipes upgrade a vanilla base into its Matcha replacement. Rewriting
# the base to the result makes the recipe circular.
PRESERVED_INPUTS_BY_RESULT = {
    "matcha:bronze_elytra": frozenset({"minecraft:elytra"}),
    "matcha:warding_shield": frozenset({"minecraft:shield"}),
}


def recipe_result(body: dict) -> str | None:
    result = body.get("result", body.get("output"))
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        item = result.get("item")
        return item if isinstance(item, str) else None
    return None


def preserved_inputs(body: dict) -> frozenset[str]:
    return PRESERVED_INPUTS_BY_RESULT.get(recipe_result(body), frozenset())
