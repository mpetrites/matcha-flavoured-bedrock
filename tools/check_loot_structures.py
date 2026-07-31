#!/usr/bin/env python3
"""Parity and reachability checks for converted loot and beta villages."""
import argparse,json,re
from pathlib import Path
from upstream import add_source_argument,baseline,validate_source
ROOT=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();add_source_argument(parser);source=validate_source(parser.parse_args().source)
loot_source=source/"data/minecraft/loot_table";loot_out=ROOT/"behavior_pack/loot_tables";structure_source=source/"data/minecraft/structure";structure_out=ROOT/"behavior_pack/structures/matcha"
source_tables={str(p.relative_to(loot_source)) for p in loot_source.rglob('*.json')};output_tables={str(p.relative_to(loot_out)) for p in loot_out.rglob('*.json') if not re.search(r' \d+\.json$',p.name)}
source_templates={str(p.relative_to(structure_source).with_suffix('.mcstructure')) for p in structure_source.rglob('*.nbt')};output_templates={str(p.relative_to(structure_out)) for p in structure_out.rglob('*.mcstructure')}
custom_items=set()
for p in (ROOT/"behavior_pack/items").rglob('*.json'):
 if re.search(r' \d+$',p.stem):continue
 try:custom_items.add(json.loads(p.read_text())["minecraft:item"]["description"]["identifier"])
 except:pass
loot_text='\n'.join(p.read_text() for p in loot_out.rglob('*.json') if not re.search(r' \d+\.json$',p.name));missing_items=sorted(set(re.findall(r'"name": "(matcha:[^"]+)"',loot_text))-custom_items)
references=set(re.findall(r'"name": "loot_tables/([^"]+\.json)"',loot_text));missing_refs=sorted(ref for ref in references if ref not in output_tables)
script=(ROOT/"behavior_pack/scripts/structures.js").read_text();main=(ROOT/"behavior_pack/scripts/main.js").read_text();loot_report=json.loads((ROOT/"docs/loot-conversion-report.json").read_text());structure_report=json.loads((ROOT/"docs/structure-conversion-report.json").read_text())
checks=[]
def add(name,expected,actual,detail=""):checks.append({"name":name,"expected":expected,"actual":actual,"status":"pass" if expected==actual else "fail","detail":detail})
add("loot source inventory",282,len(source_tables));add("loot table coverage",source_tables,output_tables,sorted(source_tables-output_tables));add("custom loot result identifiers",[],missing_items);add("internal loot references",[],missing_refs)
add("structure template inventory",16,len(source_templates));add("mcstructure coverage",source_templates,output_templates,sorted(source_templates-output_templates));add("template pools",4,structure_report['template_pools']);add("structure definitions",5,structure_report['structures']);add("structure sets",1,structure_report['structure_sets'])
for name,needles in {"80/50 placement rule":["SPACING=1280","OFFSET_RANGE=480","SALT=10387312"],"biome routing":["ALLOWED_BIOMES","getBiome"],"stable placement":["candidate(gridX,gridZ)","MARKER"],"weighted pool assembly":["town_centers/well","const ROADS=","const BUILDINGS=","extra_large_2","joint_t"],"script loaded":['import "./structures.js"']}.items():add(name,True,all(x in script+main for x in needles),needles)
for item,path in {"Divine Fragment":"blocks/spawner.json","Crystal Heart":"kleis_items/crystal_heart.json"}.items():add(item+" reachable",True,(loot_out/path).exists() and "matcha:" in (loot_out/path).read_text(),path)
report={"baseline":baseline(),"summary":{"checks":len(checks),"passed":sum(x['status']=='pass' for x in checks),"failed":sum(x['status']=='fail' for x in checks)},"checks":checks,"conversion_limits":{"conservatively_disabled_conditions":loot_report['dropped_conditions'],"approximated_or_omitted_functions":loot_report['dropped_functions']}}
(ROOT/"docs/loot-structure-check-report.json").write_text(json.dumps(report,indent=2,default=lambda x:sorted(x))+"\n")
for row in checks:print(row['status'].upper(),row['name'])
if report['summary']['failed']:raise SystemExit(1)
