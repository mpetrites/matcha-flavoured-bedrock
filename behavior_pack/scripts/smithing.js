import { EntityComponentTypes, ItemStack, system, world } from "@minecraft/server";
import { ActionFormData } from "@minecraft/server-ui";

const RECIPES = [];

function add(template, base, addition, result) {
  RECIPES.push({ template, base, addition, result });
}

const tierUpgrades = {
  bronze: { base: "copper", template: "minecraft:copper_ingot", addition: "minecraft:phantom_membrane" },
  shakudo: { base: "copper", template: "minecraft:copper_ingot", addition: "minecraft:shulker_shell" },
  steel: { base: "iron", template: "minecraft:iron_ingot", addition: "minecraft:resin_brick" },
  electrum: { base: "diamond", template: "minecraft:diamond", addition: "minecraft:heart_of_the_sea" }
};
const standardPieces = ["axe", "boots", "chestplate", "helmet", "hoe", "leggings", "pickaxe", "shovel", "spear", "sword"];

for (const [tier, spec] of Object.entries(tierUpgrades)) {
  for (const piece of standardPieces) {
    if (tier === "bronze" && piece === "sword") continue;
    const vanillaBase = ["boots", "chestplate", "helmet", "hoe", "leggings", "axe"].includes(piece);
    const base = vanillaBase
      ? `minecraft:${spec.base}_${piece}`
      : `matcha:${spec.base}_${piece}`;
    add(spec.template, base, spec.addition, `matcha:${tier}_${piece}`);
  }
  add("minecraft:netherite_upgrade_smithing_template", `minecraft:${spec.base}_axe`, spec.addition, `matcha:${tier}_dolabra`);
  add("minecraft:netherite_upgrade_smithing_template", `minecraft:${spec.base}_hoe`, spec.addition, `matcha:${tier}_mattock`);
}

add("minecraft:iron_ingot", "minecraft:shears", "minecraft:resin_brick", "matcha:steel_shears");
add("minecraft:copper_ingot", "matcha:copper_sword", "matcha:bronze_alloy", "matcha:bronze_sword");
add("minecraft:copper_ingot", "minecraft:copper_helmet", "minecraft:resin_clump", "matcha:amber_earrings");
add("minecraft:netherite_upgrade_smithing_template", "matcha:iron_sword", "minecraft:resin_brick", "matcha:butcher_knife");
add("minecraft:rabbit_hide", "minecraft:leather_boots", "minecraft:gold_ingot", "matcha:gilded_leather_boots");
add("minecraft:oak_planks", "matcha:warding_shield", "matcha:nazar", "matcha:warding_shield");
add("minecraft:prismarine_crystals", "matcha:iron_sword", "matcha:nazar", "matcha:silver_sword");
add("minecraft:prismarine_crystals", "matcha:warding_shield", "matcha:nazar", "matcha:warding_shield");
add("minecraft:iron_ingot", "matcha:iron_sword", "matcha:nazar", "matcha:warding_sword");
add("minecraft:honeycomb", "matcha:bronze_elytra", "minecraft:phantom_membrane", "matcha:bronze_elytra");

function inventory(player) {
  return player.getComponent(EntityComponentTypes.Inventory)?.container;
}

function itemCount(container, typeId) {
  let count = 0;
  for (let slot = 0; slot < container.size; slot += 1) {
    const stack = container.getItem(slot);
    if (stack?.typeId === typeId) count += stack.amount;
  }
  return count;
}

function requiredCounts(recipe) {
  const counts = new Map();
  for (const typeId of [recipe.template, recipe.base, recipe.addition]) {
    counts.set(typeId, (counts.get(typeId) ?? 0) + 1);
  }
  return counts;
}

function canSmith(container, recipe) {
  return [...requiredCounts(recipe)].every(([typeId, count]) => itemCount(container, typeId) >= count);
}

