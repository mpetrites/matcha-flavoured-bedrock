# Recipe conversion tool

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
python3 tools/generate_equipment.py tools/equipment_tiers/bronze.json
python3 tools/check_equipment.py tools/equipment_tiers/bronze.json
```

The checker audits durability, attack damage, mining rules, armor protection,
repairs, recipes, and textures and writes
`docs/equipment-check-report.json`. Add future tier JSON files beside Bronze
to reuse the same framework.

The remaining generated component items and the Estus entity loop can be
audited with:

```sh
python3 tools/convert_component_items.py
python3 tools/check_parity_1_4.py
python3 tools/check_estus.py
```

Singleton vanilla carriers are generated and checked separately. Vanilla
bases with multiple Matcha forms are deliberately excluded:

```sh
python3 tools/generate_vanilla_replacements.py /path/to/Matcha_Flavoured
python3 tools/sync_vanilla_recipe_inputs.py
python3 tools/check_vanilla_replacements.py
```
