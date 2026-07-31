#!/usr/bin/env python3
"""Static coverage checks for the entity-driven Estus loop."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(name,ok,detail):
    checks.append({"name":name,"status":"pass" if ok else "fail","detail":detail})
for item in ("raw_estus","estus_ash"):
    path=ROOT/f"behavior_pack/items/{item}.json"
    check(f"{item} item",path.exists(),str(path))
script=(ROOT/"behavior_pack/scripts/estus.js").read_text()
for mob in ("blaze","zombie","husk","drowned","zombie_villager"):
    check(f"{mob} drop hook",f'"minecraft:{mob}"' in script,mob)
for effect in ('"regeneration", 40','"resistance", 100'):
    check(f"effect {effect}",effect in script,effect)
stable=json.loads((ROOT/"behavior_pack/recipes/generated_components/stabilised_estus.json").read_text())["minecraft:recipe_shaped"]
check("stabilised Estus uses ash",stable["key"]["E"]["item"]=="matcha:estus_ash",stable["key"]["E"])
check("stabilised Estus uses benzene",stable["key"]["B"]["item"]=="matcha:benzene",stable["key"]["B"])
flask=json.loads((ROOT/"behavior_pack/recipes/generated_foods/potions_food_estus_flask.json").read_text())["minecraft:recipe_shapeless"]
ash=sum(x["item"]=="matcha:estus_ash" for x in flask["ingredients"])
check("Estus Flask uses two ash",ash==2,ash)
report={"summary":{"checks":len(checks),"passed":sum(x["status"]=="pass" for x in checks),"failed":sum(x["status"]=="fail" for x in checks)},"checks":checks}
(ROOT/"docs/estus-check-report.json").write_text(json.dumps(report,indent=2)+"\n")
print(f"Estus checks: {report['summary']['passed']}/{report['summary']['checks']} passed")
if report["summary"]["failed"]:raise SystemExit(1)
