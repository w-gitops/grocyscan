# GrocyScan Frontend (Vue 3 + Quasar)

Target UI for Homebot. Runs on port **3335** in dev; proxies `/api` and `/health` to the FastAPI backend (port 3334).

## Setup

```bash
npm install
```

## Dev

```bash
npm run dev
```

Open http://localhost:3335. Ensure the backend is running on 3334 (e.g. `uvicorn app.main:app --port 3334`).

## Build

```bash
npm run build
```

Output in `dist/`. Serve with any static host or mount under the same origin as the API for cookie-based auth.

## UI Testing (Playwright)

```bash
npm run test:e2e
```

By default, Playwright builds the frontend and runs tests against `vite preview`
on `http://127.0.0.1:4173`.

To run against a deployed preview (e.g., Vercel), set:

```bash
PLAYWRIGHT_BASE_URL="https://your-preview-url" npm run test:e2e
```

### GitHub Actions + Vercel

The `UI Tests` workflow can deploy a Vercel preview before running tests if you
add these repository secrets:

- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

Without those secrets, the workflow uses a local preview server instead.

## Stack

- Vue 3 (Composition API)
- Quasar v2 (Material UI)
- Vite
- Pinia (auth, device stores)
- Vue Router (auth guard)

## Backend API

Session auth: login at `/api/auth/login` (JSON or form); cookie `session_id` is set. All `/api/me/*` requests require `X-Device-ID` header (device fingerprint from `src/services/device.js`).
