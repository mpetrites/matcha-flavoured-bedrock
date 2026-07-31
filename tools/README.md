# Parity and conversion tools

All source-aware tools use the official Java 1.03 baseline pinned in
`upstream_baseline.json`. Verify the downloaded archive and unpack it, then
pass that same root explicitly to every generator or audit:

```sh
python3 tools/upstream.py /path/to/Matcha_Flavoured_1_03.zip
python3 tools/check_upstream.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_parity_1_03.py --source /path/to/unpacked/Matcha_Flavoured_1_03
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
the Script API effect table used by `scripts/main.js`. Splash-potion results
are emitted as throw interactions and routed through the generated
`food_interaction_data.js` table instead of becoming drinkable foods.

Audit the checked-in special carriers and cake/drink behavior with:

```sh
python3 tools/check_food_interactions.py
```

`convert_worldgen.py` converts all source biome presentation fields supported
by Bedrock's client-biome and fog schemas and records the remaining dimension,
feature, spawn, particle, and audio classifications:

```sh
python3 tools/convert_worldgen.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_worldgen.py --source /path/to/unpacked/Matcha_Flavoured_1_03
```

`convert_presentation_assets.py` installs the directly portable block texture
layers, trims, particle definitions, environment and painting mappings,
colormaps, sounds, and record audio. It also inventories Java-only model and
blockstate semantics rather than loading incompatible JSON into Bedrock:

```sh
python3 tools/convert_presentation_assets.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_presentation_assets.py --source /path/to/unpacked/Matcha_Flavoured_1_03
```

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

Generated component items and the Estus entity loop are audited with:

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

Core survival systems are audited with:

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

Loot conversion uses native Bedrock functions for enchanting, explosion
decay, suspicious stew, ominous bottles, maps, and filled containers. Java
Fortune formulas and restricted enchantment option lists are emitted as
generated helper tables. `docs/loot-conversion-report.json` records every
approximated source table and the strategy used.

Advancement definitions are normalized into a persistent Script API registry:

```sh
python3 tools/generate_advancements.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_advancements.py --source /path/to/unpacked/Matcha_Flavoured_1_03
```

Displayed advancements use source toast/chat flags. Hidden definitions complete
silently. Crafting and fishing criteria currently use result acquisition as a
Bedrock approximation; exact fidelity is recorded in the generated report.

Global mechanics are checked with:

```sh
python3 tools/check_global_mechanics.py --source /path/to/unpacked/Matcha_Flavoured_1_03
```

Singleton vanilla carriers are generated and checked separately. Vanilla
bases with multiple Matcha forms are deliberately excluded:

```sh
python3 tools/generate_vanilla_replacements.py /path/to/Matcha_Flavoured
python3 tools/sync_vanilla_recipe_inputs.py
python3 tools/check_vanilla_replacements.py
```
