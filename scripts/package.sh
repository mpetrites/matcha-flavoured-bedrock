#!/bin/sh
set -eu

project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
build_dir=$(mktemp -d)
trap 'rm -rf "$build_dir"' EXIT HUP INT TERM

bp_name="Matcha_BP.mcpack"
rp_name="Matcha_RP.mcpack"
addon_name="Matcha_Flavoured_Bedrock_Alpha_0.12.2.mcaddon"

rm -f "$project_dir/dist/$addon_name"

(
  cd "$project_dir/behavior_pack"
  zip -Xqr "$build_dir/$bp_name" . -x "* [0-9].json" "* [0-9].png"
)
(
  cd "$project_dir/resource_pack"
  zip -Xqr "$build_dir/$rp_name" . -x "* [0-9].json" "* [0-9].png"
)
(
  cd "$build_dir"
  # Keep nested names short for mobile importers. Deflate the outer archive to
  # match the packaging format used by the working 0.11.9 release.
  zip -Xq "$project_dir/dist/$addon_name" "$bp_name" "$rp_name"
)

printf 'Built %s\n' "$project_dir/dist/$addon_name"
