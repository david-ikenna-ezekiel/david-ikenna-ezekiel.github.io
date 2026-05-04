# Automations And Runbooks

This file tracks every automation-like behavior used by the site.

## 1) Build-time automation

### Essay page generation

- Name: `generate-essays`
- Trigger: Manual run when `content/essay-metadata.csv` changes for `generated` essays
- Source: `scripts/generate-essays.sh`
- Command:
  ```bash
  ./scripts/generate-essays.sh
  ```
- Inputs: `content/essay-metadata.csv`
- Outputs: `essays/*.html`
- Notes:
  - Only rows marked `generated` are rendered by this script.
  - Hand-written essays remain manual and are not overwritten.
- Rollback:
  - Restore prior `essays/*.html` files from version control.

### New essay scaffold + metadata entry

- Name: `new-essay`
- Trigger: Manual run when starting a new essay
- Source: `scripts/new-essay.sh`
- Command:
  ```bash
  ./scripts/new-essay.sh <section> <slug> "<title>" "<lede>"
  ```
- Inputs:
  - `content/essay-metadata.csv`
  - section: `life`, `data`, or `business`
- Outputs:
  - appends a metadata row with today's ISO date as `publish_date`
  - creates `essays/<slug>.html`
  - refreshes archive pages
- Notes:
  - `publish_date` auto-fills with the current date and can be edited later in metadata.

### Metadata sync

- Name: `sync-essay-metadata`
- Trigger: Manual run after editing titles or publish dates in metadata
- Source: `scripts/sync-essay-metadata.sh`
- Command:
  ```bash
  ./scripts/sync-essay-metadata.sh
  ```
- Inputs: `content/essay-metadata.csv`
- Outputs:
  - updates article titles, meta descriptions, and displayed publish dates in `essays/*.html`

### Archive rendering

- Name: `render-essay-archives`
- Trigger: Manual run after editing metadata
- Source: `scripts/render-essay-archives.sh`
- Command:
  ```bash
  ./scripts/render-essay-archives.sh
  ```
- Inputs: `content/essay-metadata.csv`
- Outputs:
  - `essays-life.html`
  - `essays-data.html`
  - `essays-business.html`

### YouTube catalogue refresh

- Name: `update-youtube-catalogue`
- Trigger: Manual run when you want to refresh the catalogue locally
- Source:
  - `scripts/import-youtube-catalogue.py`
  - `scripts/render-youtube-catalogue.py`
  - `scripts/update-youtube-catalogue.sh`
- Command:
  ```bash
  ./scripts/update-youtube-catalogue.sh
  ```
- Inputs:
  - YouTube channel videos page: `https://www.youtube.com/@thedatasignal/videos`
  - fallback source: `youtube-cv-timeline.html` when `yt-dlp` is unavailable locally
- Outputs:
  - `content/youtube-catalogue.json`
  - `youtube-cv-timeline.html`
- Notes:
  - Local runs allow HTML fallback so the page can still be regenerated without network access.
  - CI runs use `--no-fallback` so a failed fetch does not silently reuse stale data.

### Drive article sync

- Name: `sync-drive-articles`
- Trigger: Manual run when checking the publishing inbox locally
- Source: `scripts/sync-drive-articles.py`
- Command:
  ```bash
  GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json python3 scripts/sync-drive-articles.py
  ```
- Inputs:
  - Dedicated Drive folder: `https://drive.google.com/drive/folders/18Gti79TcNumQ2spebP1Ogi-de1CAHkuc`
  - Section folders named `on life`, `on data`, and `on business`
  - Google Docs with front matter including `status: ready`
- Outputs:
  - `essays/*.html`
  - `life-story-timeline.html`
  - `content/essay-metadata.csv`
  - `content/drive-article-map.json`
  - refreshed essay archive pages
- Notes:
  - Draft docs are ignored unless `status` is `ready`, `publish`, or `published`.
  - The tracking map stores Google Doc IDs so reruns update the same essay instead of duplicating it.
  - New Drive docs cannot overwrite existing manual essays or metadata rows unless an explicit Doc ID mapping already exists.
  - The script appends `- dr. calculus` if the imported article body does not already include it.
- Rollback:
  - Restore generated essay files, metadata, map, and archive pages from version control.

## 2) Repository automations (GitHub Actions)

### Biweekly YouTube catalogue PR

- Name: `youtube-catalogue-refresh`
- Trigger:
  - scheduled weekly on Monday, but only proceeds on even ISO weeks
  - manual `workflow_dispatch`
- Source: `.github/workflows/youtube-catalogue-refresh.yml`
- Behavior:
  - installs `yt-dlp`
  - refreshes `content/youtube-catalogue.json`
  - rerenders `youtube-cv-timeline.html`
  - opens or updates a PR on branch `codex/youtube-catalogue-refresh`
- Why:
  - keeps `main` protected from silent content changes
  - matches the repo rule of reviewing updates through PRs
- Rollback:
  - disable or delete `.github/workflows/youtube-catalogue-refresh.yml`
  - manually edit or restore `content/youtube-catalogue.json` and `youtube-cv-timeline.html`

### Daily Drive article PR

- Name: `drive-article-sync`
- Trigger:
  - scheduled daily at 08:00 UTC
  - manual `workflow_dispatch`
- Source: `.github/workflows/drive-article-sync.yml`
- Behavior:
  - installs Google Drive sync dependencies
  - scans the dedicated Drive article folder
  - imports only ready Google Docs
  - opens or updates a PR on branch `codex/drive-article-sync`
- Required GitHub configuration:
  - Secret: `GOOGLE_SERVICE_ACCOUNT_JSON`
  - Optional variable: `DRIVE_ARTICLES_FOLDER_URL`
  - The Drive article folder must be shared with the service account email.
- Rollback:
  - disable or delete `.github/workflows/drive-article-sync.yml`
  - restore the changed essay, metadata, map, and archive files from version control

## 3) Runtime automations (in-browser)

### Shared newsletter + rating renderer

- Name: `shared-page-enhancements`
- Trigger: `DOMContentLoaded`
- Source: `script.js` (uses values in `site-config.js`)
- Behavior:
  - Injects shared newsletter copy/labels (`.js-newsletter-*`).
  - Renders "more essays" links (`.js-more-essays`).
  - Enables interactive essay rating with localStorage state (`.js-essay-rating`).
- Rollback:
  - Remove script includes from pages or remove specific renderer calls in `script.js`.

### Quote emphasis

- Name: `quoted-text-bold`
- Trigger: `DOMContentLoaded`
- Source: `script.js` + `.quoted-text` style in `styles.css`
- Behavior:
  - Finds text wrapped in double quotes and wraps it in `<strong class="quoted-text">...</strong>`.
- Constraints:
  - Skips links, code, script/style/input-like elements.
- Rollback:
  - Remove `boldQuotedText()` from `script.js` and delete `.quoted-text` rule in `styles.css`.

## 4) Change Checklist (for future automations)

When adding a new automation, document:

1. Name and owner.
2. Trigger (manual, on build, on page load, scheduled).
3. Exact command or file/function source.
4. Inputs and outputs.
5. Failure mode and rollback steps.
