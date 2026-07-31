import {
  EntityComponentTypes,
  EquipmentSlot,
  GameMode,
  ItemStack,
  system,
  world
} from "@minecraft/server";
import { BIOME_AMBIENCE } from "./biome_ambience_data.js";

const FACE_OFFSET = {
  Up: {x: 0, y: 1, z: 0}, Down: {x: 0, y: -1, z: 0},
  North: {x: 0, y: 0, z: -1}, South: {x: 0, y: 0, z: 1},
  East: {x: 1, y: 0, z: 0}, West: {x: -1, y: 0, z: 0}
};

// Matcha's Nether dimension type disables water evaporation. Bedrock does not
// expose dimension types, so place source water through the bucket interaction.
world.beforeEvents.itemUseOn.subscribe((event) => {
  if (event.source.dimension.id !== "minecraft:nether" || event.itemStack.typeId !== "minecraft:water_bucket") return;
  const offset = FACE_OFFSET[event.blockFace] ?? FACE_OFFSET.Up;
  const location = {
    x: event.block.location.x + offset.x,
    y: event.block.location.y + offset.y,
    z: event.block.location.z + offset.z
  };
  const target = event.source.dimension.getBlock(location);
  if (!target || !["minecraft:air", "minecraft:fire", "minecraft:soul_fire"].includes(target.typeId)) return;
  event.cancel = true;
  const player = event.source;
  system.run(() => {
    const block = player.dimension.getBlock(location);
    if (!block || !["minecraft:air", "minecraft:fire", "minecraft:soul_fire"].includes(block.typeId)) return;
    block.setType("minecraft:water");
    try { player.playSound("bucket.empty_water"); } catch {}
    if (player.getGameMode() === GameMode.Creative) return;
    const equipment = player.getComponent(EntityComponentTypes.Equippable);
    if (!equipment) return;
    const main = equipment.getEquipment(EquipmentSlot.Mainhand);
    const slot = main?.typeId === "minecraft:water_bucket" ? EquipmentSlot.Mainhand : EquipmentSlot.Offhand;
    equipment.setEquipment(slot, new ItemStack("minecraft:bucket", 1));
  });
});

const PARTICLES = {
  white_ash: "minecraft:basic_smoke_particle",
  ash: "minecraft:basic_smoke_particle",
  warped_spore: "minecraft:warped_spore_particle",
  crimson_spore: "minecraft:crimson_spore_particle"
};
let ambienceTick = 0;
system.runInterval(() => {
  ambienceTick += 20;
  for (const player of world.getAllPlayers()) {
    let biome;
    try { biome = player.dimension.getBiome(player.location)?.id; } catch { continue; }
    const ambience = BIOME_AMBIENCE[biome];
    if (!ambience) continue;
    if (ambience.particle && Math.random() < 1 - Math.pow(1 - ambience.particleChance, 20)) {
      const location = {
        x: player.location.x + (Math.random() - 0.5) * 16,
        y: player.location.y + Math.random() * 6,
        z: player.location.z + (Math.random() - 0.5) * 16
      };
      try { player.dimension.spawnParticle(PARTICLES[ambience.particle] ?? `minecraft:${ambience.particle}`, location); } catch {}
    }
    if (ambience.loop && ambienceTick % 200 === 0) {
      try { player.playSound(ambience.loop, {volume: 0.55}); } catch {}
    }
    if (ambience.addition && Math.random() < 1 - Math.pow(1 - ambience.additionChance, 20)) {
      try { player.playSound(ambience.addition, {volume: 0.7}); } catch {}
    }
    if (ambience.mood && ambienceTick % Math.max(20, ambience.moodDelay) === 0 && Math.random() < 0.5) {
      try { player.playSound(ambience.mood, {volume: 0.6}); } catch {}
    }
  }
}, 20);
