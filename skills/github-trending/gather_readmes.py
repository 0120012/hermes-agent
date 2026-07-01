#!/usr/bin/env python3
import argparse, json, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

JSON_PATH = Path("cache/github_trending/llms.json")
OUTPUT_DIR = Path("cache/github_trending/readmes")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.97 Safari/537.36"
README_NAMES = ("README.md", "README.rst", "README.adoc", "README.txt", "README", "readme.md")
RAW_REFS = ("HEAD", "refs/heads/main", "refs/heads/master")
TEXT_SUFFIXES = {".md", ".rst", ".adoc", ".txt"}
EXCLUDED_DOCS = {"license", "copying", "changelog", "contributing", "security", "code_of_conduct"}
QUOTE_CHARS = "\"'“”‘’「」『』《》"
RAW_ATTEMPT_SLEEP_SECONDS = 1

def log(message):
    print(message, file=sys.stderr, flush=True)

def sleep_after_raw_attempt(success):
    # What: 每个 raw README 候选 URL 尝试结束后做轻量等待。
    # Why: 避免连续请求 raw.githubusercontent.com 或 clone 兜底前过于密集。
    status = "✅ 成功" if success else "❌ 失败"
    log(f"步骤: raw README {status}，等待 {RAW_ATTEMPT_SLEEP_SECONDS:g} 秒")
    time.sleep(RAW_ATTEMPT_SLEEP_SECONDS)

def fetch_url(url):
    errors = []
    try:
        log("  - raw 尝试 requests")
        import requests
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as exc:
        errors.append(f"requests: {exc}")
    for label, command in (
        ("curl", ["curl", "-fsSL", "--max-time", "30", "-A", USER_AGENT, url]),
        ("wget", ["wget", "-O-", "--timeout=30", "--user-agent", USER_AGENT, url]),
    ):
        try:
            log(f"  - raw 尝试 {label}")
            return subprocess.run(command, check=True, capture_output=True, timeout=35).stdout
        except Exception as exc:
            detail = (getattr(exc, "stderr", b"") or b"").decode("utf-8", "replace").strip() or str(exc)
            errors.append(f"{label}: {detail}")
    try:
        log("  - raw 尝试 urllib")
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        return urllib.request.urlopen(request, timeout=30).read()
    except Exception as exc:
        raise RuntimeError("; ".join(errors + [f"urllib: {exc}"])) from exc

def fit_text(raw, max_bytes):
    if max_bytes <= 0:
        return raw.decode("utf-8", "replace"), len(raw), False
    clipped = raw[:max_bytes]
    return clipped.decode("utf-8", "replace"), len(raw), len(raw) > max_bytes

def raw_urls(repo_name):
    return [f"https://raw.githubusercontent.com/{repo_name}/{ref}/{name}" for ref in RAW_REFS for name in README_NAMES]

def read_raw_readme(repo_name, max_bytes):
    errors = []
    for url in raw_urls(repo_name):
        log(f"步骤: 尝试 raw README {url}")
        try:
            text, size, truncated = fit_text(fetch_url(url), max_bytes)
            sleep_after_raw_attempt(True)
            return {"status": "ok", "method": "raw", "url": url, "bytes": size, "truncated": truncated, "text": text}
        except Exception as exc:
            errors.append(f"{url}: {exc}")
            log(f"步骤: raw 失败 {exc}")
            sleep_after_raw_attempt(False)
    raise RuntimeError(" | ".join(errors[-3:]))

def find_local_readme(repo_dir):
    roots = [repo_dir, repo_dir / "docs", repo_dir / "doc"]
    files = [p for root in roots if root.is_dir() for p in root.iterdir() if p.is_file()]
    preferred = [p for p in files if p.name.lower().startswith("readme")]
    if preferred:
        return sorted(preferred, key=lambda p: (p.parent != repo_dir, len(p.name)))[0]
    markdown = [p for p in files if p.suffix.lower() in TEXT_SUFFIXES and p.stem.lower() not in EXCLUDED_DOCS]
    return sorted(markdown, key=lambda p: p.stat().st_size, reverse=True)[0] if markdown else None

def process_text(value):
    if not value:
        return ""
    return value.decode("utf-8", "replace") if isinstance(value, bytes) else str(value)

