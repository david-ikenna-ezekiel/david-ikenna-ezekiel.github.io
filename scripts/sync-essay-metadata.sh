#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
METADATA_FILE="$ROOT_DIR/content/essay-metadata.csv"
ESSAYS_DIR="$ROOT_DIR/essays"

if [[ ! -f "$METADATA_FILE" ]]; then
  echo "Missing metadata file: $METADATA_FILE" >&2
  exit 1
fi

format_date() {
  date -j -f "%Y-%m-%d" "$1" "+%B %d, %Y"
}

while IFS='|' read -r slug section title publish_date lede body_mode; do
  [[ -z "$slug" ]] && continue

  essay_file="$ESSAYS_DIR/${slug}.html"
  if [[ ! -f "$essay_file" ]]; then
    continue
  fi

  display_date="$(format_date "$publish_date")"
  export TITLE="$title"
  export DISPLAY_DATE="$display_date"
  export DESCRIPTION="${title} by David Ezekiel."
  export LEDE="$lede"
  export BODY_MODE="$body_mode"

  perl -0pi -e '
    s#<title>.*?</title>#<title>$ENV{TITLE} - David Ezekiel</title>#s;
    s#content="[^"]* by [^"]*\."#content="$ENV{DESCRIPTION}"#s;
    s#(<div class="page-subheading top essay-date">).*?(</div>)#$1$ENV{DISPLAY_DATE}$2#s;
    s#(<h1 class="essay-title">).*?(</h1>)#$1$ENV{TITLE}$2#s;
    if ($ENV{BODY_MODE} eq "generated" && length $ENV{LEDE}) {
      s#<p><em>".*?"</em></p>#<p><em>"$ENV{LEDE}"</em></p>#s;
    }
  ' "$essay_file"
done < "$METADATA_FILE"

echo "Synced essay metadata into article headers."
