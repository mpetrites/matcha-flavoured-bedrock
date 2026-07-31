#!/usr/bin/env python3
"""Generate Bedrock equipment from a reusable tier definition."""
import json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "work" / "java-source-104" / "assets" / "minecraft" / "textures" / "item"
ITEMS = ROOT / "behavior_pack/items/generated_equipment"
RECIPES = ROOT / "behavior_pack/recipes/generated_equipment"
TEXTURES = ROOT / "resource_pack/textures/items/generated_equipment"
ATLAS = ROOT / "resource_pack/textures/item_texture.json"
LANG = ROOT / "resource_pack/texts/en_US.lang"
BEGIN, END = "## BEGIN GENERATED MATCHA EQUIPMENT", "## END GENERATED MATCHA EQUIPMENT"

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")

def main():
    tier_path = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "equipment_tiers/bronze.json")
    spec = json.loads(tier_path.read_text())
    ITEMS.mkdir(parents=True, exist_ok=True); RECIPES.mkdir(parents=True, exist_ok=True); TEXTURES.mkdir(parents=True, exist_ok=True)
    atlas = json.loads(ATLAS.read_text())
    lang = []
    for item in spec["items"]:
        name, ident = item["name"], f"matcha:{spec['tier']}_{item['name']}"
        key = f"matcha_{spec['tier']}_{name}"
        components = {
            "minecraft:display_name": {"value": f"item.{ident}.name"},
            "minecraft:icon": {"textures": {"default": key}},
            "minecraft:max_stack_size": 1,
            "minecraft:durability": {"max_durability": item["durability"]}
        }
        if "damage" in item:
            components.update({"minecraft:hand_equipped": True, "minecraft:damage": item["damage"],
                               "minecraft:enchantable": {"slot": item["enchant"], "value": 12}})
        if "mining" in item:
            components["minecraft:digger"] = {"use_efficiency": True, "destroy_speeds": item["mining"]}
        if "armor" in item:
            components["minecraft:wearable"] = item["armor"]
            armor_enchants = {"helmet":"armor_head","chestplate":"armor_torso","leggings":"armor_legs","boots":"armor_feet"}
            components["minecraft:enchantable"] = {"slot": armor_enchants[item["name"]], "value": 12}
        repair = item.get("repair", spec["repair"])
        components["minecraft:repairable"] = {"repair_items": [{"items": repair["items"], "repair_amount": repair["amount"]}]}
        out = {"format_version": spec["format_version"], "minecraft:item": {"description": {
            "identifier": ident, "menu_category": {"category": "equipment", "group": f"itemGroup.name.{item['group']}"}
        }, "components": components}}
        dump(ITEMS / f"{spec['tier']}_{name}.json", out)
        if item.get("recipe"):
            rec = item["recipe"]
            dump(RECIPES / f"{spec['tier']}_{name}.json", {"format_version": spec["format_version"],
                "minecraft:recipe_smithing_transform": {"description": {"identifier": ident}, "tags": ["smithing_table"],
                "template": rec["template"], "base": rec["base"], "addition": rec["addition"], "result": ident}})
        texture = SOURCE / f"{spec['tier']}_{name}.png"
        if not texture.exists(): raise SystemExit(f"Missing source texture: {texture}")
        shutil.copy2(texture, TEXTURES / texture.name)
        atlas["texture_data"][key] = {"textures": f"textures/items/generated_equipment/{spec['tier']}_{name}"}
        lang.append(f"item.{ident}.name={item['display']}")
    dump(ATLAS, atlas)
    text = LANG.read_text().rstrip()
    if BEGIN in text: text = text[:text.index(BEGIN)].rstrip()
    LANG.write_text(text + "\n\n" + BEGIN + "\n" + "\n".join(lang) + "\n" + END + "\n")
    give = ["# Generated Bronze equipment test kit"] + [f"give @s matcha:bronze_{x['name']} 1" for x in spec["items"]]
    give += ["give @s minecraft:copper_ingot 64", "give @s minecraft:phantom_membrane 64", "give @s minecraft:netherite_upgrade_smithing_template 2", "give @s minecraft:anvil 1", "give @s minecraft:smithing_table 1"]
    (ROOT / "behavior_pack/functions/matcha_bronze_equipment_test.mcfunction").write_text("\n".join(give) + "\n")
    print(f"Generated {len(spec['items'])} {spec['tier']} equipment items")

if __name__ == "__main__": main()
