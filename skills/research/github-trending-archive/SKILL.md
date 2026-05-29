---
name: github-trending-archive
description: 执行 GitHub Trending 归档时的操作步骤。
---

# GitHub Trending 归档步骤

1. 读取规则节点：
   - `read_memory("trace://stream/github_trending")`

2. 下载原始文件：
   ```bash
   wget -O /tmp/github_trending_llms.json https://blog.0120012.xyz/github_trending/llms.json
   ```

3. 解析 JSON：
   ```bash
   python ~/.hermes/skills/research/github-trending-archive/scripts/parse_llms_json.py /tmp/github_trending_llms.json > /tmp/github_trending_parsed.json
   ```

4. 渲染输出：
   ```bash
   python ~/.hermes/skills/research/github-trending-archive/scripts/build_trending_archive.py /tmp/github_trending_parsed.json
   ```

5. 从渲染结果中取出：
   - `node_date`
   - `fetch_date`
   - `archive_markdown`
   - `channel_markdown`

6. 若写入归档：
   - 目标路径：`trace://stream/github_trending/YYYY-MM-DD`
   - 若同日期节点已存在：先读，再删，再重建

7. 若只测试或用户明确要求不写记忆：
   - 不写 trace
   - 只返回结果
