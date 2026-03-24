# Narrative Engine - Development Guidelines

## Frontend Build Commands

```bash
cd frontend/src
npm run build      # Production build with typecheck
npm run dev        # Development server
npm run lint       # ESLint check
```

## Lessons Learned

### 1. Directory Structure
- **Avoid nested `src/` folders** - Use flat structure: `frontend/src/components/*` not `frontend/src/src/components/*`
- If nesting exists, flatten it immediately to prevent import confusion

### 2. Git Hygiene
- **Always create `.gitignore` BEFORE running `npm install`**
- Standard Node ignore: `node_modules/`, `dist/`, `.env.local`, `*.log`
- Prevents staging warnings and keeps commits clean

### 3. Import Path Conventions
- Establish clear patterns upfront:
  - UI components: `@/components/ui/*` or relative `../components/ui/*`
  - Views: `@/views/*` or relative `../views/*`
  - Stores: `@/stores/*` or relative `../stores/*`
- Document in a separate `CONVENTIONS.md` if team is large

### 4. Build Verification Strategy
- Run `npm run build` after each feature completion
- Catches TypeScript errors, unused variables, and import issues early
- Don't wait until all features are done

### 5. State Management Patterns
- **Separate concerns**: Split stores by domain (theme vs UI navigation)
- Use `as const` for literal types to prevent runtime switch statement bugs
- Example: `type Mode = 'plan' | 'write' | 'review' | 'inspect'`

### 6. Component Architecture
- Keep UI primitives minimal and reusable (Button, Card, Input)
- Build layout shells before views (Layout → WorkspaceShell → Views)
- Test each layer independently before integration

## Quick Fixes Reference

| Issue | Fix |
|-------|-----|
| `node_modules` staged in git | Add `.gitignore`, run `git reset HEAD` |
| Import path errors | Check actual folder structure, use absolute imports with tsconfig paths |
| Unused variable warnings | Run build after each feature, fix immediately |
| CRLF/LF warnings on Windows | Add to `.gitattributes`: `* text=auto` |
