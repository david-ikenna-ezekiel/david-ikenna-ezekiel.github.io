#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = WORKSPACE_ROOT / "content" / "youtube-catalogue.json"
DEFAULT_OUTPUT = WORKSPACE_ROOT / "youtube-cv-timeline.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render the YouTube catalogue timeline page from JSON metadata."
    )
    parser.add_argument(
        "--input",
        default=str(DEFAULT_INPUT),
        help="Path to the structured YouTube catalogue JSON.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Path to write the rendered HTML page.",
    )
    return parser.parse_args()


def format_relative_age(published_at: str | None, fallback_label: str | None) -> str:
    if not published_at:
        return fallback_label or ""

    published_date = datetime.fromisoformat(published_at).date()
    today = datetime.now(timezone.utc).date()
    delta_days = (today - published_date).days

    if delta_days <= 0:
        return "today"
    if delta_days == 1:
        return "1 day ago"
    if delta_days < 7:
        return f"{delta_days} days ago"
    if delta_days < 30:
        weeks = delta_days // 7
        return f"{weeks} week ago" if weeks == 1 else f"{weeks} weeks ago"
    if delta_days < 365:
        months = delta_days // 30
        return f"{months} month ago" if months == 1 else f"{months} months ago"
    years = delta_days // 365
    return f"{years} year ago" if years == 1 else f"{years} years ago"


