#!/usr/bin/env python3
"""Static parity audit for the generated Matcha villager economy."""
import argparse, json, re
from pathlib import Path
from upstream import add_source_argument, baseline, validate_source

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(); add_source_argument(parser); source=validate_source(parser.parse_args().source)
report=json.loads((ROOT/"docs/villager-trade-report.json").read_text()); data=(ROOT/"behavior_pack/scripts/villager_trade_data.js").read_text(); script=(ROOT/"behavior_pack/scripts/villagers.js").read_text(); main=(ROOT/"behavior_pack/scripts/main.js").read_text()
source_trade_ids={str(p.relative_to(source/"data/minecraft/villager_trade").with_suffix("")) for p in (source/"data/minecraft/villager_trade").rglob("*.json")}
source_set_ids={str(p.relative_to(source/"data/minecraft/trade_set").with_suffix("")) for p in (source/"data/minecraft/trade_set").rglob("*.json")}
generated_trade_ids=set(re.findall(r'^  "([^"]+)": \{$',data.split("export const MATCHA_TRADE_SETS",1)[0],re.M))
generated_set_ids=set(re.findall(r'^  "([^"]+)": \{$',data.split("export const MATCHA_TRADE_SETS",1)[1],re.M))
checks=[]
def add(name,expected,actual,detail=""): checks.append({"name":name,"expected":expected,"actual":actual,"status":"pass" if expected==actual else "fail","detail":detail})
add("trade inventory",235,len(source_trade_ids)); add("trade set inventory",68,len(source_set_ids))
add("generated trade coverage",source_trade_ids,generated_trade_ids,sorted(source_trade_ids-generated_trade_ids)); add("generated set coverage",source_set_ids,generated_set_ids,sorted(source_set_ids-generated_set_ids))
for name,needles in {
 "profession routing":["PROFESSION_BY_VARIANT",'getComponent("minecraft:variant")',"wandering_trader"],"tier progression":["LEVEL_THRESHOLDS","matcha:trade_level"],
 "deterministic offers":["chosenMembers","entity.id"],"daily restock":["getAbsoluteTime","matcha:trade_restock_day"],
 "stock enforcement":["maxUses","out of stock"],"inventory-safe payment":["itemCount(player","removeItems(player"],
 "component-specific outputs":["generated_trade_items","villager_trade_data.js"],"interaction UI":["ActionFormData","MessageFormData","event.cancel=true"]}.items():
  add(name,True,all(x in script+data+json.dumps(report) for x in needles),needles)
add("script loaded",True,'import "./villagers.js"' in main)
report["checks"]=checks; report["summary"]={"checks":len(checks),"passed":sum(x["status"]=="pass" for x in checks),"failed":sum(x["status"]=="fail" for x in checks)}
report["approximations"]=["Offers restock once per Minecraft day rather than at workstation visits.","Java reputation discounts and demand curves are recorded but not exposed by Bedrock Script API.","Exploration-map destinations and several Java-only stack components remain presentation-only until their owning structure/loot systems are ported."]
(ROOT/"docs/villager-trade-report.json").write_text(json.dumps(report,indent=2,default=lambda x:sorted(x))+"\n")
for row in checks: print(row["status"].upper(),row["name"])
if report["summary"]["failed"]: raise SystemExit(1)
