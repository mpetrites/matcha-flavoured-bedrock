#!/usr/bin/env python3
"""Convert all pinned Java loot tables into safe Bedrock loot definitions."""
import argparse, hashlib, json, shutil
from collections import Counter
from pathlib import Path
from upstream import add_source_argument, baseline, validate_source

ROOT=Path(__file__).resolve().parents[1]; parser=argparse.ArgumentParser(); add_source_argument(parser); JAVA=validate_source(parser.parse_args().source)
SOURCE=JAVA/"data/minecraft/loot_table"; OUTPUT=ROOT/"behavior_pack/loot_tables"; ITEMS=ROOT/"behavior_pack/items/generated_loot"; TEXTURES=ROOT/"resource_pack/textures/items/generated_loot"
source_by_stem={}
for source_path in SOURCE.rglob("*.json"):source_by_stem.setdefault(source_path.stem,[]).append(source_path.relative_to(SOURCE))
ATLAS=ROOT/"resource_pack/textures/item_texture.json"; LANG=ROOT/"resource_pack/texts/en_US.lang"
for d in (OUTPUT,ITEMS,TEXTURES): d.mkdir(parents=True,exist_ok=True)
for p in OUTPUT.rglob("*.json"): p.unlink()
for d in (ITEMS,TEXTURES):
 for p in d.iterdir():
  if p.is_file():p.unlink()
atlas=json.loads(ATLAS.read_text()); atlas["texture_data"]={k:v for k,v in atlas["texture_data"].items() if not k.startswith("matcha_loot_")}
source_lang=json.loads((JAVA/"assets/minecraft/lang/en_us.json").read_text()); model_map={}
for p in (ROOT/"behavior_pack/items").rglob("*.json"):
 if p.parent==ITEMS or " " in p.stem:continue
 try:model_map[p.stem]=json.loads(p.read_text())["minecraft:item"]["description"]["identifier"]
 except:pass
model_map.update({"heart_container":"matcha:heart_container","crystal_heart":"matcha:heart_container"})
signature_map={}
for recipe_path in (JAVA/"data").glob("*/recipe/*.json"):
 try:result=json.loads(recipe_path.read_text()).get("result",{});components=result.get("components") or {}
 except:continue
 if not components:continue
 item_path=next(iter((ROOT/"behavior_pack/items").rglob(recipe_path.stem+".json")),None)
 if not item_path:continue
 try:identifier=json.loads(item_path.read_text())["minecraft:item"]["description"]["identifier"]
 except:continue
 signature_map[result.get("id","")+"|"+json.dumps(components,sort_keys=True,separators=(",",":"))]=identifier
custom={}; lang=[]; dropped_functions=Counter(); dropped_conditions=Counter(); entry_types=Counter(); empty=[]
def display(c,base):
 v=c.get("minecraft:item_name") or c.get("minecraft:custom_name")
 if isinstance(v,str):return v
 if isinstance(v,dict):return v.get("text") or source_lang.get(v.get("translate"),v.get("translate"))
 return base.split(":")[-1].replace("_"," ").title()
def custom_item(base,c):
 model=str(c.get("minecraft:item_model","")).split(":")[-1]
 if model in model_map:return model_map[model]
 sig=base+"|"+json.dumps(c,sort_keys=True,separators=(",",":"))
 if sig in signature_map:return signature_map[sig]
 if sig in custom:return custom[sig]
 h=hashlib.sha1(sig.encode()).hexdigest()[:10]; ident=f"matcha:loot_item_{h}"; custom[sig]=ident; key=f"matcha_loot_{h}"
 src=JAVA/f"assets/minecraft/textures/item/{model}.png"
 if model and src.exists():shutil.copy2(src,TEXTURES/f"{h}.png"); texture=f"textures/items/generated_loot/{h}"
 else:texture=f"textures/items/{base.split(':')[-1]}"
 atlas["texture_data"][key]={"textures":texture}; comps={"minecraft:display_name":{"value":f"item.{ident}.name"},"minecraft:icon":{"textures":{"default":key}},"minecraft:max_stack_size":c.get("minecraft:max_stack_size",1 if c.get("minecraft:max_damage") else 64)}
 if c.get("minecraft:max_damage"):comps["minecraft:durability"]={"max_durability":c["minecraft:max_damage"]}
 if c.get("minecraft:enchantment_glint_override") or c.get("minecraft:enchantments") or c.get("minecraft:stored_enchantments"):comps["minecraft:glint"]=True
 item={"format_version":"1.21.100","minecraft:item":{"description":{"identifier":ident,"menu_category":{"category":"items"}},"components":comps}}
 (ITEMS/f"{h}.json").write_text(json.dumps(item,indent=2)+"\n");lang.append(f"item.{ident}.name={display(c,base)}");return ident
def number(v):
 if isinstance(v,(int,float)):return v
 if isinstance(v,dict):return {k:v[k] for k in ("min","max") if k in v}
 return 1
