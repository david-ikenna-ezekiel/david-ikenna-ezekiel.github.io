# Design Decisions

Use this as a lightweight ADR (Architecture/Design Decision Record) log.

## Format

- Date:
- Decision:
- Why:
- Affected files:
- Rollback:

---

## 2026-03-18 - Minimalist personal-site direction

- Decision: Keep a minimal, content-first layout inspired by shaanpuri.com with serif body typography and generous spacing.
- Why: Fast scanning, strong readability, low visual noise.
- Affected files: `index.html`, `styles.css`, `article-extras.css`.
- Rollback: Revert layout/typography blocks in `styles.css` and page-level inline style overrides.

## 2026-03-18 - Life/Business/Data essay IA split

- Decision: Organize essays into `on life...`, `on data...`, and `on business...`, each with a "view more essays" entry point.
- Why: Makes discovery easier and reduces homepage overload.
- Affected files: `index.html`, `essays-life.html`, `essays-data.html`, `essays-business.html`.
- Rollback: Merge section blocks back into a single list on the homepage.

## 2026-03-18 - Interactive essay rating + shared newsletter module

- Decision: Use `script.js` + `site-config.js` to render rating interactions and newsletter content from shared config.
- Why: Avoid repeated hardcoded text and keep behavior consistent across article pages.
- Affected files: `script.js`, `site-config.js`, `essays/*.html`.
- Rollback: Remove `js-` hooks and restore static HTML in each page.

## 2026-03-18 - Quote emphasis rule

- Decision: Automatically bold text in double quotes at runtime.
- Why: Consistent editorial emphasis without manually editing every page.
- Affected files: `script.js`, `styles.css`, all HTML files that include `script.js`.
- Rollback: Remove `boldQuotedText()` call and `.quoted-text` style.

## 2026-03-18 - Author signature normalization

- Decision: End essays with `- dr. calculus`.
- Why: Consistent author identity and brand voice.
- Affected files: `essays/*.html`, `scripts/generate-essays.sh`.
- Rollback: Bulk replace footer signature text to previous value.

## 2026-04-17 - Essay metadata as single source of truth

- Decision: Store essay metadata in one file with an explicit `publish_date` field and drive article/archive dates from it.
- Why: Avoid hardcoded dates scattered across pages and make new article creation deterministic.
- Affected files: `content/essay-metadata.csv`, `scripts/new-essay.sh`, `scripts/sync-essay-metadata.sh`, `scripts/render-essay-archives.sh`, `scripts/generate-essays.sh`.
- Rollback: Restore the previous CSV/workflow and re-hardcode dates in article/archive pages.

## 2026-04-17 - YouTube catalogue generated from structured metadata

- Decision: Move the YouTube catalogue to a generated workflow backed by structured metadata and a scheduled PR-based refresh.
- Why: Manual edits to `youtube-cv-timeline.html` drift from the actual channel quickly. A generated page keeps content synchronized while still protecting `main`.
- Affected files: `content/youtube-catalogue.json`, `scripts/import-youtube-catalogue.py`, `scripts/render-youtube-catalogue.py`, `scripts/update-youtube-catalogue.sh`, `.github/workflows/youtube-catalogue-refresh.yml`, `youtube-cv-timeline.html`.
- Rollback: Remove the workflow/scripts and revert `youtube-cv-timeline.html` to a static hand-edited page.

## 2026-05-04 - Drive folder as essay publishing inbox

- Decision: Import ready Google Docs from the dedicated Drive article folder into generated essay pages and open daily PRs for changes.
- Why: New essays can be drafted in Drive and published through the existing review workflow without pasting article text into Codex.
- Affected files: `scripts/sync-drive-articles.py`, `content/drive-article-map.json`, `.github/workflows/drive-article-sync.yml`, `docs/drive-article-sync.md`, `content/essay-metadata.csv`, `essays/*.html`.
- Rollback: Disable the workflow, remove the sync script/map, and restore essay files and metadata from version control.
