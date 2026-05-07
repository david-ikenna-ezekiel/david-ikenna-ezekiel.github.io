#!/usr/bin/env python3
"""Import ready Google Docs from the website article Drive folder."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_FOLDER_URL = "https://drive.google.com/drive/folders/18Gti79TcNumQ2spebP1Ogi-de1CAHkuc"
DRIVE_FOLDER_RE = re.compile(r"/folders/([A-Za-z0-9_-]+)")
DRIVE_OPEN_RE = re.compile(r"[?&]id=([A-Za-z0-9_-]+)")
DOC_URL_RE = re.compile(r"/d/([A-Za-z0-9_-]+)")

SECTION_FOLDERS = {
    "on life": "life",
    "life": "life",
    "on data": "data",
    "data": "data",
    "on business": "business",
    "business": "business",
}

LIFE_STORY_FOLDERS = {"my life story"}
LIFE_STORY_SLUG = "my-life-story"
LIFE_STORY_PATH = "life-story-timeline.html"
LIFE_STORY_TAGS = {
    "The Break-It Era": "lesson: curiosity often looks like chaos",
    "The Search Era": "theme: identity gets forged in search",
    "The Pivot Era": "lesson: pivots create new futures",
    "The Dad Era": "focus: family, craft, compounding",
}

ALLOWED_TAGS = {
    "a",
    "br",
    "em",
    "h2",
    "h3",
    "li",
    "ol",
    "p",
    "strong",
    "ul",
}

FRONT_MATTER_KEYS = {"title", "slug", "section", "publish_date", "status", "lede"}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def folder_id_from(value: str) -> str:
    for pattern in (DRIVE_FOLDER_RE, DRIVE_OPEN_RE, DOC_URL_RE):
        match = pattern.search(value)
        if match:
            return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]+", value):
        return value
    raise ValueError(f"Could not parse a Google Drive folder ID from: {value}")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    if not value:
        raise ValueError("Slug cannot be empty.")
    return value


def today_iso() -> str:
    return dt.date.today().isoformat()


def format_display_date(value: str) -> str:
    date_value = dt.date.fromisoformat(value)
    return date_value.strftime("%B %d, %Y")


def pipe_safe(value: str, field_name: str) -> str:
    if "|" in value:
        raise ValueError(f"{field_name} cannot contain '|': {value}")
    return value


def load_service():
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise SystemExit(
            "Missing Google API dependencies. Install with:\n"
            "python3 -m pip install google-api-python-client google-auth beautifulsoup4"
        ) from exc

    scopes = ["https://www.googleapis.com/auth/drive.readonly"]
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "").strip()

    if service_account_json:
        info = json.loads(service_account_json)
        credentials = service_account.Credentials.from_service_account_info(info, scopes=scopes)
    else:
        credentials_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
        if not credentials_file:
            raise SystemExit(
                "Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS before syncing Drive articles."
            )
        credentials = service_account.Credentials.from_service_account_file(credentials_file, scopes=scopes)

    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def list_children(service, folder_id: str) -> list[dict[str, Any]]:
    query = f"'{folder_id}' in parents and trashed = false"
    response = (
        service.files()
        .list(
            q=query,
            fields="files(id,name,mimeType,modifiedTime,webViewLink)",
            pageSize=1000,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            orderBy="name",
        )
        .execute()
    )
    return response.get("files", [])


def export_doc(service, file_id: str, mime_type: str) -> str:
    data = service.files().export(fileId=file_id, mimeType=mime_type).execute()
    if isinstance(data, bytes):
        return data.decode("utf-8")
    return str(data)


def parse_front_matter(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    seen_any = False

    for raw_line in text.splitlines():
        line = raw_line.strip().lstrip("\ufeff")
        if line.lower() == "metadata" or re.fullmatch(r"[_-]{3,}", line):
            continue
        if not line:
            if seen_any:
                break
            continue

        match = re.match(r"^([A-Za-z_]+)\s*:\s*(.*)$", line)
        if not match:
            if seen_any:
                break
            continue

        key = match.group(1).lower()
        seen_any = True
        if key in FRONT_MATTER_KEYS:
            metadata[key] = match.group(2).strip()

    return metadata


def strip_front_matter_text(text: str) -> str:
    lines = text.splitlines()
    body_start = 0
    seen_any = False

    for index, raw_line in enumerate(lines):
        line = raw_line.strip().lstrip("\ufeff")
        if line.lower() == "metadata" or re.fullmatch(r"[_-]{3,}", line):
            body_start = index + 1
            continue
        if not line:
            if seen_any:
                body_start = index + 1
                break
            body_start = index + 1
            continue
        if re.match(r"^[A-Za-z_]+\s*:", line):
            seen_any = True
            body_start = index + 1
            continue
        if seen_any:
            body_start = index
            break

    return "\n".join(lines[body_start:]).strip()


def render_article_html_from_text(text: str) -> str:
    body = strip_front_matter_text(text)
    fragments: list[str] = []

    for chunk in re.split(r"\n\s*\n", body):
        lines = [line.strip() for line in chunk.splitlines() if line.strip()]
        if not lines:
            continue

        if all(re.match(r"^[-*]\s+", line) for line in lines):
            items = []
            for line in lines:
                cleaned = re.sub(r"^[-*]\s+", "", line)
                items.append(f"<li>{html.escape(cleaned)}</li>")
            items_html = "".join(items)
            fragments.append(f"<ul>{items_html}</ul>")
            continue

        paragraph = " ".join(lines).strip()
        if paragraph:
            fragments.append(f"<p>{html.escape(paragraph)}</p>")

    body_html = "\n".join(f"          {line}" for line in fragments)
    if "- dr. calculus" not in body_html.lower():
        body_html += "\n          <p>- dr. calculus</p>"
    return body_html


def article_structure_metrics(body_html: str) -> dict[str, int]:
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise SystemExit("Missing beautifulsoup4. Install with: python3 -m pip install beautifulsoup4") from exc

    soup = BeautifulSoup(body_html, "html.parser")
    text = soup.get_text(" ", strip=True)
    paragraphs = len([tag for tag in soup.find_all("p") if tag.get_text(" ", strip=True)])
    lists = len(soup.find_all(["ul", "ol"]))
    headings = len(soup.find_all(["h2", "h3"]))
    total_blocks = paragraphs + lists + headings
    longest_paragraph = max(
        (len(tag.get_text(" ", strip=True)) for tag in soup.find_all("p")),
        default=0,
    )
    return {
        "paragraphs": paragraphs,
        "lists": lists,
        "headings": headings,
        "total_blocks": total_blocks,
        "text_length": len(text),
        "longest_paragraph": longest_paragraph,
    }


def validate_article_structure(title: str, body_html: str) -> None:
    metrics = article_structure_metrics(body_html)
    if metrics["text_length"] < 900:
        return
    if metrics["total_blocks"] >= 3:
        return
    if metrics["paragraphs"] >= 2 and metrics["longest_paragraph"] < 1400:
        return
    raise ValueError(
        f"Imported article '{title}' looks structurally collapsed "
        f"({metrics['paragraphs']} paragraphs, {metrics['total_blocks']} blocks, "
        f"longest paragraph {metrics['longest_paragraph']} chars)."
    )


def clean_article_html(source_html: str, text_export: str, title: str) -> str:
    try:
        from bs4 import BeautifulSoup
        from bs4.element import Tag
    except ImportError as exc:
        raise SystemExit("Missing beautifulsoup4. Install with: python3 -m pip install beautifulsoup4") from exc

    soup = BeautifulSoup(source_html, "html.parser")
    body = soup.body or soup

    for tag in body.find_all(["script", "style"]):
        tag.decompose()

    removed_front_matter = True
    for child in list(body.children):
        if not isinstance(child, Tag):
            continue
        text = child.get_text(" ", strip=True)
        if not text:
            child.decompose()
            if removed_front_matter:
                continue
        if text.lower() == "metadata" or re.fullmatch(r"[_-]{3,}", text):
            child.decompose()
            continue
        if re.match(r"^[A-Za-z_]+\s*:", text):
            child.decompose()
            continue
        removed_front_matter = False
        break

    for tag in body.find_all(True):
        if tag.name in {"b"}:
            tag.name = "strong"
        elif tag.name in {"i"}:
            tag.name = "em"
        elif tag.name in {"span", "font"}:
            tag.unwrap()
            continue
        elif tag.name not in ALLOWED_TAGS:
            tag.unwrap()
            continue

        allowed_attrs: dict[str, str] = {}
        if tag.name == "a":
            href = tag.get("href")
            if href and re.match(r"^https?://", href):
                allowed_attrs["href"] = href
        tag.attrs = allowed_attrs

    fragments: list[str] = []
    for child in body.children:
        if isinstance(child, Tag):
            text = child.get_text(" ", strip=True)
            if text:
                fragments.append(str(child))

    body_html = "\n".join(f"          {line}" for line in fragments)
    if "- dr. calculus" not in BeautifulSoup(body_html, "html.parser").get_text(" ", strip=True).lower():
        body_html += "\n          <p>- dr. calculus</p>"

    html_metrics = article_structure_metrics(body_html)
    text_body_html = render_article_html_from_text(text_export)
    text_metrics = article_structure_metrics(text_body_html)

    html_collapsed = html_metrics["text_length"] >= 900 and html_metrics["total_blocks"] <= 2
    text_is_better = text_metrics["total_blocks"] >= max(3, html_metrics["total_blocks"] + 1)
    if html_collapsed and text_is_better:
        body_html = text_body_html

    validate_article_structure(title, body_html)
    return body_html


def parse_life_story_items(text: str) -> list[dict[str, str]]:
    body = strip_front_matter_text(text)
    items: list[dict[str, str]] = []

    for paragraph in re.split(r"\n\s*\n", body):
        paragraph = " ".join(line.strip() for line in paragraph.splitlines()).strip()
        if not paragraph:
            continue
        match = re.match(r"^(ages\s+[^:]+):\s*([^.]*)\.\s*(.*)$", paragraph, re.I)
        if not match:
            continue
        title = match.group(2).strip()
        items.append(
            {
                "age": match.group(1).strip(),
                "title": title,
                "copy": match.group(3).strip(),
                "tag": LIFE_STORY_TAGS.get(title, ""),
            }
        )

    if not items:
        raise ValueError("No life story timeline items found. Use: ages 2-10: Title. Body copy")
    return items


def render_life_story_page(items: list[dict[str, str]]) -> str:
    item_html = []
    for item in items:
        tag_html = (
            f'\n              <div class="timeline-tag">{html.escape(item["tag"])}</div>'
            if item.get("tag")
            else ""
        )
        item_html.append(
            f"""            <article class="timeline-item">
              <div class="timeline-dot"></div>
              <div class="timeline-age">{html.escape(item["age"])}</div>
              <div class="timeline-title">{html.escape(item["title"])}</div>
              <div class="timeline-copy">
                {html.escape(item["copy"])}
              </div>{tag_html}
            </article>"""
        )

    timeline_items = "\n\n".join(item_html)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>David Ezekiel - Life Story Timeline</title>
    <meta
      name="description"
      content="Experimental timeline layout for the my life story section."
    />
    <link rel="stylesheet" href="styles.css" />
    <style>
      .page-wrapp {{ background-color: #fafbfc; }}
      .timeline-page {{ width: 900px; max-width: 94%; }}
      .timeline-intro {{ max-width: 740px; }}
      .timeline-wrap {{ position: relative; margin-top: 10px; padding-left: 42px; }}
      .timeline-wrap::before {{ content: ""; position: absolute; left: 15px; top: 4px; bottom: 4px; width: 2px; background: #d5d8dd; }}
      .timeline-item {{ position: relative; margin-bottom: 26px; padding-bottom: 2px; }}
      .timeline-item:last-child {{ margin-bottom: 0; }}
      .timeline-dot {{ position: absolute; left: -35px; top: 7px; width: 12px; height: 12px; border-radius: 999px; background: #161717; box-shadow: 0 0 0 5px #fafbfc; }}
      .timeline-age {{ opacity: 0.68; margin-bottom: 5px; font-family: Minion Pro, sans-serif; font-size: 1.02rem; line-height: 1.2em; }}
      .timeline-title {{ margin-bottom: 5px; font-family: Minion Pro, sans-serif; font-size: 1.52rem; font-weight: 500; line-height: 1.2em; }}
      .timeline-copy {{ max-width: 740px; font-family: Minion Pro, sans-serif; font-size: 1.22rem; line-height: 1.55em; }}
      .timeline-highlight {{ font-style: italic; }}
      .timeline-tag {{ display: inline-flex; margin-top: 10px; padding: 4px 9px; border-radius: 999px; border: 1px solid #d8dbe0; font-family: Ppneuemontreal, sans-serif; font-size: 0.83rem; letter-spacing: 0.02em; line-height: 1em; }}
      .timeline-link {{ width: fit-content; text-decoration-color: #d7d9de; }}
      .timeline-link:hover {{ text-decoration-color: #ffa568; }}
      @media screen and (max-width: 767px) {{
        .timeline-wrap {{ padding-left: 32px; }}
        .timeline-wrap::before {{ left: 12px; }}
        .timeline-dot {{ left: -24px; width: 10px; height: 10px; }}
        .timeline-title {{ font-size: 1.32rem; }}
        .timeline-copy {{ font-size: 1.08rem; }}
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
          <h1 class="page-heading">my life story:</h1>
          <div class="page-subheading">
            Experimental timeline view. Built as a separate page so you can keep or delete it
            without affecting the live homepage.
          </div>
        </div>

        <div class="content-block">
          <div class="timeline-wrap">
{timeline_items}
          </div>
        </div>

        <div class="content-block">
          <a href="index.html#hall-of-fame" class="content-link timeline-link">
            continue to internet hall of fame
          </a>
        </div>
      </div>
    </div>
      <script src="script.js?v=8"></script>
  </body>
</html>
"""


