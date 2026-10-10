#!/usr/bin/env python3
"""Build a precise GitHub shortlist for Codex-powered video editing projects.

Usage (networked env):
  python research/collect_codex_video_projects.py --token "$GITHUB_TOKEN"

This script queries GitHub Search API with multiple keyword sets, de-duplicates
repositories, computes a simple relevance score, and writes markdown output to:
  research/codex-video-editing-projects-precise.md
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

API = "https://api.github.com/search/repositories"
OUTPUT = Path("research/codex-video-editing-projects-precise.md")

QUERIES = [
    "(codex OR openai) (video editor OR video editing) (ffmpeg OR moviepy) language:Python",
    "(llm OR gpt) automated video editing ffmpeg language:Python",
    "agentic video editing whisper moviepy language:Python",
    "text to video editing pipeline ffmpeg open-source",
]

KEYWORDS = {
    "ffmpeg": 3,
    "moviepy": 2,
    "whisper": 3,
    "subtitle": 2,
    "caption": 2,
    "agent": 2,
    "workflow": 1,
    "timeline": 1,
    "openai": 1,
    "codex": 2,
}


@dataclass
class Repo:
    full_name: str
    html_url: str
    description: str
    stars: int
    updated_at: str
    language: str
    topics: List[str]
    readme_hint: str

    @property
    def score(self) -> int:
        text = " ".join(
            [self.description or "", self.readme_hint or "", " ".join(self.topics)]
        ).lower()
        total = 0
        for key, weight in KEYWORDS.items():
            if key in text:
                total += weight
        return total + min(self.stars // 50, 8)


def _fetch_json(url: str, headers: Dict[str, str]) -> dict:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_repos(token: str | None, per_query: int = 20, sleep_s: float = 0.8) -> List[Repo]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "codex-video-project-shortlist",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    by_name: Dict[str, Repo] = {}
    for query in QUERIES:
        params = urllib.parse.urlencode({"q": query, "sort": "stars", "order": "desc", "per_page": per_query})
        data = _fetch_json(f"{API}?{params}", headers)
        for item in data.get("items", []):
            name = item["full_name"]
            if name in by_name:
                continue
            topics = item.get("topics") or []
            readme_hint = f"{item.get('name','')} {item.get('default_branch','')}"
            by_name[name] = Repo(
                full_name=name,
                html_url=item["html_url"],
                description=item.get("description") or "",
                stars=int(item.get("stargazers_count") or 0),
                updated_at=item.get("updated_at") or "",
                language=item.get("language") or "",
                topics=topics,
                readme_hint=readme_hint,
            )
        time.sleep(sleep_s)

    return sorted(by_name.values(), key=lambda r: (r.score, r.stars), reverse=True)


def write_markdown(repos: Iterable[Repo], output: Path, generated_at: str) -> None:
    lines = [
        "# Codex 自動剪輯影片：精準專案清單（可連網環境產生）",
        "",
        f"生成時間：{generated_at}",
        "",
        "| Rank | Repository | Score | Stars | Language | Updated | Why it matched |",
        "|---:|---|---:|---:|---|---|---|",
    ]

    for idx, repo in enumerate(repos, start=1):
        why = []
        low = f"{repo.description} {' '.join(repo.topics)}".lower()
        for kw in ["ffmpeg", "whisper", "moviepy", "agent", "subtitle", "caption", "codex", "openai"]:
            if kw in low:
                why.append(kw)
        why_text = ", ".join(why[:6]) if why else "keyword overlap"
        desc = (repo.description or "").replace("|", "/")
        lines.append(
            f"| {idx} | [{repo.full_name}]({repo.html_url})<br>{desc[:120]} | {repo.score} | {repo.stars} | {repo.language or '-'} | {repo.updated_at[:10]} | {why_text} |"
        )
        if idx >= 20:
            break

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", default=None, help="GitHub token; optional but recommended")
    parser.add_argument("--generated-at", default=time.strftime("%Y-%m-%d %H:%M:%S"))
    parser.add_argument("--dry-run", action="store_true", help="Write empty table without network calls")
    args = parser.parse_args()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        write_markdown([], OUTPUT, args.generated_at)
        print(f"Wrote dry-run output to {OUTPUT}")
        return 0

    repos = search_repos(token=args.token)
    write_markdown(repos, OUTPUT, args.generated_at)
    print(f"Wrote {min(len(repos), 20)} rows to {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
