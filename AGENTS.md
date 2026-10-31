# Repository notes for automated agents

## What this repo is

A Python simulation prototype of the Chronos Coherence Engine (CCE) plus a
static landing page. There is **no** frontend framework, build step, database or
external API call in the code:

- `index.html` — the only web asset; served at `/` in the preview.
- `CCE` — standalone hardened prototype runtime (no extension); `python CCE` runs
  a 20-report synthetic demo that prints to stdout.
- `cce_test_harness/` — `cce_core.py` reference module with `pytest` suites
  (`test_cce.py`, `test_runtime.py`). Only `pytest` is needed.

## Running it

```bash
docker compose -f docker-compose.base44.yml up -d --build   # web on host port 3000
docker compose -f docker-compose.base44.yml run --rm tests  # pytest suite
docker compose -f docker-compose.base44.yml run --rm web python /app/CCE      # print demo
```

## Quirks

- The web service is `python -m http.server` over the bind-mounted repo, so it
  serves the whole checkout (including the `.zip`/`.pdf` files). Static files are
  read per request: editing `index.html` shows up on refresh, no restart needed.
- The simulation is synthetic by design; output is labelled as such and is not
  financial advice or evidence of savings.
- No credentials are required. `.base44/environment.json` declares no secrets.

## Verifying it works

`curl -s http://localhost:3000/ | grep -q "Chronos Coherence Engine"` and
`docker compose -f docker-compose.base44.yml run --rm tests` both pass.
