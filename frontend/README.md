# ScaiLab Frontend

Next.js frontend for prompt-based 3D model generation.

## Local Startup

Run frontend commands from `frontend/`.

1. Install dependencies:

```bash
npm install
```

2. Start the backend API from the repository root:

```bash
python run.py
```

By default the backend runs on `http://localhost:5000`.

3. Start the frontend:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## API URL

The frontend reads the backend URL from `NEXT_PUBLIC_API_BASE_URL`.

The local value is stored in [`.env.example`](./.env.example):

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:5000
```

For another backend, change the value in the environment used to run or deploy the frontend. Use only the API origin, without a trailing slash:

```env
NEXT_PUBLIC_API_BASE_URL=https://demo-api.example.com
```

Do not put secrets in `NEXT_PUBLIC_*` variables. Next.js exposes them to the browser.

If the variable is missing, `services/api.ts` falls back to `http://localhost:5000`.

## Backend Unavailable Fallback

All API calls go through `services/api.ts`. Network failures and `502`, `503`, or `504` responses open a global Service Unavailable modal over the current page.

The retry button checks the backend root endpoint and closes the modal only after the backend responds again.

## Frontend Documentation

The frontend documentation is stored in the repository-level `docs/` directory:

- [`docs/frontend_api_integration.md`](../docs/frontend_api_integration.md) - backend API communication, authentication cookies, generation polling, generated file access, uploads, history, feedback, analytics, and backend availability handling.
- [`docs/frontend_site_functionality.md`](../docs/frontend_site_functionality.md) - main user-facing site behavior, including login, prompt input, generation, preview, download, modification, imported assets, history, feedback, analytics, and service fallback behavior.

## Single-User Demo Deployment

1. Deploy or start the backend API first.
2. Confirm the backend allows the deployed frontend origin for cookies/CORS.
3. Deploy this `frontend` directory as a Next.js app.
4. Set `NEXT_PUBLIC_API_BASE_URL` in the hosting provider environment settings.
5. Build with `npm run build` and run with `npm run start`, or use the included `vercel.json` for Vercel.

The frontend stores no API secrets. Authentication remains cookie-based through the backend.
