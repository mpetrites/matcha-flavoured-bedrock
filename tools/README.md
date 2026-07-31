# Recipe conversion tool

All source-aware tools use the official Java 1.03 baseline pinned in
`upstream_baseline.json`. Verify the downloaded archive and unpack it, then
pass that same root explicitly to every generator or audit:

```sh
python3 tools/upstream.py /path/to/Matcha_Flavoured_1_03.zip
python3 tools/check_upstream.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_parity_1_4.py --source /path/to/unpacked/Matcha_Flavoured_1_03
```

Source-aware tools deliberately have no fallback path. A missing source or
an inventory mismatch is an error, preventing empty `0/0` parity passes.

`convert_recipes.py` translates component-free Java recipes into Bedrock
recipe definitions.

```sh
python3 tools/convert_recipes.py \
  /path/to/Matcha_Flavoured/data \
  behavior_pack/recipes/generated \
  docs/recipe-conversion-report.json
```

Alternative ingredient arrays are expanded into separate Bedrock recipe
variants. Recipes whose outputs contain Java item components are deliberately
reported and skipped because dropping those components would silently produce
the wrong item.

`convert_foods.py` handles the food subset of those component-bearing results:

```sh
python3 tools/convert_foods.py \
  /path/to/unpacked/Matcha_Flavoured \
  behavior_pack \
  resource_pack \
  docs/food-conversion-report.json
```

It generates custom items, recipe variants, texture-atlas entries, names, and
the Script API effect table used by `scripts/main.js`.

`generate_equipment.py` builds a complete equipment tier from a declarative
file. Bronze is the reference tier:

```sh
python3 tools/generate_equipment.py --source /path/to/unpacked/Matcha_Flavoured_1_03 tools/equipment_tiers/bronze.json
python3 tools/check_equipment.py tools/equipment_tiers/bronze.json
```

The checker audits durability, attack damage, mining rules, armor protection,
repairs, recipes, and textures and writes
`docs/equipment-check-report.json`. Add future tier JSON files beside Bronze
to reuse the same framework.

The remaining generated component items and the Estus entity loop can be
audited with:

```sh
python3 tools/convert_component_items.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_parity_1_4.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_estus.py
```

Enchantments and blessing proxies are generated and audited with:

```sh
python3 tools/generate_enchantments.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_enchantments.py --source /path/to/unpacked/Matcha_Flavoured_1_03
```

Because Bedrock has no custom-enchantment registry equivalent, a blessing is
used from the main hand while its target is held in the off hand. Supported
vanilla enchantments are written to that item; custom Matcha effects are
persisted and executed by the Script API.

The remaining core survival systems are audited with:

```sh
python3 tools/check_survival_milestone.py --source /path/to/unpacked/Matcha_Flavoured_1_03
```

The complete villager economy is generated and audited with:

```sh
python3 tools/generate_villager_trades.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_villager_trades.py --source /path/to/unpacked/Matcha_Flavoured_1_03
```

Loot and beta-village structures are converted and audited with:

```sh
python3 tools/convert_loot.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 -m pip install --target /tmp/matcha_pydeps nbtlib
PYTHONPATH=/tmp/matcha_pydeps python3 tools/convert_structures.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_loot_structures.py --source /path/to/unpacked/Matcha_Flavoured_1_03
```

Singleton vanilla carriers are generated and checked separately. Vanilla
bases with multiple Matcha forms are deliberately excluded:

```sh
python3 tools/generate_vanilla_replacements.py /path/to/Matcha_Flavoured
python3 tools/sync_vanilla_recipe_inputs.py
python3 tools/check_vanilla_replacements.py
```
