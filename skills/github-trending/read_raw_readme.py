#!/usr/bin/env python3
import argparse
import sys
from urllib.parse import urlparse

from gather_readmes import clone_readme, fetch_url, read_raw_readme as read_repo_raw

MAX_BYTES = 120000

def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)

def parse_repo_url(url: str):
    parsed = urlparse(url)
    if parsed.netloc.lower() != "github.com":
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        return None
    repo = f"{parts[0]}/{parts[1].removesuffix('.git')}"
    return repo, f"https://github.com/{repo}"

def main() -> int:
    parser = argparse.ArgumentParser(description="读取 raw README URL 或 GitHub 仓库 URL 的 README 正文")
    parser.add_argument("target", help="raw.githubusercontent.com URL 或 github.com 仓库 URL")
    parser.add_argument("--max-bytes", type=int, default=MAX_BYTES, help="仓库 URL 模式下 README 最多输出字节数")
    args = parser.parse_args()
    if args.max_bytes <= 0:
        print("--max-bytes 必须大于 0", file=sys.stderr)
        return 2
    target = args.target.strip()
    # What: 同时支持 raw README URL 和 GitHub 仓库 URL，正文统一输出到 stdout。
    try:
        if urlparse(target).netloc.lower() == "raw.githubusercontent.com":
            log(f"步骤1: 输入识别为 raw README URL {target}")
            raw = fetch_url(target)
            log(f"步骤2: raw 读取完成，收到 {len(raw)} 字节，正文输出到 stdout")
            sys.stdout.buffer.write(raw)
            return 0
        repo = parse_repo_url(target)
        if repo is None:
            print("输入必须是 raw.githubusercontent.com URL 或 github.com 仓库 URL", file=sys.stderr)
            return 2
        repo_name, repo_url = repo
        log(f"步骤1: 输入识别为 GitHub 仓库 {repo_name}")
        try:
            result = read_repo_raw(repo_name, args.max_bytes)
        except Exception as raw_error:
            log(f"步骤2: raw 候选全部失败，准备 clone 兜底: {raw_error}")
            result = clone_readme(repo_name, repo_url, args.max_bytes)
        # Why: 这个脚本只负责取 README 正文，结构化分析留给模型或 gather_readmes.py。
        log(f"步骤3: README 读取完成，method={result.get('method')}，bytes={result.get('bytes')}，truncated={result.get('truncated')}")
        print(result.get("text", ""), end="")
        return 0
    except Exception as exc:
        print(f"读取失败: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
