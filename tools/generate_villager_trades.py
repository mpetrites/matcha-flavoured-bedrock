#!/usr/bin/env python3
"""Generate the complete Script-API villager economy from Java 1.03."""
import argparse, hashlib, json, shutil
from pathlib import Path
from upstream import add_source_argument, baseline, validate_source

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(); add_source_argument(parser); JAVA=validate_source(parser.parse_args().source)
ITEMS=ROOT/"behavior_pack/items/generated_trades"; TEXTURES=ROOT/"resource_pack/textures/items/generated_trades"
ATLAS=ROOT/"resource_pack/textures/item_texture.json"; LANG=ROOT/"resource_pack/texts/en_US.lang"
for directory in (ITEMS,TEXTURES):
    directory.mkdir(parents=True,exist_ok=True)
    for path in directory.iterdir():
        if path.is_file(): path.unlink()
source_lang=json.loads((JAVA/"assets/minecraft/lang/en_us.json").read_text())
atlas=json.loads(ATLAS.read_text()); atlas["texture_data"]={k:v for k,v in atlas["texture_data"].items() if not k.startswith("matcha_trade_")}

# Existing generated items are preferred whenever a trade stack uses their model.
model_to_item={}
for path in (ROOT/"behavior_pack/items").rglob("*.json"):
    if path.parent==ITEMS or " " in path.stem: continue
    try: identifier=json.loads(path.read_text())["minecraft:item"]["description"]["identifier"]
    except Exception: continue
    model_to_item[path.stem]=identifier
model_to_item.update({"heart_container":"matcha:heart_container","crystal_heart":"matcha:heart_container"})
custom_by_signature={}; custom_audit=[]; lang=[]

def component_name(components, fallback):
    value=components.get("minecraft:item_name") or components.get("minecraft:custom_name")
    if isinstance(value,str): return value
    if isinstance(value,dict): return value.get("text") or source_lang.get(value.get("translate"),value.get("translate"))
    return fallback.replace("minecraft:","").replace("_"," ").title()

def resolve_stack(stack, context):
    base=stack["id"]; count=stack.get("count",1); components=stack.get("components") or {}
    if not components: return {"item":base,"count":count,"name":base.split(":")[-1].replace("_"," ").title()}
    signature=base+"|"+json.dumps(components,sort_keys=True,separators=(",",":"))
    model=str(components.get("minecraft:item_model","")).split(":")[-1]
    identifier=model_to_item.get(model)
    if not identifier:
        identifier=custom_by_signature.get(signature)
    if not identifier:
        digest=hashlib.sha1(signature.encode()).hexdigest()[:10]; identifier=f"matcha:trade_item_{digest}"; custom_by_signature[signature]=identifier
        stem=identifier.split(":")[1]; key=f"matcha_trade_{digest}"; texture_source=JAVA/f"assets/minecraft/textures/item/{model}.png"
        if model and texture_source.exists(): shutil.copy2(texture_source,TEXTURES/f"{digest}.png"); texture=f"textures/items/generated_trades/{digest}"
        else: texture=f"textures/items/{base.split(':')[-1]}"
        atlas["texture_data"][key]={"textures":texture}; name=component_name(components,base)
        item_components={"minecraft:display_name":{"value":f"item.{identifier}.name"},"minecraft:icon":{"textures":{"default":key}},"minecraft:max_stack_size":components.get("minecraft:max_stack_size",64)}
        if components.get("minecraft:max_damage"): item_components["minecraft:durability"]={"max_durability":components["minecraft:max_damage"]}; item_components["minecraft:max_stack_size"]=1
        if components.get("minecraft:enchantment_glint_override") or components.get("minecraft:enchantments") or components.get("minecraft:stored_enchantments"): item_components["minecraft:glint"]=True
        item={"format_version":"1.21.100","minecraft:item":{"description":{"identifier":identifier,"menu_category":{"category":"items"}},"components":item_components}}
        (ITEMS/f"{digest}.json").write_text(json.dumps(item,indent=2)+"\n"); lang.append(f"item.{identifier}.name={name}")
        supported={"minecraft:item_name","minecraft:custom_name","minecraft:item_model","minecraft:max_stack_size","minecraft:max_damage","minecraft:enchantment_glint_override","minecraft:rarity","minecraft:lore","minecraft:tooltip_display"}
        custom_audit.append({"identifier":identifier,"contexts":[context],"untranslated_components":sorted(set(components)-supported)})
    else:
        for row in custom_audit:
            if row["identifier"]==identifier and context not in row["contexts"]: row["contexts"].append(context)
    return {"item":identifier,"count":count,"name":component_name(components,base)}

trades={}; trade_root=JAVA/"data/minecraft/villager_trade"
for path in sorted(trade_root.rglob("*.json")):
    rel=path.relative_to(trade_root).with_suffix(""); trade_id=str(rel)
    source=json.loads(path.read_text()); discard=any(x.get("function")=="minecraft:discard" for x in source.get("given_item_modifiers",[]))
    trades[trade_id]={"id":trade_id,"profession":rel.parts[0],"level":int(rel.parts[1]) if rel.parts[1].isdigit() else 1,
        "wants":resolve_stack(source["wants"],trade_id+":wants"),"gives":resolve_stack(source["gives"],trade_id+":gives"),
        "maxUses":source.get("max_uses",16),"xp":source.get("xp",0),"reputationDiscount":source.get("reputation_discount",0),"discard":discard,
        "modifiers":[x.get("function","").split(":")[-1] for x in source.get("given_item_modifiers",[])]}

sets={}; set_root=JAVA/"data/minecraft/trade_set"; tag_root=JAVA/"data/minecraft/tags/villager_trade"
for path in sorted(set_root.rglob("*.json")):
    rel=path.relative_to(set_root).with_suffix(""); source=json.loads(path.read_text()); tag=source["trades"].split(":",1)[-1]
    members=json.loads((tag_root/f"{tag}.json").read_text()).get("values",[])
    members=[value.split(":",1)[-1] for value in members]
    sets[str(rel)]={"profession":rel.parts[0],"level":int(rel.stem.split("_")[-1]) if rel.stem.startswith("level_") else 1,
                    "amount":int(source["amount"]),"trades":members}

data="// Generated by tools/generate_villager_trades.py; do not edit.\n"
data+=f"export const MATCHA_TRADES = {json.dumps(trades,indent=2)};\nexport const MATCHA_TRADE_SETS = {json.dumps(sets,indent=2)};\n"
(ROOT/"behavior_pack/scripts/villager_trade_data.js").write_text(data)
text=LANG.read_text(); begin="## BEGIN GENERATED MATCHA TRADE ITEMS"; end="## END GENERATED MATCHA TRADE ITEMS"
if begin in text: text=text.split(begin,1)[0].rstrip()+"\n"+text.split(end,1)[1].lstrip()
LANG.write_text(text.rstrip()+"\n\n"+begin+"\n"+"\n".join(sorted(lang))+"\n"+end+"\n"); ATLAS.write_text(json.dumps(atlas,indent=2)+"\n")
report={"baseline":baseline(),"source_trades":len(trades),"source_trade_sets":len(sets),"generated_trade_items":len(custom_audit),"discard_entries":sum(x["discard"] for x in trades.values()),"component_audit":custom_audit}
(ROOT/"docs/villager-trade-report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({k:v for k,v in report.items() if k!="component_audit"}))
