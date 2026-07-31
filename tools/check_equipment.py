#!/usr/bin/env python3
"""Static parity checks for every generated equipment tier."""
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
paths=[Path(p) for p in sys.argv[1:]] or sorted((Path(__file__).parent/"equipment_tiers").glob("*.json"))
atlas=json.loads((ROOT/"resource_pack/textures/item_texture.json").read_text())["texture_data"]
checks=[]; failures=[]
def check(ok,item,field,expected,actual):
    row={"item":item,"field":field,"status":"pass" if ok else "fail","expected":expected,"actual":actual}
    checks.append(row)
    if not ok: failures.append(row)
for path in paths:
    spec=json.loads(path.read_text())
    for item in spec["items"]:
        stem=f"{spec['tier']}_{item['name']}"; p=ROOT/f"behavior_pack/items/generated_equipment/{stem}.json"
        try:c=json.loads(p.read_text())["minecraft:item"]["components"]
        except Exception as e:check(False,stem,"item_file","readable",str(e));continue
        check(c.get("minecraft:durability",{}).get("max_durability")==item["durability"],stem,"durability",item["durability"],c.get("minecraft:durability"))
        if "damage" in item:check(c.get("minecraft:damage")==item["damage"],stem,"damage",item["damage"],c.get("minecraft:damage"))
        if "mining" in item:check(c.get("minecraft:digger",{}).get("destroy_speeds")==item["mining"],stem,"mining",item["mining"],c.get("minecraft:digger"))
        if item["name"]=="spear":check("minecraft:kinetic_weapon" in c,stem,"kinetic_weapon","present","present" if "minecraft:kinetic_weapon" in c else "absent")
        if "armor" in item:
            check(c.get("minecraft:wearable")==item["armor"],stem,"armor",item["armor"],c.get("minecraft:wearable"))
            ap=ROOT/f"resource_pack/attachables/generated_equipment/{stem}.json"
            check(ap.exists(),stem,"worn_visual","attachable present","present" if ap.exists() else "absent")
        repair=item.get("repair",spec["repair"]); actual=c.get("minecraft:repairable",{}).get("repair_items",[{}])[0]
        expected={"items":repair["items"],"repair_amount":repair["amount"]}
        check(actual==expected,stem,"repair",expected,actual)
        rp=ROOT/f"behavior_pack/recipes/generated_equipment/{stem}.json"
        check(rp.exists()==bool(item.get("recipe")),stem,"recipe","present" if item.get("recipe") else item.get("recipe_note","intentionally absent"),"present" if rp.exists() else "absent")
        check(f"matcha_{stem}" in atlas,stem,"texture_atlas","present","present" if f"matcha_{stem}" in atlas else "absent")
report={"tiers":[json.loads(p.read_text())["tier"] for p in paths],"summary":{"checks":len(checks),"passed":len(checks)-len(failures),"failed":len(failures)},"checks":checks}
(ROOT/"docs/equipment-check-report.json").write_text(json.dumps(report,indent=2)+"\n")
print(f"Equipment checks: {report['summary']['passed']}/{report['summary']['checks']} passed across {len(paths)} tiers")
if failures:
    for f in failures:print("FAIL",f["item"],f["field"],f["actual"])
    raise SystemExit(1)
