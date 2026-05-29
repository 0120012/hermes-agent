#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


def normalize_repo(repo, index):
    if not isinstance(repo, dict):
        repo = {}
    return {
        "index": index,
        "name": repo.get("name") or "unknown/unknown",
        "url": repo.get("url") or "",
        "stars": repo.get("stars") if repo.get("stars") not in (None, "") else "未知",
        "language": repo.get("language") or "未知",
        "description": repo.get("description") or "暂无仓库说明",
    }


def normalize_group(group, fallback_index):
    if not isinstance(group, dict):
        group = {}
    name = group.get("name") or group.get("title") or f"Group-{fallback_index}"
    repos = group.get("repos")
    if not isinstance(repos, list):
        repos = []
    normalized_repos = [normalize_repo(repo, i) for i, repo in enumerate(repos, 1)]
    return {
        "name": name,
        "repo_count": len(normalized_repos),
        "repos": normalized_repos,
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: parse_llms_json.py /path/to/llms.json", file=sys.stderr)
        sys.exit(2)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Input file not found: {path}", file=sys.stderr)
        sys.exit(1)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    groups = data.get("groups")
    if not isinstance(groups, list):
        print("Invalid schema: 'groups' must be a list", file=sys.stderr)
        sys.exit(1)

    normalized_groups = [normalize_group(group, i) for i, group in enumerate(groups, 1)]
    total_repo_count = sum(group["repo_count"] for group in normalized_groups)
    hk_now = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S %Z")

    result = {
        "title": data.get("title") or "每日仓库更新",
        "source": data.get("source") or "",
        "history": data.get("history") or "",
        "fetch_date": data.get("date") or None,
        "group_count": len(normalized_groups),
        "repo_count": total_repo_count,
        "updated_at_hkt": hk_now,
        "groups": normalized_groups,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
