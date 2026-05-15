# Site Rules

This is the canonical working document for site rules, operating processes, corrections, and recurring decisions.

Update this file whenever we add a new rule, correct a recurring issue, or change how the site is maintained.

## 1) Repo And Workflow Rules

- Valid repo only:
  - `/Users/davidezekiel/Documents/private_codes/david-ikenna-ezekiel.github.io`
- Ignore the old repo:
  - `/Users/davidezekiel/Documents/private_codes/davidezekiel`
- This repo is both:
  - the source repo
  - the GitHub Pages deploy repo
- Live site:
  - `https://david-ikenna-ezekiel.github.io`
- Custom domain:
  - `https://davidezekiel.com`
- Git rules:
  - always create/use a branch prefixed with `codex/`
  - never push directly to `main`
  - push branch only, then review/merge via PR
- Repo safety rules:
  - keep `.nojekyll` in the repo root
  - before editing, verify the cwd is this Pages repo
  - use `rg` for search
  - use `apply_patch` for focused edits

## 2) Design And Visual Rules

- The site should stay close to the minimalist `shaanpuri.com` model.
- Preserve the current visual language unless an explicit redesign is requested.
- Typography should stay restrained, content-first, and serif-led.
- Primary homepage typeface:
  - `Minion Pro`
- Keep spacing and text rhythm tight enough to feel crisp on both desktop and mobile.
- Quote auto-bold exists globally for text in double quotes, except where explicitly opted out.
- The homepage heading is explicitly opted out of quote auto-bold so the nickname text does not get heavier than the rest of the heading.

## 3) Site Structure Rules

The homepage content structure is:

- `on life...`
- `on data...`
- `on business...`
- `internet hall of fame`
- `socials`
- `resume`
- `my life story`

Supporting pages include:

- individual essay pages
- archive/timeline pages for essay sections
- resume/CV timeline
- life story page
- YouTube catalogue page

## 4) Homepage Content Rules

- Homepage content should include:
  - profile intro
  - project links
  - essay sections
  - socials
  - resume
  - life story
  - subscribe CTA
- Visible life and data essay lists should be sorted descending by `publish_date`.
- Business should contain only real essays, not placeholders.
- Homepage browser title and share metadata should identify David Ezekiel.
- Profile/avatar should identify David Ezekiel.

## 5) Editorial Rules

- Essay titles should publish in lowercase.
- Imported Drive essay titles are normalized to lowercase automatically.
- All essays should end with:
  - `- dr. calculus`
- `my mission` should retain:
  - the asymmetry/leverage/Archimedes framing
  - the faith-based ending
- Current life story eras are:
  - `ages 2-10: The Break-It Era`
  - `ages 10-24: The Search Era`
  - `ages 24-29: The Pivot Era`
  - `ages 29-36: The Dad Era`

## 6) Essay Page Rules

Each individual essay page should include:

- back link
- article body
- interactive `How was this essay?` block
- `more essays...` section
- subscribe section

Current rules for article rendering:

- article recommendations should come from real essays, not placeholder titles
- the `more essays...` block should render the first four configured essays, excluding the current article
- mobile article typography should stay close to Shaan's scale
- mobile blockquotes should stay restrained and not oversized
- in `my mission`, the opening quote attribution should read:
  - `-- David Ezekiel`
- the full quote block is italicized
- the attribution line should not be bold

## 7) Metadata And Source-Of-Truth Rules

Essay metadata single source of truth:

- `content/essay-metadata.csv`

It should remain the source of truth for:

- title
- slug
- section
- lede
- publish date
- manual/generated/import status

Drive sync mapping source:

- `content/drive-article-map.json`

Rules:

- new essays should keep `publish_date`
- new essays can auto-fill today's date, with manual override later
- new Drive docs must not overwrite an existing local essay unless that same Google Doc ID is already mapped to it

## 8) Drive Publishing Inbox Rules

Dedicated Drive root folder:

- `https://drive.google.com/drive/folders/18Gti79TcNumQ2spebP1Ogi-de1CAHkuc`

Tracked folder structure:

- `on life`
- `on data`
- `on business`
- `my life story`

Google Doc front matter should include:

- `title`
- `slug`
- `section`
- `publish_date`
- `status`
- `lede`

Publishing rules:

- a doc publishes only when `status` is `ready`, `publish`, or `published`
- draft or not-ready docs are ignored
- if `slug` is missing, the sync generates one from the title
- if `publish_date` is missing, the sync uses the current date
- imported titles are lowercased automatically

Formatting rules for imported articles:

- article body should render as real paragraphs, not one collapsed block
- if Google HTML export looks structurally collapsed, the sync should rebuild paragraphs from the plain text export
- if a long imported article still looks like one or two giant blocks, the sync should fail instead of silently publishing malformed output
- if a local essay file is structurally malformed, the sync should treat it as needing repair even when the source Drive doc `modifiedTime` has not changed
- bullet-only blocks in plain text should preserve list structure on import

## 9) Archive And Recommendation Rules

Archive pages:

- `essays-life.html`
- `essays-data.html`
- `essays-business.html`

Rules:

