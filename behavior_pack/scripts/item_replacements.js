import { EquipmentSlot, GameMode, ItemStack, system, world } from "@minecraft/server";
import { VANILLA_REPLACEMENTS } from "./vanilla_replacements.js";

// Bedrock cannot unregister vanilla item identifiers.  Instead, Survival
// inventories are canonicalized to the pack's sole custom form.  Creative is
// intentionally untouched for administration, mapmaking, and test fixtures.
function convertedStack(stack) {
  const replacement=stack && VANILLA_REPLACEMENTS[stack.typeId];
  if (!replacement) return undefined;
  const converted=new ItemStack(replacement,stack.amount);
  try { converted.nameTag=stack.nameTag; } catch {}
  try { converted.setLore(stack.getLore()); } catch {}
  try {
    const oldDurability=stack.getComponent("minecraft:durability");
    const newDurability=converted.getComponent("minecraft:durability");
    if (oldDurability && newDurability) {
      newDurability.damage=Math.min(oldDurability.damage,newDurability.maxDurability);
    }
  } catch {}
  try {
    const enchantments=stack.getComponent("minecraft:enchantable")?.getEnchantments();
    if (enchantments?.length) converted.getComponent("minecraft:enchantable")?.addEnchantments(enchantments);
  } catch {}
  return converted;
}

system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    if (player.getGameMode() === GameMode.Creative || player.getGameMode() === GameMode.Spectator) continue;
    const container=player.getComponent("minecraft:inventory")?.container;
    if (!container) continue;
    for (let slot=0;slot<container.size;slot++) {
      const replacement=convertedStack(container.getItem(slot));
      if (replacement) try { container.setItem(slot,replacement); } catch {}
    }
    const equippable=player.getComponent("minecraft:equippable");
    if (!equippable) continue;
    for (const slot of [EquipmentSlot.Head,EquipmentSlot.Chest,EquipmentSlot.Legs,EquipmentSlot.Feet,EquipmentSlot.Offhand]) {
      const replacement=convertedStack(equippable.getEquipment(slot));
      if (replacement) try { equippable.setEquipment(slot,replacement); } catch {}
    }
  }
},5);
