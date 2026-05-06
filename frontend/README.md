# Agro AI — Dashboard (Shathurya P.'s component)

Next.js 16 + React 19 + TypeScript + Tailwind CSS 4 dashboard for the Agro AI big-onion yield prediction project.

## Prerequisites

- Node ≥ 20 (Next.js 16 requirement). Check with `node --version`.
- The Flask backend running on `http://localhost:5050` (see the project root README).

## Quick start

```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Configure environment (only if backend isn't on localhost:5050)
cp .env.local.example .env.local
# edit .env.local if needed

# 3. Start the dev server
npm run dev
# open http://localhost:3000
```

## Pages

| Route | What it does |
|---|---|
| `/` | KPI cards + interactive choropleth + Yala-vs-Maha comparison chart |
| `/predict` | Smart prediction form: pick (district, season, year), auto-fill the 32 features from the dataset, override values, predict |
| `/explainability` | Top-15 SHAP feature attributions |
| `/admin` | Sortable model performance table + RMSE/R² chart |

The sidebar on every page hosts the global district/season/year selector — choices persist via localStorage and propagate across pages.

## How it talks to the backend

The Next.js dev server proxies `/api/backend/*` to the Flask base URL configured in `next.config.ts` (default `http://localhost:5050`). All API calls in `lib/api.ts` go through this proxy so the browser never talks to a different origin.

API contract (verified against `src/api.py`):

- `GET /health`
- `POST /predict` — body has `district`, `season`, and any subset of the 32 numeric features.
- `GET /models/compare` — array of model rows.
- `GET /feature-importance` — array of `{rank, name, mean_abs_shap}`.
- `GET /districts` — districts/seasons/years available for the selectors.
- `GET /context?district=X&season=Y&year=Z` — prefill values for the predict form. Falls back to the (district, season) historical mean if the year isn't in the dataset.

## Build / lint / typecheck

```bash
npm run build       # production build
npm run lint        # ESLint
npx tsc --noEmit    # type check
```

## Stack notes

- **Tailwind 4** with the new `@import "tailwindcss"` and `@theme` syntax (in `app/globals.css`).
- **shadcn-style primitives** in `components/ui/*` are hand-written using Radix UI primitives — no shadcn CLI used because the official templates currently target Tailwind 3.
- **Leaflet** loads with `dynamic(() => ..., { ssr: false })` because it touches `window`.
- **Plotly** uses `plotly.js-dist-min` for tree-shaking — the wrapper in `components/plotly-chart.tsx` lazy-imports it.
- **GeoJSON** for the choropleth lives at `public/sri-lanka-target-districts.geojson` (sourced from the geoBoundaries open dataset, filtered to the four target districts).
