# Remaining parity and known discrepancies

Baseline: official Matcha Flavoured Java 1.03 compared with Bedrock Alpha
0.11.0. The source release, hashes, and expected inventory are pinned in
`tools/upstream_baseline.json`; machine-readable audit reports live in `docs/`.

Completed migration milestones are intentionally omitted from this file. The
README describes shipped coverage; this ledger contains only work or behavior
that still differs from the pinned Java source.

## Open gameplay discrepancies

| Priority | Area | Current Bedrock behavior | Remaining parity work |
| --- | --- | --- | --- |
| High | Advancements | The 234 Java advancement definitions and their UI are not ported. | Rebuild gameplay-critical triggers and rewards with Script API state; treat UI-only achievements separately. |
| High | Global survival mechanics | Core health, hunger, death, sleep, freezing water, XP, Warding Stone, Bedrock Buster, anvil, and dragon reward rules are present. | Port the extended day/load state, mob-spawn and safe-surface rules, weather controls, eerie-village behavior, boat and special-block particles, clay statues, Happy Ghast horn, stacked water bottles, and remaining one-off mechanics. |
| High | Loot semantics | All 282 tables are converted and identifiers/references are valid. | Refine or replace the unsupported Java conditions and functions listed below; verify progression through an in-game survival playthrough. |
| Medium | Food interactions | 90 custom consumables cover 120 source recipes and scripted effects. | Replace drinkable splash-potion approximations where possible and refine cake, mead, milk-bottle, and non-effect interactions. |
| Medium | World generation | Sixteen beta-village templates are assembled deterministically in eight source biomes. | Evaluate 65 biome presentation overrides and the remaining dimension/world-generation changes; validate terrain fit and village frequency in game. |
| Medium | Villager economy | All 235 trades and 68 sets are routed through custom UI with stable offers, tiers, and unlimited uses. | Validate balance in game; reputation and demand pricing have no direct Script API equivalent. |
| Medium | Enchantments and blessings | All 23 custom effects and 23 blessings have scripted equivalents. | Perform combat/movement balance verification and confirm every off-hand blessing path in game. |
| Low | Presentation | Assets required by the implemented food, equipment, blessing, loot, and trade items are present. | Port remaining models, blockstates, trims, particles, GUIs, environment textures, paintings, colormaps, two sounds, jukebox definitions, and localization as their systems land. |

## Deliberate Bedrock approximations

- Java components attached to vanilla stacks are represented by `matcha:`
  custom items. Inventories are canonicalized where one unambiguous custom
  form exists; ambiguous vanilla carriers remain distinct.
- Java attack speed uses Bedrock attack cooldowns. Very small movement-speed
  modifiers do not have a suitably precise stable equivalent.
- Multiple instances of the same Java status effect are represented by a
  scripted strongest-first timeline because Bedrock stores one instance per
  effect type. Java's `show_icon` flag is not exposed by `Entity.addEffect`.
- Odd-heart maximum health uses the smallest containing Health Boost tier and
  caps usable health to the tracked value. The HUD can briefly display one
  unavailable extra heart.
- Custom enchantments are routed by item identifier and player state because
  Bedrock has no equivalent custom-enchantment registry. Supported vanilla
  blessing effects are applied to the off-hand item; Matcha-only effects are
  persisted on the player.
- Raw Estus keeps the source base drop odds, but Looting does not increase its
  quantity. Splash-potion foods are currently drinkable custom consumables.
- Frozen-biome checks use an explicit biome list because Script API does not
  expose Java biome tags. Warding Stones use an invisible armor-stand marker
  attached to a lodestone.
- Villager offers intentionally have unlimited uses and never require
  restocking. Java reputation and demand metadata remain in the generated
  catalog, but custom UI prices use source base counts. Exploration-map destinations and some
  Java-only trade-stack presentation components are not reproduced.
- Converted loot conservatively disables Java conditions without stable
  equivalents instead of broadening drops. Current totals are 24
  `location_check`, 6 `entity_properties`, 4 `inverted`, and 2
  `damage_source_properties` conditions. Approximated or omitted functions
  are itemized in `docs/loot-conversion-report.json`.
- Structure conversion removes Java jigsaw and command blocks. Script API
  assembles the converted well and weighted road/building pools using the
  source 80/50-chunk placement parameters and salt.
- The official 1.03 Wither-fight experiment states that it is not implemented;
  this port does not invent replacement behavior.

## Release-completion checks

- Add pack-wide checks for identifiers, texture references, recipe/loot/trade
  results, and localization.
- Run the in-game function suite for equipment, components, consumables,
  enchantments, survival, villagers, and structures on the target Bedrock
  release.
- Complete a survival playthrough from a new world through Adamant, including
  death/health rules, villagers, structures, loot, and the End reward.
- Classify every remaining feature as faithful, approximated, or unsupported
  before declaring the port complete.
