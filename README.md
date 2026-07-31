# Matcha Flavoured — Bedrock Edition port

An independent, work-in-progress Bedrock Edition port of Klei Wright's
[Matcha Flavoured](https://modrinth.com/datapack/matcha-flavoured) Java
datapack.

The current alpha is a playable vertical slice, not a complete port. It
implements the first health-food recipes, the Bronze equipment tier, and the
core no-hunger approximation.

## Install

Download the `.mcaddon` from `dist/` and open it with Minecraft. Activate both
the behavior pack and resource pack on a world. This alpha targets Bedrock
1.21.100 or newer.

With cheats enabled, run `/function matcha_alpha_test` for the original test
kit or `/function matcha_bronze_equipment_test` for every Bronze item and its
smithing/repair materials.

## Included in alpha 0.5.0

- Health foods: baked apple, fried egg, charred meat, charred fish, and
  charred potato
- Original textures for those foods
- Bronze axe, pickaxe, shovel, hoe, spear, mattock, dolabra, shears, armor,
  repair rules, source textures, and smithing recipes
- Scripted regeneration effects matching the Java recipes
- Managed-hunger approximation using Bedrock's saturation effect
- 944 generated Bedrock recipe definitions translated from 751
  component-free upstream recipes
- 88 scripted custom foods from 118 upstream food recipes, including effect
  probabilities, cleansing actions, layered effects, use times, and container
  remainders
- Matcha survival rules: managed hunger, disabled natural regeneration,
  keep-inventory deaths, manual sleep time, Crystal Hearts, and persistent
  maximum-health progression

See [PORTING_STATUS.md](PORTING_STATUS.md) for exact coverage and known gaps.
The ordered remaining-work ledger is in
[REMAINING_PARITY.md](REMAINING_PARITY.md).
The machine-readable conversion audit is in
[`docs/recipe-conversion-report.json`](docs/recipe-conversion-report.json).
Food-specific coverage is in
[`docs/food-conversion-report.json`](docs/food-conversion-report.json).
Equipment parity checks are in
[`docs/equipment-check-report.json`](docs/equipment-check-report.json).

## Build

Run:

```sh
python3 tools/generate_equipment.py
python3 tools/check_equipment.py
./scripts/package.sh
```

The packaged add-on is written to `dist/`.

## Attribution and license

Matcha Flavoured was created by Klei Wright and is distributed under
CC BY-NC-SA 4.0. This port reuses and adapts assets from the original under
the same license. It is unofficial and is not endorsed by the original
creator.

See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
