#!/usr/bin/env python3
"""Coverage audit for parity milestones 1–4."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; JAVA=ROOT.parent/"work/java-source-104"
checks=[]
def add(name,expected,actual,detail=""):
    checks.append({"name":name,"status":"pass" if expected==actual else "fail","expected":expected,"actual":actual,"detail":detail})
smithing=[p for p in (JAVA/"data/smithing_table/recipe").glob("*.json")]
smithing_outputs={p.stem for p in (ROOT/"behavior_pack/recipes/generated_equipment").glob("*.json")}
smithing_outputs|={p.stem for p in (ROOT/"behavior_pack/recipes/generated_components").glob("*.json")}
smithing_outputs|={p.stem for p in (ROOT/"behavior_pack/recipes").glob("*.json")}
add("component smithing recipe coverage",len(smithing),sum(p.stem in smithing_outputs for p in smithing))
craft=[]
for p in (JAVA/"data/crafting/recipe").glob("*.json"):
    d=json.loads(p.read_text())
    if d.get("result",{}).get("components"):craft.append(p)
component_recipe_names={p.stem.split("_v",1)[0] for p in (ROOT/"behavior_pack/recipes/generated_components").glob("*.json")}
food_recipe_text=" ".join(p.name for p in (ROOT/"behavior_pack/recipes/generated_foods").glob("*.json"))
covered=sum(p.stem in component_recipe_names or p.stem in food_recipe_text for p in craft)
add("component crafting recipe coverage",len(craft),covered)
food_report=json.loads((ROOT/"docs/food-conversion-report.json").read_text())
add("food definition conflicts",0,len(food_report["conflicts"]))
add("scripted consumable identifiers",food_report["custom_food_items"],food_report["scripted_food_effects"])
equipment=json.loads((ROOT/"docs/equipment-check-report.json").read_text())
add("equipment static checks",equipment["summary"]["checks"],equipment["summary"]["passed"])
add("equipment tiers",5,len(equipment["tiers"]))
add("armor attachables",20,len(list((ROOT/"resource_pack/attachables/generated_equipment").glob("*.json"))))
report={"milestones":[1,2,3,4],"summary":{"checks":len(checks),"passed":sum(x["status"]=="pass" for x in checks),"failed":sum(x["status"]=="fail" for x in checks)},"checks":checks}
(ROOT/"docs/parity-1-4-check-report.json").write_text(json.dumps(report,indent=2)+"\n")
for row in checks:print(row["status"].upper(),row["name"],f"{row['actual']}/{row['expected']}")
if report["summary"]["failed"]:raise SystemExit(1)