- archive pages should reflect `content/essay-metadata.csv`
- if archive generation scripts are used, verify they work in the current environment before assuming generated output is current
- because of prior filesystem-permission issues, some archive updates may have been done manually
- if editing archive pages directly, verify whether the renderer should be rerun or whether the page needs a manual update

Recommendation rules:

- do not show discontinued placeholder essays in `more essays...`
- recommendation data should come from real, maintained site config and metadata-backed content
- on essay pages, `more essays...` should stay within the same category as the current essay
- if a section has fewer than four essays, show only the available essays from that section rather than mixing categories

## 10) Automation Rules

Drive article sync:

- script:
  - `scripts/sync-drive-articles.py`
- this is the main publishing automation for Drive-authored essays

Essay automation helpers:

- `scripts/new-essay.sh`
- `scripts/sync-essay-metadata.sh`
- `scripts/render-essay-archives.sh`

YouTube catalogue automation:

- metadata:
  - `content/youtube-catalogue.json`
- scripts:
  - `scripts/import-youtube-catalogue.py`
  - `scripts/render-youtube-catalogue.py`
  - `scripts/update-youtube-catalogue.sh`
- workflow:
  - `.github/workflows/youtube-catalogue-refresh.yml`

Current YouTube rule:

- it should check weekly
- the importer should retry transient `yt-dlp` failures before failing the run
- if the live YouTube fetch still fails, the workflow log should expose the underlying `yt-dlp` error clearly
- if `yt-dlp` fails, the importer should try the live YouTube channel page before using stale local HTML fallback data
- YouTube catalogue relative ages should not be copied indefinitely from old rendered HTML; live fallback data should be converted into `published_at` estimates so labels keep ageing after render

## 11) Known Pitfalls

- Two similar local repos exist. Only the Pages repo is valid.
- The old repo can be opened by mistake in VS Code.
- Preview/share caches can take time to refresh after deployment.
- Quote auto-bold is global, so heading markup changes can unintentionally change weight.
- A doc that looks correct in Google Docs can still export malformed HTML, so the sync must keep structure validation in place.
- Browser tabs stay blank if favicon links are missing from page `<head>` markup, so new pages and generators should always include the shared site icon.

## 12) Correction Log

### 2026-05-08 - Replace placeholder recommendation essays

- Problem:
  - `more essays...` still showed discontinued placeholder essays
- Correction:
  - moved recommendation rendering to real essays in shared site config
  - updated static fallbacks in existing essay pages and sync/generation scripts

### 2026-05-08 - Repair collapsed essay formatting

- Problem:
  - some imported essays published as one long paragraph despite proper paragraph breaks in the source docs
- Affected essays:
  - `why easy lives feel empty`
  - `the cost of the road not taken`
- Correction:
  - repaired the local essay files
  - added paragraph reconstruction fallback from plain text
  - added structural validation so malformed long essays fail import
  - added local-file repair detection so malformed essays are not skipped as unchanged

### 2026-05-08 - Normalize imported titles to lowercase

- Problem:
  - a new imported essay was published with title casing instead of the site's lowercase convention
- Correction:
  - added automatic lowercase normalization during Drive import
  - corrected current metadata, homepage, archive, and essay-page references

### 2026-05-08 - Keep essay recommendations section-specific

- Problem:
  - `more essays...` mixed life, data, and business links, which broke topical continuity for readers
- Correction:
  - changed shared recommendation rendering to recommend only from the current essay's section
  - removed hardcoded mixed fallback lists from essay templates

### 2026-05-08 - Add a shared favicon across the site

- Problem:
  - browser tabs showed no icon because pages did not declare a favicon
- Correction:
  - added shared favicon and apple-touch-icon links across current pages and page-generation templates

### 2026-05-11 - Expose real YouTube fetch failures in workflow logs

- Problem:
  - the weekly YouTube catalogue workflow failed, but the log only showed a Python wrapper exception after `yt-dlp` exited non-zero
- Correction:
  - added retry behavior around the `yt-dlp` fetch
  - changed the importer to surface the underlying `yt-dlp` stderr/stdout in workflow logs when all retries fail

### 2026-05-13 - Refresh YouTube metadata from live page fallback

- Problem:
  - the catalogue used stale local HTML fallback data, so relative labels like `2 weeks ago` froze and newer uploads were missing
- Correction:
  - added a live YouTube page fallback when `yt-dlp` fails
  - converted live relative age labels into estimated `published_at` values
  - merged live page results with older known catalogue entries so older videos remain listed

### 2026-05-15 - Replace CV placeholders with real concise resume timeline

- Problem:
  - the CV page still used placeholder roles and placeholder education entries
- Correction:
  - updated the page from the official CV Google Doc
  - summarised each experience at a high level instead of copying CV bullets word for word
  - keep certification names linked to their source credential URLs when present in the official CV

## 13) Update Rule

Whenever we change any of the following, update this file in the same pass:

- editorial rules
- homepage structure
- article formatting rules
- automation behavior
- sync validation logic
- recommendation logic
- publishing workflow
- known pitfalls
- recurring corrections

Supporting docs such as `docs/design-decisions.md`, `docs/automations.md`, and `docs/drive-article-sync.md` should stay aligned with this file, but this file is the canonical working reference.
