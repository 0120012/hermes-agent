from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}
LLMS_URL = "https://blog.0120012.xyz/github_trending/llms.txt"
README_WINDOW = 16000
HK = ZoneInfo("Asia/Hong_Kong")
GENERIC_PHRASES = [
    "提升效率",
    "降低门槛",
    "适用于多种场景",
    "赋能开发",
]
SECTION_HINTS = [
    "features",
    "usage",
    "quick start",
    "installation",
    "examples",
    "faq",
    "architecture",
    "who is this for",
    "overview",
    "introduction",
    "getting started",
    "install",
    "usage",
    "example",
    "feature",
    "architecture",
    "for developers",
    "for teams",
    "use case",
    "getting started",
]
TARGET_USERS = [
    ("developer", "developers"),
    ("developers", "developers"),
    ("engineer", "engineers"),
    ("engineers", "engineers"),
    ("researcher", "researchers"),
    ("researchers", "researchers"),
    ("student", "students"),
    ("students", "students"),
    ("teacher", "teachers"),
    ("teachers", "teachers"),
    ("team", "teams"),
    ("teams", "teams"),
    ("enterprise", "enterprise teams"),
    ("founder", "founders"),
    ("designers", "designers"),
    ("designer", "designers"),
]
TASK_HINTS = [
    ("markdown", "convert content to Markdown"),
    ("pdf", "process PDF documents"),
    ("document", "process documents"),
    ("documents", "process documents"),
    ("agent", "build or run agent workflows"),
    ("agents", "build or run agent workflows"),
    ("memory", "store and reuse long-term memory"),
    ("textbook", "organize and browse textbooks"),
    ("speech", "generate or process speech"),
    ("tts", "synthesize or clone speech"),
    ("coding", "assist coding workflows"),
    ("financial", "support financial research or market analysis"),
    ("market", "support market analysis or financial modeling"),
    ("storage", "build or manage storage systems"),
    ("s3", "provide S3-compatible object storage"),
    ("blender", "integrate Blender workflows"),
    ("plugin", "extend developer tools or platforms"),
    ("cli", "support CLI workflows"),
]
SCENARIO_HINTS = [
    ("rag", "retrieval-augmented knowledge workflows"),
    ("workflow", "workflow orchestration"),
    ("automation", "task automation"),
    ("research", "research analysis and prototyping"),
    ("education", "learning support and teaching materials"),
    ("coding", "daily development assistance"),
    ("document", "document transformation and ingestion"),
    ("speech", "speech generation and multilingual voice apps"),
    ("finance", "financial research and investment experiments"),
    ("storage", "storage deployment and compatibility migration"),
]
NOISE_PATTERNS = [
    r"^\s*\[!.*?\]\(.*?\)\s*$",
    r"^\s*!\[.*?\]\(.*?\)\s*$",
    r"^\s*<img .*?>\s*$",
    r"^\s*badge[s]?:?.*$",
]


