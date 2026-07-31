#!/usr/bin/env python3
"""Static parity checks for custom enchantments and blessings."""
import argparse, json, re
from pathlib import Path
from upstream import add_source_argument, baseline, validate_source

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(); add_source_argument(parser); source=validate_source(parser.parse_args().source)
source_enchantments={p.stem for p in (source/"data/main/enchantment").glob("*.json")}
source_blessings={p.stem for p in (source/"data/blessings/recipe").glob("*.json")}
items={p.stem.removeprefix("blessing_") for p in (ROOT/"behavior_pack/items/generated_blessings").glob("*.json") if not re.search(r" \d+$",p.stem)}
recipes={p.stem.split("_v",1)[0] for p in (ROOT/"behavior_pack/recipes/generated_blessings").glob("*.json") if not re.search(r" \d+$",p.stem)}
script=(ROOT/"behavior_pack/scripts/enchantments.js").read_text(); data=(ROOT/"behavior_pack/scripts/enchantment_data.js").read_text()
implemented={name for name in source_enchantments if re.search(rf'"{re.escape(name)}"',script+data)}
checks=[]
def add(name,expected,actual,detail=""):
    checks.append({"name":name,"expected":expected,"actual":actual,"status":"pass" if expected==actual else "fail","detail":detail})
add("custom enchantment inventory",23,len(source_enchantments))
add("scripted custom enchantments",source_enchantments,implemented,sorted(source_enchantments-implemented))
add("blessing item coverage",source_blessings,items,sorted(source_blessings-items))
add("blessing recipe coverage",source_blessings,recipes,sorted(source_blessings-recipes))
add("off-hand application",True,"EquipmentSlot.Offhand" in script and "addEnchantment" in script)
add("embedded equipment routing",True,"EQUIPMENT_ENCHANTMENTS" in script and "equipment_with_embedded_effects" in json.loads((ROOT/"docs/enchantment-check-report.json").read_text()))
report=json.loads((ROOT/"docs/enchantment-check-report.json").read_text()); report["checks"]=checks; report["summary"]={"checks":len(checks),"passed":sum(x["status"]=="pass" for x in checks),"failed":sum(x["status"]=="fail" for x in checks)}
(ROOT/"docs/enchantment-check-report.json").write_text(json.dumps(report,indent=2,default=lambda x:sorted(x))+"\n")
for row in checks: print(row["status"].upper(),row["name"])
if report["summary"]["failed"]: raise SystemExit(1)
