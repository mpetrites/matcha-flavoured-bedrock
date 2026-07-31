import { EntityComponentTypes, ItemStack, system, world } from "@minecraft/server";
import { ActionFormData, MessageFormData } from "@minecraft/server-ui";
import { MATCHA_TRADES, MATCHA_TRADE_SETS } from "./villager_trade_data.js";

const PROFESSION_BY_VARIANT={1:"farmer",2:"fisherman",3:"shepherd",4:"fletcher",5:"librarian",6:"cartographer",7:"cleric",8:"armorer",9:"weaponsmith",10:"toolsmith",11:"butcher",12:"leatherworker",13:"mason"};
const LEVEL_THRESHOLDS=[0,10,70,150,250];
const USES_PROPERTY="matcha:trade_uses", XP_PROPERTY="matcha:trade_xp", LEVEL_PROPERTY="matcha:trade_level", RESTOCK_PROPERTY="matcha:trade_restock_day";

function profession(entity) {
  if (entity.typeId==="minecraft:wandering_trader") return "wandering_trader";
  try {
    // villager_v2 uses `variant` for its profession. `mark_variant` is the
    // biome skin, so routing on it silently assigned trades by appearance.
    const variant=entity.getComponent("minecraft:variant")?.value;
    return PROFESSION_BY_VARIANT[variant];
  } catch { return undefined; }
}
function nativeLevel(entity) {
  const saved=entity.getDynamicProperty(LEVEL_PROPERTY); if (typeof saved==="number") return Math.max(1,Math.min(5,Math.floor(saved)));
  let level=1; try { const tier=entity.getProperty("minecraft:trade_tier"); if (typeof tier==="number") level=Math.max(1,Math.min(5,Math.floor(tier)+1)); } catch {}
  entity.setDynamicProperty(LEVEL_PROPERTY,level); return level;
}
function hash(text) { let value=2166136261; for (let i=0;i<text.length;i++) { value^=text.charCodeAt(i); value=Math.imul(value,16777619); } return value>>>0; }
function chosenMembers(entity,setKey,set) {
  const values=[...set.trades]; let state=hash(entity.id+"|"+setKey);
  for (let i=values.length-1;i>0;i--) { state=(Math.imul(state,1664525)+1013904223)>>>0; const j=state%(i+1); [values[i],values[j]]=[values[j],values[i]]; }
  return values.slice(0,Math.min(set.amount,values.length));
}
function availableTrades(entity,professionName,level) {
  const ids=[];
  for (const [key,set] of Object.entries(MATCHA_TRADE_SETS)) {
    if (set.profession!==professionName || (professionName!=="wandering_trader" && set.level>level)) continue;
    ids.push(...chosenMembers(entity,key,set));
  }
  return [...new Set(ids)].map(id=>MATCHA_TRADES[id]).filter(trade=>trade && !trade.discard);
}
function uses(entity) {
  const day=Math.floor(world.getAbsoluteTime()/24000), previous=entity.getDynamicProperty(RESTOCK_PROPERTY);
  if (previous!==day) { entity.setDynamicProperty(RESTOCK_PROPERTY,day); entity.setDynamicProperty(USES_PROPERTY,"{}"); return {}; }
  try { return JSON.parse(entity.getDynamicProperty(USES_PROPERTY) || "{}"); } catch { return {}; }
}
function saveUses(entity,value) { entity.setDynamicProperty(USES_PROPERTY,JSON.stringify(value)); }
function itemCount(player,typeId) {
  const inventory=player.getComponent(EntityComponentTypes.Inventory)?.container; if (!inventory) return 0;
  let total=0; for (let slot=0;slot<inventory.size;slot++) { const stack=inventory.getItem(slot); if (stack?.typeId===typeId) total+=stack.amount; } return total;
}
function removeItems(player,typeId,count) {
  const inventory=player.getComponent(EntityComponentTypes.Inventory)?.container; if (!inventory || itemCount(player,typeId)<count) return false;
  let remaining=count;
  for (let slot=0;slot<inventory.size && remaining>0;slot++) {
    const stack=inventory.getItem(slot); if (stack?.typeId!==typeId) continue;
    const taken=Math.min(stack.amount,remaining); remaining-=taken;
    if (stack.amount===taken) inventory.setItem(slot); else { stack.amount-=taken; inventory.setItem(slot,stack); }
  }
  return remaining===0;
}
function giveItems(player,typeId,count) {
  const inventory=player.getComponent(EntityComponentTypes.Inventory)?.container; if (!inventory) return;
  let remaining=count;
  while (remaining>0) {
    let amount=Math.min(remaining,64), stack;
    while (amount>0) { try { stack=new ItemStack(typeId,amount); break; } catch { amount=Math.floor(amount/2); } }
    if (!stack) return; remaining-=amount; const overflow=inventory.addItem(stack); if (overflow) player.dimension.spawnItem(overflow,player.location);
  }
}
function tradeLabel(trade,currentUses) {
  const stock=Math.max(0,trade.maxUses-currentUses);
  return `${trade.wants.count}× ${trade.wants.name}  →  ${trade.gives.count}× ${trade.gives.name}\n§8Stock ${stock}/${trade.maxUses}`;
}
function advanceVillager(entity,trade) {
  if (entity.typeId==="minecraft:wandering_trader") return;
  const xp=(entity.getDynamicProperty(XP_PROPERTY) || 0)+trade.xp; entity.setDynamicProperty(XP_PROPERTY,xp);
  let level=nativeLevel(entity); while (level<5 && xp>=LEVEL_THRESHOLDS[level]) level++;
  entity.setDynamicProperty(LEVEL_PROPERTY,level);
}
async function confirmTrade(player,entity,trade) {
  if (!entity.isValid || !player.isValid) return;
  const currentUses=uses(entity), used=currentUses[trade.id] || 0;
  if (used>=trade.maxUses) { player.sendMessage("§cThat trade is out of stock."); return; }
  if (itemCount(player,trade.wants.item)<trade.wants.count) { player.sendMessage(`§cYou need ${trade.wants.count}× ${trade.wants.name}.`); return; }
  const result=await new MessageFormData().title("Confirm Trade").body(tradeLabel(trade,used)).button1("Trade").button2("Cancel").show(player);
  if (result.canceled || result.selection!==0 || !entity.isValid) return;
  const refreshed=uses(entity), refreshedUses=refreshed[trade.id] || 0;
  if (refreshedUses>=trade.maxUses || !removeItems(player,trade.wants.item,trade.wants.count)) { player.sendMessage("§cThe trade could not be completed."); return; }
  giveItems(player,trade.gives.item,trade.gives.count); refreshed[trade.id]=refreshedUses+1; saveUses(entity,refreshed); advanceVillager(entity,trade);
  player.playSound("mob.villager.yes",{volume:0.7,pitch:1}); player.sendMessage(`§aReceived ${trade.gives.count}× ${trade.gives.name}.`);
}
async function openTrades(player,entity) {
  if (!entity.isValid || !player.isValid) return;
  const professionName=profession(entity); if (!professionName) { player.sendMessage("§7This villager has no Matcha profession trades."); return; }
  const level=professionName==="wandering_trader"?1:nativeLevel(entity), offers=availableTrades(entity,professionName,level), currentUses=uses(entity);
  const form=new ActionFormData().title(`${professionName.replaceAll("_"," ")} — Level ${level}`).body("Matcha Flavoured trades");
  for (const trade of offers) form.button(tradeLabel(trade,currentUses[trade.id] || 0));
  const response=await form.show(player); if (response.canceled || response.selection===undefined) return;
  await confirmTrade(player,entity,offers[response.selection]);
}

world.beforeEvents.playerInteractWithEntity.subscribe((event) => {
  if (!["minecraft:villager_v2","minecraft:wandering_trader"].includes(event.target.typeId)) return;
  event.cancel=true; system.run(()=>openTrades(event.player,event.target));
});
