# Web front end (React, Vite, Tailwind)

Requirements: Node 20 or newer.

```bash
cd web
npm install
npm run dev        # http://localhost:5173, the API must run on http://localhost:8000
npm run build      # produces web/dist, served automatically by the API (uvicorn api.main:app)
```

Structure:

```
src/main.tsx                 routes: / (landing page), /app (hall), /room/:code (trading floor), /desk/:code (trainer desk), /guide/:who
src/api.ts                   typed API client and per-room token storage
src/i18n.ts                  FR / EN strings of the application (the landing page keeps its own dictionary)
src/links.ts                 public links (repository, documentation, technical note)
src/styles.css, tailwind.config.js   design tokens (neutral palette, one accent, two weights, editorial serif for the landing page)
src/components/ui.tsx        Button, Field, Badge, Kpi, Panel, Tabs, Empty, ErrorBox, LangToggle, Header, Bars
src/components/NetworkMap.tsx   geographic network map (Natural Earth), light and dark themes
src/components/Charts.tsx    ECharts charts: prices, dispatch, flows
src/components/PriceHeatmap.tsx zones × hours price heatmap
src/pages/                   Landing, Hall, Room, Desk, Guide
scripts/extract_map.mjs      builds src/data/west_africa.geo.json from world-atlas
scripts/copy_guides.mjs      copies docs/guides into public/guides at build time
```
