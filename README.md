# Matcha Flavoured — Bedrock Edition port

An independent, work-in-progress Bedrock Edition port of Klei Wright's
[Matcha Flavoured](https://modrinth.com/datapack/matcha-flavoured) Java
datapack.

The current alpha is a playable vertical slice, not a complete port. It
implements the first health-food recipes, a bronze alloy and bronze sword,
and the core no-hunger approximation.

## Install

Download the `.mcaddon` from `dist/` and open it with Minecraft. Activate both
the behavior pack and resource pack on a world. This alpha targets Bedrock
1.21.100 or newer.

With cheats enabled, run `/function matcha_alpha_test` for a small test kit.

## Included in alpha 0.2.0

- Health foods: baked apple, fried egg, charred meat, charred fish, and
  charred potato
- Original textures for those foods
- Bronze alloy and bronze sword recipes
- Scripted regeneration effects matching the Java recipes
- Managed-hunger approximation using Bedrock's saturation effect
- 944 generated Bedrock recipe definitions translated from 751
  component-free upstream recipes

See [PORTING_STATUS.md](PORTING_STATUS.md) for exact coverage and known gaps.
The machine-readable conversion audit is in
[`docs/recipe-conversion-report.json`](docs/recipe-conversion-report.json).

## Build

Run:

```sh
./scripts/package.sh
```

The packaged add-on is written to `dist/`.

## Attribution and license

Matcha Flavoured was created by Klei Wright and is distributed under
CC BY-NC-SA 4.0. This port reuses and adapts assets from the original under
the same license. It is unofficial and is not endorsed by the original
creator.

See [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
