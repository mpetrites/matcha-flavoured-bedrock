#!/usr/bin/env python3
"""Parity and reachability checks for converted loot and beta villages."""
import argparse,json,re
from pathlib import Path
from upstream import add_source_argument,baseline,validate_source
ROOT=Path(__file__).resolve().parents[1];parser=argparse.ArgumentParser();add_source_argument(parser);source=validate_source(parser.parse_args().source)
loot_source=source/"data/minecraft/loot_table";loot_out=ROOT/"behavior_pack/loot_tables";structure_source=source/"data/minecraft/structure";structure_out=ROOT/"behavior_pack/structures/matcha"
source_tables={str(p.relative_to(loot_source)) for p in loot_source.rglob('*.json')};all_output_tables={str(p.relative_to(loot_out)) for p in loot_out.rglob('*.json') if not re.search(r' \d+\.json$',p.name)};output_tables={p for p in all_output_tables if not p.startswith('generated/')}
source_templates={str(p.relative_to(structure_source).with_suffix('.mcstructure')) for p in structure_source.rglob('*.nbt')};output_templates={str(p.relative_to(structure_out)) for p in structure_out.rglob('*.mcstructure')}
custom_items=set()
for p in (ROOT/"behavior_pack/items").rglob('*.json'):
 if re.search(r' \d+$',p.stem):continue
 try:custom_items.add(json.loads(p.read_text())["minecraft:item"]["description"]["identifier"])
 except:pass
loot_text='\n'.join(p.read_text() for p in loot_out.rglob('*.json') if not re.search(r' \d+\.json$',p.name));missing_items=sorted(set(re.findall(r'"name": "(matcha:[^"]+)"',loot_text))-custom_items)
references=set(re.findall(r'"name": "loot_tables/([^"]+\.json)"',loot_text));missing_refs=sorted(ref for ref in references if ref not in all_output_tables)
script=(ROOT/"behavior_pack/scripts/structures.js").read_text();main=(ROOT/"behavior_pack/scripts/main.js").read_text();loot_report=json.loads((ROOT/"docs/loot-conversion-report.json").read_text());structure_report=json.loads((ROOT/"docs/structure-conversion-report.json").read_text())
checks=[]
def add(name,expected,actual,detail=""):checks.append({"name":name,"expected":expected,"actual":actual,"status":"pass" if expected==actual else "fail","detail":detail})
add("loot source inventory",282,len(source_tables));add("loot table coverage",source_tables,output_tables,sorted(source_tables-output_tables));add("custom loot result identifiers",[],missing_items);add("internal loot references",[],missing_refs)
expected_translated={"explosion_decay":14,"set_enchantments":1,"set_ominous_bottle_amplifier":2,"set_stew_effect":2}
expected_approximated={"apply_bonus":13,"enchant_randomly":74,"enchant_with_levels":10,"exploration_map":3,"limit_count":1,"set_contents":1}
add("native loot function translations",expected_translated,loot_report.get("translated_functions",{}))
add("documented loot function approximations",expected_approximated,loot_report.get("approximated_functions",{}))
add("no omitted loot functions",{},loot_report["dropped_functions"])
add("generated loot helper tables",16,loot_report.get("generated_helper_tables"))
add("per-table approximation inventory",True,len(loot_report.get("approximation_details",[]))>0 and all(row.get("source_table") and row.get("strategy") for row in loot_report["approximation_details"]))
detail_counts={}
for row in loot_report.get("approximation_details",[]):detail_counts[row["function"]]=detail_counts.get(row["function"],0)+row["occurrences"]
add("approximation detail totals",loot_report.get("approximated_functions"),detail_counts)
fortune_helpers=list((loot_out/"generated/fortune").glob("*.json"));enchant_helpers=list((loot_out/"generated/enchant_options").glob("*.json"))
add("Fortune helper inventory",13,len(fortune_helpers));add("restricted enchantment helper inventory",3,len(enchant_helpers))
fortune_tiers=[]
for path in fortune_helpers:
 data=json.loads(path.read_text());fortune_tiers.append([pool.get("conditions",[{}])[0].get("enchantments",[{}])[0].get("levels") for pool in data["pools"][1:]])
add("Fortune I-III routing",True,all(tiers==[{"min":1,"max":1},{"min":2,"max":2},{"min":3,"max":3}] for tiers in fortune_tiers))
melon=json.loads(next(path for path in fortune_helpers if "matcha:loot_item_d247b21ee8" in path.read_text()).read_text());base_max=melon["pools"][0]["entries"][0]["functions"][0]["count"]["max"]
bonus_max=max((f["count"] for pool in melon["pools"][1:] for entry in pool["entries"] for f in entry.get("functions",[]) if f["function"]=="set_count"),default=0)
add("melon nine-slice cap",True,base_max+bonus_max<=9)
add("structure template inventory",16,len(source_templates));add("mcstructure coverage",source_templates,output_templates,sorted(source_templates-output_templates));add("template pools",4,structure_report['template_pools']);add("structure definitions",5,structure_report['structures']);add("structure sets",1,structure_report['structure_sets'])
for name,needles in {"80/50 placement rule":["SPACING=1280","OFFSET_RANGE=480","SALT=10387312"],"biome routing":["ALLOWED_BIOMES","getBiome"],"stable placement":["candidate(gridX,gridZ)","MARKER"],"weighted pool assembly":["town_centers/well","const ROADS=","const BUILDINGS=","extra_large_2","joint_t"],"script loaded":['import "./structures.js"']}.items():add(name,True,all(x in script+main for x in needles),needles)
for item,path in {"Divine Fragment":"blocks/spawner.json","Crystal Heart":"kleis_items/crystal_heart.json"}.items():add(item+" reachable",True,(loot_out/path).exists() and "matcha:" in (loot_out/path).read_text(),path)
report={"baseline":baseline(),"summary":{"checks":len(checks),"passed":sum(x['status']=='pass' for x in checks),"failed":sum(x['status']=='fail' for x in checks)},"checks":checks,"conversion_limits":{"conservatively_disabled_conditions":loot_report['dropped_conditions'],"translated_functions":loot_report.get('translated_functions',{}),"approximated_functions":loot_report.get('approximated_functions',{}),"omitted_functions":loot_report['dropped_functions']}}
(ROOT/"docs/loot-structure-check-report.json").write_text(json.dumps(report,indent=2,default=lambda x:sorted(x))+"\n")
for row in checks:print(row['status'].upper(),row['name'])
if report['summary']['failed']:raise SystemExit(1)
