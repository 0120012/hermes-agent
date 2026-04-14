执行 GitHub Trending llms 每日总结任务 V5。

必须加载 skill：`github-trending-v5-runner`，并严格遵守其中的约束与输出格式。

执行要求：
1. 运行生产版脚本：
   `python /www/.hermes/skills/automation/github-trending-v5-runner/scripts/run_trending_v5.py --mode daily --workdir /tmp/github_trending_v5_daily`
2. 读取脚本产出的三个文件：
   - `/tmp/github_trending_v5_daily/channel.md`
   - `/tmp/github_trending_v5_daily/archive.md`
   - `/tmp/github_trending_v5_daily/metadata.json`
3. 根据 `metadata.json` 中的节点日期，把完整归档内容写入：
   `trace://stream/github_trending/YYYY-MM-DD`
4. 若日期子节点不存在，则按父节点规则创建；Priority 固定为 3；Disclosure 固定为：
   `当我需要查看 GitHub Trending YYYY-MM-DD（Asia/Hong_Kong）全分组结果时。`
5. 若 archive.md 过长，可分批写入，但必须通过 MCP memory 工具执行，严禁绕过 MCP。
6. 回当前聊天的最终正文只发送 `channel.md` 内容，不要附带状态码、日志、raw URL、调试信息。

失败处理：
- 若 llms.txt 抓取失败、落盘校验失败、无法规范化输出、或 Trending 条目未完成，则不得伪造成功结果。
- 若只是单个仓库 README 获取失败，可退化为基于仓库主页简介、topics、目录结构等公开信息写条目。
- 若信息仍不足，明确写 `信息不足`，不得编造。
- 规则升级后，必须同步检查三处是否真的一致：memory 节点、runner 脚本、cron 模板。不要只改 memory 文本就当作已同步。
