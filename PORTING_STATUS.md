# Porting status

Source baseline: Matcha Flavoured Java 1.04, published 2026-07-30.

## Implemented

| Area | Bedrock coverage |
| --- | --- |
| Food | 88 custom foods generated from 118 upstream recipes |
| Food effects | Apply, remove, and clear actions; probabilities and layered effects |
| Survival | Managed hunger, no natural regeneration, keep inventory, manual sleep |
| Health progression | Crystal Hearts, 20–60 health tracking, one-heart death penalty |
| Progression | Bronze tools, hybrid tools, spear, shears, armor, and repairs |
| Recipes | 751 ordinary recipes plus 118 food recipes translated |
| Packaging | Linked behavior/resource packs in one `.mcaddon` |

## Bedrock approximations

- Java can attach arbitrary components to vanilla item stacks. Bedrock uses
  namespaced custom items instead.
- Java's two simultaneous regeneration instances on baked apples are
  represented with a scripted hidden-effect timeline because Bedrock keeps one
  instance of an effect type. This generalizes to every layered food effect.
- Java's `show_icon` flag has no equivalent in `Entity.addEffect`; particle
  visibility is retained, but HUD-icon visibility follows Bedrock behavior.
- Future Java effects that do not exist in the player's Bedrock engine are
  ignored safely instead of stopping the food script.
- Recipes that modify ordinary Java foods now output namespaced Bedrock
  versions. Bedrock add-ons cannot globally replace every naturally acquired
  vanilla food stack with custom item components.
- Bedrock Health Boost changes maximum health in four-point steps, while
  Matcha progresses in two-point steps. The script applies the smallest
  containing Health Boost tier and caps usable health to the exact tracked
  value. The HUD may briefly show one unavailable extra heart at odd tiers.
- The Java bronze sword is a component-rich vanilla-item override. The
  Bedrock alpha uses a custom sword with equivalent broad progression stats.
- Java attack-speed and tiny held/equipped movement-speed modifiers do not
  have faithful stable Bedrock item-component equivalents, so Bronze preserves
  damage, durability, mining speed, armor protection, repairs, and recipes
  without those modifiers.
- Bronze shears remain trade-only, as in the Java source. Their 3,000
  durability and iron repair ingredients are preserved.

## Not yet ported

The upstream pack is large (over 2,000 data files and 1,061 actual recipe
definitions). The food subset of the component-bearing recipes is now ported.
The remaining component recipes primarily produce equipment, enchantments,
blessings, and utility items. Major
unported systems include the remaining foods and intrinsic effects,
later alloy equipment sets, enchantment and blessing systems, villagers, loot and
treasures, fishing, structures, advancements, world generation, and most
vanilla recipe/equipment rebalancing.

## Next suggested milestone

Generate Steel, Shakudo, Electrum, and Adamant definitions from the reusable
equipment tier generator, then extend the framework for any tier-specific
abilities.
