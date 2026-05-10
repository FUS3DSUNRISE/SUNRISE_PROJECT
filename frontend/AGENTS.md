<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

## Frontend Team Startup

- Run frontend commands from `frontend/`.
- Install dependencies with `npm ci`.
- Copy `.env.example` to `.env.local` and set `NEXT_PUBLIC_API_BASE_URL` to the backend API origin.
- Start the backend service separately before using API-backed UI flows. The local dependency is `python run.py` from the repository root, which serves Flask on `http://localhost:5000` by default.
- Start the frontend with `npm run dev` and open `http://localhost:3000`.

## API Configuration

- Use `NEXT_PUBLIC_API_BASE_URL` for browser API calls. Do not hard-code backend origins in components.
- Keep secrets out of `NEXT_PUBLIC_*` variables because they are exposed to the browser.
- Route API calls through `services/api.ts` so backend-unavailable handling stays global.
