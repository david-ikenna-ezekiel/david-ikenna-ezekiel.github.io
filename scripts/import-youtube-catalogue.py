#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CHANNEL_VIDEOS_URL = "https://www.youtube.com/@thedatasignal/videos"
DEFAULT_CHANNEL_HOME_URL = "https://www.youtube.com/@thedatasignal"
DEFAULT_OUTPUT = WORKSPACE_ROOT / "content" / "youtube-catalogue.json"
DEFAULT_FALLBACK_HTML = WORKSPACE_ROOT / "youtube-cv-timeline.html"
YT_DLP_ATTEMPTS = 3
YT_DLP_RETRY_DELAY_SECONDS = 5

ARTICLE_RE = re.compile(r'<article class="timeline-item">(.*?)</article>', re.S)
TITLE_RE = re.compile(
    r'<div class="timeline-title"><a href="([^"]+)"[^>]*>(.*?)</a></div>',
    re.S,
)
AGE_RE = re.compile(r'<div class="timeline-age">(.*?)</div>', re.S)
COPY_RE = re.compile(r'<div class="timeline-copy">\s*(.*?)\s*</div>', re.S)
TAG_RE = re.compile(r'<div class="timeline-tag">(.*?)</div>', re.S)
YOUTUBE_LOCKUP_RE = re.compile(
    r'"metadata":\{"lockupMetadataViewModel":\{"title":\{"content":"(?P<title>(?:\\.|[^"])*)"\}'
    r'.*?"metadataRows":\[\{"metadataParts":\[\{"text":\{"content":"(?P<views>(?:\\.|[^"])*)"\}\},'
    r'\{"text":\{"content":"(?P<age>(?:\\.|[^"])*)"\}\}\]\}'
    r'.*?"url":"/watch\?v=(?P<video_id>[^"&]+)',
    re.S,
)


def collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def strip_tags(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return unescape(value).strip()


def decode_json_string(value: str) -> str:
    return json.loads(f'"{value}"')


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


def normalize_video_id(value: str | None) -> str | None:
    if not value:
        return None
    value = value.split("\\u0026", 1)[0]
    value = value.split("&", 1)[0]
    return value or None


def extract_video_id(url: str) -> str | None:
    match = re.search(r"[?&]v=([^&]+)", url)
    return normalize_video_id(match.group(1)) if match else None


def parse_view_count(label: str) -> int | None:
    cleaned = label.lower().replace("views", "").replace("view", "").strip()
    cleaned = cleaned.replace(",", "")
    match = re.match(r"^([\d.]+)\s*([km])?$", cleaned)
    if not match:
        return None

    number = float(match.group(1))
    suffix = match.group(2)
    if suffix == "k":
        number *= 1_000
    elif suffix == "m":
        number *= 1_000_000
    return int(number)


def estimate_published_at(age_label: str, now: datetime | None = None) -> str | None:
    now = now or datetime.now(timezone.utc)
    label = age_label.lower().strip()

    if label in {"today", "just now"}:
        return now.isoformat()

    match = re.match(r"^(\d+)\s+(minute|hour|day|week|month|year)s?\s+ago$", label)
    if not match:
        return None

    amount = int(match.group(1))
    unit = match.group(2)
    days_by_unit = {
        "minute": 0,
        "hour": 0,
        "day": 1,
        "week": 7,
        "month": 30,
        "year": 365,
    }
    days = amount * days_by_unit[unit]
    if unit == "minute":
        published_at = now - timedelta(minutes=amount)
    elif unit == "hour":
        published_at = now - timedelta(hours=amount)
    else:
        published_at = now - timedelta(days=days)
    return published_at.isoformat()


def format_command_failure(command: list[str], stdout: str, stderr: str, returncode: int) -> str:
    stdout = stdout.strip()
    stderr = stderr.strip()
    parts = [
        f"yt-dlp failed with exit code {returncode}.",
        f"Command: {' '.join(command)}",
    ]

    if stderr:
        parts.append(f"stderr:\n{stderr}")
    if stdout:
        parts.append(f"stdout:\n{stdout}")

    return "\n\n".join(parts)


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


def load_existing_videos(output_path: Path) -> dict[str, dict]:
    if not output_path.exists():
        return {}

    try:
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    videos = {}
    for video in payload.get("videos", []):
        video_id = normalize_video_id(video.get("video_id"))
        if video_id:
            video["video_id"] = video_id
            video["url"] = f"https://www.youtube.com/watch?v={video_id}"
            videos[video_id] = video
    return videos


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_youtube_page(channel_url: str, output_path: Path) -> dict:
    html = fetch_text(channel_url)
    existing_videos = load_existing_videos(output_path)
    try:
        for video in parse_html_fallback(DEFAULT_FALLBACK_HTML).get("videos", []):
            video_id = normalize_video_id(video.get("video_id"))
            if video_id and video_id not in existing_videos:
                video["video_id"] = video_id
                video["url"] = f"https://www.youtube.com/watch?v={video_id}"
                existing_videos[video_id] = video
    except Exception:
        pass

    videos = []
    seen_video_ids = set()
    generated_at = datetime.now(timezone.utc)

    for match in YOUTUBE_LOCKUP_RE.finditer(html):
        video_id = normalize_video_id(match.group("video_id"))
        if not video_id:
            continue
        if video_id in seen_video_ids:
            continue
        seen_video_ids.add(video_id)

        title = collapse_whitespace(decode_json_string(match.group("title")))
        age_label = collapse_whitespace(decode_json_string(match.group("age")))
        views_label = collapse_whitespace(decode_json_string(match.group("views")))
        existing = existing_videos.get(video_id, {})

        videos.append(
            {
                "position": len(videos),
                "video_id": video_id,
                "title": title,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "summary": existing.get("summary") or "",
                "description": existing.get("description") or "",
                "published_at": estimate_published_at(age_label, generated_at),
                "published_at_precision": "estimated-from-relative-age",
                "age_label": None,
                "view_count": parse_view_count(views_label),
                "duration_seconds": existing.get("duration_seconds"),
                "tag_label": existing.get("tag_label"),
            }
        )

    for existing in existing_videos.values():
        video_id = existing.get("video_id")
        if not video_id or video_id in seen_video_ids:
            continue

        copied = dict(existing)
        copied["position"] = len(videos)
        videos.append(copied)
        seen_video_ids.add(video_id)

    if not videos:
        raise RuntimeError(f"No live YouTube page entries found for {channel_url}")

    return {
        "channel_name": "The Data Signal",
        "channel_url": DEFAULT_CHANNEL_HOME_URL,
        "source_url": channel_url,
        "generated_at": generated_at.isoformat(),
        "source_mode": "youtube-page-fallback",
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
    result = None
    failure_messages: list[str] = []

    for attempt in range(1, YT_DLP_ATTEMPTS + 1):
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            break

        failure_messages.append(
            f"Attempt {attempt}/{YT_DLP_ATTEMPTS}\n"
            + format_command_failure(command, result.stdout, result.stderr, result.returncode)
        )

        if attempt < YT_DLP_ATTEMPTS:
            print(
                f"yt-dlp attempt {attempt} failed; retrying in {YT_DLP_RETRY_DELAY_SECONDS}s...",
                file=sys.stderr,
            )
            time.sleep(YT_DLP_RETRY_DELAY_SECONDS)

    if result is None or result.returncode != 0:
        attempts_text = "\n\n---\n\n".join(failure_messages) if failure_messages else "yt-dlp did not run."
        raise RuntimeError(
            f"Unable to fetch YouTube catalogue after {YT_DLP_ATTEMPTS} attempts.\n\n{attempts_text}"
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
        print(f"yt-dlp YouTube import failed: {exc}", file=sys.stderr)

        try:
            payload = parse_youtube_page(args.channel_url, output_path)
            payload["import_note"] = f"Used live YouTube page fallback because yt-dlp failed: {exc}"
            write_output(payload, output_path)
            print(
                f"Imported {len(payload['videos'])} videos from live YouTube page fallback into {output_path.relative_to(WORKSPACE_ROOT)}.",
                file=sys.stderr,
            )
            return 0
        except Exception as fallback_exc:
            if args.no_fallback:
                raise RuntimeError(
                    "Live YouTube page fallback also failed after yt-dlp failed."
                    f"\n\nyt-dlp error:\n{exc}"
                    f"\n\nYouTube page fallback error:\n{fallback_exc}"
                ) from fallback_exc

        if args.no_fallback:
            raise
        payload = parse_html_fallback(fallback_html)
        payload["import_note"] = f"Used local HTML fallback because live imports failed: {exc}"
        write_output(payload, output_path)
        print(
            f"Imported {len(payload['videos'])} videos from HTML fallback into {output_path.relative_to(WORKSPACE_ROOT)}.",
            file=sys.stderr,
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
