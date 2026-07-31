import { GameMode, ItemStack, system, world } from "@minecraft/server";

const RAW_ESTUS = "matcha:raw_estus";
const ESTUS_ASH = "matcha:estus_ash";
const RAW_ESTUS_DROPS = new Map([
  ["minecraft:blaze", 0.5],
  ["minecraft:zombie", 5 / 11],
  ["minecraft:husk", 5 / 11],
  ["minecraft:drowned", 5 / 11],
  ["minecraft:zombie_villager", 5 / 11]
]);

world.afterEvents.entityDie.subscribe(({ deadEntity, damageSource }) => {
  const chance = RAW_ESTUS_DROPS.get(deadEntity.typeId);
  if (!chance || damageSource.damagingEntity?.typeId !== "minecraft:player") return;
  if (Math.random() >= chance) return;

  deadEntity.dimension.spawnItem(
    new ItemStack(RAW_ESTUS, 1),
    deadEntity.location
  );
});

function consumeOneRawEstus(player) {
  if (player.getGameMode() === GameMode.Creative) return;
  const inventory = player.getComponent("minecraft:inventory")?.container;
  if (!inventory) return;

  for (let slot = 0; slot < inventory.size; slot += 1) {
    const stack = inventory.getItem(slot);
    if (stack?.typeId !== RAW_ESTUS) continue;

    if (stack.amount === 1) {
      inventory.setItem(slot);
    } else {
      stack.amount -= 1;
      inventory.setItem(slot, stack);
    }
    const remainder = inventory.addItem(new ItemStack(ESTUS_ASH, 1));
    if (remainder) player.dimension.spawnItem(remainder, player.location);
    player.addEffect("regeneration", 40, {
      amplifier: 4,
      showParticles: true
    });
    player.addEffect("resistance", 100, {
      amplifier: 0,
      showParticles: true
    });
    player.dimension.spawnParticle(
      "minecraft:basic_flame_particle",
      { x: player.location.x, y: player.location.y + 1.5, z: player.location.z }
    );
    player.playSound("random.orb");
    return;
  }
}

system.runInterval(() => {
  for (const player of world.getAllPlayers()) consumeOneRawEstus(player);
}, 5);
