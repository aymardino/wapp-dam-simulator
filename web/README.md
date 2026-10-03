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

## Photos, partner logos, video

- **Team photos**: drop square images (JPEG, PNG or WebP, 400 px or more) in `public/team/`, named `kodjovi-plakoo`, `enrico-patane`, `lucien-kouakou`, `mouhamadou-sow`, `wissem-hmila`, `tamsir-diop`, `adrien-atayi` (any of the extensions), then rebuild. Until a file exists, the page shows the person's initials. The list of present files is generated at build time (`scripts/media_manifest.mjs` → `src/data/media.json`).
- **Partner logos**: drop the official files in `public/partners/`, named `mines-paris-psl`, `cma`, `ms-ose`, `senelec` (SVG or PNG), only with each institution's written consent, then rebuild. Until a file exists, the name is shown as text.
- **Video**: set `video` in `src/links.ts` to a YouTube / Vimeo embed URL or to an `.mp4` path; the video section then appears under the hero.
- **Background patterns**: `public/patterns/*.svg` (topographic contours and network mesh, very low opacity), referenced from `src/pages/Landing.tsx`.
