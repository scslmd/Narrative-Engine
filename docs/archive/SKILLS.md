# General Development Skills

## Git & Version Control

### Always Create .gitignore Before Installing Dependencies
- Run `npm install` or similar AFTER creating `.gitignore`
- Prevents accidentally staging `node_modules/`, `vendor/`, etc.
- Standard ignores: dependencies, build output, env files, logs

### Verify Build After Each Feature
- Don't wait until all features complete to run build/typecheck
- Catch errors immediately when context is fresh
- Example: `npm run build` after each React component

## Code Organization

### Establish Import Conventions Early
- Define patterns before writing code (relative vs absolute, barrel exports)
- Document in project README or conventions file
- Consistent imports reduce cognitive load and merge conflicts

### Prefer Flat Directory Structures
- Avoid nested `src/src/` patterns that confuse import paths
- Use clear top-level folders: `components/`, `views/`, `lib/`, `stores/`

## State Management

### Separate Stores by Domain
- Split state into focused stores (theme, navigation, data)
- Makes testing easier and reduces unnecessary re-renders
- Each store should have a single responsibility

### Use Literal Types for Enums
- TypeScript: `type Mode = 'a' | 'b' | 'c'` with `as const`
- Prevents typos in switch statements
- Better autocomplete than string literals

## Component Architecture

### Build Bottom-Up
- UI primitives first (Button, Input)
- Layout shells second (Header, Sidebar)  
- Views last (feature components)
- Each layer testable independently
