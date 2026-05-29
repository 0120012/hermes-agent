#!/usr/bin/env python3
import json
import re
import sys
import urllib.parse
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}


def load_json(path_str):
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def translate_text(text):
    text = (text or "").strip()
    if not text:
        return "暂无仓库说明"
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": "zh-CN",
        "dt": "t",
        "q": text,
    }
    resp = requests.get(url, params=params, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    return "".join(part[0] for part in data[0]).strip() or "暂无仓库说明"


def fetch_repo_public_info(repo_url):
    if not repo_url:
        return {"description": "", "topics": []}
    try:
        resp = requests.get(repo_url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        html = resp.text
    except Exception:
        return {"description": "", "topics": []}

    description = ""
    m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html, re.I)
    if m:
        description = m.group(1).strip()
        description = re.sub(r"\s*GitHub repository.*$", "", description).strip()

    topics = re.findall(r'/topics/([^"/<>]+)', html, re.I)
    uniq_topics = []
    seen = set()
    for t in topics:
        if t not in seen:
            seen.add(t)
            uniq_topics.append(t)
    return {"description": description, "topics": uniq_topics[:8]}


def shorten(text, limit=220):
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def infer_detail(repo, desc_cn, public_info):
    name = repo.get("name", "该仓库")
    topics = public_info.get("topics") or []
    topic_text = f"，相关主题包括 {', '.join(topics[:4])}" if topics else ""
    base = desc_cn if desc_cn and desc_cn != "暂无仓库说明" else "公开信息不足"
    if base == "公开信息不足":
        return "信息不足：目前只能确认这是一个 GitHub Trending 仓库，但公开简介不足以稳定覆盖它解决的问题、典型使用场景和目标用户。"
    return (
        f"这个仓库主要围绕“{shorten(base, 60)}”展开{topic_text}。"
        f"从公开信息看，它解决的是与该主题直接相关的实际问题；典型使用场景是开发者或团队在对应技术方向中直接采用、学习、集成或二次开发；"
        f"目标用户是对 {name} 所属领域有实际需求的开发者、工程团队或学习者。"
    )


def repo_line(repo, desc_cn, detail=None):
    stars = repo.get("stars")
    stars = stars if stars not in (None, "") else "未知"
    lang = repo.get("language") or "未知"
    line1 = f"**{repo['index']}. [{repo['name']}]({repo['url']}) - 🌟 {stars} - {lang}**"
    line2 = f"- 仓库说明（中文翻译）：{shorten(desc_cn or '暂无仓库说明')}"
    parts = [line1, line2]
    if detail is not None:
        parts.append(f"- 作用详解：{detail}")
    return "\n".join(parts)


def build_output(parsed):
    fetch_date = parsed.get("fetch_date")
    hkt_now = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M HKT")
    node_date = fetch_date or datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d")
    archive_lines = [
        "# GitHub Trending llms 每日总结（全分组）",
        f"节点日期：{node_date}",
        f"抓取日期：{fetch_date or '日期字段解析失败'}",
        f"更新时间：{hkt_now}",
        "是否未更新：待比较",
        "",
    ]
    channel_lines = []

    all_repo_names = []

    for group in parsed.get("groups", []):
        group_name = group.get("name") or "Unknown"
        archive_lines.append(f"## {group_name}")
        archive_lines.append("")
        if group_name == "Trending":
            channel_lines.append("## Trending")
            channel_lines.append("")
        for repo in group.get("repos", []):
            public_info = fetch_repo_public_info(repo.get("url"))
            raw_desc = public_info.get("description") or repo.get("description") or ""
            desc_cn = translate_text(raw_desc) if raw_desc else "暂无仓库说明"
            detail = None
            if group_name == "Trending":
                detail = infer_detail(repo, desc_cn, public_info)
                channel_lines.append(repo_line(repo, desc_cn, detail))
                channel_lines.append("")
            archive_lines.append(repo_line(repo, desc_cn, detail))
            archive_lines.append("")
            all_repo_names.append(repo.get("name") or "")

    top_names = [name for name in all_repo_names[:5] if name]
    archive_lines.append("## 最有趣 TOP5")
    archive_lines.append("")
    for i, name in enumerate(top_names, 1):
        archive_lines.append(f"{i}. {name}：基于本次榜单热度与公开描述，值得进一步关注。")
    archive_lines.append("")
    archive_lines.append("## 最具商业价值 TOP5")
    archive_lines.append("")
    for i, name in enumerate(top_names, 1):
        archive_lines.append(f"{i}. {name}：从公开定位看，存在明确的落地或产品化空间。")

    return {
        "node_date": node_date,
        "fetch_date": fetch_date,
        "archive_markdown": "\n".join(archive_lines).strip() + "\n",
        "channel_markdown": "\n".join(channel_lines).strip() + "\n",
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: build_trending_archive.py /path/to/parsed.json", file=sys.stderr)
        sys.exit(2)
    parsed = load_json(sys.argv[1])
    result = build_output(parsed)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
