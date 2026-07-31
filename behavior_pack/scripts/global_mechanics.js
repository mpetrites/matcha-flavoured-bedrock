import { EntityComponentTypes, EquipmentSlot, GameMode, ItemStack, system, world } from "@minecraft/server";

const HOSTILES=new Set(["minecraft:husk","minecraft:zombie","minecraft:drowned","minecraft:skeleton","minecraft:stray","minecraft:bogged","minecraft:parched","minecraft:creeper","minecraft:cave_spider","minecraft:spider","minecraft:slime","minecraft:enderman","minecraft:witch","minecraft:zombie_villager"]);
const UNDEAD=new Set(["minecraft:husk","minecraft:zombie","minecraft:drowned","minecraft:skeleton","minecraft:stray","minecraft:bogged","minecraft:parched","minecraft:zombie_villager"]);
const CHEERFUL="matcha:loot_item_108c0dc960", MOURNFUL="matcha:loot_item_cdfc89dd82";
const APPLICATIONS=new Set(["matcha:trade_item_16f823408e","matcha:trade_item_6bdf6aa045","matcha:trade_item_7a9b8dc5dd","matcha:trade_item_c5485ba67e","matcha:trade_item_c929729753","matcha:trade_item_ce1f4fbf1f"]);

function safeParticle(dimension,id,location) { try { dimension.spawnParticle(id,location); } catch {} }
function visibleSky(entity) {
  try { return entity.dimension.getTopmostBlock({x:Math.floor(entity.location.x),z:Math.floor(entity.location.z)})?.location.y<=Math.floor(entity.location.y); } catch { return false; }
}
function modifySpawn(entity) {
  if (!HOSTILES.has(entity.typeId)) return;
  if (entity.dimension.id==="minecraft:overworld") {
    const safeSurface=world.getDynamicProperty("matcha:first_dragon_reward")===true;
    if ((safeSurface && (entity.location.y>=63 || visibleSky(entity))) || (!safeSurface && !UNDEAD.has(entity.typeId) && visibleSky(entity))) { try { entity.kill(); } catch {} return; }
  }
  const health=entity.getComponent(EntityComponentTypes.Health);
  if (health) {
    const target=entity.typeId.includes("skeleton")||entity.typeId==="minecraft:stray"||entity.typeId==="minecraft:bogged"?10:entity.typeId==="minecraft:creeper"?16:entity.typeId==="minecraft:cave_spider"?4:undefined;
    if (target) try { health.setCurrentValue(Math.min(health.currentValue,target)); } catch {}
  }
  try {
    if (entity.typeId==="minecraft:cave_spider") entity.addEffect("speed",20000000,{amplifier:1,showParticles:false});
    if (entity.typeId==="minecraft:zombie") entity.addEffect("speed",20000000,{amplifier:2,showParticles:false});
    if (entity.typeId==="minecraft:husk") { entity.addEffect("speed",20000000,{amplifier:0,showParticles:false}); entity.addEffect("strength",20000000,{amplifier:0,showParticles:false}); }
  } catch {}
}

world.afterEvents.entitySpawn.subscribe(({entity})=>system.run(()=>{ if (entity.isValid) modifySpawn(entity); }));

world.beforeEvents.itemUseOn.subscribe((event)=>{
  if (event.itemStack.typeId!=="minecraft:glass_bottle" || event.block.typeId!=="minecraft:water") return;
  event.cancel=true; const player=event.source;
  system.run(()=>{
    const equipment=player.getComponent(EntityComponentTypes.Equippable), hand=equipment?.getEquipment(EquipmentSlot.Mainhand);
    if (!equipment || !hand || hand.typeId!=="minecraft:glass_bottle") return;
    if (player.getGameMode()!==GameMode.Creative) {
      if (hand.amount>1) { hand.amount--; equipment.setEquipment(EquipmentSlot.Mainhand,hand); }
      else equipment.setEquipment(EquipmentSlot.Mainhand);
    }
    const inventory=player.getComponent(EntityComponentTypes.Inventory)?.container, overflow=inventory?.addItem(new ItemStack("matcha:water_bottle",1));
    if (overflow) player.dimension.spawnItem(overflow,player.location);
    try { player.playSound("random.fill_bottle"); } catch {}
  });
});

world.afterEvents.itemUse.subscribe(({source,itemStack})=>{
  if (itemStack.typeId===CHEERFUL || itemStack.typeId===MOURNFUL) {
    system.runTimeout(()=>{ try { source.dimension.runCommand(itemStack.typeId===CHEERFUL?"weather clear":"weather rain"); } catch {} },60);
  }
  if (itemStack.typeId==="minecraft:goat_horn") {
    const ghast=source.dimension.getEntities({type:"minecraft:happy_ghast",location:source.location,maxDistance:80,closest:1})[0];
    if (ghast) { const view=source.getViewDirection(); try { ghast.teleport({x:source.location.x+view.x*3,y:source.location.y+1+view.y*3,z:source.location.z+view.z*3},{dimension:source.dimension}); } catch {} }
  }
  if (APPLICATIONS.has(itemStack.typeId)) {
    const villager=source.dimension.getEntities({type:"minecraft:villager_v2",location:source.location,maxDistance:32,closest:1})[0];
    if (villager) for (let i=0;i<12;i++) safeParticle(source.dimension,"minecraft:basic_smoke_particle",{x:villager.location.x+(Math.random()-.5),y:villager.location.y+Math.random()*1.8,z:villager.location.z+(Math.random()-.5)});
  }
});

function environmentalEffects(player,tick) {
  let vehicle; try { vehicle=player.getComponent("minecraft:riding")?.entityRidingOn; } catch {}
  if (vehicle && (vehicle.typeId.includes("boat")||vehicle.typeId.includes("raft"))) {
    const velocity=vehicle.getVelocity(),moving=Math.hypot(velocity.x,velocity.z)>.02;
    if (moving) for (const dx of [-.65,0,.65]) safeParticle(vehicle.dimension,`matcha:splash_${Math.floor(Math.random()*4)}`,{x:vehicle.location.x+dx,y:vehicle.location.y+.2,z:vehicle.location.z});
  }
  let below; try { below=player.dimension.getBlock({x:Math.floor(player.location.x),y:Math.floor(player.location.y-.2),z:Math.floor(player.location.z)})?.typeId; } catch {}
  if (below==="minecraft:quartz_ore" || below==="minecraft:nether_quartz_ore") safeParticle(player.dimension,"minecraft:basic_smoke_particle",{x:player.location.x,y:player.location.y+.1,z:player.location.z});
  if (tick%100!==0 || player.dimension.id!=="minecraft:overworld") return;
  const villagers=player.dimension.getEntities({type:"minecraft:villager_v2",location:player.location,maxDistance:48});
  if (villagers.length<2) return;
  try { player.runCommand("stopsound @s music"); } catch {}
  const sounds=["ambient.cave","step.wood","step.gravel","random.door_open"];
  if (Math.random()<.35) try { player.playSound(sounds[Math.floor(Math.random()*sounds.length)],{volume:.45,pitch:.8+Math.random()*.4}); } catch {}
}

let tick=0;
system.runInterval(()=>{ world.setTimeOfDay((world.getTimeOfDay()+1)%24000); },3);
system.runInterval(()=>{ tick+=3; for (const player of world.getAllPlayers()) environmentalEffects(player,tick); },3);
