#!/usr/bin/env python3
"""Convert component-bearing crafting outputs into auditable Bedrock items."""
import argparse, copy, json, re, shutil
from pathlib import Path
from convert_recipes import convert, safe_name
from upstream import add_source_argument, validate_source

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
add_source_argument(parser)
args=parser.parse_args()
JAVA=validate_source(args.source)
SOURCE_DIRS=[JAVA/"data/crafting/recipe",JAVA/"data/food/recipe",JAVA/"data/custom_music/recipe",JAVA/"data/smithing_table/recipe"]
ITEMS=ROOT/"behavior_pack/items/generated_components"
RECIPES=ROOT/"behavior_pack/recipes/generated_components"
TEXTURES=ROOT/"resource_pack/textures/items/generated_components"
ATLAS=ROOT/"resource_pack/textures/item_texture.json"
LANG=ROOT/"resource_pack/texts/en_US.lang"
REPORT=ROOT/"docs/component-item-conversion-report.json"
BEGIN,END="## BEGIN GENERATED MATCHA COMPONENT ITEMS","## END GENERATED MATCHA COMPONENT ITEMS"
EXISTING={"crystal_heart":"matcha:heart_container","bronze_sword":"matcha:bronze_sword"}
CUSTOM_TEXTURE_STEMS={"dough","flour","warding_shield"}
ARMOR_SLOTS={"head":"slot.armor.head","chest":"slot.armor.chest","legs":"slot.armor.legs","feet":"slot.armor.feet"}
BEDROCK_RECORD_EVENTS={"golden":"record.11","labyrinthine":"record.cat"}
JUKEBOX_SONGS={}
for song_path in (JAVA/"data/main/jukebox_song").glob("*.json"):
    song=json.loads(song_path.read_text())
    event=BEDROCK_RECORD_EVENTS.get(song_path.stem)
    JUKEBOX_SONGS[f"main:{song_path.stem}"]={
        "comparator_signal":song.get("comparator_output",1),
        "duration":song.get("length_in_seconds",0),
        "sound_event":event,
    } if event else None

def reset(path,suffix,preserve=frozenset()):
    path.mkdir(parents=True,exist_ok=True)
    for p in path.glob("*"+suffix):
        if p.stem not in preserve: p.unlink()
def number_from_lore(c,symbol):
    for line in c.get("minecraft:lore",[]):
        text=line.get("text","") if isinstance(line,dict) else str(line)
        if symbol in text:
            m=re.search(r"-?\\d+(?:\\.\\d+)?",text)
            if m:return float(m.group())
def attr(c,kind):
    return next((x.get("amount") for x in c.get("minecraft:attribute_modifiers",[]) if x.get("type")==kind),None)
def display(c,stem,lang):
    n=c.get("minecraft:item_name")
    if isinstance(n,str): return n
    if isinstance(n,dict):
        if n.get("text"): return n["text"]
        translated=lang.get(n.get("translate"),"")
        if translated and not translated.startswith(("item.","tile.","entity.","%")): return translated
    return stem.replace("_"," ").title()
def replace_block(path,begin,end,entries):
    text=path.read_text()
    if begin in text:
        before=text.split(begin,1)[0].rstrip(); after=text.split(end,1)[1].lstrip()
        text=before+("\n"+after if after else "")
    path.write_text(text.rstrip()+"\n\n"+begin+"\n"+"\n".join(entries)+"\n"+end+"\n")

reset(ITEMS,".json"); reset(RECIPES,".json"); reset(TEXTURES,".png",CUSTOM_TEXTURE_STEMS)
lang=json.loads((JAVA/"assets/minecraft/lang/en_us.json").read_text())
atlas=json.loads(ATLAS.read_text())
atlas["texture_data"]={k:v for k,v in atlas["texture_data"].items() if not k.startswith("matcha_component_")}
names=[]; audit=[]; generated_ids={}
sources=[]
for p in sorted(x for directory in SOURCE_DIRS for x in directory.glob("*.json")):
    d=json.loads(p.read_text()); c=d.get("result",{}).get("components",{})
    if not c or "minecraft:consumable" in c or "minecraft:potion_contents" in c: continue
    if p.parent.parent.name=="smithing_table" and (ROOT/f"behavior_pack/items/generated_equipment/{p.stem}.json").exists():
        continue
    sources.append((p,d,c))

# Several Java recipes are alternate ways to obtain one component-defined
# item.  Give identical vanilla-id/component pairs one canonical Bedrock id.
def component_signature(d,c):
    return d["result"]["id"],json.dumps(c,sort_keys=True,separators=(",",":"))
def canonical_source(group):
    return min(group,key=lambda x:("_from_" in x[0].stem,len(x[0].stem),x[0].stem))
