# AgniCalendar — Next.js web demo

NASA Space Apps Challenge 2026 — **Harmonization of MODIS and VIIRS Hot Spots**,
Bangladesh. This is the Next.js version of the public web demo. The plain-HTML
demo in `../web/` remains the fallback — same data, same numbers, zero build step.

## What it is

A static Next.js (App Router, plain CSS, no Tailwind, no backend, no login) site
that renders the already-computed harmonized calendar:

- **244,308** raw NASA FIRMS detections (2003–2024) → **117,602** harmonized fire
  events; peak month **2023-04 (4,746 events)**. Every figure comes from
  `src/lib/harmonized.json`, a copy of `../web/data/harmonized.json` — nothing is
  invented, and no number is fetched from a server at runtime.

Pages: `/` dashboard (headline stats, interactive heatmap with click-for-detail,
raw/harmonized yearly chart with toggle, two-year comparison, monthly
climatology, critical-periods table, CSV/JSON downloads), `/critical` (all 13
critical months + early-warning guidance), `/method` (method, sensor-era warning,
limitations, FIRMS sources).

## Run it

```bash
cd web-nextjs
npm install
npm run dev        # http://localhost:3000
```

## Build it (static export)

```bash
npm run build      # writes the static site to out/
```

`next.config.mjs` sets `output: 'export'`, so `out/` works on any static host
with no Node server. Serve it locally to check:

```bash
python3 -m http.server --directory out 8000
# open http://localhost:8000  (and /critical/ and /method/)
```

## Deploy

- **GitHub Pages (project site):** push the repo, then in the repo settings
  enable Pages from GitHub Actions with a workflow that runs `npm install &&
  npm run build` in `web-nextjs/` and uploads `web-nextjs/out/`. If the site
  lives at `https://<user>.github.io/AgniCalender/` (a sub-path, not the domain
  root), set `basePath: '/AgniCalender'` in `next.config.mjs` and rebuild —
  the default config (no basePath) is correct for a custom domain or a
  user/org root site. The plain-HTML `web/` folder needs no basePath change
  and works as-is on Pages, which is why it stays the fallback demo.
- **Vercel:** import the repo, set the Root Directory to `web-nextjs`, and
  deploy. The static export also works there; no server functions are used.
- **Any static host:** upload the contents of `out/` (Netlify Drop, Cloudflare
  Pages, S3, nginx, …). No environment variables, no API keys, no backend.

## Notes

- `node_modules/`, `.next/` and `out/` are gitignored — do not commit them.
- Data is bundled at build time from `src/lib/harmonized.json` (also served
  as `public/data/harmonized.json` for the JSON download button). To update
  the numbers, re-run `python -m backend.processing.harmonize` in the repo
  root, copy the new `web/data/harmonized.json` over both copies here, and
  rebuild.
- This site makes no runtime network calls: no fetch to `localhost:8001`, no
  FIRMS API call, no analytics. It is a static presentation of precomputed data.
