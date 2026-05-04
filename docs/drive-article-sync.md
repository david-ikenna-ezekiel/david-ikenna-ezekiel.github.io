# Drive Article Sync

Use the dedicated Google Drive folder as the publishing inbox for website essays.

## Folder Layout

- `on life`
- `on data`
- `on business`
- `my life story`

The essay folders publish to `essays/*.html` and essay archive pages. The `my life story` folder publishes to `life-story-timeline.html` when the doc slug is `my-life-story`.

## Google Doc Front Matter

Put this block at the top of each Google Doc, then leave a blank line before the article body:

```text
Metadata
title: example essay title
slug: example-essay-title
section: on life
publish_date: 2026-05-04
status: ready
lede: One short sentence for archive pages.
________________
```

Required for publishing:

- `status: ready`

Recommended:

- `title`
- `slug`
- `section`
- `publish_date`
- `lede`

If `slug` is missing, the sync creates one from the title. If `publish_date` is missing, the sync uses the current date.

Extra metadata lines, such as `featured: true`, are ignored for now.

If a new Drive doc uses a slug that already exists on the website but is not already mapped to that same Google Doc ID, the sync stops instead of overwriting the existing essay.

For `my life story`, write each timeline item as:

```text
ages 2-10: The Break-It Era. Timeline copy goes here.
```

## Local Run

```bash
python3 -m pip install google-api-python-client google-auth beautifulsoup4
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json python3 scripts/sync-drive-articles.py
```

Use `--dry-run --verbose` to inspect what would publish without writing files.

## GitHub Action Setup

1. Create a Google service account.
2. Share the Drive article folder with the service account email.
3. Add the service account JSON as a GitHub secret named `GOOGLE_SERVICE_ACCOUNT_JSON`.
4. Optionally add a repository variable named `DRIVE_ARTICLES_FOLDER_URL`.

The daily workflow opens or updates a PR on `codex/drive-article-sync`; it does not push to `main`.