function removeOne(container, typeId, preferredSlot = -1) {
  const slots = preferredSlot >= 0
    ? [preferredSlot, ...Array.from({ length: container.size }, (_, index) => index).filter(index => index !== preferredSlot)]
    : Array.from({ length: container.size }, (_, index) => index);
  for (const slot of slots) {
    const stack = container.getItem(slot);
    if (stack?.typeId !== typeId) continue;
    if (stack.amount === 1) container.setItem(slot);
    else { stack.amount -= 1; container.setItem(slot, stack); }
    return { stack, slot };
  }
}

function copyItemState(source, target) {
  try { if (source.nameTag) target.nameTag = source.nameTag; } catch {}
  try { target.setLore(source.getLore()); } catch {}
  try {
    const oldDurability = source.getComponent("minecraft:durability");
    const newDurability = target.getComponent("minecraft:durability");
    if (oldDurability && newDurability) {
      const fraction = oldDurability.maxDurability ? oldDurability.damage / oldDurability.maxDurability : 0;
      newDurability.damage = Math.min(newDurability.maxDurability, Math.round(fraction * newDurability.maxDurability));
    }
  } catch {}
  try {
    const oldEnchantable = source.getComponent("minecraft:enchantable");
    const newEnchantable = target.getComponent("minecraft:enchantable");
    if (oldEnchantable && newEnchantable) {
      for (const enchantment of oldEnchantable.getEnchantments()) {
        try { newEnchantable.addEnchantment(enchantment); } catch {}
      }
    }
  } catch {}
  try {
    for (const id of source.getDynamicPropertyIds()) target.setDynamicProperty(id, source.getDynamicProperty(id));
  } catch {}
}

function title(typeId) {
  return typeId.split(":").pop().replaceAll("_", " ").replace(/\b\w/g, letter => letter.toUpperCase());
}

function short(typeId) {
  return title(typeId).replace("Netherite Upgrade Smithing Template", "Upgrade Template");
}

function performSmith(player, recipe) {
  const container = inventory(player);
  if (!container || !canSmith(container, recipe)) {
    player.sendMessage("§cThe required smithing ingredients are no longer in your inventory.");
    return;
  }
  let baseSlot = -1;
  for (let slot = 0; slot < container.size; slot += 1) {
    if (container.getItem(slot)?.typeId === recipe.base) { baseSlot = slot; break; }
  }
  const base = container.getItem(baseSlot);
  if (!base) return;
  removeOne(container, recipe.base, baseSlot);
  removeOne(container, recipe.template);
  removeOne(container, recipe.addition);

  const result = new ItemStack(recipe.result, 1);
  copyItemState(base, result);
  const overflow = container.addItem(result);
  if (overflow) player.dimension.spawnItem(overflow, player.location);
  player.playSound("random.anvil_use", { volume: 0.8, pitch: 1.1 });
  player.sendMessage(`§aSmelted ${title(recipe.result)}.`);
}

async function openSmithing(player) {
  const container = inventory(player);
  if (!container) return;
  const relevant = RECIPES.filter(recipe => itemCount(container, recipe.base) > 0);
  if (relevant.length === 0) {
    player.sendMessage("§7Carry a compatible tool or armor piece, then sneak-use the smithing table again.");
    return;
  }
  const form = new ActionFormData()
    .title("Matcha Smithing")
    .body("Choose an upgrade. Compatible item state will be transferred.");
  for (const recipe of relevant) {
    const ready = canSmith(container, recipe);
    form.button(`${ready ? "§a" : "§c"}${title(recipe.result)}\n§8${short(recipe.template)} + ${short(recipe.addition)}`);
  }
  const response = await form.show(player);
  if (response.canceled || response.selection === undefined) return;
  performSmith(player, relevant[response.selection]);
}

world.beforeEvents.playerInteractWithBlock?.subscribe(event => {
  if (event.block?.typeId !== "minecraft:smithing_table" || !event.player.isSneaking) return;
  event.cancel = true;
  system.run(() => openSmithing(event.player));
});
