#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from html import unescape
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHANNEL_VIDEOS_URL = "https://www.youtube.com/@thedatasignal/videos"
DEFAULT_CHANNEL_HOME_URL = "https://www.youtube.com/@thedatasignal"
DEFAULT_OUTPUT = WORKSPACE_ROOT / "content" / "youtube-catalogue.json"
DEFAULT_FALLBACK_HTML = WORKSPACE_ROOT / "youtube-cv-timeline.html"

ARTICLE_RE = re.compile(r'<article class="timeline-item">(.*?)</article>', re.S)
TITLE_RE = re.compile(
    r'<div class="timeline-title"><a href="([^"]+)"[^>]*>(.*?)</a></div>',
    re.S,
)
AGE_RE = re.compile(r'<div class="timeline-age">(.*?)</div>', re.S)
COPY_RE = re.compile(r'<div class="timeline-copy">\s*(.*?)\s*</div>', re.S)
TAG_RE = re.compile(r'<div class="timeline-tag">(.*?)</div>', re.S)


def collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def strip_tags(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return unescape(value).strip()


def truncate_text(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    clipped = value[: max_chars - 3].rsplit(" ", 1)[0].rstrip(" ,;:")
    return f"{clipped}..."


def summarize_description(description: str, max_chars: int = 220) -> str:
    paragraphs = [
        collapse_whitespace(paragraph)
        for paragraph in re.split(r"\n\s*\n", description.replace("\r", ""))
        if collapse_whitespace(paragraph)
    ]
    for paragraph in paragraphs:
        if not paragraph.lower().startswith(("http://", "https://")):
            return truncate_text(paragraph, max_chars)
    return truncate_text(collapse_whitespace(description), max_chars)


def parse_duration_to_seconds(label: str) -> int | None:
    parts = label.split(":")
    if not parts or any(not chunk.isdigit() for chunk in parts):
        return None
    numbers = [int(chunk) for chunk in parts]
    if len(numbers) == 2:
        minutes, seconds = numbers
        return minutes * 60 + seconds
    if len(numbers) == 3:
        hours, minutes, seconds = numbers
        return (hours * 3600) + (minutes * 60) + seconds
    return None


def extract_video_id(url: str) -> str | None:
    match = re.search(r"[?&]v=([^&]+)", url)
    return match.group(1) if match else None


def parse_html_fallback(fallback_html: Path) -> dict:
    html = fallback_html.read_text(encoding="utf-8")
    videos = []

    for index, article_match in enumerate(ARTICLE_RE.finditer(html)):
        article = article_match.group(1)

        title_match = TITLE_RE.search(article)
        age_match = AGE_RE.search(article)
        copy_match = COPY_RE.search(article)
        tag_match = TAG_RE.search(article)

        if not title_match or not copy_match:
            continue

        url = unescape(title_match.group(1).strip())
        title = strip_tags(title_match.group(2))
        summary = collapse_whitespace(strip_tags(copy_match.group(1)))
        age_label = collapse_whitespace(strip_tags(age_match.group(1))) if age_match else ""
        tag_label = collapse_whitespace(strip_tags(tag_match.group(1))) if tag_match else ""

        view_count = None
        duration_seconds = None
        if tag_label:
            tag_parts = [part.strip() for part in tag_label.split("•")]
            if len(tag_parts) == 2:
                views_match = re.search(r"([\d,]+)\s+views", tag_parts[0], re.I)
                if views_match:
                    view_count = int(views_match.group(1).replace(",", ""))
                duration_seconds = parse_duration_to_seconds(tag_parts[1])

        videos.append(
            {
                "position": index,
                "video_id": extract_video_id(url),
                "title": title,
                "url": url,
                "summary": summary,
                "description": summary,
                "published_at": None,
                "age_label": age_label,
                "view_count": view_count,
                "duration_seconds": duration_seconds,
                "tag_label": tag_label,
            }
        )

    if not videos:
        raise RuntimeError(f"No catalogue entries found in fallback HTML: {fallback_html}")

    return {
        "channel_name": "The Data Signal",
        "channel_url": DEFAULT_CHANNEL_HOME_URL,
        "source_url": DEFAULT_CHANNEL_VIDEOS_URL,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_mode": "html-fallback",
        "videos": videos,
    }


def parse_ytdlp(channel_url: str) -> dict:
    if not shutil.which("yt-dlp"):
        raise FileNotFoundError("yt-dlp is not installed")

    command = [
        "yt-dlp",
        "--dump-single-json",
        "--skip-download",
        "--playlist-end",
        "250",
        channel_url,
    ]
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    entries = payload.get("entries") or []
    videos = []

    for index, entry in enumerate(entries):
        title = collapse_whitespace(entry.get("title") or "")
        if not title:
            continue

        video_id = entry.get("id")
        url = entry.get("webpage_url") or (
            f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
        )
        description = (entry.get("description") or "").strip()
        published_at = None

        if entry.get("timestamp"):
            published_at = datetime.fromtimestamp(
                int(entry["timestamp"]), tz=timezone.utc
            ).isoformat()
        elif entry.get("upload_date"):
            published_at = datetime.strptime(
                entry["upload_date"], "%Y%m%d"
            ).replace(tzinfo=timezone.utc).isoformat()

        videos.append(
            {
                "position": index,
                "video_id": video_id,
                "title": title,
                "url": url,
                "summary": summarize_description(description),
                "description": description,
                "published_at": published_at,
                "age_label": None,
                "view_count": entry.get("view_count"),
                "duration_seconds": entry.get("duration"),
                "tag_label": None,
            }
        )

    if not videos:
        raise RuntimeError(f"yt-dlp returned no entries for {channel_url}")

    videos.sort(
        key=lambda item: (
            item.get("published_at") is not None,
            item.get("published_at") or "",
            -(item.get("position") or 0),
        ),
        reverse=True,
    )

    return {
        "channel_name": payload.get("channel") or payload.get("uploader") or "The Data Signal",
        "channel_url": payload.get("channel_url") or DEFAULT_CHANNEL_HOME_URL,
        "source_url": channel_url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_mode": "yt-dlp",
        "videos": videos,
    }


def write_output(payload: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import The Data Signal YouTube catalogue into structured JSON."
    )
    parser.add_argument(
        "--channel-url",
        default=DEFAULT_CHANNEL_VIDEOS_URL,
        help="YouTube videos tab URL to fetch with yt-dlp.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Where to write the structured JSON catalogue.",
    )
    parser.add_argument(
        "--fallback-html",
        default=str(DEFAULT_FALLBACK_HTML),
        help="Existing rendered HTML page to parse when yt-dlp is unavailable.",
    )
    parser.add_argument(
        "--no-fallback",
        action="store_true",
        help="Fail instead of parsing the current HTML page if yt-dlp import fails.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output).resolve()
    fallback_html = Path(args.fallback_html).resolve()

    try:
        payload = parse_ytdlp(args.channel_url)
        write_output(payload, output_path)
        print(
            f"Imported {len(payload['videos'])} videos from YouTube into {output_path.relative_to(WORKSPACE_ROOT)}."
        )
        return 0
    except Exception as exc:
        if args.no_fallback:
            raise
        payload = parse_html_fallback(fallback_html)
        payload["import_note"] = f"Used HTML fallback because live import failed: {exc}"
        write_output(payload, output_path)
        print(
            f"Imported {len(payload['videos'])} videos from HTML fallback into {output_path.relative_to(WORKSPACE_ROOT)}.",
            file=sys.stderr,
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
