#!/usr/bin/env python3
"""Convert all pinned Java loot tables into safe Bedrock loot definitions."""
import argparse, copy, hashlib, json, math, shutil
from collections import Counter
from fractions import Fraction
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
atlas=json.loads(ATLAS.read_text()); stale_atlas_keys={k for k in atlas["texture_data"] if k.startswith("matcha_loot_")}
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
custom={}; lang=[]; translated_functions=Counter(); approximated_functions=Counter(); dropped_functions=Counter(); dropped_conditions=Counter(); entry_types=Counter(); empty=[]
generated_tables={}; approximation_details=Counter(); CURRENT_TABLE=""
def note_approximation(function,strategy):approximation_details[(CURRENT_TABLE,function,strategy)]+=1
def display(c,base):
 v=c.get("minecraft:item_name") or c.get("minecraft:custom_name")
 if isinstance(v,str):return v
 if isinstance(v,dict):
  if v.get("text"):return v["text"]
  translation=v.get("translate")
  if translation in source_lang:return source_lang[translation]
  model=str(c.get("minecraft:item_model","")).split(":")[-1]
  fallback=model or str(translation or "").rsplit(".",1)[-1]
  if fallback:return fallback.replace("_"," ").title()
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
 atlas["texture_data"][key]={"textures":texture};stale_atlas_keys.discard(key);comps={"minecraft:display_name":{"value":f"item.{ident}.name"},"minecraft:icon":{"textures":{"default":key}},"minecraft:max_stack_size":c.get("minecraft:max_stack_size",1 if c.get("minecraft:max_damage") else 64)}
 if model in {"cheerful_clay_statue","mournful_clay_statue"}:
  comps["minecraft:interact_button"]="Use";comps["minecraft:use_animation"]="bow";comps["minecraft:use_modifiers"]={"use_duration":0.1,"movement_modifier":1.0}
 if c.get("minecraft:max_damage"):comps["minecraft:durability"]={"max_durability":c["minecraft:max_damage"]}
 if c.get("minecraft:enchantment_glint_override") or c.get("minecraft:enchantments") or c.get("minecraft:stored_enchantments"):comps["minecraft:glint"]=True
 item={"format_version":"1.21.100","minecraft:item":{"description":{"identifier":ident,"menu_category":{"category":"items"}},"components":comps}}
 (ITEMS/f"{h}.json").write_text(json.dumps(item,indent=2)+"\n");lang.append(f"item.{ident}.name={display(c,base)}");return ident
def number(v):
 if isinstance(v,(int,float)):return v
 if isinstance(v,dict):return {k:v[k] for k in ("min","max") if k in v}
 return 1
def integer_values(v):
 n=number(v)
 if isinstance(n,dict):return list(range(int(n.get("min",1)),int(n.get("max",n.get("min",1)))+1))
 return [int(n)]
