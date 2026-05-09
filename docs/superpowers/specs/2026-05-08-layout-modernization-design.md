# Frontend Layout Modernization Design Spec

**Date:** 2026-05-08  
**Direction:** Warm Creative Studio (Approach B - Moderate Refactor)  
**Status:** Approved

## Summary

Deliver a coherent modern shell/layout across home, guided setup, and workspace routes with a warm creative aesthetic. Unify styling to CSS variables (eliminate hardcoded dark/light ternaries), extract 4 shared primitives, and standardize border radii, shadows, and spacing.

## Design Tokens

### Border Radii Scale
| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 6px | Badges, small pills |
| `--radius-md` | 10px | Buttons, inputs, nav icons |
| `--radius-lg` | 14px | Cards, panel containers |
| `--radius-xl` | 20px | Page-level shells |

### Shadow System
| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-card` | `0 1px 4px rgba(0,0,0,0.06)` | Default card elevation |
| `--shadow-card-hover` | `0 4px 12px rgba(0,0,0,0.1)` | Hover state |
| `--shadow-elevated` | `0 8px 24px rgba(0,0,0,0.12)` | Modals, overlays |

### Warm Accent Palette
| Token | Value | Usage |
|-------|-------|-------|
| `--accent-primary` | `#f59e0b` | Primary warm accent (amber-500) |
| `--accent-secondary` | `#d97706` | Darker amber (amber-600) |
| `--accent-subtle` | `#fef3c7` | Tinted backgrounds (amber-100) |
| `--accent-ring` | `rgba(245,158,11,0.3)` | Focus ring color |

### Existing Variables Preserved
All current `--bg-*`, `--text-*`, `--border-*`, and `--color-primary-*` variables remain untouched. New tokens are additive.

## Shared Primitives

### ThemeCard (`components/primitives/ThemeCard.tsx`)
Replaces all hardcoded `isDark ? 'bg-slate-900' : 'bg-white'` patterns.

**Props:**
- `variant: 'elevated' | 'subtle' | 'ghost'` — visual treatment
- `children: ReactNode`
- `className?: string` — additional Tailwind classes

**Behavior:** Uses CSS variables for all colors. No `isDark` prop needed. Consumers just pick a variant.

### PageHeader (`components/primitives/PageHeader.tsx`)
Unified header pattern for route-level pages.

**Props:**
- `title: string` — page title
- `actions?: ReactNode` — right-side action buttons
- `backTo?: string` — optional back navigation URL (renders ArrowLeft + link)

**Behavior:** Matches Layout.tsx header styling. Uses `.page-header` utility class.

### StageIndicator (`components/primitives/StageIndicator.tsx`)
Shows current workflow stage in the WorkspaceShell sidebar.

**Props:**
- `stage: 'planning' | 'writing' | 'review'` — active stage

**Behavior:** Renders small amber dot + stage label at top of sidebar nav. Uses CSS variable colors.

### FieldWrapper (`components/primitives/FieldWrapper.tsx`)
Extracted from ProjectList's inline `Field` component.

**Props:**
- `label: string` — field label text
- `icon: LucideIcon` — label icon
- `children: ReactNode` — input/select/textarea

**Behavior:** Renders label + icon with CSS variable colors. No `isDark` prop. Uses `--text-tertiary` for label, consistent uppercase tracking.

## Per-View Changes

### T1-T2: Layout.tsx (Global Shell)
- Stage switcher active state shadow: use warm amber (`shadow-amber-500/30`)
- Project genre badge: no change (keep `rounded-full` pill shape)
- Mobile stage bar active border: amber color
- Header bg: already uses CSS vars, no change needed

### T3-T4: WorkspaceShell (Sidebar Nav)
- Add StageIndicator component at top of sidebar (above nav items)
- Active nav item background: `--accent-subtle` with `--accent-primary` text (replaces blue-tinted `--color-primary-subtle`)
- Card container border radius: `--radius-lg` (14px, was `rounded-xl` = 12px)
- Nav icon wrapper: `--radius-md` (10px, was `rounded-lg` = 8px)

### T5: Workspace View
- Grid gap: standardize to 12px (`gap-3`)
- Content section + side panels: `--radius-lg` border, `--shadow-card`
- xl breakpoint grid split unchanged (1fr + 20rem)

### T6: ProjectList (Biggest Change)
- Remove all ~80 instances of `isDark ? 'text-slate-XXX' : 'text-slate-YYY'` ternaries
- Hero section: ThemeCard variant="subtle", `--radius-lg`
- Project cards: ThemeCard variant="elevated", hover uses `--shadow-card-hover`
- Create form inputs: `--radius-md`, amber focus ring (`--accent-ring`)
- Inline `Field` component → FieldWrapper primitive
- Search input: CSS variable colors, amber focus ring

### T7: GuidedSetupView
- Inline header → PageHeader with `backTo="/" ` and CTA in `actions` slot
- Outer container: `--radius-xl` (20px)
- LLM health badge: amber/green pill using CSS vars
- "Save Project" button: amber-emerald gradient (was violet-purple)
- Split pane panels: `--radius-lg`, 12px gap
- **Dependency:** Cannot run until guided-setup-readiness and guided-setup-planning plans are shipped

### T8: Global CSS Utilities (index.css)
New utility classes (additive only, no existing selectors modified):
```css
.page-header { /* shared header layout */ }
.page-header__title { /* title typography */ }
.page-header__actions { /* right-side action group */ }
.section-stack { /* vertical card stack with gap-3 */ }
.route-shell { /* page-level container: --radius-xl, bg, overflow-hidden */ }
.warm-badge { /* amber-tinted status pill */ }
```

## Execution Order (All Serial)

1. **T8** — Global CSS utilities (foundation, zero component changes)
2. **T1 → T2** — Layout tests then shell modernization
3. **T3 → T4** — WorkspaceShell tests then nav modernization
4. **T5** — Workspace view structural update
5. **T6** — ProjectList information architecture refresh (largest task)
6. **T7** — GuidedSetupView layout refresh (blocked by other plans)

Track 3 is serial (T5 → T6 → T7), not parallel, to reduce risk during the large ProjectList refactor.

## Verification

After each task:
- `npm run test` — green
- `npm run typecheck` — clean

After all 8 tasks:
- `npm run lint` — zero warnings
- `npm run build` — CSS retained in bundle
- No hardcoded dark/light classes remain in modified files

## Cross-Plan Dependencies
- T7 depends on `guided-setup-readiness` and `guided-setup-planning` plans completing first (both modify FieldPreview.tsx)
- T6 and T7 both use ThemeCard (created in T2)
- T5 uses ThemeCard and CSS variables from T8

## Migration Path to Deep Refactor (Future C)
This spec establishes the foundation for a future deep restructure:
- ThemeCard can evolve into a full component library
- CSS variable system enables responsive grid primitives
- StageIndicator pattern extends to global navigation state
- PageHeader abstraction unifies all route-level headers
