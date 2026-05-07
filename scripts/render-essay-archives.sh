#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
METADATA_FILE="$ROOT_DIR/content/essay-metadata.csv"

if [[ ! -f "$METADATA_FILE" ]]; then
  echo "Missing metadata file: $METADATA_FILE" >&2
  exit 1
fi

format_date() {
  python3 -c 'import datetime, sys; print(datetime.date.fromisoformat(sys.argv[1]).strftime("%B %d, %Y"))' "$1"
}

render_archive() {
  local section="$1"
  local heading="$2"
  local output_file="$3"
  local count
  local items_html=""

  count="$(awk -F'|' -v wanted="$section" '$2 == wanted { count += 1 } END { print count + 0 }' "$METADATA_FILE")"

  while IFS='|' read -r slug row_section title publish_date lede body_mode; do
    local display_date
    display_date="$(format_date "$publish_date")"
    items_html+="          <article class=\"timeline-item\"><div class=\"timeline-dot\"></div><div class=\"timeline-age\">${display_date}</div><div class=\"timeline-title\"><a href=\"essays/${slug}.html\" class=\"content-link\">${title}</a></div><div class=\"timeline-copy\">${lede}</div></article>"$'\n'
  done < <(awk -F'|' -v wanted="$section" '$2 == wanted' "$METADATA_FILE" | sort -t'|' -k4,4r)

  cat > "$output_file" <<HTML
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>David Ezekiel - ${heading} Essays</title>
    <meta name="description" content="All ${section} essays by David Ezekiel." />
    <link rel="stylesheet" href="styles.css" />
    <style>
      :root { --essay-title-size: 2.5rem; --essay-title-lh: 1em; --essay-body-size: 1.1rem; --essay-body-lh: 1.6em; }
      .page-wrapp { background-color: #fafbfc; }
      .timeline-page { width: 900px; max-width: 94%; }
      .timeline-wrap { position: relative; margin-top: 10px; padding-left: 42px; }
      .timeline-wrap::before { content: ""; position: absolute; left: 15px; top: 4px; bottom: 4px; width: 2px; background: #d5d8dd; }
      .timeline-item { position: relative; margin-bottom: 26px; }
      .timeline-dot { position: absolute; left: -35px; top: 7px; width: 12px; height: 12px; border-radius: 999px; background: #161717; box-shadow: 0 0 0 5px #fafbfc; }
      .timeline-age, .timeline-title, .timeline-copy { font-family: Minion Pro, sans-serif; font-size: var(--essay-body-size); line-height: var(--essay-body-lh); }
      .timeline-age { opacity: 0.68; margin-bottom: 4px; }
      .timeline-title { margin-bottom: 4px; font-weight: 500; }
      .timeline-copy { max-width: 760px; }
      .timeline-intro .page-heading { letter-spacing: 0; text-transform: none; margin-bottom: 0; font-size: var(--essay-title-size); font-weight: 500; line-height: var(--essay-title-lh); }
      .timeline-intro .page-subheading { font-size: var(--essay-body-size); line-height: var(--essay-body-lh); }
      @media screen and (max-width: 991px) { :root { --essay-title-size: 2.1rem; --essay-body-size: 1.05rem; --essay-body-lh: 1.6em; } }
      @media screen and (max-width: 767px) {
        :root { --essay-title-size: 1.7rem; --essay-title-lh: 1.15em; --essay-body-size: 1rem; --essay-body-lh: 1.58em; }
        .timeline-wrap { padding-left: 32px; }
        .timeline-wrap::before { left: 12px; }
        .timeline-dot { left: -24px; width: 10px; height: 10px; }
      }
    </style>
  </head>
  <body>
    <div class="page-wrapp min-height">
      <div class="page-contain less timeline-page">
        <div class="content-block"><a href="index.html" class="content-link back">Back to homepage</a></div>
        <div class="content-block timeline-intro"><h1 class="page-heading">on ${section}: all essays</h1><div class="page-subheading">all ${section} essays in one timeline (${count} total).</div></div>
        <div class="content-block"><div class="timeline-wrap">
${items_html}        </div></div>
      </div>
    </div>
      <script src="script.js?v=8"></script>
  </body>
</html>
HTML
}

render_archive "life" "Life" "$ROOT_DIR/essays-life.html"
render_archive "data" "Data" "$ROOT_DIR/essays-data.html"
render_archive "business" "Business" "$ROOT_DIR/essays-business.html"

echo "Rendered essay archive pages from metadata."
