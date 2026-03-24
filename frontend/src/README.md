# Narrative Engine Frontend

React + TypeScript + Vite frontend for the Narrative Engine.

## Quick Start

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Start dev server
npm run dev
```

## Configuration

Edit `.env.local` to configure:
- `VITE_API_BASE_URL`: Backend API URL (default: http://localhost:8000/api)
- `VITE_USE_MOCKS`: Enable mock services (default: true)
- `VITE_THEME`: Light or dark mode (default: light)
- `VITE_STAGE_THEME`: Stage theme - planning, writing, review, or inspect (default: writing)

## Scripts

- `npm run dev` - Start development server (port 5173)
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build

## Tech Stack

- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- Zustand (state management)
- TanStack Query (server state)
- React Router v6 (routing)
- React Hook Form + Zod (forms)
- TipTap (rich text editor)
- dnd-kit (drag and drop)

## Documentation

- Task specifications: `../../TODO.md`
- API alignment: `../../docs/Frontend API Alignment Summary.md`
- Development readiness: `../../docs/Frontend Development Readiness.md`