def conditions(values):
 out=[]
 for c in values or []:
  kind=str(c.get("condition","")).split(":")[-1]
  if kind=="random_chance":out.append({"condition":"random_chance","chance":c.get("chance",1)})
  elif kind in ("killed_by_player","survives_explosion"):out.append({"condition":kind})
  elif kind=="match_tool":
   predicate=c.get("predicate",{});condition={"condition":"match_tool"}
   if predicate.get("items"):condition["item"]=predicate["items"]
   enchants=predicate.get("predicates",{}).get("minecraft:enchantments")
   if enchants:condition["enchantments"]=[{"enchantment":x.get("enchantments","minecraft:silk_touch").split(":")[-1],"levels":x.get("levels",{"min":1})} for x in enchants]
   out.append(condition)
  elif kind=="block_state_property":out.append({"condition":"block_state_property","block":c.get("block"),"properties":c.get("properties",{})})
  elif kind=="any_of":out.append({"condition":"alternative","terms":conditions(c.get("terms"))})
  elif kind=="table_bonus":out.append({"condition":"random_chance","chance":(c.get("chances") or [0])[0]})
  elif kind=="random_chance_with_enchanted_bonus":out.append({"condition":"random_chance_with_looting","chance":c.get("unenchanted_chance",0),"looting_multiplier":c.get("enchanted_chance",{}).get("per_level_above_first",0)})
  elif kind=="entity_properties" and not c.get("predicate"):pass
  else:dropped_conditions[kind]+=1;out.append({"condition":"random_chance","chance":0})
 return out
def functions(values,entry):
 out=[]; component_data={}
 for f in values or []:
  kind=str(f.get("function","")).split(":")[-1]
  if kind=="set_components":component_data.update(f.get("components",{}));continue
  if kind=="set_count":out.append({"function":"set_count","count":number(f.get("count",1))})
  elif kind=="enchanted_count_increase":out.append({"function":"looting_enchant","count":number(f.get("count",1))})
  elif kind in ("furnace_smelt","set_name","set_lore","set_damage","set_potion"):out.append({k:v for k,v in f.items() if k not in ("conditions",) }|{"function":kind})
  else:dropped_functions[kind]+=1
 if component_data and entry.get("name"):entry["name"]=custom_item(entry["name"],component_data)
 return out
def entry(e):
 kind=str(e.get("type","item")).split(":")[-1];entry_types[kind]+=1
 if kind in ("alternatives","group"):
  children=[entry(x) for x in e.get("children",[])];children=[x for x in children if x]
  return {"type":"group","children":children,"weight":e.get("weight",1)} if children else None
 if kind=="empty":return {"type":"empty","weight":e.get("weight",1)}
 if kind not in ("item","loot_table"):return None
 name=e.get("name") or e.get("value"); out={"type":kind,"name":name,"weight":e.get("weight",1)}
 if kind=="loot_table" and name:
  relative=Path(name.split(":")[-1]+".json")
  if not (SOURCE/relative).exists() and len(source_by_stem.get(relative.stem,[]))==1:relative=source_by_stem[relative.stem][0]
  out["name"]="loot_tables/"+str(relative)
 fs=functions(e.get("functions"),out);cs=conditions(e.get("conditions"))
 if fs:out["functions"]=fs
 if cs:out["conditions"]=cs
 return out
converted=0
for p in sorted(SOURCE.rglob("*.json")):
 rel=p.relative_to(SOURCE)
 try:d=json.loads(p.read_text())
 except:empty.append(str(rel));d={"pools":[]}
 pools=[]
 for pool in d.get("pools",[]):
  entries=[entry(x) for x in pool.get("entries",[])];entries=[x for x in entries if x]
  if not entries:continue
  out={"rolls":number(pool.get("rolls",1)),"entries":entries};cs=conditions(pool.get("conditions"));
  if cs:out["conditions"]=cs
  pools.append(out)
 target=OUTPUT/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps({"pools":pools},indent=2)+"\n");converted+=1
ATLAS.write_text(json.dumps(atlas,indent=2)+"\n");text=LANG.read_text();begin="## BEGIN GENERATED MATCHA LOOT ITEMS";end="## END GENERATED MATCHA LOOT ITEMS"
if begin in text:text=text.split(begin,1)[0].rstrip()+"\n"+text.split(end,1)[1].lstrip()
LANG.write_text(text.rstrip()+"\n\n"+begin+"\n"+"\n".join(sorted(lang))+"\n"+end+"\n")
report={"baseline":baseline(),"source_tables":len(list(SOURCE.rglob('*.json'))),"converted_tables":converted,"generated_loot_items":len(custom),"empty_sources":empty,"entry_types":entry_types,"dropped_functions":dropped_functions,"dropped_conditions":dropped_conditions}
(ROOT/"docs/loot-conversion-report.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps({k:v for k,v in report.items() if k not in ('entry_types','dropped_functions','dropped_conditions')}))
