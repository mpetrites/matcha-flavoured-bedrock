# Matcha Flavoured — Bedrock Edition port

An independent, work-in-progress Bedrock Edition port of Klei Wright's
[Matcha Flavoured](https://modrinth.com/datapack/matcha-flavoured) Java
datapack.

The current alpha is a playable vertical slice, not a complete port. It
implements the health-food system, five equipment tiers, component-bearing
items, and the core no-hunger approximation.

## Install

Download the `.mcaddon` from `dist/` and open it with Minecraft. Activate both
the behavior pack and resource pack on a world. This alpha targets Bedrock
1.21.130 or newer.

With cheats enabled, use `/function matcha_equipment_test`,
`/function matcha_component_items_test`, `/function matcha_consumables_test`,
`/function matcha_enchantment_test`, `/function matcha_survival_test`,
`/function matcha_villager_test`, or `/function matcha_structure_test`.

## Included in alpha 0.11.0

- Health foods: baked apple, fried egg, charred meat, charred fish, and
  charred potato
- Original textures for those foods
- Bronze, Steel, Shakudo, Electrum, and Adamant equipment: 62 generated items
  with recipes, repairs, worn armor, attack cooldowns, and kinetic spears
- 104 component-bearing custom items and 109 recipe variants
- Scripted regeneration effects matching the Java recipes
- Managed-hunger approximation using Bedrock's saturation effect
- 945 generated Bedrock recipe definitions translated from 752
  component-free recipes in the pinned 1.03 upstream release
- 90 scripted custom consumables from 120 upstream recipes, including effect
  probabilities, cleansing actions, layered effects, use times, and container
  remainders; Estus potion effects are included
- Entity-driven Estus progression: source-faithful Raw Estus drops from
  player-killed Blazes, Zombies, Husks, Drowned, and Zombie Villagers; pickup
  healing; Estus Ash conversion; Benzene stabilization; and Flask recipes
- Matcha survival rules: managed hunger, disabled natural regeneration,
  keep-inventory deaths, manual sleep time, Crystal Hearts, and persistent
  maximum-health progression
- All 23 source custom enchantments routed through Bedrock equivalents, plus
  23 blessing items and 24 recipe variants
- Frozen-biome water hazards and Freezing Protection
- Placeable Warding Stones with undead suppression, friendly regeneration,
  recovery when broken, and Trial Chamber rejection
- Bedrock Buster delayed demolition, the anvil XP window, global XP removal,
  and the first-dragon Nether Star reward
- All 235 official villager and Wandering Trader entries assembled through
  all 68 trade sets, including stable per-villager offers, five profession
  tiers, stock limits, daily restocks, and 119 component-specific trade items
- All 282 official loot tables converted, with nested-table resolution and
  98 additional component-specific loot items
- All 16 eerie beta-village templates converted to native `.mcstructure`
  assets and assembled in the eight official village biomes using the source
  spacing, separation, salt, pools, and placement inventory

See [REMAINING_PARITY.md](REMAINING_PARITY.md) for the audited discrepancy
ledger. Machine-readable conversion and parity reports are under `docs/`.

## Build

Run:

```sh
python3 tools/generate_equipment.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_equipment.py
python3 tools/convert_component_items.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_parity_1_4.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_estus.py
python3 tools/generate_enchantments.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_enchantments.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_survival_milestone.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/generate_villager_trades.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_villager_trades.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/convert_loot.py --source /path/to/unpacked/Matcha_Flavoured_1_03
PYTHONPATH=/tmp/matcha_pydeps python3 tools/convert_structures.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_loot_structures.py --source /path/to/unpacked/Matcha_Flavoured_1_03
./scripts/package.sh
```

The packaged add-on is written to `dist/`.

## Attribution and license

Matcha Flavoured was created by Klei Wright and is distributed under
CC BY-NC-SA 4.0. This port reuses and adapts assets from the original under
the same license. It is unofficial and is not endorsed by the original
creator.

See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