def weighted_entries(item,distribution,extra_functions):
 weights={count:max(1,round(float(chance)*100000)) for count,chance in distribution.items() if chance>0};common=0
 for weight in weights.values():common=math.gcd(common,weight)
 entries=[]
 for count,weight in sorted(weights.items()):
  if count<=0:entries.append({"type":"empty","weight":weight//common})
  else:
   fs=[{"function":"set_count","count":count}]+copy.deepcopy(extra_functions)
   entries.append({"type":"item","name":item,"weight":weight//common,"functions":fs})
 return entries
def fortune_distribution(source_functions,apply,level):
 count_fn=next((f for f in source_functions if str(f.get("function","")).endswith("set_count")),None)
 bases=integer_values(count_fn.get("count",1) if count_fn else 1);formula=str(apply.get("formula","")).split(":")[-1];out=Counter()
 if formula=="uniform_bonus_count":
  maximum=int(apply.get("parameters",{}).get("bonusMultiplier",1))*level
  bonuses={x:Fraction(1,maximum+1) for x in range(maximum+1)}
 elif formula=="binomial_with_bonus_count":
  params=apply.get("parameters",{});trials=level+int(params.get("extra",0));p=Fraction(str(params.get("probability",0))).limit_denominator(1000000)
  bonuses={x:Fraction(math.comb(trials,x))*p**x*(1-p)**(trials-x) for x in range(trials+1)}
 else:
  # Java ore_drops chooses max(0, random[0..level+1]-1)+1 as a multiplier.
  bonuses={0:Fraction(2,level+2)}
  for multiplier in range(2,level+1):bonuses[multiplier-1]=Fraction(1,level+2)
  bonuses[level]=Fraction(1,level+2)
 cap=next((int(f.get("limit",{}).get("max")) for f in source_functions if str(f.get("function","")).endswith("limit_count") and f.get("limit",{}).get("max") is not None),None)
 for base in bases:
  for bonus,chance in bonuses.items():
   extra=base*bonus if formula=="ore_drops" else bonus
   if cap is not None:extra=min(extra,max(0,cap-max(bases)))
   out[extra]+=Fraction(1,len(bases))*chance
 return out
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
def functions(values,entry,track=True):
 out=[]; component_data={}
 for f in values or []:
  kind=str(f.get("function","")).split(":")[-1]
  if kind=="set_components":component_data.update(f.get("components",{}));continue
  if kind=="set_count":out.append({"function":"set_count","count":number(f.get("count",1))})
  elif kind=="enchanted_count_increase":out.append({"function":"looting_enchant","count":number(f.get("count",1))})
  elif kind in ("furnace_smelt","set_name","set_lore","set_damage","set_potion"):out.append({k:v for k,v in f.items() if k not in ("conditions",) }|{"function":kind})
  elif kind=="explosion_decay":
   out.append({"function":"explosion_decay"});translated_functions[kind]+=int(track)
  elif kind=="enchant_with_levels":
   # Bedrock supports the enchanting-table algorithm but uses a treasure flag
   # instead of Java's enchantment option tag.
   options=f.get("options")
   out.append({"function":"enchant_with_levels","levels":number(f.get("levels",1)),"treasure":options=="#minecraft:on_random_loot"})
   approximated_functions[kind]+=int(track)
   if track:note_approximation(kind,"Bedrock enchanting-table algorithm preserves levels; Java option tag becomes the treasure flag")
  elif kind=="enchant_randomly" and f.get("options")=="#minecraft:on_random_loot":
   out.append({"function":"enchant_randomly","treasure":True});approximated_functions[kind]+=int(track)
   if track:note_approximation(kind,"Bedrock enchant_randomly with treasure enabled replaces Java #minecraft:on_random_loot")
  elif kind=="enchant_randomly" and f.get("options")=="#minecraft:in_enchanting_table":
   out.append({"function":"enchant_randomly","treasure":False});approximated_functions[kind]+=int(track)
   if track:note_approximation(kind,"Bedrock enchant_randomly with treasure disabled replaces Java #minecraft:in_enchanting_table")
  elif kind=="enchant_randomly" and isinstance(f.get("options"),str):
   enchantment=f["options"].split(":")[-1];out.append({"function":"specific_enchants","enchants":[enchantment]});approximated_functions[kind]+=int(track)
   if track:note_approximation(kind,"single Java option routed through Bedrock specific_enchants")
  elif kind=="set_stew_effect":
   effects=[]
   for effect in f.get("effects",[]):
    effects.append({"type":str(effect.get("type","")).split(":")[-1],"duration":number(effect.get("duration",1))})
   out.append({"function":"set_stew_effect","effects":effects});translated_functions[kind]+=int(track)
  elif kind=="exploration_map":
   # Every source occurrence is the buried-treasure map used by shipwrecks or
   # underwater ruins; Bedrock expresses the target as a destination string.
   out.append({"function":"exploration_map","destination":"buriedtreasure"});approximated_functions[kind]+=int(track)
   if track:note_approximation(kind,"source map context mapped to Bedrock buriedtreasure destination")
  elif kind=="set_ominous_bottle_amplifier":
   out.append({"function":"set_ominous_bottle_amplifier","amplifier":number(f.get("amplifier",0))});translated_functions[kind]+=int(track)
  elif kind=="set_enchantments":
   enchants=[{"id":str(ident).split(":")[-1],"level":level} for ident,level in f.get("enchantments",{}).items()]
   out.append({"function":"specific_enchants","enchants":enchants});translated_functions[kind]+=int(track)
  elif kind=="set_contents":
   entries=f.get("entries",[]);value=entries[0].get("value","") if len(entries)==1 and entries[0].get("type","").endswith("loot_table") else ""
   if value:
    out.append({"function":"fill_container","loot_table":"loot_tables/"+value.split(":")[-1]+".json"});approximated_functions[kind]+=int(track)
    if track:note_approximation(kind,"single Java container entry mapped to Bedrock fill_container")
   else:dropped_functions[kind]+=1
  else:dropped_functions[kind]+=1
 if component_data and entry.get("name"):entry["name"]=custom_item(entry["name"],component_data)
 return out
def entry(e,track=True):
 kind=str(e.get("type","item")).split(":")[-1]
 if track:entry_types[kind]+=1
 if kind in ("alternatives","group"):
  children=[entry(x,track) for x in e.get("children",[])];children=[x for x in children if x]
  return {"type":"group","children":children,"weight":e.get("weight",1)} if children else None
 if kind=="empty":return {"type":"empty","weight":e.get("weight",1)}
 if kind not in ("item","loot_table"):return None
 functions_in=e.get("functions") or []
 option_function=next((f for f in functions_in if str(f.get("function","")).endswith("enchant_randomly") and isinstance(f.get("options"),list)),None)
 if kind=="item" and option_function:
  variants=[]
  for enchantment in option_function["options"]:
   clone=copy.deepcopy(e);clone.pop("conditions",None);clone["weight"]=1
   for f in clone.get("functions",[]):
    if str(f.get("function","")).endswith("enchant_randomly") and isinstance(f.get("options"),list):f["options"]=enchantment
   variants.append(entry(clone,False))
  digest=hashlib.sha1((CURRENT_TABLE+json.dumps(option_function["options"],sort_keys=True)).encode()).hexdigest()[:12];relative=f"generated/enchant_options/{digest}.json"
  generated_tables[relative]={"pools":[{"rolls":1,"entries":variants}]};approximated_functions["enchant_randomly"]+=1;note_approximation("enchant_randomly","restricted Java option list expanded into an equal-weight Bedrock helper table")
  out={"type":"loot_table","name":"loot_tables/"+relative,"weight":e.get("weight",1)};cs=conditions(e.get("conditions"))
  if cs:out["conditions"]=cs
  return out
 apply=next((f for f in functions_in if str(f.get("function","")).endswith("apply_bonus")),None)
 if kind=="item" and apply:
  clone=copy.deepcopy(e);clone.pop("conditions",None);clone["weight"]=1;clone["functions"]=[f for f in functions_in if not str(f.get("function","")).endswith(("apply_bonus","limit_count"))]
  base=entry(clone,False);extra_functions=[{"function":"explosion_decay"}] if any(str(f.get("function","")).endswith("explosion_decay") for f in functions_in) else []
  if extra_functions:translated_functions["explosion_decay"]+=1
  pools=[{"rolls":1,"entries":[base]}]
  for level in (1,2,3):
   pools.append({"rolls":1,"conditions":[{"condition":"match_tool","enchantments":[{"enchantment":"fortune","levels":{"min":level,"max":level}}]}],"entries":weighted_entries(base["name"],fortune_distribution(functions_in,apply,level),extra_functions)})
  digest=hashlib.sha1((CURRENT_TABLE+json.dumps(e,sort_keys=True)).encode()).hexdigest()[:12];relative=f"generated/fortune/{digest}.json";generated_tables[relative]={"pools":pools}
  approximated_functions["apply_bonus"]+=1
  if any(str(f.get("function","")).endswith("limit_count") for f in functions_in):approximated_functions["limit_count"]+=1
  note_approximation("apply_bonus","Java Fortune formula emitted as exact-level weighted bonus pools; randomized base and bonus samples are independent")
  if any(str(f.get("function","")).endswith("limit_count") for f in functions_in):note_approximation("limit_count","Fortune bonus clipped against the maximum possible base count so combined melon output cannot exceed nine")
  out={"type":"loot_table","name":"loot_tables/"+relative,"weight":e.get("weight",1)};cs=conditions(e.get("conditions"))
  if cs:out["conditions"]=cs
  return out
 name=e.get("name") or e.get("value"); out={"type":kind,"name":name,"weight":e.get("weight",1)}
 if kind=="loot_table" and name:
  relative=Path(name.split(":")[-1]+".json")
  if not (SOURCE/relative).exists() and len(source_by_stem.get(relative.stem,[]))==1:relative=source_by_stem[relative.stem][0]
  out["name"]="loot_tables/"+str(relative)
 fs=functions(e.get("functions"),out,track);cs=conditions(e.get("conditions"))
 if fs:out["functions"]=fs
 if cs:out["conditions"]=cs
 return out
converted=0
for p in sorted(SOURCE.rglob("*.json")):
 rel=p.relative_to(SOURCE);CURRENT_TABLE=str(rel)
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
for relative,data in generated_tables.items():
 target=OUTPUT/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(data,indent=2)+"\n")
for key in stale_atlas_keys:del atlas["texture_data"][key]
ATLAS.write_text(json.dumps(atlas,indent=2)+"\n");text=LANG.read_text();begin="## BEGIN GENERATED MATCHA LOOT ITEMS";end="## END GENERATED MATCHA LOOT ITEMS";section=begin+"\n"+"\n".join(sorted(lang))+"\n"+end
if begin in text:
 prefix=text.split(begin,1)[0].rstrip();suffix=text.split(end,1)[1].lstrip();text=prefix+"\n"+section+("\n\n"+suffix if suffix else "\n")
else:text=text.rstrip()+"\n\n"+section+"\n"
LANG.write_text(text)
approximation_rows=[{"source_table":table,"function":function,"strategy":strategy,"occurrences":count} for (table,function,strategy),count in sorted(approximation_details.items())]
report={"baseline":baseline(),"source_tables":len(list(SOURCE.rglob('*.json'))),"converted_tables":converted,"generated_helper_tables":len(generated_tables),"generated_loot_items":len(custom),"empty_sources":empty,"entry_types":entry_types,"translated_functions":translated_functions,"approximated_functions":approximated_functions,"dropped_functions":dropped_functions,"dropped_conditions":dropped_conditions,"approximation_details":approximation_rows}
(ROOT/"docs/loot-conversion-report.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps({k:v for k,v in report.items() if k not in ('entry_types','dropped_functions','dropped_conditions')}))
