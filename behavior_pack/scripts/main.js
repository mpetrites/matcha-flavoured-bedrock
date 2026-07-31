import { system, world } from "@minecraft/server";

const HEALING_FOODS = new Map([
  ["matcha:charred_meat", { duration: 15, amplifier: 3 }],
  ["matcha:charred_fish", { duration: 15, amplifier: 3 }],
  ["matcha:charred_potato", { duration: 20, amplifier: 2 }],
  ["matcha:fried_egg", { duration: 24, amplifier: 2 }]
]);

world.afterEvents.playerSpawn.subscribe(({ initialSpawn, player }) => {
  if (!initialSpawn || player.hasTag("matcha_alpha_welcomed")) return;

  player.addTag("matcha_alpha_welcomed");
  player.sendMessage("§aMatcha Flavoured Bedrock Alpha 0.1.1");
  player.sendMessage("§7Food restores health instead of hunger. Try cooking an egg, apple, or raw meat.");
  player.sendMessage("§7With cheats enabled, run §f/function matcha_alpha_test§7 for a test kit.");
});

world.afterEvents.itemCompleteUse.subscribe(({ itemStack, source }) => {
  if (itemStack.typeId === "matcha:baked_apple") {
    // Java layers Regen III for 48 ticks over Regen I for 200 ticks. Bedrock
    // cannot retain two instances of one effect, so reproduce the visible
    // phases: 48 ticks at amplifier 2, then the remaining 152 at amplifier 0.
    source.addEffect("regeneration", 48, {
      amplifier: 2,
      showParticles: false
    });
    system.runTimeout(() => {
      if (!source.isValid) return;
      source.addEffect("regeneration", 152, {
        amplifier: 0,
        showParticles: false
      });
    }, 48);
    return;
  }

  const effect = HEALING_FOODS.get(itemStack.typeId);
  if (!effect) return;

  source.addEffect("regeneration", effect.duration, {
    amplifier: effect.amplifier,
    showParticles: false
  });
});

// Alpha approximation of Matcha's managed-hunger system. Keeping saturation
// topped up makes the test foods usable as health consumables at any time.
system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    player.addEffect("saturation", 100, {
      amplifier: 0,
      showParticles: false
    });
  }
}, 80);
