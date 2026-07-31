#!/usr/bin/env python3
"""Generate the compact Bedrock advancement registry from pinned Java data."""
import argparse, json, re
from pathlib import Path
from upstream import add_source_argument, baseline, validate_source

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(); add_source_argument(parser)
source=validate_source(parser.parse_args().source)

def text(value):
    if isinstance(value,str): return value
    if isinstance(value,dict): return value.get("text") or value.get("translate") or ""
    return ""

def strings(value,key):
    found=[]
    if isinstance(value,dict):
        for k,v in value.items():
            if k==key:
                found.extend(v if isinstance(v,list) else [v])
            found.extend(strings(v,key))
    elif isinstance(value,list):
        for v in value: found.extend(strings(v,key))
    return [v for v in found if isinstance(v,str)]

def model_ids(value):
    return [v.split(":",1)[-1] for v in strings(value,"minecraft:item_model")]

recipe_results={}
for path in source.glob("data/*/recipe/*.json"):
    data=json.loads(path.read_text()); result=data.get("result",{})
    if isinstance(result,str): item=result
    else: item=result.get("id") or result.get("item")
    models=model_ids(result)
    rid=f"{path.parent.parent.name}:{path.stem}"
    recipe_results[rid]={"items":[item] if item else [],"models":models}

files=sorted(set(source.glob("data/*/advancement/**/*.json"))|set(source.glob("data/*/advancement/*.json")))
advancements=[]; criterion_index=0; trigger_counts={}
for path in files:
    data=json.loads(path.read_text()); namespace=path.parents[len(path.parts)-len(source.parts)-3].name
    # The namespace is the directory immediately below data.
    namespace=path.relative_to(source/"data").parts[0]
    rel=path.relative_to(source/"data"/namespace/"advancement").with_suffix("")
    aid=f"{namespace}:{rel.as_posix()}"; criteria=[]
    for name,criterion in data.get("criteria",{}).items():
        trigger=criterion.get("trigger","minecraft:unknown").split(":",1)[-1]
        conditions=criterion.get("conditions",{}); items=strings(conditions,"items")
        models=model_ids(conditions); recipe=strings(conditions,"recipe_id") or strings(conditions,"recipe")
        result={"items":[],"models":[]}
        for rid in recipe:
            mapped=recipe_results.get(rid,{})
            result["items"].extend(mapped.get("items",[])); result["models"].extend(mapped.get("models",[]))
        entity_types=strings(conditions,"minecraft:entity_type")
        professions=[]
        for nbt in strings(conditions,"minecraft:nbt"):
            professions.extend(re.findall(r'profession:\\?"minecraft:([^"}]+)',nbt))
        entry={"index":criterion_index,"name":name,"trigger":trigger}
        for key,value in (("items",sorted(set(items))),("models",sorted(set(models))),
                          ("recipes",recipe),("resultItems",sorted(set(result["items"]))),
                          ("resultModels",sorted(set(result["models"]))),("entities",entity_types),
                          ("dimensions",strings(conditions,"to")),("structures",strings(conditions,"structures")),
                          ("professions",sorted(set(professions))),("blocks",strings(conditions,"blocks"))):
            if value: entry[key]=value
        criteria.append(entry); criterion_index+=1; trigger_counts[trigger]=trigger_counts.get(trigger,0)+1
    requirements=data.get("requirements") or [[name] for name in data.get("criteria",{})]
    display=data.get("display"); normalized={"id":aid,"criteria":criteria,"requirements":requirements}
    if display:
        normalized["display"]={"title":text(display.get("title")),"description":text(display.get("description")),
                               "frame":display.get("frame","task"),"toast":display.get("show_toast",True),
                               "chat":display.get("announce_to_chat",True),"hidden":display.get("hidden",False)}
    if data.get("rewards"): normalized["rewards"]=data["rewards"]
    advancements.append(normalized)

out=ROOT/"behavior_pack/scripts/advancement_data.js"
out.write_text("// Generated from pinned Matcha Java 1.03.\nexport const ADVANCEMENTS = "+json.dumps(advancements,separators=(",",":"),ensure_ascii=False)+";\n")
report={"baseline":baseline(),"advancements":len(advancements),"criteria":criterion_index,
        "displayed":sum("display" in a for a in advancements),"hidden":sum("display" not in a for a in advancements),
        "triggers":dict(sorted(trigger_counts.items())),"status":"pass"}
(ROOT/"docs/advancement-conversion-report.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,default=str))
