import { EntityComponentTypes, system, world } from "@minecraft/server";

const BASE_HEALTH = 20;
const MAX_HEALTH = 60;
const HEALTH_PROPERTY = "matcha:max_health";
const HEART_CONTAINER = "matcha:heart_container";

function trackedMaxHealth(player) {
  const value = player.getDynamicProperty(HEALTH_PROPERTY);
  if (typeof value !== "number") {
    player.setDynamicProperty(HEALTH_PROPERTY, BASE_HEALTH);
    return BASE_HEALTH;
  }
  return Math.max(BASE_HEALTH, Math.min(MAX_HEALTH, Math.floor(value)));
}

function setTrackedMaxHealth(player, value) {
  const clamped = Math.max(BASE_HEALTH, Math.min(MAX_HEALTH, Math.floor(value)));
  player.setDynamicProperty(HEALTH_PROPERTY, clamped);
  applyTrackedHealth(player);
  return clamped;
}

function applyTrackedHealth(player) {
  if (!player.isValid) return;

  const target = trackedMaxHealth(player);
  const extraHealth = target - BASE_HEALTH;
  if (extraHealth > 0) {
    // Bedrock Health Boost advances in four-point steps. Use the smallest
    // effect that contains Matcha's tracked maximum, then cap current health
    // below so one-heart (two-point) progression remains mechanically exact.
    const amplifier = Math.ceil(extraHealth / 4) - 1;
    player.addEffect("health_boost", 240, {
      amplifier,
      showParticles: false
    });
  } else {
    player.removeEffect("health_boost");
  }

  const health = player.getComponent(EntityComponentTypes.Health);
  if (health && health.currentValue > target) {
    health.setCurrentValue(target);
  }
}

function consumeHeartContainer(player) {
  const inventory = player.getComponent(EntityComponentTypes.Inventory)?.container;
  if (!inventory || trackedMaxHealth(player) >= MAX_HEALTH) return false;

  for (let slotIndex = 0; slotIndex < inventory.size; slotIndex += 1) {
    const stack = inventory.getItem(slotIndex);
    if (!stack || stack.typeId !== HEART_CONTAINER) continue;

    if (stack.amount > 1) {
      stack.amount -= 1;
      inventory.setItem(slotIndex, stack);
    } else {
      inventory.setItem(slotIndex);
    }

    const newMaximum = setTrackedMaxHealth(
      player,
      trackedMaxHealth(player) + 2
    );
    player.addEffect("regeneration", 60, {
      amplifier: 10,
      showParticles: false
    });
    player.playSound("random.totem", { volume: 0.5, pitch: 1 });
    player.sendMessage(
      `§cMaximum health increased to ${newMaximum / 2} hearts.`
    );
    return true;
  }
  return false;
}

function manageHunger(player) {
  const hunger = player.getComponent(EntityComponentTypes.Hunger);
  if (!hunger) return;

  // Hunger is not part of Matcha's survival loop. Keep it full so exhaustion
  // can never gate sprinting; food healing is handled by its consume effects.
  // Directly setting the component also avoids Saturation/Hunger effects
  // interacting with Bedrock's hunger and regeneration implementation.
  try {
    hunger.setCurrentValue(hunger.effectiveMax);
    player.removeEffect("hunger");
  } catch {}
}

function advanceSleepingTime() {
  if (!world.getAllPlayers().some((player) => player.isSleeping)) return;
  world.setTimeOfDay((world.getTimeOfDay() + 120) % 24000);
}

system.run(() => {
  world.gameRules.naturalRegeneration = false;
  world.gameRules.keepInventory = true;
  world.gameRules.doInsomnia = false;
  world.gameRules.doDayLightCycle = false;
  world.gameRules.playersSleepingPercentage = 100;
});

world.afterEvents.playerSpawn.subscribe(({ initialSpawn, player }) => {
  if (initialSpawn) {
    trackedMaxHealth(player);
  } else {
    const previousMaximum = trackedMaxHealth(player);
    if (previousMaximum > BASE_HEALTH) {
      setTrackedMaxHealth(player, previousMaximum - 2);
      player.sendMessage("§cYou lost one maximum heart on death.");
    }
  }
  system.run(() => {
    applyTrackedHealth(player);
    try {
      player.runCommand("hud @s hide hunger");
    } catch {}
  });
});

system.runInterval(advanceSleepingTime);

system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    manageHunger(player);
    consumeHeartContainer(player);
    applyTrackedHealth(player);
  }
});
