# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
```bash
bun dev          # Start development server at http://localhost:3000 with Turbopack
bun run build    # Build for production with Turbopack
bun start        # Start production server
bun lint         # Run ESLint
```

The project uses `bun` as the package manager (faster than npm). All npm commands work with `bun` prefix.

### Docker
```bash
docker build -t playground-frontend .
docker run -p 3000:3000 playground-frontend
```

## Architecture

This is a Next.js 15 application using App Router with the following key patterns:

### Authentication Flow
- JWT-based authentication with tokens stored in localStorage
- `AuthProvider` in `lib/auth-context.tsx` wraps the entire app and manages auth state
- Protected routes use `components/ProtectedRoute.tsx` component
- Middleware (`middleware.ts`) handles initial route protection
- Sessions expire after 72 hours with automatic cleanup

### API Integration
- Centralized `ApiClient` class in `lib/api.ts` handles all backend communication
- Automatic Bearer token injection from localStorage
- React Query hooks in `lib/hooks.ts` provide caching and state management
- API base URL configured via `NEXT_PUBLIC_API_URL` environment variable

### State Management
- React Query (TanStack Query) for server state with 1-minute cache
- Context API for global auth state
- Local component state for UI interactions

### File Structure
- `/app` - Next.js pages and layouts using App Router
- `/components` - Reusable React components
- `/lib` - Core utilities, API client, hooks, and providers
- `/types` - TypeScript type definitions matching backend contracts

### Key Technologies
- Next.js 15 with React 19 and TypeScript 5
- Tailwind CSS v4 for styling
- React Query for data fetching and caching
- Turbopack for fast development builds

## Implementation Status

### Working Features
- User authentication (login/logout)
- Protected route system
- Session management with countdown timer
- API client with auth headers

### Placeholder Features (UI only, no backend integration)
- Document upload and management
- Chat interface
- Export functionality

## Environment Variables

Required in `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MAX_FILE_SIZE_MB=100
NEXT_PUBLIC_ALLOWED_FILE_TYPES=.pdf,.txt,.docx
```

## Development Notes

- Authentication is fully functional - use existing patterns in `lib/auth-context.tsx` and `lib/api.ts`
- Follow established React Query patterns in `lib/hooks.ts` when adding new API calls
- All new components should use TypeScript with types from `types/index.ts`
- Maintain consistency with existing Tailwind utility classes for styling
- Backend API exists at port 8000 but most endpoints return placeholder data