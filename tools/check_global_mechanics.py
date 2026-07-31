#!/usr/bin/env python3
"""Audit the remaining Matcha global mechanics implemented by Script API."""
import argparse,json
from pathlib import Path
from upstream import add_source_argument,baseline,validate_source
ROOT=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();add_source_argument(parser);source=validate_source(parser.parse_args().source)
script=(ROOT/"behavior_pack/scripts/global_mechanics.js").read_text();main=(ROOT/"behavior_pack/scripts/main.js").read_text();checks=[]
def add(name,*needles):checks.append({"name":name,"status":"pass" if all(n in script for n in needles) else "fail","evidence":list(needles)})
add("extended day cycle","setTimeOfDay","},3)")
add("spawn sky restriction","entitySpawn","visibleSky","UNDEAD")
add("post-dragon safe surface","matcha:first_dragon_reward","location.y>=63")
add("mob health rebalance","minecraft:cave_spider","setCurrentValue")
add("mob movement and damage approximation","minecraft:zombie","minecraft:husk","strength","speed")
add("clay statue weather","matcha:loot_item_108c0dc960","matcha:loot_item_cdfc89dd82","weather clear","weather rain")
add("eerie village ambience","villager_v2","stopsound @s music","ambient.cave")
add("Happy Ghast horn","minecraft:goat_horn","minecraft:happy_ghast","teleport")
add("stackable water bottles","matcha:water_bottle","minecraft:glass_bottle","minecraft:water")
add("boat particles","minecraft:riding","matcha:splash_","getVelocity")
add("sulfur particles","minecraft:nether_quartz_ore","basic_smoke_particle")
add("asylum application particles","APPLICATIONS","villager_v2","basic_smoke_particle")
checks.append({"name":"script loaded","status":"pass" if 'import "./global_mechanics.js"' in main else "fail","evidence":["main.js import"]})
report={"baseline":baseline(),"summary":{"checks":len(checks),"passed":sum(x["status"]=="pass" for x in checks),"failed":sum(x["status"]=="fail" for x in checks)},"checks":checks,"approximations":["Sky exposure uses the topmost-block test because Bedrock Script API has no can_see_sky predicate.","Unsupported entity base-attribute mutation is represented by current-health caps and long status effects.","Bedrock does not expose Java equipment drop-chance NBT, so natural equipment drops retain Bedrock behavior.","Village structure membership is approximated by nearby villagers for eerie ambience.","Divine-favour item gravity cannot be disabled stably; its presentation remains particle-only.","Water bottles use a stackable matcha:water_bottle carrier filled by using glass bottles on water."]}
(ROOT/"docs/global-mechanics-check-report.json").write_text(json.dumps(report,indent=2)+"\n")
for row in checks:print(row["status"].upper(),row["name"])
if report["summary"]["failed"]:raise SystemExit(1)
