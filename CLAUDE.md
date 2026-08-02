# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Post-test cleanup (always do this)

- **Kill all headless browser instances after test runs.** Any test, demo, or
  video-generation run that launches a browser (Chromium, headless_shell,
  Playwright, Puppeteer, chromedriver) must not leave processes behind. After
  the run finishes — pass or fail — check and kill leftovers:

  ```bash
  pkill -f "headless_shell" ; pkill -f "chromium" ; pkill -f "chrome.*--headless" ; pkill -f "playwright" ; true
  ps aux | grep -iE "chrom|headless|playwright" | grep -v grep   # verify nothing remains
  ```

- **Clear caches after heavy install/test cycles.** Free disk before ending a
  session or when space runs low:

  ```bash
  npm cache clean --force
  pnpm store prune 2>/dev/null
  rm -rf ~/.cache/uv ~/.cache/pip
  rm -rf ui/.next ui/node_modules/.cache
  ```

  Also sweep temp dirs for stray browser downloads and build logs
  (e.g. `/tmp/<chrome-version>/`, `node-compile-cache`, `ruby-build.*.log`).

- **Audit the machine for further cleanup opportunities.** After cleanup,
  look for anything else consuming space or resources: large tracked binaries,
  orphaned work dirs, duplicate lockfiles, leftover server processes
  (`uvicorn`, `next dev`). Report findings rather than silently deleting
  anything that is tracked in git or user-created.

## Known audit findings (as of 2026-08-02)

- `test videos/` is listed in `.gitignore` but ~18 MB of MP4s are already
  tracked in git (added before the ignore rule). `docs/demo/` (~40 MB) and
  `docs/videos/` (~9 MB) also hold large media; git pack is ~108 MB. Removing
  these from history would need a coordinated rewrite — don't do it unilaterally.
- `ui/` contains both `package-lock.json` and `pnpm-lock.yaml`; pick one
  package manager to avoid drift.
- `python-backend/generate_test_videos.py` uses macOS-only paths
  (`/private/tmp`, `/Library/Fonts`) — it will not run on Linux CI containers.

## Project layout

- `ui/` — Next.js frontend (Tailwind, shadcn-style components).
- `python-backend/` — FastAPI voice-agent backend (`start_server.py`,
  `api.py`, tools modules, `rag_docs/` reference PDFs).
- `test videos/` — generated sample-call MP4s (regenerate with
  `python-backend/generate_test_videos.py`).
- `docs/` — deployment docs, demo media, screenshots.
