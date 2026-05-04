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

The preferred path is the Codex automation, because it can use the connected Google Drive tools directly.

Manual Codex run:

1. Read the Drive root folder and section folders.
2. Compare each ready doc's Drive ID and `modifiedTime` with `content/drive-article-map.json`.
3. Import only new or changed ready docs.
4. Update the matching local page, metadata, map, and archive pages.
5. Commit changes on a `codex/` branch and push that branch only.

The Python helper `scripts/sync-drive-articles.py` remains available for credential-based local runs, but the Codex automation does not require GitHub Actions or a Google service account.
