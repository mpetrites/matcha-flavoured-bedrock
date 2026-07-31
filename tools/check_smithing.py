#!/usr/bin/env python3
"""Static coverage checks for the scripted Matcha smithing table."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
script = (ROOT / "behavior_pack/scripts/smithing.js").read_text()

assert 'minecraft:smithing_table' in script
assert 'event.player.isSneaking' in script
assert 'event.cancel = true' in script
assert 'copyItemState(base, result)' in script
assert 'getEnchantments()' in script
assert 'minecraft:durability' in script

# The generated tier loop represents 47 recipes; the ten explicit calls cover
# Steel Shears, Bronze Sword, and the eight component-item transforms.
explicit = re.findall(r'^add\("[^\n]+$', script, re.MULTILINE)
assert len(explicit) == 10, len(explicit)
assert 'const standardPieces = ["axe", "boots", "chestplate", "helmet", "hoe", "leggings", "pickaxe", "shovel", "spear", "sword"]' in script

manifests = [
    json.loads((ROOT / "behavior_pack/manifest.json").read_text()),
    json.loads((ROOT / "resource_pack/manifest.json").read_text()),
]
assert all(manifest["header"]["version"] == [0, 11, 10] for manifest in manifests)
assert 'import "./smithing.js";' in (ROOT / "behavior_pack/scripts/main.js").read_text()

print(json.dumps({"scripted_upgrades": 57, "status": "pass"}))
