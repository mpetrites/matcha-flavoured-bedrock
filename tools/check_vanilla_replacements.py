#!/usr/bin/env python3
"""Validate generated singleton replacement targets and recipe inputs."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
table=json.loads((ROOT/"tools/vanilla_replacements.json").read_text())
replacements=table["replacements"]; recipe_targets=replacements | table.get("recipe_overrides", {}); ambiguous=table["ambiguous"]
for recipe_id, relative_source in table.get("recipe_override_sources", {}).items():
    source=json.loads((ROOT/"behavior_pack/recipes"/relative_source).read_text())
    body=next(value for key,value in source.items() if key.startswith("minecraft:recipe_"))
    result=body.get("result",body.get("output"))
    recipe_targets[recipe_id]=result.get("item") if isinstance(result,dict) else result
identifiers=set()
for path in (ROOT/"behavior_pack/items").rglob("*.json"):
    data=json.loads(path.read_text())
    ident=data.get("minecraft:item",{}).get("description",{}).get("identifier")
    if ident: identifiers.add(ident)

missing={base:target for base,target in replacements.items() if target not in identifiers}
overlap=sorted(set(replacements)&set(ambiguous))
stale=[]
recipe_overrides={}
preserved_inputs={
    ("behavior_pack/recipes/generated_components/lesser_warding_shield.json","minecraft:shield"),
    ("behavior_pack/recipes/generated_components/warding_shield.json","minecraft:shield"),
    ("behavior_pack/recipes/generated_vanilla_overrides/shield.json","minecraft:shield"),
}
def visit(value,path):
    if isinstance(value,dict):
        for key,child in value.items():
            if key in {"item","input","base","addition","template"} and isinstance(child,str) and child in replacements:
                relative=str(path.relative_to(ROOT))
                if (relative,child) not in preserved_inputs:
                    stale.append({"recipe":relative,"vanilla_input":child,"replacement":replacements[child]})
            visit(child,path)
    elif isinstance(value,list):
        for child in value: visit(child,path)
for path in (ROOT/"behavior_pack/recipes").rglob("*.json"):
    data=json.loads(path.read_text()); visit(data,path)
    for key,body in data.items():
        if key.startswith("minecraft:recipe_") and isinstance(body,dict):
            ident=body.get("description",{}).get("identifier")
            result=body.get("result",body.get("output"))
            result_id=result.get("item") if isinstance(result,dict) else result
            if ident in recipe_targets: recipe_overrides[ident]=result_id

missing_recipe_overrides={base:target for base,target in recipe_targets.items() if recipe_overrides.get(base)!=target}
report={"replacement_count":len(replacements),"recipe_target_count":len(recipe_targets),"ambiguous_count":len(ambiguous),"missing_targets":missing,"ambiguous_overlap":overlap,"stale_recipe_inputs":stale,"recipe_override_count":len(recipe_overrides),"missing_or_incorrect_recipe_overrides":missing_recipe_overrides,"status":"pass" if not (missing or overlap or stale or missing_recipe_overrides) else "fail"}
(ROOT/"docs/vanilla-replacement-check-report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({k:(len(v) if isinstance(v,(list,dict)) else v) for k,v in report.items()}))
if report["status"]!="pass": raise SystemExit(1)
