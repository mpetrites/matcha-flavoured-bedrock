# Remaining parity and known discrepancies

Baseline: official Matcha Flavoured Java 1.03 compared with Bedrock Alpha
0.11.8. The source release, hashes, and expected inventory are pinned in
`tools/upstream_baseline.json`; machine-readable audit reports live in `docs/`.

Completed migration milestones are intentionally omitted from this file. The
README describes shipped coverage; this ledger contains only work or behavior
that still differs from the pinned Java source.

## Open gameplay discrepancies

| Priority | Area | Current Bedrock behavior | Remaining parity work |
| --- | --- | --- | --- |
| Medium | Advancements | All 223 definitions and 507 criteria have persistent completion and requirement handling; 67 displayed definitions use toast/chat feedback. | Add exact structure-location adapters; replace result-acquisition approximations if Bedrock adds stable crafting and fishing events. |
| Medium | Global survival mechanics | Health, hunger, death, sleep, freezing water, XP, Warding Stone, Bedrock Buster, anvil, dragon reward, extended days, spawn/safe-surface rules, weather statues, eerie villages, particles, Happy Ghast horns, applications, and stacked water bottles are present. | Refine the documented spawn attributes, village membership, divine-item gravity, and other engine-limited approximations through in-game testing. |
| High | Loot semantics | All 282 tables are converted; native functions, restricted enchantment routing, Fortune I–III distributions, and the melon cap are preserved or explicitly approximated. | Replace the remaining context-sensitive Java conditions listed below and verify progression through an in-game survival playthrough. |
| Medium | Food interactions | 90 custom consumables cover 120 source recipes and scripted effects; both splash preserves are aimed area effects, cake heals per bite, and mead/milk preserve drink completion and bottle semantics. | Validate cake-bite timing and splash targeting in the target Bedrock release; Bedrock does not expose a native custom splash-potion projectile. |
| Medium | World generation | All 65 biome presentation overrides, 40 active music routes (plus Pale Garden's empty/default entry), 16 particle routes, and five ambient-sound sets are wired; sixteen beta-village templates are assembled in eight source biomes; Nether water placement matches the non-evaporation rule. | Validate rendering, audio, terrain fit, and village frequency in game. Java feature, carver, spawn-table, and vanilla dimension-type replacement remain engine-limited. |
| Medium | Villager economy | All 235 trades and 68 sets are routed through custom UI with stable offers, tiers, and unlimited uses. | Validate balance in game; reputation and demand pricing have no direct Script API equivalent. |
| Medium | Enchantments and blessings | All 23 custom effects and 23 blessings have scripted equivalents. | Perform combat/movement balance verification and confirm every off-hand blessing path in game. |
| Low | Presentation | Implemented items plus source block texture layers, trims, particles, environment art, paintings, colormaps, sounds, and playable Golden and Labyrinthine discs are present. Java's 699 model and 30 blockstate files are classified and their usable textures are ported. | Port remaining GUIs and localization; replace Java model/blockstate geometry only where a corresponding custom Bedrock block or entity is introduced. |

## Deliberate Bedrock approximations

- Java components attached to vanilla stacks are represented by `matcha:`
  custom items. Inventories are canonicalized where one unambiguous custom
  form exists; ambiguous vanilla carriers remain distinct.
- Java attack speed uses Bedrock attack cooldowns. Very small movement-speed
  modifiers do not have a suitably precise stable equivalent.
- Matcha smithing is a sneak-use smithing-table UI because Bedrock's native
  smithing transform only accepts its fixed upgrade slots. The scripted path
  preserves the base item's name, lore, durability ratio, enchantments, and
  dynamic properties. Ordinary generated shapeless recipes remain loadable
  fallbacks but create a fresh result item.
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
  quantity. Custom splash foods use a short aimed trajectory and scripted
  distance-scaled area impact because stable Bedrock item components cannot
  attach custom potion contents to a native splash-potion projectile.
- Frozen-biome checks use an explicit biome list because Script API does not
  expose Java biome tags. Warding Stones use an invisible armor-stand marker
  attached to a lodestone.
- Villager offers intentionally have unlimited uses and never require
  restocking. Java reputation and demand metadata remain in the generated
  catalog, but custom UI prices use source base counts. Some Java-only
  trade-stack presentation components are not reproduced.
- Converted loot conservatively disables Java conditions without stable
  equivalents instead of broadening drops. Current totals are 24
  `location_check`, 6 `entity_properties`, 4 `inverted`, and 2
  `damage_source_properties` conditions. No source loot functions are silently
  omitted; every native translation or approximation is itemized by source
  table and strategy in `docs/loot-conversion-report.json`.
- Structure conversion removes Java jigsaw and command blocks. Script API
  assembles the converted well and weighted road/building pools using the
  source 80/50-chunk placement parameters and salt.
- Bedrock 2.0 has no stable recipe-crafted or fishing-hook event. Those
  criteria complete when their result enters inventory; recipe-unlock criteria
  are treated as available because behavior-pack recipes are globally exposed.
  Structure-location criteria remain pending exact adapters; block-underfoot
  and started-riding criteria use stable component checks.
- Sky exposure uses Bedrock's topmost block as a `can_see_sky` approximation.
  Mob base attributes and equipment drop chances are not mutable through the
  stable Script API, so health is capped and movement/damage use long effects;
  equipment drops retain Bedrock behavior. Eerie-village membership uses
  nearby villagers. Divine-favour items retain particles but not Java's
  no-gravity NBT.
- Client-biome files reproduce source sky, water, grass, foliage, dry-foliage,
  and fog colors. Bedrock retains its terrain/carvers/features and weighted
  biome spawn tables; vanilla dimension geometry and lighting cannot be
  replaced safely. See `docs/WORLDGEN_PORT.md` for the field-level evaluation.
- Sixteen colored-banner recipes are omitted because the Java result IDs are
  not valid Bedrock item identifiers. Golden and Labyrinthine use native
  Bedrock record events `11` and `cat`, with those two events overridden by the
  resource pack. Consequently, vanilla Disc 11 and Cat also play the Matcha
  tracks while this resource pack is active.
- The official 1.03 Wither-fight experiment states that it is not implemented;
  this port does not invent replacement behavior.

## Release-completion checks

- Run the in-game function suite for equipment, components, consumables,
  enchantments, survival, villagers, structures, advancements, and global
  mechanics on the target Bedrock release.
- Complete a survival playthrough from a new world through Adamant, including
  death/health rules, villagers, structures, loot, and the End reward.
- Re-run the full static parity suite after each source or target-engine update;
  the current pinned 1.03 audit passes every checker listed in `tools/README.md`.
