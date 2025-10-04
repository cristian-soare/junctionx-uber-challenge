# JunctionX Uber Challenge

## Tech Stack

### Client

- Bun + Expo + React Native + TypeScript
- Cross-platform: iOS, Android, Web
- ESLint, Prettier
- Jest (unit tests)

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

- Client (Web): http://localhost:8081
- Client (Mobile): Use Expo Go app and scan QR code from terminal
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
cd client && bunx expo start --web
```

For mobile development, run `bunx expo start` (requires Expo Go app or emulator)

## Commands

### Client

**Development:**
```bash
bunx expo start              # Start Expo dev server (iOS, Android, Web)
bunx expo start --web        # Start web only
bunx expo start --ios        # Start iOS only (macOS required)
bunx expo start --android    # Start Android only
```

**Testing:**
```bash
bun run test                 # Run unit tests (Jest)
bun run test:watch           # Run tests in watch mode
bun run test:coverage        # Run tests with coverage
bun run e2e                  # Run E2E tests (Playwright)
bun run e2e:ui               # Run E2E tests with UI
```

**Code Quality:**
```bash
bun run lint                 # Lint with ESLint (Google rules)
bun run format               # Format with Prettier
bun run type-check           # TypeScript type checking
bun run check                # Run format, lint, type-check, and test
```

**Build:**
```bash
bunx expo export -p web      # Build for web production
bunx expo export -p ios      # Build for iOS production
bunx expo export -p android  # Build for Android production
```

**Mobile Development:**
- Install Expo Go on your phone (iOS/Android)
- Scan QR code from terminal
- Or use iOS Simulator / Android Emulator

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
