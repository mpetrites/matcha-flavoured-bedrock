#!/usr/bin/env python3
"""Convert Matcha's Java structure NBT templates to Bedrock mcstructure."""
import argparse, json, sys
from pathlib import Path
from upstream import add_source_argument, baseline, validate_source
try: import nbtlib
except ImportError: raise SystemExit("nbtlib is required: python3 -m pip install --target /tmp/matcha_pydeps nbtlib; then set PYTHONPATH=/tmp/matcha_pydeps")

ROOT=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();add_source_argument(parser);JAVA=validate_source(parser.parse_args().source)
SOURCE=JAVA/"data/minecraft/structure";OUTPUT=ROOT/"behavior_pack/structures/matcha"
for p in OUTPUT.rglob("*.mcstructure"):p.unlink()
FACING={"down":0,"up":1,"north":2,"south":3,"west":4,"east":5};DIRECTION={"east":0,"south":1,"west":2,"north":3}
def states(name,props):
 out={}
 if "facing" in props:
  if "door" in name:out["direction"]=nbtlib.Int(DIRECTION.get(str(props["facing"]),0))
  else:out["facing_direction"]=nbtlib.Int(FACING.get(str(props["facing"]),2))
 if "hinge" in props:out["door_hinge_bit"]=nbtlib.Byte(str(props["hinge"])=="right")
 if "half" in props and "door" in name:out["upper_block_bit"]=nbtlib.Byte(str(props["half"])=="upper")
 if "open" in props:out["open_bit"]=nbtlib.Byte(str(props["open"])=="true")
 if "powered" in props:out["powered_bit"]=nbtlib.Byte(str(props["powered"])=="true")
 if "delay" in props:out["repeater_delay"]=nbtlib.Int(int(str(props["delay"])))
 if "level" in props:out["liquid_depth"]=nbtlib.Int(int(str(props["level"])))
 return nbtlib.Compound(out)
def convert(path):
 java=nbtlib.load(path);size=[int(x) for x in java["size"]];palette=[];palette_map={};dropped=[]
 for i,p in enumerate(java["palette"]):
  name=str(p["Name"]);props=p.get("Properties",{})
  if name in ("minecraft:jigsaw","minecraft:command_block"):name="minecraft:air";dropped.append(i)
  key=(name,tuple(sorted((k,str(v)) for k,v in props.items())) if name!="minecraft:air" else ())
  if key not in palette_map:
   palette_map[key]=len(palette);palette.append(nbtlib.Compound({"name":nbtlib.String(name),"states":states(name,props),"version":nbtlib.Int(18168865)}))
  palette_map[("source",i)]=palette_map[key]
 volume=size[0]*size[1]*size[2];indices=[-1]*volume;position_data={}
 for block in java["blocks"]:
  x,y,z=(int(v) for v in block["pos"]);indices[x*size[1]*size[2]+y*size[2]+z]=palette_map[("source",int(block["state"]))]
  if "nbt" in block and str(block["nbt"].get("id",""))=="minecraft:brushable_block":
   index=x*size[1]*size[2]+y*size[2]+z;position_data[str(index)]=nbtlib.Compound({"block_entity_data":nbtlib.Compound({"id":nbtlib.String("BrushableBlock"),"LootTable":nbtlib.String("loot_tables/archaeology/village_plains.json"),"LootTableSeed":nbtlib.Long(0),"x":nbtlib.Int(x),"y":nbtlib.Int(y),"z":nbtlib.Int(z)})})
 root=nbtlib.Compound({"format_version":nbtlib.Int(1),"size":nbtlib.List[nbtlib.Int](size),"structure":nbtlib.Compound({"block_indices":nbtlib.List[nbtlib.List[nbtlib.Int]]([nbtlib.List[nbtlib.Int](indices),nbtlib.List[nbtlib.Int]([-1]*volume)]),"entities":nbtlib.List[nbtlib.Compound]([]),"palette":nbtlib.Compound({"default":nbtlib.Compound({"block_palette":nbtlib.List[nbtlib.Compound](palette),"block_position_data":nbtlib.Compound(position_data)})})}),"structure_world_origin":nbtlib.List[nbtlib.Int]([0,0,0])})
 rel=path.relative_to(SOURCE).with_suffix(".mcstructure");target=OUTPUT/rel;target.parent.mkdir(parents=True,exist_ok=True);nbtlib.File(root).save(target,gzipped=False,byteorder="little");return {"source":str(rel.with_suffix('.nbt')),"output":str(target.relative_to(ROOT)),"size":size,"blocks":len(java['blocks']),"palette":len(palette),"java_only_blocks_replaced":len(dropped),"block_entities":len(position_data)}
templates=[convert(p) for p in sorted(SOURCE.rglob("*.nbt"))]
worldgen=JAVA/"data/minecraft/worldgen";report={"baseline":baseline(),"templates":templates,"template_count":len(templates),"template_pools":len(list((worldgen/'template_pool').rglob('*.json'))),"structures":len(list((worldgen/'structure').rglob('*.json'))),"structure_sets":len(list((worldgen/'structure_set').rglob('*.json'))),"placement":{"spacing_chunks":80,"separation_chunks":50,"salt":10387312}}
(ROOT/"docs/structure-conversion-report.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps({k:v for k,v in report.items() if k!='templates'}))
