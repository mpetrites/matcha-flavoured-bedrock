import {
  EntityComponentTypes,
  EquipmentSlot,
  GameMode,
  system,
  world
} from "@minecraft/server";
import { SPLASH_FOODS } from "./food_interaction_data.js";

const SPLASH_RADIUS = 4;
const SPLASH_RANGE = 8;
const lastSplash = new Map();

function consumeMainHand(player, typeId) {
  if (player.getGameMode() === GameMode.Creative) return;
  const equipment = player.getComponent(EntityComponentTypes.Equippable);
  const hand = equipment?.getEquipment(EquipmentSlot.Mainhand);
  if (!hand || hand.typeId !== typeId) return;
  if (hand.amount > 1) {
    hand.amount -= 1;
    equipment.setEquipment(EquipmentSlot.Mainhand, hand);
  } else {
    equipment.setEquipment(EquipmentSlot.Mainhand);
  }
}

function impactLocation(player) {
  try {
    const hit = player.getBlockFromViewDirection({maxDistance: SPLASH_RANGE});
    if (hit?.block) {
      const location = hit.block.location;
      return {x: location.x + 0.5, y: location.y + 0.5, z: location.z + 0.5};
    }
  } catch {}
  const direction = player.getViewDirection();
  return {
    x: player.location.x + direction.x * SPLASH_RANGE,
    y: player.location.y + 1.5 + direction.y * SPLASH_RANGE,
    z: player.location.z + direction.z * SPLASH_RANGE
  };
}

function applySplash(entity, actions, scale) {
  for (const action of actions) {
    if (Math.random() > (action.probability ?? 1)) continue;
    if (action.type === "apply_effects") {
      for (const effect of action.effects) {
        try {
          entity.addEffect(effect.id, Math.max(1, Math.round(effect.duration * scale)), {
            amplifier: effect.amplifier,
            showParticles: effect.showParticles
          });
        } catch {}
      }
    } else if (action.type === "remove_effects") {
      for (const effect of action.effects) try { entity.removeEffect(effect); } catch {}
    } else if (action.type === "clear_all_effects") {
      for (const effect of entity.getEffects()) entity.removeEffect(effect.typeId);
    }
  }
}

world.afterEvents.itemUse.subscribe(({source, itemStack}) => {
  const actions = SPLASH_FOODS[itemStack.typeId];
  if (!actions || source.typeId !== "minecraft:player") return;
  const now = system.currentTick;
  if (now - (lastSplash.get(source.id) ?? -20) < 5) return;
  lastSplash.set(source.id, now);

  const impact = impactLocation(source);
  consumeMainHand(source, itemStack.typeId);
  try { source.playSound("random.bow", {volume: 0.45, pitch: 1.35}); } catch {}
  system.runTimeout(() => {
    try { source.dimension.playSound("random.glass", impact, {volume: 0.8, pitch: 1.1}); } catch {}
    for (let index = 0; index < 18; index += 1) {
      try {
        source.dimension.spawnParticle("minecraft:splash_spell_emitter", {
          x: impact.x + (Math.random() - 0.5) * 2,
          y: impact.y + Math.random(),
          z: impact.z + (Math.random() - 0.5) * 2
        });
      } catch {}
    }
    for (const entity of source.dimension.getEntities({location: impact, maxDistance: SPLASH_RADIUS})) {
      const distance = Math.hypot(
        entity.location.x - impact.x,
        entity.location.y - impact.y,
        entity.location.z - impact.z
      );
      applySplash(entity, actions, Math.max(0.25, 1 - distance / SPLASH_RADIUS));
    }
  }, 4);
});

// A vanilla cake remains placeable. Compare its bite state on the next tick so
// full-hunger clicks and adding candles do not grant free healing, while the
// final bite (which replaces the block with air) still counts.
world.beforeEvents.playerInteractWithBlock.subscribe(({player, block, itemStack}) => {
  if (block.typeId !== "minecraft:cake") return;
  if (itemStack?.typeId === "minecraft:candle" || itemStack?.typeId?.endsWith("_candle")) return;
  const beforeBites = block.permutation.getState("bite_counter") ?? 0;
  const location = {...block.location};
  const dimension = block.dimension;
  system.run(() => {
    const after = dimension.getBlock(location);
    const successful = after?.typeId === "minecraft:air" || (
      after?.typeId === "minecraft:cake" &&
      (after.permutation.getState("bite_counter") ?? 0) > beforeBites
    );
    if (!successful || !player.isValid) return;
    try {
      player.addEffect("regeneration", 24, {amplifier: 2, showParticles: false});
      player.playSound("random.burp", {volume: 0.25, pitch: 1.15});
    } catch {}
  });
});
