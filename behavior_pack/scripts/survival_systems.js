import { EntityComponentTypes, EquipmentSlot, GameMode, ItemStack, system, world } from "@minecraft/server";
import { playerHasEnchantment } from "./enchantments.js";

const WARDING_STONE="matcha:warding_stone", BEDROCK_BUSTER="matcha:bedrock_buster";
const WARDING_TAG="matcha_warding_stone_marker", ANVIL_TAG="matcha_anvil_session";
const FROZEN_BIOMES=new Set(["minecraft:frozen_ocean","minecraft:deep_frozen_ocean","minecraft:frozen_river","minecraft:snowy_plains","minecraft:ice_spikes","minecraft:snowy_taiga","minecraft:snowy_beach","minecraft:grove","minecraft:snowy_slopes","minecraft:frozen_peaks","minecraft:jagged_peaks"]);
const UNDEAD=new Set(["minecraft:zombie","minecraft:husk","minecraft:drowned","minecraft:zombie_villager","minecraft:skeleton","minecraft:stray","minecraft:wither_skeleton","minecraft:phantom","minecraft:zoglin","minecraft:zombified_piglin","minecraft:wither"]);
const FRIENDS=new Set(["minecraft:villager","minecraft:wandering_trader","minecraft:iron_golem","minecraft:snow_golem"]);
const FACE_OFFSET={Up:{x:0,y:1,z:0},Down:{x:0,y:-1,z:0},North:{x:0,y:0,z:-1},South:{x:0,y:0,z:1},East:{x:1,y:0,z:0},West:{x:-1,y:0,z:0}};

function consumeMainHand(player,typeId) {
  if (player.getGameMode()===GameMode.Creative) return;
  const equipment=player.getComponent(EntityComponentTypes.Equippable), hand=equipment?.getEquipment(EquipmentSlot.Mainhand);
  if (!hand || hand.typeId!==typeId) return;
  if (hand.amount>1) { hand.amount--; equipment.setEquipment(EquipmentSlot.Mainhand,hand); }
  else equipment.setEquipment(EquipmentSlot.Mainhand);
}
function trialChamberNearby(player,location) {
  for (let x=-12;x<=12;x+=2) for (let y=-8;y<=8;y+=2) for (let z=-12;z<=12;z+=2) {
    const type=player.dimension.getBlock({x:location.x+x,y:location.y+y,z:location.z+z})?.typeId;
    if (type==="minecraft:trial_spawner" || type==="minecraft:vault") return true;
  }
  return false;
}
function targetLocation(event) {
  const offset=FACE_OFFSET[event.blockFace] ?? {x:0,y:1,z:0};
  return {x:event.block.location.x+offset.x,y:event.block.location.y+offset.y,z:event.block.location.z+offset.z};
}

world.beforeEvents.playerInteractWithBlock.subscribe((event) => {
  const {itemStack,player:source}=event;
  if (!itemStack || (itemStack.typeId!==WARDING_STONE && itemStack.typeId!==BEDROCK_BUSTER)) return;
  const location=targetLocation(event);
  system.run(() => {
  if (itemStack.typeId===WARDING_STONE) {
    if (trialChamberNearby(source,location)) { source.sendMessage("§cThe Trial Chamber violently rejects the Warding Stone."); source.dimension.createExplosion(location,1,{breaksBlocks:false,source}); return; }
    const block=source.dimension.getBlock(location); if (!block || block.typeId!=="minecraft:air") { source.sendMessage("§7The Warding Stone needs an empty block."); return; }
    block.setType("minecraft:lodestone"); const marker=source.dimension.spawnEntity("minecraft:armor_stand",{x:location.x+0.5,y:location.y,z:location.z+0.5});
    marker.addTag(WARDING_TAG); marker.addEffect("invisibility",20000000,{showParticles:false}); marker.nameTag="";
    consumeMainHand(source,WARDING_STONE); source.playSound("mob.wither.spawn",{volume:0.25,pitch:1.2}); source.sendMessage("§bWarding Stone set.");
  }
  if (itemStack.typeId===BEDROCK_BUSTER) {
    consumeMainHand(source,BEDROCK_BUSTER); const tnt=source.dimension.spawnEntity("minecraft:tnt",{x:location.x+0.5,y:location.y+0.5,z:location.z+0.5});
    try { tnt.addEffect("glowing",100,{showParticles:false}); } catch {}
    system.runTimeout(() => {
      if (!source.dimension) return;
      for (let x=-1;x<=1;x++) for (let y=-3;y<=3;y++) for (let z=-1;z<=1;z++) {
        const block=source.dimension.getBlock({x:location.x+x,y:location.y+y,z:location.z+z}); if (block?.typeId==="minecraft:bedrock") block.setType("minecraft:air");
      }
      try { source.dimension.spawnParticle("minecraft:endrod",{x:location.x+0.5,y:location.y+0.5,z:location.z+0.5}); } catch {}
    },79);
  }
  });
});