def format_duration(duration_seconds: int | None) -> str:
    if not duration_seconds:
        return ""
    total_seconds = int(duration_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def format_tag(video: dict) -> str:
    view_count = video.get("view_count")
    duration_seconds = video.get("duration_seconds")
    if view_count is None and duration_seconds is None:
        return video.get("tag_label") or ""
    pieces = []
    if view_count is not None:
        pieces.append(f"{int(view_count):,} views")
    duration_label = format_duration(duration_seconds)
    if duration_label:
        pieces.append(duration_label)
    return " • ".join(pieces)


def render_article(video: dict) -> str:
    title = escape(video["title"])
    url = escape(video["url"], quote=True)
    age_label = escape(format_relative_age(video.get("published_at"), video.get("age_label")))
    summary = escape(video.get("summary") or "")
    tag_label = escape(format_tag(video))

    tag_html = (
        f'\n              <div class="timeline-tag">{tag_label}</div>'
        if tag_label
        else ""
    )

    return f"""            <article class="timeline-item">
              <div class="timeline-dot"></div>
              <div class="timeline-age">{age_label}</div>
              <div class="timeline-title"><a href="{url}" class="content-link" target="_blank" rel="noopener noreferrer">{title}</a></div>
              <div class="timeline-copy">
                {summary}
              </div>{tag_html}
            </article>"""


def render_html(payload: dict) -> str:
    videos = payload.get("videos", [])
    articles = "\n\n".join(render_article(video) for video in videos)
    channel_name = escape(payload.get("channel_name") or "The Data Signal")
    channel_url = escape(
        payload.get("channel_url") or "https://www.youtube.com/@thedatasignal",
        quote=True,
    )
    sync_date = datetime.fromisoformat(payload["generated_at"]).date().strftime("%B %d, %Y")
    video_count = len(videos)

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>David Ezekiel - YouTube Catalogue</title>
    <meta
      name="description"
      content="Timeline view of {channel_name} uploads."
    />
    <link rel="stylesheet" href="styles.css" />
    <style>
      :root {{
        --essay-title-size: 2.5rem;
        --essay-title-lh: 1em;
        --essay-body-size: 1.1rem;
        --essay-body-lh: 1.6em;
      }}

      .page-wrapp {{
        background-color: #fafbfc;
      }}

      .timeline-page {{
        width: 900px;
        max-width: 94%;
      }}

      .timeline-intro {{
        max-width: 760px;
      }}

      .timeline-wrap {{
        position: relative;
        margin-top: 10px;
        padding-left: 42px;
      }}

      .timeline-wrap::before {{
        content: "";
        position: absolute;
        left: 15px;
        top: 4px;
        bottom: 4px;
        width: 2px;
        background: #d5d8dd;
      }}

      .timeline-item {{
        position: relative;
        margin-bottom: 26px;
        padding-bottom: 2px;
      }}

      .timeline-item:last-child {{
        margin-bottom: 0;
      }}

      .timeline-dot {{
        position: absolute;
        left: -35px;
        top: 7px;
        width: 12px;
        height: 12px;
        border-radius: 999px;
        background: #161717;
        box-shadow: 0 0 0 5px #fafbfc;
      }}

      .timeline-age {{
        opacity: 0.68;
        margin-bottom: 5px;
        font-family: Minion Pro, sans-serif;
        font-size: var(--essay-body-size);
        line-height: var(--essay-body-lh);
      }}

      .timeline-title {{
        margin-bottom: 5px;
        font-family: Minion Pro, sans-serif;
        font-size: var(--essay-body-size);
        font-weight: 500;
        line-height: var(--essay-body-lh);
      }}

      .timeline-copy {{
        max-width: 760px;
        font-family: Minion Pro, sans-serif;
        font-size: var(--essay-body-size);
        line-height: var(--essay-body-lh);
      }}

      .timeline-tag {{
        display: inline-flex;
        margin-top: 10px;
        padding: 4px 9px;
        border-radius: 999px;
        border: 1px solid #d8dbe0;
        font-family: Ppneuemontreal, sans-serif;
        font-size: 0.83rem;
        letter-spacing: 0.02em;
        line-height: 1em;
      }}

      .timeline-link {{
        width: fit-content;
        text-decoration-color: #d7d9de;
      }}

      .timeline-link:hover {{
        text-decoration-color: #ffa568;
      }}

      .timeline-intro .page-heading {{
        letter-spacing: 0;
        text-transform: none;
        margin-bottom: 0;
        font-size: var(--essay-title-size);
        font-weight: 500;
        line-height: var(--essay-title-lh);
      }}

      .timeline-intro .page-subheading {{
        font-size: var(--essay-body-size);
        line-height: var(--essay-body-lh);
      }}

      @media screen and (max-width: 991px) {{
        :root {{
          --essay-title-size: 2.1rem;
          --essay-body-size: 1.05rem;
          --essay-body-lh: 1.6em;
        }}
      }}

      @media screen and (max-width: 767px) {{
        :root {{
          --essay-title-size: 1.7rem;
          --essay-title-lh: 1.15em;
          --essay-body-size: 1rem;
          --essay-body-lh: 1.58em;
        }}

        .timeline-wrap {{
          padding-left: 32px;
        }}

        .timeline-wrap::before {{
          left: 12px;
        }}

        .timeline-dot {{
          left: -24px;
          width: 10px;
          height: 10px;
        }}
      }}
    </style>
  </head>
  <body>
    <div class="page-wrapp min-height">
      <div class="page-contain less timeline-page">
        <div class="content-block">
          <a href="index.html" class="content-link back">Back to homepage</a>
        </div>

        <div class="content-block timeline-intro">
          <h1 class="page-heading">data signal catalogue:</h1>
          <div class="page-subheading">
            every public upload from
            <a href="{channel_url}" class="content-link" target="_blank" rel="noopener noreferrer">@thedatasignal</a>,
            ordered newest to oldest, with a short summary for each video. videos listed: {video_count}. last synced: {sync_date}.
          </div>
        </div>

        <div class="content-block">
          <div class="timeline-wrap">
{articles}
          </div>
        </div>

        <div class="content-block">
          <a href="{channel_url}" class="content-link timeline-link" target="_blank" rel="noopener noreferrer">
            open full channel on youtube
          </a>
        </div>
      </div>
    </div>
    <script src="script.js?v=8"></script>
  </body>
</html>
"""


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()

    payload = json.loads(input_path.read_text(encoding="utf-8"))
    output_path.write_text(render_html(payload), encoding="utf-8")
    print(
        f"Rendered YouTube catalogue page to {output_path.relative_to(WORKSPACE_ROOT)}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
