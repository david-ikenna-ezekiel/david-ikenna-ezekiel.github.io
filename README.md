# David Ezekiel Personal Site

This repository powers David Ezekiel's minimalist personal website: a content-first home for essays on life, data, and business, alongside curated links, a YouTube catalogue, and supporting profile pages.

Live site:

- [david-ikenna-ezekiel.github.io](https://david-ikenna-ezekiel.github.io)

## Key Files

- Homepage: `index.html`
- Shared styles: `styles.css`
- Shared behavior: `script.js`
- Config: `site-config.js`
- Essay pages: `essays/`

## Documentation

- Docs index: `docs/README.md`
- Design decisions log: `docs/design-decisions.md`
- Automation inventory/runbooks: `docs/automations.md`

## Common Commands

Create a new essay with today's publish date:

```bash
./scripts/new-essay.sh <section> <slug> "<title>" "<lede>"
```

Sync article headers from metadata:

```bash
./scripts/sync-essay-metadata.sh
```

Render archive pages from metadata:

```bash
./scripts/render-essay-archives.sh
```

Generate templated essays from metadata:

```bash
./scripts/generate-essays.sh
```

Update the YouTube catalogue from current channel uploads and rerender the page:

```bash
./scripts/update-youtube-catalogue.sh
```

Force a live YouTube refresh and fail instead of falling back to the current HTML page:

```bash
python3 scripts/import-youtube-catalogue.py --no-fallback
python3 scripts/render-youtube-catalogue.py
```
