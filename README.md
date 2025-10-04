# JunctionX Uber Challenge

## Tech Stack

### Client

- Bun + React + TypeScript + Vite
- ESLint, Prettier
- Vitest (unit tests)
- Playwright (E2E tests)

### Server

- FastAPI + Python 3.11+
- Hatch (environment management)
- Ruff (linting & formatting)
- SQLAlchemy + SQLite
- Redis

## Development

### Using Docker Compose

Start all services (client, server, redis):

```bash
docker-compose up
```

Services:

- Client: http://localhost:5173
- Server: http://localhost:8000
- Server API docs: http://localhost:8000/docs
- Redis: localhost:6379

### Using VS Code DevContainer

1. Open project in VS Code
2. Install "Dev Containers" extension
3. Press `Cmd/Ctrl + Shift + P` → "Dev Containers: Reopen in Container"
4. Wait for setup to complete (installs dependencies automatically)

Run servers from integrated terminal:

```bash
cd server && hatch run dev
cd client && bun run dev
```

## Commands

### Client

```bash
bun run dev          # Start dev server
bun run build        # Build for production
bun run preview      # Preview production build
bun run test         # Run unit tests
bunx playwright test # Run E2E tests
```

### Server

```bash
hatch run dev        # Start dev server
hatch run test       # Run tests
hatch run lint       # Lint with ruff
hatch run format     # Format with ruff
hatch run check      # Format, lint, and test
```

## Production

Build and run production containers:

```bash
docker-compose -f docker-compose.prod.yml up --build
```

Services:

- Client: http://localhost:3000
- Server: http://localhost:8000
- Server API docs: http://localhost:8000/docs
