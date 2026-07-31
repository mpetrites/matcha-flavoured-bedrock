import { EnchantmentTypes, EntityComponentTypes, EquipmentSlot, system, world } from "@minecraft/server";
import { BLESSINGS, EQUIPMENT_ENCHANTMENTS } from "./enchantment_data.js";

const TAG_PREFIX = "matcha_ench_";
const UNDEAD = new Set(["minecraft:zombie","minecraft:husk","minecraft:drowned","minecraft:zombie_villager","minecraft:skeleton","minecraft:stray","minecraft:wither_skeleton","minecraft:phantom","minecraft:zoglin","minecraft:zombified_piglin","minecraft:wither"]);
const LIVESTOCK = new Set(["minecraft:cow","minecraft:pig","minecraft:sheep","minecraft:chicken","minecraft:rabbit","minecraft:goat","minecraft:mooshroom"]);
const WARDING_LEVELS = ["warding0","warding1","warding2","warding3"];

function tagName(enchantment) { return TAG_PREFIX + enchantment.replace(/[^a-z0-9_]/g, "_"); }
function equipmentEnchantments(player) {
  const found=new Set(); const equipment=player.getComponent(EntityComponentTypes.Equippable);
  if (!equipment) return found;
  for (const slot of [EquipmentSlot.Mainhand,EquipmentSlot.Offhand,EquipmentSlot.Head,EquipmentSlot.Chest,EquipmentSlot.Legs,EquipmentSlot.Feet]) {
    const item=equipment.getEquipment(slot); for (const enchantment of EQUIPMENT_ENCHANTMENTS[item?.typeId] ?? []) found.add(enchantment);
  }
  return found;
}
function active(player,enchantment,equipped) { return player.hasTag(tagName(enchantment)) || equipped.has(enchantment); }
export function playerHasEnchantment(player,enchantment) { return active(player,enchantment,equipmentEnchantments(player)); }
function safeEffect(player,id,duration=30,amplifier=0) { try { player.addEffect(id,duration,{amplifier,showParticles:false}); } catch {} }
function nearTrialChamber(player) {
  const base=player.location;
  for (let x=-12;x<=12;x+=2) for (let y=-8;y<=8;y+=2) for (let z=-12;z<=12;z+=2) {
    const type=player.dimension.getBlock({x:Math.floor(base.x+x),y:Math.floor(base.y+y),z:Math.floor(base.z+z)})?.typeId;
    if (type==="minecraft:trial_spawner" || type==="minecraft:vault") return true;
  }
  return false;
}

world.afterEvents.itemUse.subscribe(({itemStack,source}) => {
  if (itemStack.typeId==="matcha:warding_stone" && nearTrialChamber(source)) {
    source.sendMessage("§cThe Trial Chamber rejects the Warding Stone.");
    source.playSound("random.anvil_land",{volume:0.5,pitch:0.6});
    return;
  }
  const enchantments=BLESSINGS[itemStack.typeId]; if (!enchantments) return;
  const equipment=source.getComponent(EntityComponentTypes.Equippable), target=equipment?.getEquipment(EquipmentSlot.Offhand);
  if (!target) { source.sendMessage("§7Hold the item to bless in your off hand."); return; }
  const enchantable=target.getComponent("minecraft:enchantable");
  if (!enchantable) { source.sendMessage("§cThat item cannot receive a blessing."); return; }
  let applied=0;
  for (const [fullName,level] of Object.entries(enchantments)) {
    if (fullName.startsWith("main:")) { source.addTag(tagName(fullName.slice(5))); applied++; continue; }
    try { const type=EnchantmentTypes.get(fullName); if (type) { enchantable.addEnchantment({type,level}); applied++; } } catch {}
  }
  if (!applied) { source.sendMessage("§cNo compatible blessing effects could be applied."); return; }
  equipment.setEquipment(EquipmentSlot.Offhand,target);
  const hand=equipment.getEquipment(EquipmentSlot.Mainhand);
  if (hand?.typeId===itemStack.typeId) equipment.setEquipment(EquipmentSlot.Mainhand);
  source.playSound("random.levelup",{volume:0.7,pitch:1.25});
  source.sendMessage(`§dBlessing applied: §f${Object.keys(enchantments).map(x=>x.split(":").pop()).join(", ")}`);
});

