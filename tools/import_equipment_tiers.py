#!/usr/bin/env python3
"""Extract reusable tier definitions from Matcha's Java smithing recipes."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT.parent / "work/java-source-104"
RECIPES = JAVA / "data/smithing_table/recipe"
LANG = json.loads((JAVA / "assets/minecraft/lang/en_us.json").read_text())
OUT = Path(__file__).parent / "equipment_tiers"
TIERS = ("steel", "shakudo", "electrum", "adamant")
TOOL_TAGS = {
    "axe": ("axe", "query.any_tag( 'wood' )"),
    "pickaxe": ("pickaxe", "query.any_tag( 'stone', 'metal' )"),
    "shovel": ("shovel", "query.any_tag( 'dirt', 'sand', 'gravel', 'snow' )"),
    "hoe": ("hoe", "query.any_tag( 'plant', 'leaves' )"),
    "mattock": ("hoe", "query.any_tag( 'plant', 'leaves', 'dirt', 'sand', 'gravel', 'snow' )"),
    "dolabra": ("axe", "query.any_tag( 'wood', 'stone', 'metal' )"),
}
GROUPS = {"spear":"sword", "sword":"sword", "claymore":"sword", "shears":"shears"}
ARMOR = {"helmet":("slot.armor.head","armor_head"),"chestplate":("slot.armor.chest","armor_torso"),
         "leggings":("slot.armor.legs","armor_legs"),"boots":("slot.armor.feet","armor_feet")}

def lore_number(components, symbol):
    for line in components.get("minecraft:lore", []):
        text = line.get("text", "") if isinstance(line, dict) else str(line)
        if symbol in text:
            found = re.search(r"(-?\\d+(?:\\.\\d+)?)", text)
            if found: return float(found.group(1))

def attr(components, kind):
    return next((x.get("amount") for x in components.get("minecraft:attribute_modifiers", [])
                 if x.get("type")==kind), None)

for tier in TIERS:
    items=[]; tier_repair=None
    for path in sorted(RECIPES.glob(f"{tier}_*.json")):
        source=json.loads(path.read_text()); c=source["result"]["components"]; name=path.stem[len(tier)+1:]
        if name not in set(TOOL_TAGS)|set(GROUPS)|set(ARMOR): continue
        repair=c.get("minecraft:repairable",{}).get("items") or {
            "steel":["minecraft:iron_ingot"],"shakudo":["minecraft:copper_ingot"],
            "electrum":["minecraft:diamond","minecraft:gold_ingot"],
            "adamant":["minecraft:diamond_block","minecraft:gold_block"]
        }[tier]
        durability=c["minecraft:max_damage"]
        item={"name":name,"display":LANG.get(c.get("minecraft:item_name",{}).get("translate",""),path.stem.replace("_"," ").title()),
              "durability":durability,"group":GROUPS.get(name,name),
              "texture":(c.get("minecraft:item_model") or source["result"]["id"]).split(":",1)[-1],
              "repair":{"items":repair,"amount":max(1,durability//4)},
              "recipe":{"template":source["template"],"base":source["base"],
                        "addition":source["addition"] if ":" in source["addition"] else "minecraft:"+source["addition"]},
              "source_enchantments":c.get("minecraft:enchantments",{})}
        if name in ARMOR:
            protection=attr(c,"minecraft:armor") or lore_number(c,"⛊") or {"helmet":3,"chestplate":8,"leggings":6,"boots":3}[name]
            item["armor"]={"slot":ARMOR[name][0],"protection":int(protection)}
        else:
            damage=attr(c,"minecraft:attack_damage")
            if damage is None: damage=lore_number(c,"🗡")
            item["damage"]=int((damage or 0)+1)
            item["enchant"]=TOOL_TAGS.get(name,(name,None))[0] if name not in ("claymore",) else "sword"
            attack_speed=attr(c,"minecraft:attack_speed")
            if attack_speed is not None and 4+attack_speed>0:
                item["attack_cooldown"]=round(1/(4+attack_speed),4)
            if name in TOOL_TAGS:
                rules=c.get("minecraft:tool",{}).get("rules",[])
                speed=rules[0].get("speed",1) if rules else 1
                item["mining"]=[{"speed":speed,"block":{"tags":TOOL_TAGS[name][1]}}]
        items.append(item)
    spec={"tier":tier,"format_version":"1.21.130","repair":{"items":items[0]["repair"]["items"],"amount":items[0]["repair"]["amount"]},"items":items}
    (OUT/f"{tier}.json").write_text(json.dumps(spec,indent=2)+"\n")
    print(tier,len(items))
