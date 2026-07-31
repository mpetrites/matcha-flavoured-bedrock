# Porting status

Source baseline: Matcha Flavoured Java 1.04, published 2026-07-30.

## Implemented

| Area | Bedrock coverage |
| --- | --- |
| Food | Baked apple, fried egg, charred meat, charred fish, charred potato |
| Food effects | Scripted regeneration; baked apple's layered effect is sequenced |
| Survival | Hunger is kept full so health foods remain usable |
| Progression | Bronze alloy and bronze sword |
| Packaging | Linked behavior/resource packs in one `.mcaddon` |

## Bedrock approximations

- Java can attach arbitrary components to vanilla item stacks. Bedrock uses
  namespaced custom items instead.
- Java's two simultaneous regeneration instances on baked apples are
  represented as two sequential phases because Bedrock keeps one instance of
  an effect type.
- The full Java hunger and natural-regeneration overhaul is currently
  approximated by periodically applying saturation.
- The Java bronze sword is a component-rich vanilla-item override. The
  Bedrock alpha uses a custom sword with equivalent broad progression stats.

## Not yet ported

The upstream pack is large (over 2,000 data files and over 1,000 recipes).
Major unported systems include the remaining foods and intrinsic effects,
alloy equipment sets, enchantment and blessing systems, villagers, loot and
treasures, fishing, structures, advancements, world generation, and most
vanilla recipe/equipment rebalancing.

## Next suggested milestone

Port the remaining simple food recipes and textures as custom items, then add
automated schema checks for every item and recipe before moving into
equipment and progression systems.
