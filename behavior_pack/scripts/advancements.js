import { EntityComponentTypes, system, world } from "@minecraft/server";
import { ADVANCEMENTS } from "./advancement_data.js";

const CRITERIA_PROPERTY="matcha:advancement_criteria_v1";
const COMPLETE_PROPERTY="matcha:advancements_v1";
const HEX="0123456789abcdef";
const BY_TRIGGER=new Map(), BY_ID=new Map();

for (let advancementIndex=0;advancementIndex<ADVANCEMENTS.length;advancementIndex++) {
  const advancement=ADVANCEMENTS[advancementIndex]; advancement.index=advancementIndex; BY_ID.set(advancement.id,advancement);
  for (const criterion of advancement.criteria) {
    criterion.advancement=advancement;
    const list=BY_TRIGGER.get(criterion.trigger) ?? []; list.push(criterion); BY_TRIGGER.set(criterion.trigger,list);
  }
}

function bits(player,key) { const value=player.getDynamicProperty(key); return typeof value==="string"?value:""; }
function hasBit(value,index) { const digit=parseInt(value[Math.floor(index/4)]??"0",16); return (digit&(1<<(index%4)))!==0; }
function setBit(value,index) {
  const position=Math.floor(index/4), chars=value.padEnd(position+1,"0").split("");
  chars[position]=HEX[parseInt(chars[position],16)|(1<<(index%4))]; return chars.join("");
}
function normalized(value) { return value?.replace(/^minecraft:/,"")?.replace(/^matcha:/,""); }
function itemMatches(criterion,typeId) {
  if (!typeId) return false; const short=normalized(typeId);
  return (criterion.items??[]).some(id=>id===typeId || normalized(id)===short) ||
    (criterion.models??[]).some(id=>normalized(id)===short) ||
    (criterion.resultItems??[]).some(id=>id===typeId || normalized(id)===short) ||
    (criterion.resultModels??[]).some(id=>normalized(id)===short);
}
function requirementsMet(advancement,criterionBits) {
  const byName=new Map(advancement.criteria.map(c=>[c.name,c]));
  return advancement.requirements.every(group=>group.some(name=>hasBit(criterionBits,byName.get(name)?.index??-1)));
}
function notify(player,advancement) {
  const display=advancement.display; if (!display || display.hidden) return;
  const title=display.title||advancement.id, description=display.description||"";
  if (display.toast) {
    try { player.onScreenDisplay.setTitle(`§6${title}`,{subtitle:description?`§f${description}`:"§7Advancement made",fadeInDuration:5,stayDuration:60,fadeOutDuration:10}); } catch {}
    try { player.playSound(display.frame==="challenge"?"random.levelup":"random.orb",{volume:0.8,pitch:display.frame==="challenge"?0.8:1.2}); } catch {}
  }
  if (display.chat) player.sendMessage(`§eAdvancement Made! §f${title}${description?` §7— ${description}`:""}`);
}
function complete(player,advancement,criterionBits) {
  let completed=bits(player,COMPLETE_PROPERTY); if (hasBit(completed,advancement.index)) return;
  if (!requirementsMet(advancement,criterionBits)) return;
  completed=setBit(completed,advancement.index); player.setDynamicProperty(COMPLETE_PROPERTY,completed); notify(player,advancement);
  // Recipe rewards are already globally available in Bedrock. The 19 Java
  // function rewards are owned by their existing Bedrock gameplay systems
  // (Estus, hearts, food effects, Warding Stone, anvil, and dragon reward),
  // preventing completion from applying the same reward twice.
}
function grantCriterion(player,criterion) {
  let value=bits(player,CRITERIA_PROPERTY); if (hasBit(value,criterion.index)) return;
  value=setBit(value,criterion.index); player.setDynamicProperty(CRITERIA_PROPERTY,value); complete(player,criterion.advancement,value);
}
function emit(player,trigger,payload={}) {
  for (const criterion of BY_TRIGGER.get(trigger)??[]) {
    if (payload.item && !itemMatches(criterion,payload.item)) continue;
    if (criterion.entities?.length && !criterion.entities.includes(payload.entity)) continue;
    if (criterion.dimensions?.length && !criterion.dimensions.includes(payload.dimension)) continue;
    if (criterion.professions?.length && !criterion.professions.includes(payload.profession)) continue;
    grantCriterion(player,criterion);
  }
}
function inventoryIds(player) {
  const container=player.getComponent(EntityComponentTypes.Inventory)?.container, ids=new Set(); if (!container) return ids;
  for (let slot=0;slot<container.size;slot++) { const stack=container.getItem(slot); if (stack) ids.add(stack.typeId); }
  return ids;
}
function reconcile(player) {
  const ids=inventoryIds(player);
  for (const trigger of ["inventory_changed","recipe_crafted","fishing_rod_hooked"]) {
    for (const criterion of BY_TRIGGER.get(trigger)??[]) {
      const constrained=(criterion.items?.length||criterion.models?.length||criterion.resultItems?.length||criterion.resultModels?.length);
      if (!constrained || [...ids].some(id=>itemMatches(criterion,id))) grantCriterion(player,criterion);
    }
  }
  for (const criterion of BY_TRIGGER.get("recipe_unlocked")??[]) grantCriterion(player,criterion);
  for (const criterion of BY_TRIGGER.get("tick")??[]) grantCriterion(player,criterion);
  let below; try { below=player.dimension.getBlock({x:Math.floor(player.location.x),y:Math.floor(player.location.y-0.2),z:Math.floor(player.location.z)})?.typeId; } catch {}
  for (const criterion of BY_TRIGGER.get("location")??[]) {
    if (criterion.blocks?.includes(below)) grantCriterion(player,criterion);
  }
  try {
    const vehicle=player.getComponent("minecraft:riding")?.entityRidingOn;
    if (vehicle && (vehicle.typeId.includes("boat") || vehicle.typeId.includes("raft"))) {
      for (const criterion of BY_TRIGGER.get("started_riding")??[]) grantCriterion(player,criterion);
    }
  } catch {}
}

world.afterEvents.playerSpawn.subscribe(({player})=>system.run(()=>reconcile(player)));
world.afterEvents.playerDimensionChange.subscribe(({player,toDimension})=>emit(player,"changed_dimension",{dimension:toDimension.id}));
world.afterEvents.itemCompleteUse.subscribe(({source,itemStack})=>emit(source,"consume_item",{item:itemStack.typeId}));
world.afterEvents.itemUse.subscribe(({source,itemStack})=>emit(source,"using_item",{item:itemStack.typeId}));
world.afterEvents.itemUseOn?.subscribe(({source,itemStack})=>emit(source,"item_used_on_block",{item:itemStack.typeId}));
world.afterEvents.entityDie.subscribe(({deadEntity,damageSource})=>{ const player=damageSource.damagingEntity; if (player?.typeId==="minecraft:player") emit(player,"player_killed_entity",{entity:deadEntity.typeId}); });
system.runInterval(()=>{ for (const player of world.getAllPlayers()) reconcile(player); },20);

export function recordVillagerTrade(player,profession,wantedItem,givenItem) {
  for (const item of [wantedItem,givenItem]) emit(player,"villager_trade",{profession,item});
}
export function grantMatchaAdvancement(player,id) {
  const advancement=BY_ID.get(id); if (!advancement) return false;
  for (const criterion of advancement.criteria) grantCriterion(player,criterion); return true;
}
