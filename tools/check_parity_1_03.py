#!/usr/bin/env python3
"""Audit changes specifically introduced by the official Java 1.03 release."""
import argparse, json
from pathlib import Path
from upstream import add_source_argument, baseline, validate_source

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(); add_source_argument(parser); source=validate_source(parser.parse_args().source)
checks=[]
def add(name,ok,detail,ownership="implemented"):
    checks.append({"name":name,"status":"pass" if ok else "fail","ownership":ownership,"detail":detail})
def recipe(path,key): return json.loads(path.read_text())[key]

carbon=recipe(ROOT/"behavior_pack/recipes/generated_components/carbon_rich_iron.json","minecraft:recipe_shapeless")
add("Carbon-Rich Iron intermediary",carbon["result"]=={"item":"matcha:carbon_rich_iron","count":4},carbon["result"])
electrum=recipe(ROOT/"behavior_pack/recipes/generated/crafting_electrum_alloy.json","minecraft:recipe_shapeless")
add("Electrum consumes Divine Fragment",any(x.get("item")=="matcha:divine_fragment" for x in electrum["ingredients"]),electrum["ingredients"])
electrum_item=json.loads((ROOT/"behavior_pack/items/generated_equipment/electrum_sword.json").read_text())["minecraft:item"]["components"]
add("Electrum enchanted presentation",electrum_item.get("minecraft:glint") is True,electrum_item.get("minecraft:glint"))
script=(ROOT/"behavior_pack/scripts/enchantments.js").read_text()
add("Warding Stone Trial Chamber rejection","trial_spawner" in script and "matcha:warding_stone" in script,"scripted proximity rejection")
estus=(ROOT/"behavior_pack/scripts/estus.js").read_text()
add("nerfed Blaze Estus chance",'["minecraft:blaze", 0.5]' in estus,"50% base chance")
for stem in ("silver_sword","warding_sword","warding_shield"):
    path=ROOT/f"behavior_pack/items/generated_components/{stem}.json"
    add(f"{stem} 1.03 source regeneration",path.exists(),str(path.relative_to(ROOT)))
for stem in ("food_bruschetta","food_baked_apple","smoking_charcoal","smoking_terracotta_from_smoking_clay"):
    needle=stem.replace("food_","")
    paths=[p for p in (ROOT/"behavior_pack/recipes").rglob("*.json") if needle in p.stem]
    add(f"{stem} recipe",bool(paths),[p.name for p in paths])
loot_report=json.loads((ROOT/"docs/loot-conversion-report.json").read_text())
survival=(ROOT/"behavior_pack/scripts/survival_systems.js").read_text()
add("Trial Chamber reward table conversion",loot_report["converted_tables"]==282,loot_report["converted_tables"])
add("Spawner loot conversion",(ROOT/"behavior_pack/loot_tables/blocks/spawner.json").exists(),"blocks/spawner.json")
add("frozen-water effect nerf",all(x in survival for x in ("FROZEN_BIOMES","slowness","darkness","applyDamage(2)")),"scripted frozen-water effects")
report={"baseline":baseline(),"summary":{"checks":len(checks),"passed":sum(x["status"]=="pass" for x in checks),"failed":sum(x["status"]=="fail" for x in checks)},"checks":checks}
(ROOT/"docs/parity-1-03-report.json").write_text(json.dumps(report,indent=2)+"\n")
for row in checks: print(row["status"].upper(),row["name"])
if report["summary"]["failed"]: raise SystemExit(1)
