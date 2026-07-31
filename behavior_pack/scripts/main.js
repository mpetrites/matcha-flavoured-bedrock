import { system, world } from "@minecraft/server";
import { FOOD_EFFECTS } from "./food_effects.js";
import "./survival.js";
import "./estus.js";

world.afterEvents.playerSpawn.subscribe(({ initialSpawn, player }) => {
  if (!initialSpawn || player.hasTag("matcha_alpha_welcomed")) return;

  player.addTag("matcha_alpha_welcomed");
  player.sendMessage("§aMatcha Flavoured Bedrock Alpha 0.7.0");
  player.sendMessage("§7Food restores health instead of hunger. Try cooking an egg, apple, or raw meat.");
  player.sendMessage("§7Test kits: §f/function matcha_equipment_test§7, §fmatcha_component_items_test§7, or §fmatcha_consumables_test§7.");
});

function applyEffectTimeline(source, effectId, effects, elapsed = 0) {
  if (!source.isValid) return;

  const remaining = effects.filter((effect) => effect.duration > elapsed);
  if (remaining.length === 0) return;

  // Java keeps weaker instances hidden while a stronger instance is active.
  // Bedrock stores one instance per effect type, so select Java's active
  // instance now and schedule the next hidden instance when it would surface.
  remaining.sort(
    (left, right) =>
      right.amplifier - left.amplifier || right.duration - left.duration
  );
  const active = remaining[0];
  const duration = active.duration - elapsed;

  try {
    source.addEffect(effectId, duration, {
      amplifier: active.amplifier,
      showParticles: active.showParticles
    });
  } catch {
    // A future Java effect may not yet exist in the installed Bedrock build.
    return;
  }

  const nextElapsed = active.duration;
  if (remaining.some((effect) => effect.duration > nextElapsed)) {
    system.runTimeout(
      () => applyEffectTimeline(source, effectId, effects, nextElapsed),
      duration
    );
  }
}

function applyEffects(source, effects) {
  const grouped = new Map();
  for (const effect of effects) {
    const group = grouped.get(effect.id) ?? [];
    group.push(effect);
    grouped.set(effect.id, group);
  }
  for (const [effectId, timeline] of grouped) {
    applyEffectTimeline(source, effectId, timeline);
  }
}

function consumeFood(source, actions) {
  for (const action of actions) {
    if (Math.random() > (action.probability ?? 1)) continue;

    if (action.type === "apply_effects") {
      applyEffects(source, action.effects);
      continue;
    }

    if (action.type === "remove_effects") {
      for (const effectId of action.effects) {
        try {
          source.removeEffect(effectId);
        } catch {
          // Ignore effects unavailable in this Bedrock engine version.
        }
      }
      continue;
    }

    if (action.type === "clear_all_effects") {
      for (const effect of source.getEffects()) {
        source.removeEffect(effect.typeId);
      }
    }
  }
}

world.afterEvents.itemCompleteUse.subscribe(({ itemStack, source }) => {
  const actions = FOOD_EFFECTS[itemStack.typeId];
  if (actions) consumeFood(source, actions);
});
