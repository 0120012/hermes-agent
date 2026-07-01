#!/usr/bin/env python3
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

SOURCE_URL = "https://blog.0120012.xyz/github_trending/llms.json"
DEFAULT_OUTPUT = Path("cache/github_trending/llms.json")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.97 Safari/537.36"

def fetch_raw(log) -> bytes:
    errors = []
    try:
        log("步骤3.1: 尝试 requests 包请求")
        import requests
        response = requests.get(SOURCE_URL, headers={"User-Agent": USER_AGENT}, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as exc:
        errors.append(f"requests: {exc}")
        log(f"步骤3.1失败: {exc}")
    for label, command in (
        ("curl", ["curl", "-fsSL", "--max-time", "30", "-A", USER_AGENT, SOURCE_URL]),
        ("wget", ["wget", "-O-", "--timeout=30", "--user-agent", USER_AGENT, SOURCE_URL]),
    ):
        try:
            log(f"步骤3.2: 尝试 {label}")
            return subprocess.run(command, check=True, capture_output=True, timeout=35).stdout
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr.decode("utf-8", "replace").strip() or str(exc)
            errors.append(f"{label}: {detail}")
            log(f"步骤3.2失败: {label}: {detail}")
        except Exception as exc:
            errors.append(f"{label}: {exc}")
            log(f"步骤3.2失败: {label}: {exc}")
    try:
        log("步骤3.3: 尝试 urllib 标准库")
        with urllib.request.urlopen(urllib.request.Request(SOURCE_URL, headers={"User-Agent": USER_AGENT}), timeout=30) as response:
            return response.read()
    except Exception as exc:
        errors.append(f"urllib: {exc}")
        raise RuntimeError("; ".join(errors)) from exc

def main() -> int:
    def log(message: str) -> None:
        print(message, flush=True)

    if len(sys.argv) > 2:
        print("用法: python3 fetch_llms_json.py [output_path]", file=sys.stderr)
        return 2
    output = Path(sys.argv[1]) if len(sys.argv) == 2 else DEFAULT_OUTPUT
    # What: 固定抓取 llms.json，并先验证顶层结构再写入本地缓存。
    try:
        log(f"步骤1: 数据源固定为 {SOURCE_URL}")
        log(f"步骤2: 缓存输出路径为 {output}")
        log("步骤3: 开始请求 llms.json")
        raw = fetch_raw(log)
        log(f"步骤4: 请求完成，收到 {len(raw)} 字节")
        data = json.loads(raw)
    except Exception as exc:
        print(f"拉取或解析失败: {exc}", file=sys.stderr)
        return 1
    if not isinstance(data, dict) or not data.get("date") or not isinstance(data.get("groups"), list):
        print("数据结构无效: 缺少 date 或 groups", file=sys.stderr)
        return 1
    # Why: 使用临时文件替换目标文件，避免失败时留下半截缓存。
    log(f"步骤5: 校验通过，抓取日期 {data['date']}，分组数 {len(data['groups'])}")
    group_names = [group.get("name") for group in data["groups"] if isinstance(group, dict) and group.get("name")]
    log(f"步骤6: 分组名称 {', '.join(group_names) if group_names else '无'}")
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp_output = output.with_suffix(output.suffix + ".tmp")
    tmp_output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_output.replace(output)
    log(f"完成: 已缓存 {data['date']} 到 {output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