world.afterEvents.playerInteractWithBlock.subscribe(({player,block}) => {
  if (!["minecraft:anvil","minecraft:chipped_anvil","minecraft:damaged_anvil"].includes(block.typeId)) return;
  player.addTag(ANVIL_TAG); player.resetLevel(); player.addLevels(50);
  system.runTimeout(() => { if (player.isValid) { player.removeTag(ANVIL_TAG); player.resetLevel(); } },300);
});

world.afterEvents.entityDie.subscribe(({deadEntity}) => {
  if (deadEntity.typeId!=="minecraft:ender_dragon" || world.getDynamicProperty("matcha:first_dragon_reward")) return;
  world.setDynamicProperty("matcha:first_dragon_reward",true);
  const end=world.getDimension("the_end"); end.spawnItem(new ItemStack("minecraft:nether_star",1),{x:0,y:100,z:0});
});

function freezingWater(player) {
  if (player.getGameMode()===GameMode.Creative || playerHasEnchantment(player,"freezing_protection")) return;
  const head={x:Math.floor(player.location.x),y:Math.floor(player.location.y+1),z:Math.floor(player.location.z)};
  if (player.dimension.getBlock(head)?.typeId!=="minecraft:water") return;
  let biome; try { biome=player.dimension.getBiome(player.location)?.id; } catch { return; }
  if (!FROZEN_BIOMES.has(biome)) return;
  player.addEffect("slowness",100,{amplifier:4,showParticles:false}); player.addEffect("darkness",100,{amplifier:0,showParticles:false}); player.applyDamage(2);
}
function wardingStones(dimension) {
  for (const marker of dimension.getEntities({type:"minecraft:armor_stand",tags:[WARDING_TAG]})) {
    const block=dimension.getBlock(marker.location);
    if (block?.typeId!=="minecraft:lodestone") { dimension.spawnItem(new ItemStack("matcha:raw_estus",7),marker.location); marker.kill(); continue; }
    for (const entity of dimension.getEntities({location:marker.location,maxDistance:26})) {
      if (FRIENDS.has(entity.typeId)) entity.addEffect("regeneration",60,{amplifier:0,showParticles:false});
      if (!UNDEAD.has(entity.typeId)) continue;
      entity.addEffect("slowness",40,{amplifier:1,showParticles:false});
      if (Math.hypot(entity.location.x-marker.location.x,entity.location.y-marker.location.y,entity.location.z-marker.location.z)<=14) entity.applyDamage(entity.typeId==="minecraft:wither"?2:7);
    }
    try { dimension.spawnParticle("minecraft:blue_flame_particle",{x:marker.location.x,y:marker.location.y+0.5,z:marker.location.z}); } catch {}
  }
}

let second=0;
system.runInterval(() => {
  second++;
  for (const player of world.getAllPlayers()) { freezingWater(player); if (!player.hasTag(ANVIL_TAG) && player.level>0) player.resetLevel(); }
  if (second%2===0) for (const id of ["overworld","nether","the_end"]) wardingStones(world.getDimension(id));
},20);
