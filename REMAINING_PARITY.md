# Remaining parity backlog

Baseline: Matcha Flavoured Java 1.04 compared with Bedrock Alpha 0.6.0.

Milestones 1–4 were completed as a playable conversion scope in Alpha 0.6.0.
Embedded enchantments remain owned by milestone 5 and the Bronze-shears trade
remains owned by milestone 7.

This is the working backlog for gameplay parity. Counts describe the Java
source inventory, not an estimate of Bedrock files: one Java definition can
require several Bedrock items, scripts, entities, or recipes.

## Current audit

| Source area | Java inventory | Current Bedrock state | Remaining work |
| --- | ---: | --- | --- |
| Ordinary recipes | 1,061 recipes total | 751 source recipes converted into 944 Bedrock variants | Resolve the 310 component-bearing results |
| Food recipes/effects | 120 consumable/potion recipes | 90 scripted custom consumables; no conflicts | Thrown-potion and cake refinements |
| Equipment | Five generated tiers | 62 pieces; 365/365 static checks pass | Embedded enchantments are milestone 5 |
| Enchantments | 23 custom definitions | Not ported | Bedrock equivalents, application rules, effects, books, and tests |
| Blessings | 23 recipes | Not ported | Blessing conversion and combined-enchantment behavior |
| Villager economy | 237 profession trade entries and 68 trade sets | Not ported | All professions, wandering trader, tier unlocks, pricing, and custom outputs |
| Loot | 291 loot tables | Not ported | Chests, entities, blocks, archaeology, fishing/gameplay, shearing, and special drops |
| World generation | 75 worldgen files | Not ported | 65 biomes plus structures, pools, and placement |
| Advancements | 234 definitions including Endless Repairs | Not ported | Replace gameplay-critical triggers with script/state tracking; optional UI achievements later |
| Resource pack | 1,644 texture-side files plus models, sounds, and item definitions | Food and Bronze subsets only | Port assets as their owning systems are implemented |

## Recommended implementation order

### 1. Finish the reusable equipment tiers — completed in Alpha 0.6.0

- Generate Steel, Shakudo, Electrum, and Adamant from the tier framework.
- Include each tier's axe, pickaxe, shovel, hoe, spear, mattock, dolabra,
  sword, armor, repair rules, recipes, names, and textures.
- Add exceptional pieces that do not fit the common template:
  - Adamant claymore
  - Bronze elytra
  - Steel shears
  - Silver sword
  - Butcher knife
  - Warding sword and shields
  - Lesser Warding shield
  - Gilded leather boots
  - Amber earrings
- Extend automated checks to cover every tier and exceptional item.
- Add upgrade-path checks so every recipe input exists in the target Bedrock
  version or has a custom substitute.

### 2. Close Bronze behavior gaps — completed within stable Bedrock scope

- Implement the spear's kinetic/lunge behavior rather than treating it only
  as a melee weapon.
- Decide how to approximate Java attack-speed modifiers.
- Decide how to approximate the small held/equipped movement bonuses.
- Add armor attachables so the supplied Bronze armor layers render when worn,
  then add a visual equipment test.
- Port the shepherd trade that supplies Bronze shears.
- Add Bronze elytra behavior, recipe, repair rule, worn model, and texture.
- Add in-game smoke tests for durability loss, repair, mining targets, damage,
  armor protection, and smithing—not only static JSON checks.

### 3. Complete component-bearing crafting outputs — completed in Alpha 0.6.0

The recipe converter intentionally skipped 310 Java recipes because silently
discarding result components would change their behavior. After subtracting
food, blessings, and smithing equipment, the crafting backlog contains 94
component-rich outputs, including:

- Copper, iron, gold, diamond, and wood equipment rebalance
- Copper/iron/diamond hybrid tools and spears
- Chainmail, leather, and sturdy leather armor
- Carbon-rich iron and alloy progression ingredients
- Crystal Heart integration with the generated recipe set
- Amnestic, bedrock buster, tinder, wooden cross, nazar, divine fragment, and
  Warding Stone
- Custom compasses, invisible item frames, campfires, mace, snow shovel, and
  steel minecart conversion
- Custom music discs and Estus progression

Each output needs a custom item definition or a scripted vanilla-item
substitute before its recipe can be enabled.

### 4. Finish food and consumable parity — playable scope completed

- Reconcile all 118 audited food recipes against the 88 generated custom food
  identifiers and five reused hand-authored items.
