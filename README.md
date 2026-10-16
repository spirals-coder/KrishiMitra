# KrishiMitra — Smart Agriculture Chatbot

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/spirals-coder/KrishiMitra)

KrishiMitra is a responsive agriculture guidance demonstration for farmers and college project presentations. It combines a React/Vite dashboard with a Python/FastAPI service, Open-Meteo weather and geocoding, optional backend-only OpenAI chat, and local SQLite conversation history.

## Architecture

- `frontend/`: React single-page application, responsive CSS/Tailwind setup, Recharts forecasts, Lucide icons.
- `backend/app/`: FastAPI REST API, validated Pydantic requests, modular weather and AI providers, transparent crop rules, SQLite history.
- The browser calls the backend using `VITE_API_BASE_URL`. Secrets stay in backend environment variables.

## Run locally

Requirements: Python 3.10+ and Node.js 18+.

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

The API starts at `http://localhost:8000`; interactive API docs are at `/docs`. SQLite is initialized at first startup. Set `DATABASE_PATH` to choose a database location.

### Frontend

In a second terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open the Vite URL (normally `http://localhost:5173`). Set `VITE_API_BASE_URL` before building for a hosted backend, then run `npm run build`; production assets are in `frontend/dist`.

## Optional AI configuration

Set `OPENAI_API_KEY` and optionally `OPENAI_MODEL` in the backend environment to enable chat through the OpenAI Chat Completions API. Never put this key in a `VITE_` variable or frontend file. Without it, chat returns clearly labeled general educational guidance in English or Hindi. An AI vision provider is not implemented; plant health always uses the questionnaire fallback and does not claim image diagnosis.

Weather and geocoding use Open-Meteo public APIs and require network access from the backend. Errors are shown as service unavailable; the app does not substitute simulated weather.

## API endpoints

- `GET /api/health`
- `GET /api/geocode?q=place`
- `GET /api/weather?lat=...&lon=...`
- `POST /api/chat` (optional `conversation_id`, farm `context`)
- `GET /api/chat-history`, `GET /api/chat-history/{id}`, `DELETE /api/chat-history/{id}`
- `POST /api/crop-recommendations`
- `POST /api/fertilizer-guidance`
- `POST /api/plant-health` (multipart form, optional image, maximum 5 MB)
- `POST /api/irrigation-guidance`
- `GET /api/knowledge`

Chat and chat-history requests require the frontend's random `X-Session-ID` UUID. It scopes each browser profile's conversations; it is not account authentication.

## Tests

```powershell
cd backend
pip install -r requirements.txt
pytest
```

Frontend production build check:

```powershell
cd frontend
npm install
npm run build
```

## Deployment

### Render Blueprint

The root `render.yaml` defines a free Render API service and static frontend in Singapore. To publish, use the [Deploy to Render button](https://render.com/deploy?repo=https://github.com/spirals-coder/KrishiMitra) or follow these steps:

1. Push this project to a GitHub repository you control. Keep `.env` files and secrets out of the repository; only the `.env.example` files belong in source control.
2. In Render, choose **New → Blueprint**, connect that repository, and select its branch. Render reads `render.yaml`, builds the frontend and backend, and wires the public API URL into `VITE_API_BASE_URL` and the frontend URL into backend CORS.
3. Review the Blueprint resources and apply them. Auto-deploy is off to avoid deploying this repository into every Render account that uses the button; trigger future deploys manually after pushing changes.
4. After both services are live, open the static site URL and check the API health endpoint at `<API URL>/api/health`.
5. To enable AI chat, add `OPENAI_API_KEY` to the backend service's Environment settings and redeploy. Never add the key to the frontend.

The free Blueprint writes SQLite to `/tmp`, which is intentionally temporary. Chat history is scoped by a browser session ID, but it is lost when the free service restarts, spins down, or redeploys. Free Render web services can spin down after inactivity and take about a minute to wake. For durable history, use paid persistent storage or move the backend to a managed database; confirm current hosting costs before upgrading. Render Blueprints can create the web and static services from one repository, and service environment variables can reference each other's public URLs.

For other hosts, deploy `frontend/dist` as a static site with build-time `VITE_API_BASE_URL` set to the API URL. Run the backend with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, set `CORS_ORIGINS` to the exact frontend origin, and configure `DATABASE_PATH` on persistent storage. SQLite is suitable for a single-instance demonstration; production multi-instance hosting should use a managed database.

## Limitations and safety

- Crop ranking uses small documented heuristics and broad crop descriptions, not a validated district dataset. Sowing dates, input costs, durations, yields, and profits are not numerically predicted. Confirm local varieties and calendars with the district agriculture office or KVK.
- Weather readings and forecasts come from Open-Meteo; forecasts are uncertain and field conditions can differ.
- Fertilizer and irrigation endpoints provide educational considerations only. They do not calculate field rates or schedules. Use soil tests, observed moisture, product labels, and local expert guidance.
- Plant health output lists overlapping possibilities. No image is sent to a vision model. Confirm serious or spreading cases with an agricultural extension officer or plant pathologist; no pesticides are automatically prescribed.
- Government scheme eligibility, benefits, deadlines, and subsidy figures are omitted until verified on current official sources.
- There are no user accounts. Conversation history is scoped to a browser-generated session ID; anyone sharing the same browser profile can access that profile's history. Do not enter sensitive personal information.
- Chat and plant-health endpoints have a basic per-IP in-process limit of 20 requests per minute. It resets on restart and is not shared across instances; add gateway rate limits and authentication before public deployment.

## Troubleshooting

- **Weather/geocoding unavailable:** Check backend network access and Open-Meteo availability. Weather search needs a place name; direct weather requests validate latitude and longitude.
- **Frontend cannot reach API:** Confirm the backend is running and `VITE_API_BASE_URL` points to it. Update backend `CORS_ORIGINS` to the frontend origin and restart.
- **Chat says AI provider is not configured:** This is expected until `OPENAI_API_KEY` is set on the backend. The fallback remains usable.
- **Database is read-only:** Set `DATABASE_PATH` to a writable persistent directory.
- **Image rejected:** Use a genuine JPG, PNG, or WebP image at or below 5 MB.
