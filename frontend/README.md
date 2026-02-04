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

## Stack

- Vue 3 (Composition API)
- Quasar v2 (Material UI)
- Vite
- Pinia (auth, device stores)
- Vue Router (auth guard)

## Backend API

Session auth: login at `/api/auth/login` (JSON or form); cookie `session_id` is set. All `/api/me/*` requests require `X-Device-ID` header (device fingerprint from `src/services/device.js`).
