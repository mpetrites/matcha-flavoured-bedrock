# World-generation and biome presentation evaluation

The pinned Matcha 1.03 source contains 75 `worldgen` definitions: 65 complete
vanilla-biome replacements, four village template pools, five village
structures, and one structure set. It also replaces the Overworld and Nether
dimension types.

## Ported

- All 65 biome presentation records are native Bedrock client-biome files.
- The source supplies 55 sky colors, 65 water colors, five grass colors, seven
  foliage colors, four dry-foliage colors, and 42 combined air/water fog
  definitions. Values are copied without palette approximation.
- The 16 village templates, pool weights, eight-biome routing, and 80/50-chunk
  placement rule remain handled by the structure system.
- The Nether `water_evaporates: false` rule is approximated by controlled water
  bucket placement, including empty-bucket conversion in Survival mode.
- Sixteen biome particle attributes are routed through stable Bedrock particle
  identifiers. Five Nether ambient sets and 40 active biome music definitions
  are mapped to Bedrock sound events; Pale Garden retains its empty/default
  entry and the Deep Dark volume multiplier is retained.

## Retained from Bedrock

- Vanilla Bedrock terrain, carvers, placed features, and weighted biome spawn
  tables remain authoritative. Java configured-feature registries cannot safely
  replace vanilla Bedrock generation, and replacing all 65 server biomes would
  destabilize normal seed compatibility.
- Native Overworld/Nether height, coordinate scale, skylight, ceiling, portal,
  bed, and respawn-anchor behavior already matches the corresponding source
  dimension fields closely enough to retain.

## Engine-limited gameplay differences

- Java dimension cloud height/color, ambient light, sky lighting, logical
  height, and timeline definitions have no equivalent stable dimension-type
  override for vanilla Bedrock dimensions.
- The Java biome gameplay attributes for fire burnout, snow-golem melting,
  patrols, and local water evaporation remain governed by Bedrock or by the
  existing global mechanics where applicable.

The machine-readable field inventory and per-biome classification is in
`worldgen-conversion-report.json`; `worldgen-check-report.json` verifies the
generated pack surface.

The broader models, blockstates, trims, environment, paintings, colormaps,
particles, sounds, and jukebox inventory is recorded in
`presentation-assets-report.json`.
