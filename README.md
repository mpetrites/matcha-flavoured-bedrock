# Matcha Flavoured — Bedrock Edition port

An independent, work-in-progress Bedrock Edition port of Klei Wright's
[Matcha Flavoured](https://modrinth.com/datapack/matcha-flavoured) Java
datapack.

The current alpha ports the major progression and survival systems, but it is
not yet parity-complete. Engine-limited behavior and the remaining validation
work are tracked separately from shipped coverage.

## Install

Download the `.mcaddon` from `dist/` and open it with Minecraft. Activate both
the behavior pack and resource pack on a world. This alpha targets Bedrock
1.21.130 or newer.

With cheats enabled, use `/function matcha_equipment_test`,
`/function matcha_component_items_test`, `/function matcha_consumables_test`,
`/function matcha_enchantment_test`, `/function matcha_survival_test`,
`/function matcha_villager_test`, `/function matcha_structure_test`, or
`/function matcha_advancement_test`. Use `/function matcha_global_mechanics_test`
for environment and interaction systems.

## Included in alpha 0.11.5

- Health foods: baked apple, fried egg, charred meat, charred fish, and
  charred potato
- Original textures for those foods
- Bronze, Steel, Shakudo, Electrum, and Adamant equipment: 62 generated items
  with recipes, repairs, worn armor, attack cooldowns, and kinetic spears
- 57 smithing-table upgrades exposed through a sneak-use UI that carries the
  base item's name, lore, durability ratio, enchantments, and dynamic state
- 104 component-bearing custom items and 109 recipe variants
- Scripted regeneration effects matching the Java recipes
- Hunger disabled by keeping it full and hiding its HUD element
- 930 loadable generated Bedrock recipe definitions translated from 752
  component-free recipes in the pinned 1.03 upstream release; 16 colored-banner
  recipes are omitted because their Java results have no valid Bedrock item ID
- 90 scripted custom consumables from 120 upstream recipes, including effect
  probabilities, cleansing actions, layered effects, use times, and container
  remainders; Estus potion effects are included. The poison and weakness
  preserves are aimed area splashes, mead and milk are completion-gated drinks,
  and placed cake supplies a health pulse per bite.
- Entity-driven Estus progression: source-faithful Raw Estus drops from
  player-killed Blazes, Zombies, Husks, Drowned, and Zombie Villagers; pickup
  healing; Estus Ash conversion; Benzene stabilization; and Flask recipes
- Matcha survival rules: disabled and hidden hunger, disabled natural regeneration,
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
  tiers, unlimited uses, and 119 component-specific trade items
- All 282 official loot tables converted, with nested-table resolution,
  native Bedrock loot functions, restricted-enchantment routing, Fortune
  distributions, the nine-slice melon cap, and 98 component-specific items
- All 16 eerie beta-village templates converted to native `.mcstructure`
  assets and assembled in the eight official village biomes using the source
  spacing, separation, salt, pools, and placement inventory
- Persistent behavior for all 223 source advancement definitions and 507
  criteria, with source requirement grouping, silent internal completions, and
  toast/chat feedback for displayed advancements
- Extended day timing, sky/safe-surface spawn restrictions, hostile-mob
  rebalance, clay-statue weather, eerie village ambience, Happy Ghast horns,
  stackable water bottles, asylum applications, and boat/sulfur particles
- Native presentation overrides for all 65 source biomes, including sky,
  water, vegetation, and fog colors, plus persistent Nether water placement
- Source block texture layers, armor trims, four splash particles, sun/rain/moon
  environment art, painting atlas, colormaps, bell audio, both playable custom
  music discs, 40 active biome music routes, and scripted particles/ambience

See [REMAINING_PARITY.md](REMAINING_PARITY.md) for the audited discrepancy
ledger. Machine-readable conversion and parity reports are under `docs/`.
Passing static checks establish source inventory and pack-surface coverage;
they do not replace the in-game validation listed in that ledger.

## Build

Run:

```sh
python3 tools/check_upstream.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_parity_1_03.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/generate_equipment.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_equipment.py
python3 tools/check_smithing.py
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
python3 tools/generate_advancements.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_advancements.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_global_mechanics.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_food_interactions.py
python3 tools/convert_worldgen.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_worldgen.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/convert_presentation_assets.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_presentation_assets.py --source /path/to/unpacked/Matcha_Flavoured_1_03
python3 tools/check_vanilla_replacements.py
./scripts/package.sh
```

The packaged add-on is written to `dist/`.

## Attribution and license

Matcha Flavoured was created by Klei Wright and is distributed under
CC BY-NC-SA 4.0. This port reuses and adapts assets from the original under
the same license. It is unofficial and is not endorsed by the original
creator.

See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
