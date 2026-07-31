#!/usr/bin/env python3
"""Rewrite Bedrock recipe inputs that Survival canonicalizes away."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
replacements=json.loads((ROOT/"tools/vanilla_replacements.json").read_text())["replacements"]
INPUT_KEYS={"item","input","base","addition","template"}

def rewrite(value):
    changed=0
    if isinstance(value,dict):
        for key,child in list(value.items()):
            if key in INPUT_KEYS and isinstance(child,str) and child in replacements:
                value[key]=replacements[child]; changed+=1
            else: changed+=rewrite(child)
    elif isinstance(value,list):
        for child in value: changed+=rewrite(child)
    return changed

files=changes=0
for path in (ROOT/"behavior_pack/recipes").rglob("*.json"):
    data=json.loads(path.read_text()); count=rewrite(data)
    if count:
        path.write_text(json.dumps(data,indent=2)+"\n"); files+=1; changes+=count
print(json.dumps({"files_updated":files,"inputs_rewritten":changes}))