world.afterEvents.entityHitEntity.subscribe(({damagingEntity,hitEntity}) => {
  if (damagingEntity.typeId!=="minecraft:player") return;
  const equipped=equipmentEnchantments(damagingEntity);
  if (active(damagingEntity,"sanguine",equipped)) safeEffect(damagingEntity,"regeneration",20,2);
  if (active(damagingEntity,"slaughter",equipped) && LIVESTOCK.has(hitEntity.typeId)) hitEntity.applyDamage(40,{damagingEntity});
  if (active(damagingEntity,"anemos",equipped)) {
    safeEffect(damagingEntity,"slow_falling",25,0);
    try { damagingEntity.playSound("random.explode",{volume:0.25,pitch:1.8}); } catch {}
  }
});

world.afterEvents.entityHurt.subscribe(({hurtEntity,damageSource}) => {
  if (hurtEntity.typeId!=="minecraft:player") return;
  const player=hurtEntity, equipped=equipmentEnchantments(player), attacker=damageSource.damagingEntity;
  if (attacker?.isValid && active(player,"riposte",equipped)) attacker.applyDamage(2,{damagingEntity:player});
});

function tickPlayer(player,tick) {
  const equipped=equipmentEnchantments(player);
  if (active(player,"bloodrage",equipped)) {
    const health=player.getComponent(EntityComponentTypes.Health);
    if (health && health.currentValue<=10) { safeEffect(player,"strength",30,0); safeEffect(player,"resistance",30,1); }
  }
  if (active(player,"cleanse_armor_head",equipped)) { player.removeEffect("blindness"); player.removeEffect("darkness"); }
  if (active(player,"cleanse_armor_chest",equipped)) { player.removeEffect("poison"); player.removeEffect("wither"); }
  if (active(player,"cleanse_armor_legs",equipped)) player.removeEffect("slowness");
  if (active(player,"cleanse_armor_feet",equipped)) player.removeEffect("levitation");
  if (active(player,"conduit_power",equipped)) { safeEffect(player,"conduit_power"); safeEffect(player,"dolphins_grace"); }
  if (active(player,"fire_proof",equipped)) safeEffect(player,"fire_resistance");
  if (active(player,"freezing_protection",equipped)) { player.removeEffect("slowness"); player.removeEffect("darkness"); }
  if (active(player,"haste",equipped)) safeEffect(player,"haste",30,1);
  if (active(player,"regeneration",equipped) && !player.getEffect("regeneration")) safeEffect(player,"regeneration",60,0);
  if (active(player,"traversal",equipped)) safeEffect(player,"speed",30,0);
  if (active(player,"zephyr",equipped) && player.isSneaking) safeEffect(player,"slow_falling",30,0);
  if (active(player,"divinity",equipped) && tick%600===0) safeEffect(player,"absorption",600,0);
  if (active(player,"reach",equipped)) safeEffect(player,"haste",30,0); // block-range approximation
  if (tick%20!==0) return;
  let ward=0;
  for (let level=3;level>=0;level--) if (active(player,WARDING_LEVELS[level],equipped)) { ward=Math.max(ward,level+1); break; }
  if (active(player,"warding_armour",equipped)) ward=Math.max(ward,2);
  if (!ward) return;
  const radius=[0,3,8,12,24][ward], damage=[0,1,1,3,19][ward];
  for (const entity of player.dimension.getEntities({location:player.location,maxDistance:radius})) {
    if (entity.id===player.id || !UNDEAD.has(entity.typeId)) continue;
    safeEffect(entity,"slowness",25,Math.min(ward,3)); entity.applyDamage(entity.typeId==="minecraft:wither"?Math.min(ward,2):damage,{damagingEntity:player});
  }
}

let tick=0;
system.runInterval(() => { tick+=10; for (const player of world.getAllPlayers()) tickPlayer(player,tick); },10);