def render_essay(title: str, publish_date: str, body_html: str) -> str:
    display_date = format_display_date(publish_date)
    escaped_title = html.escape(title)
    description = html.escape(f"{title} by David Ezekiel.")
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escaped_title} - David Ezekiel</title>
    <meta
      name="description"
      content="{description}"
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
          <div class="page-subheading top essay-date">{display_date}</div>
          <h1 class="essay-title">{escaped_title}</h1>
        </div>

        <div class="content-block essay-content">
{body_html}
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
            <a class="more-essays-link" href="why-data-teams-disagree-even-when-everyone-is-right.html">why data teams disagree even when everyone is right</a>
            <a class="more-essays-link" href="build-for-demand-not-assumptions.html">build for demand, not assumptions</a>
            <a class="more-essays-link" href="the-cost-of-the-road-not-taken.html">the cost of the road not taken</a>
            <a class="more-essays-link" href="positioning-by-subtraction.html">positioning by subtraction</a>
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
"""


def load_metadata(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="|")
        for row in reader:
            if not row:
                continue
            while len(row) < 6:
                row.append("")
            rows.append(
                {
                    "slug": row[0],
                    "section": row[1],
                    "title": row[2],
                    "publish_date": row[3],
                    "lede": row[4],
                    "body_mode": row[5],
                }
            )
    return rows


def write_metadata(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="|", lineterminator="\n")
        for row in rows:
            writer.writerow(
                [
                    pipe_safe(row["slug"], "slug"),
                    pipe_safe(row["section"], "section"),
                    pipe_safe(row["title"], "title"),
                    pipe_safe(row["publish_date"], "publish_date"),
                    pipe_safe(row["lede"], "lede"),
                    pipe_safe(row["body_mode"], "body_mode"),
                ]
            )


def load_article_map(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"documents": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def write_article_map(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def upsert_metadata(rows: list[dict[str, str]], incoming: dict[str, str]) -> None:
    for row in rows:
        if row["slug"] == incoming["slug"]:
            row.update(incoming)
            return
    rows.append(incoming)


def run_post_sync(root: Path) -> None:
    subprocess.run([str(root / "scripts/sync-essay-metadata.sh")], check=True)
    subprocess.run([str(root / "scripts/render-essay-archives.sh")], check=True)


def is_unchanged_record(record: dict[str, Any], item: dict[str, Any], slug: str, local_path: Path) -> bool:
    return (
        record.get("modified_time") == item.get("modifiedTime")
        and record.get("slug") == slug
        and local_path.exists()
    )


def sync_life_story_folder(
    service,
    folder: dict[str, Any],
    article_map: dict[str, Any],
    root: Path,
    args: argparse.Namespace,
) -> tuple[int, int]:
    imported = 0
    skipped = 0

    for item in list_children(service, folder["id"]):
        if item.get("mimeType") != "application/vnd.google-apps.document":
            continue

        local_path = root / LIFE_STORY_PATH
        text_export = export_doc(service, item["id"], "text/plain")
        front_matter = parse_front_matter(text_export)
        slug = slugify(front_matter.get("slug") or item["name"])
        status = front_matter.get("status", "").strip().lower()

        if slug != LIFE_STORY_SLUG:
            skipped += 1
            if args.verbose:
                print(f"Skipping {item['name']}: slug is not {LIFE_STORY_SLUG}")
            continue

        if status not in {"ready", "publish", "published"}:
            skipped += 1
            if args.verbose:
                print(f"Skipping {item['name']}: status is not ready")
            continue

        existing_record = article_map["documents"].get(item["id"], {})
        if is_unchanged_record(existing_record, item, LIFE_STORY_SLUG, local_path):
            skipped += 1
            if args.verbose:
                print(f"Skipping {item['name']}: unchanged since last sync")
            continue

        if args.dry_run:
            print(f"Would import {item['name']} -> {LIFE_STORY_PATH}")
            imported += 1
            continue

        local_path.write_text(render_life_story_page(parse_life_story_items(text_export)), encoding="utf-8")
        article_map["documents"][item["id"]] = {
            "slug": LIFE_STORY_SLUG,
            "section": "my-life-story",
            "local_path": LIFE_STORY_PATH,
            "drive_name": item["name"],
            "drive_url": item.get("webViewLink", ""),
            "modified_time": item.get("modifiedTime", ""),
            "last_synced": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        }
        imported += 1
        print(f"Imported {item['name']} -> {LIFE_STORY_PATH}")

    return imported, skipped


def sync_articles(args: argparse.Namespace) -> int:
    root = repo_root()
    metadata_path = root / "content/essay-metadata.csv"
    map_path = root / "content/drive-article-map.json"
    essays_dir = root / "essays"
    essays_dir.mkdir(exist_ok=True)

    service = load_service()
    root_folder_id = folder_id_from(args.folder)
    root_children = list_children(service, root_folder_id)
    section_folders = {
        SECTION_FOLDERS[item["name"].strip().lower()]: item
        for item in root_children
        if item.get("mimeType") == "application/vnd.google-apps.folder"
        and item["name"].strip().lower() in SECTION_FOLDERS
    }
    life_story_folders = [
        item
        for item in root_children
        if item.get("mimeType") == "application/vnd.google-apps.folder"
        and item["name"].strip().lower() in LIFE_STORY_FOLDERS
    ]

    rows = load_metadata(metadata_path)
    slug_to_doc = {
        record.get("slug"): doc_id
        for doc_id, record in load_article_map(map_path).get("documents", {}).items()
    }
    article_map = load_article_map(map_path)
    article_map.setdefault("documents", {})

    imported = 0
    skipped = 0

    for section, folder in sorted(section_folders.items()):
        for item in list_children(service, folder["id"]):
            if item.get("mimeType") != "application/vnd.google-apps.document":
                continue

            existing_record = article_map["documents"].get(item["id"], {})
            if existing_record:
                existing_slug = existing_record.get("slug", "")
                local_path = root / existing_record.get("local_path", "")
                if is_unchanged_record(existing_record, item, existing_slug, local_path):
                    skipped += 1
                    if args.verbose:
                        print(f"Skipping {item['name']}: unchanged since last sync")
                    continue

            text_export = export_doc(service, item["id"], "text/plain")
            front_matter = parse_front_matter(text_export)
            status = front_matter.get("status", "").strip().lower()

            if status not in {"ready", "publish", "published"}:
                skipped += 1
                if args.verbose:
                    print(f"Skipping {item['name']}: status is not ready")
                continue

            title = front_matter.get("title") or item["name"]
            slug = slugify(front_matter.get("slug") or title)
            publish_date = front_matter.get("publish_date") or today_iso()
            dt.date.fromisoformat(publish_date)
            lede = front_matter.get("lede", "")
            declared_section = SECTION_FOLDERS.get(front_matter.get("section", "").strip().lower(), section)

            existing_doc_id = slug_to_doc.get(slug)
            if existing_doc_id and existing_doc_id != item["id"]:
                raise SystemExit(
                    f"Slug collision: {slug} is already mapped to another Google Doc ({existing_doc_id})."
                )

            essay_path = essays_dir / f"{slug}.html"
            if not existing_doc_id and essay_path.exists():
                raise SystemExit(
                    f"Refusing to overwrite existing essay not mapped to Drive: {essay_path.relative_to(root)}. "
                    "Choose a different slug or add an explicit mapping in content/drive-article-map.json."
                )

            if not existing_doc_id and any(row["slug"] == slug for row in rows):
                raise SystemExit(
                    f"Refusing to overwrite existing metadata row not mapped to Drive: {slug}. "
                    "Choose a different slug or add an explicit mapping in content/drive-article-map.json."
                )

            html_export = export_doc(service, item["id"], "text/html")
            body_html = clean_article_html(html_export, text_export, title)

            if args.dry_run:
                print(f"Would import {item['name']} -> {essay_path.relative_to(root)}")
                imported += 1
                continue

            essay_path.write_text(render_essay(title, publish_date, body_html), encoding="utf-8")
            upsert_metadata(
                rows,
                {
                    "slug": slug,
                    "section": declared_section,
                    "title": title,
                    "publish_date": publish_date,
                    "lede": lede,
                    "body_mode": "drive",
                },
            )
            article_map["documents"][item["id"]] = {
                "slug": slug,
                "section": declared_section,
                "local_path": str(essay_path.relative_to(root)),
                "drive_name": item["name"],
                "drive_url": item.get("webViewLink", ""),
                "modified_time": item.get("modifiedTime", ""),
                "last_synced": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
            }
            imported += 1
            print(f"Imported {item['name']} -> {essay_path.relative_to(root)}")

    for folder in life_story_folders:
        life_story_imported, life_story_skipped = sync_life_story_folder(service, folder, article_map, root, args)
        imported += life_story_imported
        skipped += life_story_skipped

    if not args.dry_run:
        write_metadata(metadata_path, rows)
        write_article_map(map_path, article_map)
        run_post_sync(root)

    print(f"Drive article sync complete: {imported} imported or updated, {skipped} skipped.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync ready Google Docs from Drive into essay pages.")
    parser.add_argument(
        "--folder",
        default=os.environ.get("DRIVE_ARTICLES_FOLDER_URL") or DEFAULT_FOLDER_URL,
        help="Drive folder URL or ID. Defaults to DRIVE_ARTICLES_FOLDER_URL, then the dedicated website folder.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Read Drive and print intended changes without writing.")
    parser.add_argument("--verbose", action="store_true", help="Print skipped draft documents.")
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(sync_articles(parse_args()))
