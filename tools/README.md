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
