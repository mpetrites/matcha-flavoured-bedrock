# Porting status

Source baseline: Matcha Flavoured Java 1.04, published 2026-07-30.

## Implemented

| Area | Bedrock coverage |
| --- | --- |
| Food | 90 custom consumables generated from 120 upstream recipes |
| Food effects | Apply, remove, and clear actions; probabilities and layered effects |
| Survival | Managed hunger, no natural regeneration, keep inventory, manual sleep |
| Health progression | Crystal Hearts, 20–60 health tracking, one-heart death penalty |
| Progression | Five alloy tiers, equipment exceptions, ingredients, and utilities |
| Equipment | 62 generated items; 365/365 static checks; 20 armor attachables |
| Component outputs | 105 custom items and 112 recipe variants |
| Estus | Entity death drops, pickup conversion, buffs, Ash, Stabilised Estus, and Flasks |
| Recipes | 751 ordinary recipes plus component and consumable recipes |
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
- Java attack speed is approximated with Bedrock 1.21.130 attack cooldowns.
  Tiny movement-speed modifiers have no suitably precise stable equivalent.
- Bronze shears remain trade-only, as in the Java source. Their 3,000
  durability and iron repair ingredients are preserved; the trade belongs to
  the villager milestone.
- Java splash-potion foods are currently drinkable custom consumables.
- Embedded source enchantments are recorded for the enchantment milestone.
- Looting does not yet increase Raw Estus quantity; the base Java drop odds
  are preserved by the entity-death script.

## Not yet ported

The upstream pack is large (over 2,000 data files and 1,061 actual recipe
definitions). Food, equipment, and ordinary component-item outputs are now
ported. The remaining component recipes are the 23 blessings. Major unported
systems include enchantments and blessings, villagers, loot and treasures,
fishing, structures, advancements, world generation, and global mechanics.

## Next suggested milestone

Port the 23 custom enchantments and 23 blessing recipes.

See [REMAINING_PARITY.md](REMAINING_PARITY.md) for the quantified, ordered
parity backlog.
