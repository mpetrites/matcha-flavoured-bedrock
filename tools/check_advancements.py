#!/usr/bin/env python3
"""Static coverage audit for the Bedrock advancement behavior engine."""
import argparse,json,re
from pathlib import Path
from upstream import add_source_argument,baseline,validate_source
ROOT=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();add_source_argument(parser);source=validate_source(parser.parse_args().source)
files=sorted(set(source.glob("data/*/advancement/**/*.json"))|set(source.glob("data/*/advancement/*.json")))
source_criteria=sum(len(json.loads(p.read_text()).get("criteria",{})) for p in files)
report=json.loads((ROOT/"docs/advancement-conversion-report.json").read_text());data=(ROOT/"behavior_pack/scripts/advancement_data.js").read_text();script=(ROOT/"behavior_pack/scripts/advancements.js").read_text();main=(ROOT/"behavior_pack/scripts/main.js").read_text();villagers=(ROOT/"behavior_pack/scripts/villagers.js").read_text()
checks=[]
def add(name,expected,actual,detail=""):checks.append({"name":name,"expected":expected,"actual":actual,"status":"pass" if expected==actual else "fail","detail":detail})
add("advancement inventory",len(files),report["advancements"]);add("criterion inventory",source_criteria,report["criteria"]);add("display inventory",67,report["displayed"])
for name,needles in {
 "persistent criteria":["matcha:advancement_criteria_v1","setDynamicProperty"],
 "persistent completion":["matcha:advancements_v1","requirementsMet"],
 "toast and chat":["onScreenDisplay.setTitle","Advancement Made!","display.toast","display.chat"],
 "inventory reconciliation":["inventoryIds(player)","inventory_changed","recipe_crafted"],
 "stable event adapters":["playerDimensionChange","itemCompleteUse","itemUseOn","entityDie","minecraft:riding"],
 "villager trade adapter":["recordVillagerTrade","villager_trade"],
 "runtime loaded":['import "./advancements.js"']}.items(): add(name,True,all(x in script+main+villagers for x in needles),needles)
report["checks"]=checks;report["summary"]={"checks":len(checks),"passed":sum(x["status"]=="pass" for x in checks),"failed":sum(x["status"]=="fail" for x in checks)}
report["trigger_fidelity"]={"exact":["inventory_changed","consume_item","using_item","item_used_on_block","player_killed_entity","changed_dimension","villager_trade","tick","started_riding","location:stepping_on"],"approximated":{"recipe_crafted":"completed when its result is acquired because Bedrock 2.0 has no stable recipe-crafted event","recipe_unlocked":"treated as available because Bedrock pack recipes are globally discoverable","fishing_rod_hooked":"completed when the matching catch enters inventory because Bedrock has no stable fishing-hook event"},"pending":["location:structures"]}
(ROOT/"docs/advancement-conversion-report.json").write_text(json.dumps(report,indent=2)+"\n")
for row in checks:print(row["status"].upper(),row["name"])
if report["summary"]["failed"]:raise SystemExit(1)
