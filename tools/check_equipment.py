#!/usr/bin/env python3
"""Static parity checks for generated equipment; runs anywhere Python does."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = json.loads((Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent/"equipment_tiers/bronze.json").read_text())
checks, failures = [], []
def check(ok, item, field, expected, actual):
    checks.append({"item":item,"field":field,"status":"pass" if ok else "fail","expected":expected,"actual":actual})
    if not ok: failures.append(checks[-1])
for item in spec["items"]:
    ident=f"{spec['tier']}_{item['name']}"; p=ROOT/f"behavior_pack/items/generated_equipment/{ident}.json"
    try: c=json.loads(p.read_text())["minecraft:item"]["components"]
    except Exception as e: check(False,ident,"item_file","readable",str(e)); continue
    check(c.get("minecraft:durability",{}).get("max_durability")==item["durability"],ident,"durability",item["durability"],c.get("minecraft:durability"))
    if "damage" in item: check(c.get("minecraft:damage")==item["damage"],ident,"damage",item["damage"],c.get("minecraft:damage"))
    if "mining" in item: check(c.get("minecraft:digger",{}).get("destroy_speeds")==item["mining"],ident,"mining",item["mining"],c.get("minecraft:digger"))
    if "armor" in item: check(c.get("minecraft:wearable")==item["armor"],ident,"armor",item["armor"],c.get("minecraft:wearable"))
    repair=item.get("repair",spec["repair"]); actual=c.get("minecraft:repairable",{}).get("repair_items",[{}])[0]
    check(actual=={"items":repair["items"],"repair_amount":repair["amount"]},ident,"repair",repair,actual)
    rp=ROOT/f"behavior_pack/recipes/generated_equipment/{ident}.json"
    check(rp.exists()==bool(item.get("recipe")),ident,"recipe","present" if item.get("recipe") else item.get("recipe_note","intentionally absent"),"present" if rp.exists() else "absent")
    tx=ROOT/f"resource_pack/textures/items/generated_equipment/{ident}.png"
    check(tx.exists(),ident,"texture","present","present" if tx.exists() else "absent")
report={"tier":spec["tier"],"summary":{"checks":len(checks),"passed":len(checks)-len(failures),"failed":len(failures)},"checks":checks}
(ROOT/"docs/equipment-check-report.json").write_text(json.dumps(report,indent=2)+"\n")
print(f"Equipment checks: {report['summary']['passed']}/{report['summary']['checks']} passed")
if failures:
    for f in failures: print(f"FAIL {f['item']} {f['field']}: {f['actual']}")
    raise SystemExit(1)
