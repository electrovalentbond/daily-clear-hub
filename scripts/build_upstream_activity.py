"""Build the sortable dependency list and its README preview."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape


SOURCE = Path(__file__).resolve().parents[1] / "docs" / "upstream-activity"
PREVIEW_ROWS = 12


def utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def fetch_json(url: str, headers: dict[str, str], *, allow_missing: bool = False) -> dict | None:
    request = Request(url, headers={"User-Agent": "daily-clear-hub-upstream-activity", **headers})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=15) as response:
                body = response.read().decode("utf-8")
            if body.startswith(")]}'"):
                body = body.split("\n", 1)[1]
            return json.loads(body)
        except HTTPError as exc:
            if exc.code == 404 and allow_missing:
                return None
            if exc.code < 500 or attempt == 2:
                raise
        except (TimeoutError, URLError):
            if attempt == 2:
                raise
        time.sleep(2 ** attempt)


def collect(project: dict, token: str) -> dict:
    row = {key: value for key, value in project.items() if key not in {"github", "ref", "gitiles"}}
    if gitiles := project.get("gitiles"):
        commit = fetch_json(gitiles, {})
        row["date"] = utc_timestamp(parsedate_to_datetime(commit["committer"]["time"]))
        row["commit_url"] = f"{project['source_url'].rstrip('/')}/+/{commit['commit']}"
        return row

    repo = project["github"]
    ref = quote(project.get("ref", "HEAD"), safe="")
    commit = fetch_json(
        f"https://api.github.com/repos/{repo}/commits/{ref}",
        {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}"},
        allow_missing=True,
    )
    if commit is None:
        row["date"] = None
        row.setdefault("date_label", "GitHub 暂不可查")
    else:
        row["date"] = utc_timestamp(datetime.fromisoformat(commit["commit"]["committer"]["date"]))
        row["commit_url"] = commit["html_url"]
        row.pop("date_label", None)
    return row


def preview(projects: list[dict], updated_at: str) -> str:
    rows = [project for project in projects if project["date"]][:PREVIEW_ROWS]
    height = 95 + 28 * len(rows)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 {height}" width="680" height="{height}">',
        '<title>依赖项目最近 Git 提交时间</title>',
        '<style>text{font-family:system-ui,sans-serif;fill:#1f2328}.muted{fill:#57606a}'
        '.background{fill:#fff;stroke:#d0d7de}.line{stroke:#d8dee4}.date{font-family:monospace}'
        '@media(prefers-color-scheme:dark){text{fill:#f0f6fc}.muted{fill:#9198a1}'
        '.background{fill:#0d1117;stroke:#30363d}.line{stroke:#30363d}}</style>',
        f'<rect class="background" x=".5" y=".5" width="679" height="{height - 1}" rx="8"/>',
        '<text x="20" y="29" font-size="17" font-weight="600">最近更新的依赖</text>',
        f'<text class="muted" x="20" y="50" font-size="12">数据刷新 {updated_at.replace("T", " ")}</text>',
        '<text class="muted" x="20" y="75" font-size="13">项目</text>',
        '<text class="muted" x="660" y="75" font-size="13" text-anchor="end">最近提交（UTC）↓</text>',
    ]
    for index, project in enumerate(rows):
        top = 83 + index * 28
        name = escape(project["name"])
        date = project["date"].replace("T", " ").removesuffix("Z")
        lines.extend([
            f'<path class="line" d="M20 {top}H660"/>',
            f'<text x="20" y="{top + 19}" font-size="14">{name}</text>',
            f'<text class="date" x="660" y="{top + 19}" font-size="14" text-anchor="end">{date}</text>',
        ])
    return "\n".join([*lines, "</svg>", ""])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        parser.error("GITHUB_TOKEN is required to read public commits within the API rate limit")

    catalog = json.loads((SOURCE / "catalog.json").read_text(encoding="utf-8"))
    with ThreadPoolExecutor(max_workers=8) as pool:
        projects = list(pool.map(lambda project: collect(project, token), catalog))
    projects.sort(key=lambda project: project["date"] or "", reverse=True)
    updated_at = utc_timestamp(datetime.now(timezone.utc))
    args.output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE / "index.html", args.output / "index.html")
    data = {"updated_at": updated_at, "projects": projects}
    (args.output / "projects.json").write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.output / "preview.svg").write_text(preview(projects, updated_at), encoding="utf-8")
    print(f"Built dependency activity for {len(projects)} projects")


if __name__ == "__main__":
    main()
