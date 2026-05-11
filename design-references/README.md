# Design References

Curated collection of [DESIGN.md](https://stitch.withgoogle.com/docs/design-md/overview/) files from popular brand design systems.

**Source:** [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) (MIT License)

## What is DESIGN.md?

A plain-text design system document that AI agents read to generate consistent UI. Drop one into your project and any AI coding agent instantly understands how the UI should look — colors, typography, spacing, components, do's and don'ts.

## Structure

Each directory contains a `DESIGN.md` file extracted from the corresponding brand's website:

| Directory | Brand | Key Characteristics |
|---|---|---|
| `raycast/` | Raycast | Dark canvas, command-palette cards, Inter + ss03, hairline borders, surface ladder |
| `linear.app/` | Linear | Deepest dark (#010102), lavender-blue accent, negative tracking, product-screenshot-led |
| `notion/` | Notion | Warm minimalism, serif headings, soft surfaces, editorial layout |
| `vercel/` | Vercel | Black-and-white precision, Geist font, geometric cards |
| `cursor/` | Cursor | Dark IDE interface, gradient accents, code-forward |
| `warp/` | Warp | Dark terminal UI, block-based commands, JetBrains Mono |
| ...and 64 more | — | See directory listing |

## Usage

For launcher/desktop UI work:
- **Raycast** — best reference for tray launchers, status popups, command palettes
- **Linear** — best reference for minimal dark UI, status indicators, hairline cards
- **Notion** — best reference for warm, approachable desktop chrome

For web/frontend work:
- Pick any brand that matches your target aesthetic.

## Adding New Designs

```bash
npx getdesign@latest add <brand-name>
mv design-md/<brand-name>/design.md design-references/<brand-name>/DESIGN.md
```

Or request custom designs at [getdesign.md/request](https://getdesign.md/request).