canonical_by_signature={}
groups={}
for entry in sources: groups.setdefault(component_signature(entry[1],entry[2]),[]).append(entry)
for signature,group in groups.items(): canonical_by_signature[signature]=canonical_source(group)[0].stem
for p,d,c in sources:
    source_name=str(p.relative_to(JAVA))
    model=(c.get("minecraft:item_model") or d["result"]["id"]).split(":",1)[-1]
    canonical=canonical_by_signature[component_signature(d,c)]
    stem=safe_name(canonical)
    ident=EXISTING.get(canonical,f"matcha:{stem}")
    generated_ids[p]=ident
    if any(x["item"]==ident and x["status"]=="generated" for x in audit):
        audit.append({"source":source_name,"item":ident,"status":"canonical_alias"}); continue
    if ident in EXISTING.values():
        audit.append({"source":source_name,"item":ident,"status":"existing_item_reused"}); continue
    texture_key=f"matcha_component_{stem}"
    source_texture=JAVA/f"assets/minecraft/textures/item/{model}.png"
    custom_texture=TEXTURES/f"{stem}.png"
    if custom_texture.exists():
        texture=f"textures/items/generated_components/{stem}"
    elif source_texture.exists():
        shutil.copy2(source_texture,TEXTURES/f"{stem}.png"); texture=f"textures/items/generated_components/{stem}"
    else: texture=d["result"]["id"].split(":",1)[-1]
    atlas["texture_data"][texture_key]={"textures":texture}
    components={"minecraft:display_name":{"value":f"item.{ident}.name"},
                "minecraft:icon":{"textures":{"default":texture_key}},
                "minecraft:max_stack_size":c.get("minecraft:max_stack_size",1 if c.get("minecraft:max_damage") else d["result"].get("count",64))}
    if stem in {"warding_stone","bedrock_buster"}:
        components["minecraft:interact_button"]="Place" if stem=="warding_stone" else "Prime"
        components["minecraft:use_animation"]="bow"
        components["minecraft:use_modifiers"]={"use_duration":0.1,"movement_modifier":1.0}
    if c.get("minecraft:max_damage"):
        components["minecraft:durability"]={"max_durability":c["minecraft:max_damage"]}
        if c.get("minecraft:unbreakable"):
            components["minecraft:durability"]["damage_chance"]={"min":0,"max":0}
    if c.get("minecraft:enchantment_glint_override") is not None:
        components["minecraft:glint"]=bool(c["minecraft:enchantment_glint_override"])
    if c.get("minecraft:fire_resistant"):
        components["minecraft:fire_resistant"]=True
    jukebox=c.get("minecraft:jukebox_playable")
    if JUKEBOX_SONGS.get(jukebox):
        components["minecraft:record"]=JUKEBOX_SONGS[jukebox]
    damage=attr(c,"minecraft:attack_damage")
    if damage is None: damage=number_from_lore(c,"🗡")
    if damage is not None:
        components["minecraft:damage"]=int(damage+1); components["minecraft:hand_equipped"]=True
    tool=c.get("minecraft:tool",{}); rules=tool.get("rules",[])
    if rules:
        converted=[]
        for rule in rules:
            tag=str(rule.get("blocks","#minecraft:mineable/pickaxe")).split("/")[-1]
            converted.append({"speed":int(rule.get("speed",1)),"block":{"tags":f"query.any_tag( '{tag}' )"}})
        components["minecraft:digger"]={"use_efficiency":True,"destroy_speeds":converted}
    eq=c.get("minecraft:equippable",{})
    if eq.get("slot") in ARMOR_SLOTS:
        protection=attr(c,"minecraft:armor") or number_from_lore(c,"⛊") or 0
        components["minecraft:wearable"]={"slot":ARMOR_SLOTS[eq["slot"]],"protection":int(protection)}
    repair=c.get("minecraft:repairable",{}).get("items")
    if repair and c.get("minecraft:max_damage"):
        repair_items=repair if isinstance(repair,list) else [repair]
        components["minecraft:repairable"]={"repair_items":[{"items":repair_items,"repair_amount":max(1,c["minecraft:max_damage"]//4)}]}
    item={"format_version":"1.21.100","minecraft:item":{"description":{"identifier":ident,"menu_category":{"category":"equipment" if c.get("minecraft:max_damage") else "items"}},"components":components}}
    (ITEMS/f"{stem}.json").write_text(json.dumps(item,indent=2)+"\n")
    names.append(f"item.{ident}.name={display(c,p.stem,lang)}")
    supported={"minecraft:item_name","minecraft:custom_name","minecraft:item_model","minecraft:max_stack_size","minecraft:max_damage","minecraft:attribute_modifiers","minecraft:tool","minecraft:equippable","minecraft:repairable","minecraft:lore","minecraft:tooltip_display","minecraft:enchantment_glint_override","minecraft:fire_resistant","minecraft:unbreakable","minecraft:rarity","minecraft:jukebox_playable"}
    audit.append({"source":source_name,"item":ident,"status":"generated","untranslated_components":sorted(set(c)-supported)})
for p,d,c in sources:
    ident=generated_ids[p]; recipe=copy.deepcopy(d); recipe["result"]={"id":ident,"count":d["result"].get("count",1)}
    if p.stem in {"lesser_warding_shield","warding_shield"}:
        recipe["base"] = "minecraft:shield"
    if p.stem == "stabilised_estus":
        recipe["key"]["E"] = "matcha:estus_ash"
    if ident in EXISTING.values() and (ROOT/f"behavior_pack/recipes/{p.stem}.json").exists():
        continue
    namespace=p.parent.parent.name
    for i,out in enumerate(convert(recipe,namespace,f"component_{p.stem}")):
        suffix=f"_v{i+1}" if i else ""
        (RECIPES/f"{p.stem}{suffix}.json").write_text(json.dumps(out,indent=2)+"\n")
ATLAS.write_text(json.dumps(atlas,indent=2)+"\n"); replace_block(LANG,BEGIN,END,sorted(names))
report={"source_component_item_recipes":len(sources),"custom_items_generated":sum(x["status"]=="generated" for x in audit),
        "existing_items_reused":sum(x["status"]!="generated" for x in audit),"recipe_files_generated":len(list(RECIPES.glob("*.json"))),"items":audit}
REPORT.write_text(json.dumps(report,indent=2)+"\n")
give=["# Generated component-item test kit"]+[f"give @s {item['item']} 1" for item in audit if item["status"]=="generated"]
(ROOT/"behavior_pack/functions/matcha_component_items_test.mcfunction").write_text("\n".join(give)+"\n")
print(json.dumps({k:v for k,v in report.items() if k!="items"}))
