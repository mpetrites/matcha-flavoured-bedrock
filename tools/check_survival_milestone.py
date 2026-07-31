#!/usr/bin/env python3
"""Static coverage audit for the post-enchantment survival milestone."""
import argparse, json
from pathlib import Path
from upstream import add_source_argument, baseline, validate_source

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(); add_source_argument(parser); source=validate_source(parser.parse_args().source)
script=(ROOT/"behavior_pack/scripts/survival_systems.js").read_text(); main=(ROOT/"behavior_pack/scripts/main.js").read_text()
checks=[]
def add(name,*needles): checks.append({"name":name,"status":"pass" if all(n in script for n in needles) else "fail","evidence":list(needles)})
add("freezing-water biome gate","FROZEN_BIOMES","minecraft:water","slowness","darkness","applyDamage(2)")
add("freezing protection bypass","playerHasEnchantment(player,\"freezing_protection\")")
add("Warding Stone placement","matcha:warding_stone","minecraft:lodestone","matcha_warding_stone_marker")
add("Warding Stone friend regeneration","FRIENDS","regeneration")
add("Warding Stone undead field","UNDEAD","maxDistance:26","applyDamage")
add("Warding Stone recovery","matcha:raw_estus",",7)")
add("Trial Chamber rejection","trial_spawner","minecraft:vault","violently rejects")
add("Bedrock Buster delay and volume","matcha:bedrock_buster","},79)","minecraft:bedrock","y=-3","y<=3")
add("anvil XP window","matcha_anvil_session","addLevels(50)","},300)")
add("global XP removal","player.level>0","resetLevel()")
add("first dragon Nether Star","minecraft:ender_dragon","matcha:first_dragon_reward","minecraft:nether_star")
checks.append({"name":"script loaded","status":"pass" if 'import \"./survival_systems.js\"' in main else "fail","evidence":["main.js import"]})
notes=[
 "Bedrock has no Java repair_cost component or Too Expensive escalation, so Endless Repairs is native behavior rather than a mutation.",
 "Bedrock already evaporates placed water in the Nether.",
 "Official 1.03 labels its Wither-fight experiment as not implemented; no invented boss behavior was added."
]
report={"baseline":baseline(),"summary":{"checks":len(checks),"passed":sum(x["status"]=="pass" for x in checks),"failed":sum(x["status"]=="fail" for x in checks)},"checks":checks,"native_or_not_upstream":notes}
(ROOT/"docs/survival-milestone-report.json").write_text(json.dumps(report,indent=2)+"\n")
for row in checks: print(row["status"].upper(),row["name"])
if report["summary"]["failed"]: raise SystemExit(1)
