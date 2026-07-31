#!/usr/bin/env python3
"""Audit the unpacked source against the pinned official inventory."""
import argparse, json
from pathlib import Path
from upstream import add_source_argument, baseline, validate_source

parser=argparse.ArgumentParser(); add_source_argument(parser)
source=validate_source(parser.parse_args().source); expected=baseline()["inventory"]
data=source/"data"
actual={
    "recipes":len(list(data.glob("*/recipe/*.json"))),
    "custom_enchantments":len(list((data/"main/enchantment").glob("*.json"))),
    "blessings":len(list((data/"blessings/recipe").glob("*.json"))),
    "villager_trades":len(list((data/"minecraft/villager_trade").rglob("*.json"))),
    "trade_sets":len(list((data/"minecraft/trade_set").rglob("*.json"))),
    "loot_tables":len(list((data/"minecraft/loot_table").rglob("*.json"))),
    "worldgen_files":len(list((data/"minecraft/worldgen").rglob("*.json"))),
}
checks=[{"name":name,"expected":value,"actual":actual[name],"status":"pass" if actual[name]==value else "fail"}
        for name,value in expected.items()]
report={"baseline":baseline(),"checks":checks,"summary":{"checks":len(checks),"passed":sum(x["status"]=="pass" for x in checks),"failed":sum(x["status"]=="fail" for x in checks)}}
(Path(__file__).resolve().parents[1]/"docs/upstream-inventory-report.json").write_text(json.dumps(report,indent=2)+"\n")
for row in checks: print(row["status"].upper(),row["name"],f"{row['actual']}/{row['expected']}")
if report["summary"]["failed"]: raise SystemExit(1)
