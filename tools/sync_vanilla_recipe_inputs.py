#!/usr/bin/env python3
"""Rewrite Bedrock recipe inputs that Survival canonicalizes away."""
import json
from pathlib import Path
from recipe_input_policy import preserved_inputs

ROOT=Path(__file__).resolve().parents[1]
replacements=json.loads((ROOT/"tools/vanilla_replacements.json").read_text())["replacements"]
INPUT_KEYS={"item","input","base","addition","template"}

def rewrite(value,preserved):
    changed=0
    if isinstance(value,dict):
        for key,child in list(value.items()):
            if key in INPUT_KEYS and isinstance(child,str) and child in replacements and child not in preserved:
                value[key]=replacements[child]; changed+=1
            else: changed+=rewrite(child,preserved)
    elif isinstance(value,list):
        for child in value: changed+=rewrite(child,preserved)
    return changed

files=changes=0
for path in (ROOT/"behavior_pack/recipes").rglob("*.json"):
    data=json.loads(path.read_text())
    body=next((value for key,value in data.items() if key.startswith("minecraft:recipe_") and isinstance(value,dict)),{})
    count=rewrite(data,preserved_inputs(body))
    if count:
        path.write_text(json.dumps(data,indent=2)+"\n"); files+=1; changes+=count
print(json.dumps({"files_updated":files,"inputs_rewritten":changes}))
