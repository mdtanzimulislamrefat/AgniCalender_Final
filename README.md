# AgniCalendar workspace

**NASA Space Apps Challenge 2026 — Harmonization of MODIS and VIIRS Hot Spots.**
**Start here (judges): the public web demo needs no login, server or APK.** The Next.js version is in `web-nextjs/` (static export — `npm install && npm run build`, then host `out/`; same data, with clickable months, year comparison, raw/harmonized toggle and CSV/JSON download). The plain-HTML version in `web/` (serve `web/` and open `web/index.html`) is the fallback demo. Both show the harmonized burning activity calendar for Bangladesh, 2003–2024: **244,308 raw FIRMS detections → 117,602 harmonized fire events**, peak month **April 2023 (4,746 events)**. Submission pack (project description, 7 slides, 30-sec + 240-sec video scripts, checklist): see [submission/README.md](submission/README.md). Method: [backend/data/output/HARMONIZATION_METHOD.md](backend/data/output/HARMONIZATION_METHOD.md).

Hosting for free (Neon + Render + UptimeRobot) and building the judge APK: see [DEPLOY.md](DEPLOY.md).

One repository with a public web demo, a Flutter app and a Python backend.

```text
web-nextjs/          Next.js demo (static export, no login) — dashboard, /critical, /method
web/                 Plain-HTML harmonized-calendar demo (no login) + web/data/harmonized.json (fallback)
submission/          Submission pack: description, 7 slides, video scripts, checklist
app/                 Flutter AgniCalendar dashboard, map and calendar
backend/
  processing/        NASA FIRMS download, cleanup, calendar pipeline + harmonize.py
  api/               HTTP API, including GET /v1/harmonized/calendar
  storage/           PostgreSQL report persistence
  data/raw/          Downloaded CSV snapshots (gitignored)
  data/output/       JSON reports and legacy migration inputs (gitignored)
  tests/             Python tests
```

## Android app

In `flutter-dev`:

```bash
cd "$HOME/Documents/ChatGPT/nasa_space_chalange_2026/app"
adb reverse tcp:8001 tcp:8001
flutter pub get
flutter run -d UGHILZHQKZ9LEAX8
```

Use `flutter devices` to check your phone's ID. Press `r` to hot reload and `q` to stop. See [app/README.md](app/README.md).

## Backend

FastAPI + PostgreSQL. First follow [backend setup](backend/README.md) to start PostgreSQL, install dependencies and migrate the schema. Then, inside `flutter-dev`, from the repository root:

```bash
cd "$HOME/Documents/ChatGPT/nasa_space_chalange_2026"
source backend/.venv-flutter/bin/activate
python -m pip install -r backend/requirements.lock.txt   # after pulling auth changes
python -m backend.storage.manage migrate                 # schema + AUTH_JWT_SECRET
python -m backend.processing.pipeline --fetch          # optional: the server also fetches automatically
python -m backend.processing.archive                     # multi-year season (once, ~2 min)
python -m backend.processing.recent --days 30           # 7/30-day map (needs free FIRMS_MAP_KEY in backend/.env)
python -m backend.ml.static_sources train                # industrial-source model (after the archive import)
python -m backend.api.server --port 8001
```

Server: `http://127.0.0.1:8001`; summary at `/v1/summary`, calendar at `/v1/calendar`, interactive docs at `/docs`. Ctrl+C stops it. Default data paths resolve inside `backend/data/`. See [backend/README.md](backend/README.md) for historical imports, endpoints and scientific limitations.

## Validation

From the repository root:

```bash
source backend/.venv-flutter/bin/activate
python -m unittest discover -s backend/tests -v
cd app
flutter analyze
flutter test
flutter build apk --debug
```

The Flutter app connects to the backend on port 8001 using USB port forwarding. While running, the server fetches NASA's rolling feeds at startup and every 3 hours (`--fetch-every`); the app's Refresh reloads the newest report. Sign-in is required to view data in the app and API. The web demo in `web/` needs no sign-in.

## Harmonized calendar

```bash
python -m backend.processing.harmonize --years 2003-2024 --products modis,viirs-snpp,viirs-jpss1
```

Same-UTC-day detections within 1.0 km merge into one fire event, regardless of sensor (vegetation fires only, FIRMS type 0; FRP never summed across sensors). Output: `backend/data/output/harmonized_monthly.json` and `web/data/harmonized.json`, served at `GET /v1/harmonized/calendar`. Full method and real numbers: [backend/data/output/HARMONIZATION_METHOD.md](backend/data/output/HARMONIZATION_METHOD.md). The backend does not predict fires; the harmonized calendar is a cleaned historical record, not a forecast.
