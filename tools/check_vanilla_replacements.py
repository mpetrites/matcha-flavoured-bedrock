#!/usr/bin/env python3
"""Validate generated singleton replacement targets and recipe inputs."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
table=json.loads((ROOT/"tools/vanilla_replacements.json").read_text())
replacements=table["replacements"]; ambiguous=table["ambiguous"]
identifiers=set()
for path in (ROOT/"behavior_pack/items").rglob("*.json"):
    data=json.loads(path.read_text())
    ident=data.get("minecraft:item",{}).get("description",{}).get("identifier")
    if ident: identifiers.add(ident)

missing={base:target for base,target in replacements.items() if target not in identifiers}
overlap=sorted(set(replacements)&set(ambiguous))
stale=[]
def visit(value,path):
    if isinstance(value,dict):
        for key,child in value.items():
            if key in {"item","input","base","addition","template"} and isinstance(child,str) and child in replacements:
                stale.append({"recipe":str(path.relative_to(ROOT)),"vanilla_input":child,"replacement":replacements[child]})
            visit(child,path)
    elif isinstance(value,list):
        for child in value: visit(child,path)
for path in (ROOT/"behavior_pack/recipes").rglob("*.json"):
    visit(json.loads(path.read_text()),path)

report={"replacement_count":len(replacements),"ambiguous_count":len(ambiguous),"missing_targets":missing,"ambiguous_overlap":overlap,"stale_recipe_inputs":stale,"status":"pass" if not (missing or overlap or stale) else "fail"}
(ROOT/"docs/vanilla-replacement-check-report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({k:(len(v) if isinstance(v,(list,dict)) else v) for k,v in report.items()}))
if report["status"]!="pass": raise SystemExit(1)