- Port missing intermediate ingredients such as flour, flour bags, dough,
  uncooked curries, and uncooked ramen.
- Verify every furnace, smoker, and campfire variant returns the intended
  custom output.
- Finish Estus Flask and Stabilised Estus behavior, charges, particles,
  containers, and recipe progression.
- Port cake interaction, mead behavior, milk-bottle behavior, and any
  non-effect actions that cannot be represented by `minecraft:food`.
- Add automated nutrition, use-time, remainder, probability, cleansing, and
  effect-duration comparisons.

### 5. Port enchantments and blessings

- Implement the 23 custom enchantments:
  Anemos, Bloodrage, Cleanse armor slots, Conduit Power, Divinity, Fire Proof,
  Freezing Protection, Haste, Reach, Regeneration, Riposte, Sanguine,
  Slaughter, Traversal, Warding levels/armor, and Zephyr.
- Implement all 23 blessing recipes that merge or transform enchantments.
- Preserve incompatibilities, supported item slots, costs, levels, treasure
  status, and effect triggers.
- Rebuild Java-only effects in Script API where Bedrock enchantment JSON
  cannot express them.
- Add combat, movement, damage-resistance, cleansing, and application tests.

### 6. Port survival mechanics not covered by Alpha 0.5.0

- Freezing water checks and cold protection.
- Nether water behavior.
- Extended day cycle and related load/tick state.
- Mob spawn modification and safe-surface handling.
- Wither summon restrictions and Nether Star handling.
- Warding Stone area effects, restrictions, particles, and sounds.
- Bedrock buster interaction.
- Anvil interaction and Endless Repairs.
- XP removal/restoration mechanics.
- Weather controls, eerie village behavior, boat particles, and special block
  particles.
- First-dragon reward, clay statues, Happy Ghast horn, stacked water bottles,
  and remaining one-off mechanics.

### 7. Rebuild villagers and progression economy

- Port 237 villager trade entries across all professions.
- Port 68 trade-set definitions and profession-level unlock progression.
- Preserve price ranges, quantities, maximum uses, XP, demand behavior, and
  custom components.
- Include the wandering trader and special equipment/food trades.
- Check that every traded custom item exists before enabling a trade tier.

### 8. Port loot, fishing, and treasures

- Convert 291 loot tables by category:
  - 71 chest tables
  - 73 gameplay tables
  - 47 block tables
  - 33 entity tables
  - 19 shearing tables
  - 16 food tables
  - 15 custom-item tables
  - 7 archaeology tables
  - Remaining equipment, harvest, pot, spawner, and advancement tables
- Recreate Java component-bearing loot as Bedrock custom items.
- Port fishing rewards and treasure distribution.
- Add reachability checks ensuring every progression-critical item has at
  least one survival source.

### 9. Port structures and world generation

- Evaluate 65 biome overrides for safe Bedrock equivalents.
- Port five structure definitions, four template pools, and their structure
  set/placement data.
- Port required structure templates and processor behavior.
- Reconcile dimension-type changes with what Bedrock permits.
- Treat unsupported global biome/dimension changes as documented
  approximations rather than silently omitting them.

### 10. Finish presentation and release parity

- Port item/block models, blockstates, trim assets, particles, GUIs,
  environment textures, paintings, and colormaps required by completed
  systems.
- Port the two custom sounds and three jukebox-song definitions plus the
  labyrinthine music disc.
- Complete all localization keys, including item lore and effect text.
- Add pack-wide identifier, texture-reference, recipe-result, loot-result,
  trade-result, and localization checks.
- Add an in-game regression world/function suite for console-bound builds.
- Perform final survival playthroughs covering acquisition from a new world,
  progression through Adamant, death/health rules, villagers, structures,
  loot, and the End.

## Known parity limits requiring an explicit decision

- Java item components attached to vanilla items versus Bedrock namespaced
  custom items.
- Exact attack-speed and very small movement-speed attribute modifiers.
- Multiple simultaneous instances of the same status effect.
- Exact odd-heart maximum-health display.
- Java advancement UI and datapack predicates.
- Global vanilla recipe, biome, dimension, and loot replacement where
  Bedrock only exposes partial override hooks.
- Java structure/worldgen features with no direct stable Bedrock schema.

These should be recorded as **faithful**, **approximated**, or **unsupported**
per feature before the port is declared complete.
