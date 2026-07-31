#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
build_dir=$(mktemp -d)
trap 'rm -rf "$build_dir"' EXIT HUP INT TERM

bp_name="Matcha_Flavoured_Alpha_BP_0.4.0.mcpack"
rp_name="Matcha_Flavoured_Alpha_RP_0.4.0.mcpack"
addon_name="Matcha_Flavoured_Bedrock_Alpha_0.4.0.mcaddon"

(
  cd "$project_dir/behavior_pack"
  zip -qr "$build_dir/$bp_name" . -x "* 2.json" "* 2.png"
)
(
  cd "$project_dir/resource_pack"
  zip -qr "$build_dir/$rp_name" . -x "* 2.json" "* 2.png"
)
(
  cd "$build_dir"
  zip -q "$project_dir/dist/$addon_name" "$bp_name" "$rp_name"
)

printf 'Built %s\n' "$project_dir/dist/$addon_name"
