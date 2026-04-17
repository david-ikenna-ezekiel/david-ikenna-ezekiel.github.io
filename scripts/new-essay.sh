#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
METADATA_FILE="$ROOT_DIR/content/essay-metadata.csv"
ESSAYS_DIR="$ROOT_DIR/essays"

if [[ $# -lt 3 ]]; then
  echo "Usage: ./scripts/new-essay.sh <section> <slug> <title> [lede]" >&2
  exit 1
fi

section="$1"
slug="$2"
title="$3"
lede="${4:-}"
publish_date="$(date +%F)"

case "$section" in
  life|data|business) ;;
  *)
    echo "Section must be one of: life, data, business" >&2
    exit 1
    ;;
esac

if [[ ! -f "$METADATA_FILE" ]]; then
  echo "Missing metadata file: $METADATA_FILE" >&2
  exit 1
fi

if rg -n "^${slug}\|" "$METADATA_FILE" >/dev/null 2>&1; then
  echo "Essay slug already exists in metadata: $slug" >&2
  exit 1
fi

mkdir -p "$ESSAYS_DIR"

display_date="$(date -j -f "%Y-%m-%d" "$publish_date" "+%B %d, %Y")"
essay_file="$ESSAYS_DIR/${slug}.html"

if [[ -e "$essay_file" ]]; then
  echo "Essay file already exists: $essay_file" >&2
  exit 1
fi

printf '%s|%s|%s|%s|%s|manual\n' "$slug" "$section" "$title" "$publish_date" "$lede" >> "$METADATA_FILE"

cat > "$essay_file" <<HTML
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${title} - David Ezekiel</title>
    <meta
      name="description"
      content="${title} by David Ezekiel."
    />
    <link rel="stylesheet" href="/styles.css" />
    <link rel="stylesheet" href="../styles.css" />
    <link rel="stylesheet" href="/article-extras.css?v=6" />
    <link rel="stylesheet" href="../article-extras.css?v=6" />
    <link rel="stylesheet" href="/article-subscribe-polish.css?v=6" />
    <link rel="stylesheet" href="../article-subscribe-polish.css?v=6" />
  </head>
  <body>
    <div class="page-wrapp min-height">
      <div class="page-contain less essay-page">
        <div class="content-block essay-top">
          <a href="../index.html" class="content-link back">Back to all essays</a>
        </div>

        <div class="content-block">
          <div class="page-subheading top essay-date">${display_date}</div>
          <h1 class="essay-title">${title}</h1>
        </div>

        <div class="content-block essay-content">
          <p><em>"${lede}"</em></p>
          <p>Replace this scaffold with the real essay body.</p>
          <p>- dr. calculus</p>
        </div>

        <div class="content-block">
          <div class="essay-rating js-essay-rating">
            <p class="essay-rating-title">How was this essay?</p>
            <div class="essay-rating-grid">
              <div class="essay-rating-item"><div class="essay-stars">* * *</div><div class="essay-votes">1632</div></div>
              <div class="essay-rating-item"><div class="essay-stars">* *</div><div class="essay-votes">112</div></div>
              <div class="essay-rating-item"><div class="essay-stars">*</div><div class="essay-votes">14</div></div>
            </div>
          </div>
        </div>

        <div class="content-block">
          <div class="more-essays-heading">more essays...</div>
          <div class="more-essays-list js-more-essays">
            <a class="more-essays-link" href="borrowed-confidence.html">borrowed confidence</a>
            <a class="more-essays-link" href="the-wedge-strategy.html">the wedge strategy</a>
            <a class="more-essays-link" href="one-metric-that-matters.html">one metric that matters</a>
            <a class="more-essays-link" href="the-weekly-operating-system.html">the weekly operating system</a>
          </div>
        </div>

        <div class="content-block">
          <p class="essay-newsletter-text js-newsletter-text">
            I build data products, pipelines&hellip; and everything in between. Join The Data Signal &mdash; let's build together!
          </p>
          <form class="essay-newsletter-form" action="#" method="post">
            <input
              type="email"
              class="essay-newsletter-input js-newsletter-input"
              placeholder="Email address"
              aria-label="Email address"
            />
            <button type="submit" class="essay-newsletter-button js-newsletter-button">Subscribe</button>
          </form>
        </div>
      </div>
    </div>

    <script src="/site-config.js?v=7"></script>
    <script src="../site-config.js?v=7"></script>
    <script src="/script.js?v=8"></script>
    <script src="../script.js?v=8"></script>
  </body>
</html>
HTML

"$ROOT_DIR/scripts/sync-essay-metadata.sh"
"$ROOT_DIR/scripts/render-essay-archives.sh"

echo "Created metadata row and scaffold: $essay_file"
