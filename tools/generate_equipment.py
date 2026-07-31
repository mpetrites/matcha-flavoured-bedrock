#!/usr/bin/env python3
"""Generate Bedrock equipment from a reusable tier definition."""
import argparse, json, shutil
from pathlib import Path
from upstream import add_source_argument, validate_source

ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "behavior_pack/items/generated_equipment"
RECIPES = ROOT / "behavior_pack/recipes/generated_equipment"
TEXTURES = ROOT / "resource_pack/textures/items/generated_equipment"
ATTACHABLES = ROOT / "resource_pack/attachables/generated_equipment"
ARMOR_TEXTURES = ROOT / "resource_pack/textures/models/armor"
ATLAS = ROOT / "resource_pack/textures/item_texture.json"
LANG = ROOT / "resource_pack/texts/en_US.lang"
BEGIN, END = "## BEGIN GENERATED MATCHA EQUIPMENT", "## END GENERATED MATCHA EQUIPMENT"

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")

def main():
    parser=argparse.ArgumentParser(); add_source_argument(parser)
    parser.add_argument("tiers",nargs="*",type=Path)
    args=parser.parse_args(); java=validate_source(args.source)
    source_textures=java / "assets/minecraft/textures/item"
    armor_source_textures=java / "assets/minecraft/textures/entity/equipment"
    tier_paths = args.tiers or sorted((Path(__file__).parent / "equipment_tiers").glob("*.json"))
    ITEMS.mkdir(parents=True, exist_ok=True); RECIPES.mkdir(parents=True, exist_ok=True); TEXTURES.mkdir(parents=True, exist_ok=True)
    ATTACHABLES.mkdir(parents=True, exist_ok=True); ARMOR_TEXTURES.mkdir(parents=True, exist_ok=True)
    atlas = json.loads(ATLAS.read_text())
    lang = []
    generated = []
    for tier_path in tier_paths:
        spec = json.loads(tier_path.read_text())
        for item in spec["items"]:
            name, ident = item["name"], f"matcha:{spec['tier']}_{item['name']}"
            key = f"matcha_{spec['tier']}_{name}"
            components = {
                "minecraft:display_name": {"value": f"item.{ident}.name"},
                "minecraft:icon": {"textures": {"default": key}},
                "minecraft:max_stack_size": 1,
                "minecraft:durability": {"max_durability": item["durability"]}
            }
            if item.get("source_enchantments"):
                # Bedrock cannot store arbitrary Java enchantments. Preserve
                # their enchanted presentation while the script layer applies
                # the pinned source effects.
                components["minecraft:glint"] = True
            if "damage" in item:
                components.update({"minecraft:hand_equipped": True, "minecraft:damage": item["damage"],
                                   "minecraft:enchantable": {"slot": item["enchant"], "value": item.get("enchantability", 12)}})
                if item.get("attack_cooldown"):
                    components["minecraft:cooldown"] = {
                        "category": f"matcha_{spec['tier']}_{name}",
                        "duration": item["attack_cooldown"], "type": "attack"
                    }
                    components["minecraft:swing_duration"] = {"value": min(item["attack_cooldown"], 1.0)}
            if name == "spear":
                components["minecraft:kinetic_weapon"] = {
                    "damage_conditions": {"min_speed": 0.1},
                    "damage_multiplier": 4.0, "damage_modifier": item["damage"],
                    "delay": 2, "hitbox_margin": 0.35, "reach": {"min": 0, "max": 4.5}
                }
                components["minecraft:use_modifiers"] = {"use_duration": 72000, "movement_modifier": 1.0}
                components["minecraft:use_animation"] = "spear"
            if "mining" in item:
                components["minecraft:digger"] = {"use_efficiency": True, "destroy_speeds": item["mining"]}
            if "armor" in item:
                components["minecraft:wearable"] = item["armor"]
                armor_enchants = {"helmet":"armor_head","chestplate":"armor_torso","leggings":"armor_legs","boots":"armor_feet"}
                components["minecraft:enchantable"] = {"slot": armor_enchants[item["name"]], "value": item.get("enchantability", 12)}
            repair = item.get("repair", spec["repair"])
            components["minecraft:repairable"] = {"repair_items": [{"items": repair["items"], "repair_amount": repair["amount"]}]}
            out = {"format_version": spec["format_version"], "minecraft:item": {"description": {
                "identifier": ident, "menu_category": {"category": "equipment", "group": f"minecraft:itemGroup.name.{item['group']}"}
            }, "components": components}}
            dump(ITEMS / f"{spec['tier']}_{name}.json", out)
            if "armor" in item:
                layer = 2 if name == "leggings" else 1
                source_tier = "netherite" if spec["tier"] == "adamant" else spec["tier"]
                source_dir = "humanoid_leggings" if layer == 2 else "humanoid"
                armor_source = armor_source_textures / source_dir / f"{source_tier}.png"
                if armor_source.exists(): shutil.copy2(armor_source, ARMOR_TEXTURES / f"{spec['tier']}_{layer}.png")
                geometry = {"helmet":"helmet","chestplate":"chestplate","leggings":"leggings","boots":"boots"}[name]
                variable = {"helmet":"helmet","chestplate":"chest","leggings":"leg","boots":"boot"}[name]
                attachable = {"format_version":"1.20.60","minecraft:attachable":{"description":{
                    "identifier":ident,"materials":{"default":"armor","enchanted":"armor_enchanted"},
                    "textures":{"default":f"textures/models/armor/{spec['tier']}_{layer}","enchanted":"textures/misc/enchanted_actor_glint"},
                    "geometry":{"default":f"geometry.humanoid.armor.{geometry}"},
                    "scripts":{"parent_setup":f"variable.{variable}_layer_visible = 0.0;"},
                    "render_controllers":["controller.render.armor"]}}}
                dump(ATTACHABLES / f"{spec['tier']}_{name}.json", attachable)
            if item.get("recipe"):
                rec = item["recipe"]
                dump(RECIPES / f"{spec['tier']}_{name}.json", {"format_version": spec["format_version"],
                    "minecraft:recipe_shapeless": {"description": {"identifier": ident}, "tags": ["crafting_table"],
                    "unlock": {"context": "AlwaysUnlocked"},
                    "ingredients": [{"item": rec[field]} for field in ("template", "base", "addition")],
                    "result": {"item": ident}}})
            texture_name = item.get("texture", f"{spec['tier']}_{name}")
            texture = source_textures / f"{texture_name}.png"
            if texture.exists():
                shutil.copy2(texture, TEXTURES / f"{spec['tier']}_{name}.png")
                texture_ref = f"textures/items/generated_equipment/{spec['tier']}_{name}"
            else:
                texture_ref = texture_name
            atlas["texture_data"][key] = {"textures": texture_ref}
            lang.append(f"item.{ident}.name={item['display']}")
            generated.append(ident)
    dump(ATLAS, atlas)
    text = LANG.read_text().rstrip()
    if BEGIN in text: text = text[:text.index(BEGIN)].rstrip()
    LANG.write_text(text + "\n\n" + BEGIN + "\n" + "\n".join(lang) + "\n" + END + "\n")
    give = ["# Generated equipment parity test kit"] + [f"give @s {ident} 1" for ident in generated]
    give += ["give @s minecraft:anvil 1", "give @s minecraft:smithing_table 1"]
    (ROOT / "behavior_pack/functions/matcha_equipment_test.mcfunction").write_text("\n".join(give) + "\n")
    print(f"Generated {len(generated)} equipment items from {len(tier_paths)} tiers")

if __name__ == "__main__": main()