def clone_readme(repo_name, repo_url, max_bytes):
    tmp_dir = Path(tempfile.mkdtemp(prefix="github_trending_", dir="/private/tmp"))
    repo_dir = tmp_dir / repo_name.replace("/", "__")
    try:
        log(f"步骤: raw 全部失败，clone 到临时目录 {repo_dir}")
        try:
            subprocess.run(["git", "clone", "--depth", "1", repo_url, str(repo_dir)], check=True, capture_output=True, timeout=120)
        except subprocess.CalledProcessError as exc:
            detail = process_text(exc.stderr).strip() or process_text(exc.stdout).strip() or str(exc)
            raise RuntimeError(f"git clone 失败: {detail}") from exc
        except subprocess.TimeoutExpired as exc:
            detail = process_text(exc.stderr).strip() or process_text(exc.stdout).strip()
            raise RuntimeError(f"git clone 超时: {detail}".strip()) from exc
        readme = find_local_readme(repo_dir)
        if readme is None:
            raise RuntimeError("clone 成功但未找到 README 或可用文档")
        text, size, truncated = fit_text(readme.read_bytes(), max_bytes)
        return {"status": "ok", "method": "clone", "path": str(readme.relative_to(repo_dir)), "bytes": size, "truncated": truncated, "text": text}
    finally:
        log(f"步骤: 清理临时目录 {tmp_dir}")
        shutil.rmtree(tmp_dir, ignore_errors=True)

def read_repo(repo, max_bytes):
    repo_name = repo.get("name")
    repo_url = repo.get("url") or f"https://github.com/{repo_name}"
    item = {key: repo.get(key) for key in ("name", "url", "language", "stars", "description")}
    if not repo_name or "/" not in repo_name:
        item["readme"] = {"status": "failed", "error": "仓库 name 无效"}
        return item
    try:
        item["readme"] = read_raw_readme(repo_name, max_bytes)
    except Exception as raw_error:
        try:
            item["readme"] = clone_readme(repo_name, repo_url, max_bytes)
            item["readme"]["raw_error"] = str(raw_error)
        except Exception as clone_error:
            item["readme"] = {"status": "failed", "raw_error": str(raw_error), "clone_error": str(clone_error)}
    return item

def main():
    parser = argparse.ArgumentParser(description="按 llms.json 分组读取 GitHub 仓库 README")
    parser.add_argument("group", help="要读取的固定分组名，例如 Trending")
    parser.add_argument("--json", default=str(JSON_PATH), help="llms.json 路径")
    parser.add_argument("--max-bytes", type=int, default=120000, help="每个 README 最多读取字节数，0 表示不限制")
    args = parser.parse_args()
    if args.max_bytes < 0:
        print("--max-bytes 必须大于等于 0", file=sys.stderr)
        return 2
    group_name = args.group.strip().strip(QUOTE_CHARS).strip()
    if not group_name:
        print("分组不能为空", file=sys.stderr)
        return 2
    # What: 按模型传入的单个固定分组读取仓库 README，并写入可供模型分析的 JSON。
    log(f"步骤1: 读取 JSON {args.json}")
    try:
        data = json.loads(Path(args.json).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"读取 JSON 失败: 文件不存在 {args.json}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"解析 JSON 失败: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"读取 JSON 失败: {exc}", file=sys.stderr)
        return 1
    if not isinstance(data, dict) or not isinstance(data.get("groups"), list):
        print("JSON 结构无效: 缺少 groups 数组", file=sys.stderr)
        return 1
    groups = {group.get("name"): group.get("repos", []) for group in data.get("groups", []) if isinstance(group, dict)}
    if group_name not in groups:
        print(f"分组不存在: {group_name}；可用分组: {', '.join(groups)}", file=sys.stderr)
        return 2
    output = {"date": data.get("date"), "source": data.get("source"), "groups": []}
    repos = groups[group_name]
    log(f"步骤2: 开始分组 {group_name}，仓库数 {len(repos)}")
    # Why: 只抓取 README 上下文，商业价值判断保留给模型，避免脚本编造分析结论。
    output["groups"].append({"name": group_name, "repos": [read_repo(repo, args.max_bytes) for repo in repos]})
    safe_group = "".join(ch if ch.isalnum() else "_" for ch in group_name).strip("_") or "group"
    output_dir = OUTPUT_DIR / str(data.get("date") or "unknown")
    output_path = output_dir / f"{safe_group}.json"
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp_path.replace(output_path)
    except OSError as exc:
        print(f"写入 JSON 失败: {exc}", file=sys.stderr)
        return 1
    print(f"README 上下文 JSON：{output_path.resolve()}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