def save_and_readback(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    readback = path.read_text(encoding="utf-8")
    if readback != text:
        raise RuntimeError(f"readback mismatch: {path}")
    return readback


def fetch_text(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def parse_fetch_date(text: str) -> str:
    m = re.search(r"^日期:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else "日期字段解析失败"


def parse_sections(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^##\s+(.+?)\n", text, re.M))
    out = []
    for i, m in enumerate(matches):
        name = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((name, text[start:end].strip()))
    return out


def parse_section_repos(section_body: str) -> list[dict]:
    entries = re.findall(
        r"(\d+)\.\s+([^|]+?)\s+\|\s+⭐\s*([^|]*?)\s+\|\s*(.*?)\n\s+(https://github\.com/[^\s]+)\n(?:\s+(.*?))?(?=\n\d+\. |\Z)",
        section_body,
        re.S,
    )
    out = []
    for num, repo, stars, lang, url, desc in entries:
        out.append(
            {
                "index": int(num),
                "repo": repo.strip(),
                "stars": (stars or "").strip() or "未知",
                "lang": (lang or "").strip() or "未知",
                "url": url.strip(),
                "desc": (desc or "").strip() or "暂无仓库说明",
            }
        )
    return out


def raw_candidates(repo_url: str) -> list[str]:
    parts = [x for x in urlparse(repo_url).path.split("/") if x]
    if len(parts) < 2:
        return []
    owner, repo = parts[0], parts[1]
    out = []
    for branch in ["main", "master"]:
        for name in ["README.md", "readme.md", "README.MD"]:
            out.append(f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{name}")
    return out


def fetch_readme(repo_url: str) -> tuple[str, str]:
    for cand in raw_candidates(repo_url):
        try:
            r = requests.get(cand, headers=HEADERS, timeout=60)
            if r.status_code == 200 and r.text.strip():
                return cand, r.text
        except Exception:
            pass
    return "", ""


def clean_text(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if any(re.search(p, line, re.I) for p in NOISE_PATTERNS):
            continue
        lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`]+`", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_markdown_sections(text: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.M)
    matches = list(pattern.finditer(text))
    if not matches:
        return []
    out = []
    for i, m in enumerate(matches):
        title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        out.append((title, body))
    return out


def extract_targeted_context(readme_text: str) -> str:
    sections = split_markdown_sections(readme_text)
    picked = []
    for title, body in sections:
        lower_title = title.lower()
        if any(h in lower_title for h in SECTION_HINTS):
            picked.append(f"{title}\n{body[:3000]}")
    if picked:
        return "\n\n".join(picked[:6])

    paragraphs = re.split(r"\n\s*\n", readme_text)
    matched = []
    for para in paragraphs:
        low = para.lower()
        if any(h in low for h in SECTION_HINTS):
            matched.append(para[:3000])
    return "\n\n".join(matched[:6])


def collect_context(repo: dict, readme_text: str) -> str:
    desc = repo.get("desc", "")
    first_pass = readme_text[:README_WINDOW]
    targeted = extract_targeted_context(readme_text)
    combined = "\n\n".join(x for x in [desc, first_pass, targeted] if x).strip()
    return clean_text(combined)


def infer_target_user(text: str, section_name: str) -> str:
    low = text.lower()
    found = []
    for key, zh in TARGET_USERS:
        if key in low and zh not in found:
            found.append(zh)
    if found:
        # Why: 标签值已切到英文，连接符和默认回退也必须同步英文，否则最终摘要会混入中英文拼接噪音。
        return ", ".join(found[:3])
    if section_name == "Trending":
        return "developers, researchers, or related technical teams"
    return "developers, researchers, or practical users in this area"


def infer_task(text: str) -> str:
    low = text.lower()
    found = []
    for key, zh in TASK_HINTS:
        if key in low and zh not in found:
            found.append(zh)
    if found:
        return "、".join(found[:3])
    return "信息不足"


def infer_scenario(text: str) -> str:
    low = text.lower()
    found = []
    for key, zh in SCENARIO_HINTS:
        if key in low and zh not in found:
            found.append(zh)
    if found:
        return "、".join(found[:3])
    return "信息不足"


def build_repo_desc(repo: dict, context: str) -> str:
    desc = repo.get("desc", "暂无仓库说明").strip()
    if desc and desc != "暂无仓库说明":
        return f"这是一个开源仓库，主要内容与“{desc}”相关。"
    task = infer_task(context)
    if task != "信息不足":
        return f"这是一个开源仓库，主要用于{task}。"
    return "这是一个开源仓库，但当前公开材料不足以稳定概括其核心定位。"


def build_trending_use_detail(repo: dict, context: str, section_name: str) -> str:
    task = infer_task(context)
    scenario = infer_scenario(context)
    users = infer_target_user(context, section_name)

    problem = task if task != "信息不足" else "信息不足"
    scen = scenario if scenario != "信息不足" else "信息不足"
    user = users if users else "信息不足"

    parts = [
        f"这个仓库主要用于{problem}。" if problem != "信息不足" else "这个仓库主要解决什么问题：信息不足。",
        f"典型使用场景包括：{scen}。" if scen != "信息不足" else "典型使用场景：信息不足。",
        f"目标用户主要是：{user}。" if user != "信息不足" else "目标用户：信息不足。",
    ]
    text = " ".join(parts)
    return enforce_specificity(text, repo)


def enforce_specificity(text: str, repo: dict) -> str:
    for phrase in GENERIC_PHRASES:
        if phrase in text and not any(k in text for k in ["文件", "文档", "语音", "教材", "工作流", "开发者", "研究者", "团队", "Markdown", "PDF"]):
            return f"这个仓库的公开信息显示它与“{repo.get('desc', '暂无仓库说明')}”相关，但当前材料不足以支持更具体且不空泛的作用详解。"
    return text


def summarize_repo(repo: dict, readme_text: str, section_name: str) -> tuple[str, str | None]:
    context = collect_context(repo, readme_text)
    zh_desc = build_repo_desc(repo, context)
    if section_name == "Trending":
        use = build_trending_use_detail(repo, context, section_name)
    else:
        use = None
    return zh_desc, use


def render_section(section_name: str, repos: list[dict]) -> str:
    lines = [f"## {section_name}", ""]
    for idx, item in enumerate(repos, start=1):
        lines.append(f"**{idx}. [{item['repo']}]({item['url']}) - 🌟 {item['stars']} - {item['lang']}**  ")
        lines.append(f"- 仓库说明（中文翻译）：{item['zh_desc']}  ")
        if section_name == "Trending":
            lines.append(f"- 作用详解：{item['use'] or '信息不足'}  ")
        lines.append("")
    return "\n".join(lines).rstrip()


def split_for_channel(text: str, limit: int = 1800) -> list[str]:
    if len(text) <= limit:
        return [text]
    lines = text.splitlines(keepends=True)
    chunks, current = [], ""
    for line in lines:
        if len(current) + len(line) > limit and current:
            chunks.append(current.rstrip())
            current = line
        else:
            current += line
    if current.strip():
        chunks.append(current.rstrip())
    return chunks


def top5_reason(item: dict) -> str:
    text = item.get("use") or item.get("zh_desc", "")
    if "信息不足" in text:
        return "公开信息有限，但该项目在本次榜单中仍具代表性。"
    return text[:80] + ("..." if len(text) > 80 else "")


def build_top5(trending_repos: list[dict], title: str) -> str:
    lines = [f"## {title}", ""]
    for idx, item in enumerate(trending_repos[:5], start=1):
        lines.append(f"{idx}. {item['repo']}：{top5_reason(item)}")
    return "\n".join(lines).rstrip()


def normalize_repo_safely(repo: dict, section_name: str, workdir: Path) -> dict:
    # Why: Trending 批处理里单仓库网络或落盘异常很常见，必须按仓库降级，不能让整批结果一起失败。
    try:
        raw_url = ""
        readme = ""
        if section_name == "Trending":
            raw_url, readme = fetch_readme(repo["url"])
            if readme:
                save_and_readback(workdir / f"{repo['repo'].replace('/', '__')}_README.md", readme)
        zh_desc, use = summarize_repo(repo, readme, section_name)
        return {**repo, "raw_url": raw_url, "zh_desc": zh_desc, "use": use}
    except Exception:
        fallback_use = "信息不足" if section_name == "Trending" else None
        return {**repo, "raw_url": "", "zh_desc": build_repo_desc(repo, ""), "use": fallback_use}


def run_daily(workdir: Path) -> dict:
    now = datetime.now(HK)
    update_time = now.strftime("%Y-%m-%d %H:%M:%S %Z")

    llms_text = fetch_text(LLMS_URL)
    llms_text = save_and_readback(workdir / "llms.txt", llms_text)
    fetch_date = parse_fetch_date(llms_text)
    node_date = fetch_date if re.fullmatch(r"\d{4}-\d{2}-\d{2}", fetch_date or "") else now.strftime("%Y-%m-%d")
    sections = parse_sections(llms_text)

    normalized_sections = []
    trending_output = None
    trending_repos_for_top = []

    for raw_name, body in sections:
        clean_name = raw_name.split("（")[0].strip()
        repos = parse_section_repos(body)
        normalized = []
        for repo in repos:
            normalized.append(normalize_repo_safely(repo, clean_name, workdir))
        block = render_section(clean_name, normalized)
        normalized_sections.append(block)
        if clean_name == "Trending":
            trending_output = block
            trending_repos_for_top = normalized

    top_interesting = build_top5(trending_repos_for_top, "最有趣的 TOP5 仓库")
    top_business = build_top5(trending_repos_for_top, "最具商业价值的 TOP5 仓库")

    header = f"抓取日期：{fetch_date}\n更新时间：{update_time}\n"
    channel_body = header + "\n" + (trending_output or "## Trending\n")
    archive_body = "\n\n".join([
        f"节点日期：{node_date}",
        f"抓取日期：{fetch_date}",
        f"更新时间：{update_time}",
        "是否未更新：否",
        *normalized_sections,
        top_interesting,
        top_business,
    ])

    (workdir / "channel.md").write_text(channel_body, encoding="utf-8")
    (workdir / "archive.md").write_text(archive_body, encoding="utf-8")
    channel_chunks = split_for_channel(channel_body)
    (workdir / "channel_chunks.json").write_text(json.dumps(channel_chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    metadata = {
        "node_date": node_date,
        "fetch_date": fetch_date,
        "update_time": update_time,
        "unchanged": False,
        "channel_chunks": len(channel_chunks),
        "channel_path": str(workdir / "channel.md"),
        "archive_path": str(workdir / "archive.md"),
        "channel_chunks_path": str(workdir / "channel_chunks.json"),
    }
    (workdir / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata


def run_test(limit: int, repo_urls: list[str], workdir: Path) -> None:
    entries = []
    if repo_urls:
        for i, url in enumerate(repo_urls, start=1):
            parts = [x for x in urlparse(url).path.split("/") if x]
            repo = f"{parts[0]}/{parts[1]}"
            entries.append({"index": i, "repo": repo, "stars": "未知", "lang": "未知", "url": url, "desc": "暂无仓库说明"})
    else:
        llms_text = fetch_text(LLMS_URL)
        llms_text = save_and_readback(workdir / "llms.txt", llms_text)
        sections = parse_sections(llms_text)
        for name, body in sections:
            if name.startswith("Trending"):
                entries = parse_section_repos(body)[:limit]
                break

    out = []
    for repo in entries:
        out.append(normalize_repo_safely(repo, "Trending", workdir))

    print(render_section("Trending", out))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["daily", "trending-test", "repo-test"], default="trending-test")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--repo-url", action="append", default=[])
    ap.add_argument("--workdir", default="/tmp/github_trending_v5")
    args = ap.parse_args()

    workdir = Path(args.workdir)
    workdir.mkdir(parents=True, exist_ok=True)

    if args.mode == "daily":
        metadata = run_daily(workdir)
        print(json.dumps(metadata, ensure_ascii=False, indent=2))
    elif args.mode == "repo-test":
        run_test(limit=args.limit, repo_urls=args.repo_url, workdir=workdir)
    else:
        run_test(limit=args.limit, repo_urls=[], workdir=workdir)


if __name__ == "__main__":
    main()
