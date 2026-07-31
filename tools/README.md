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
