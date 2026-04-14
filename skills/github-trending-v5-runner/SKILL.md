---
name: github-trending-v5-runner
description: Production-ready GitHub Trending llms V5 workflow for cron jobs — fetch llms.txt, prefer raw README text, summarize in concrete Chinese, prepare channel and archive outputs, support MCP archive writes, and default to result-only output unless diagnostics are requested.
---

# GitHub Trending V5 runner

用于 `trace://stream/github_trending` 的**可直接用于定时任务的生产版执行 skill**。

适用场景：
- 每日 GitHub Trending llms 正式跑批
- 单仓库 / 多仓库抽样测试
- 生成频道正文版与完整归档版
- 为后续 MCP memory 写入提供结构化产物

## 核心契约
1. `llms.txt` 只能用 Python `requests` 抓取，禁止 `curl`。
2. 所有网络响应都必须先落盘，再从本地文件读回；读回文本必须与响应文本一致。
3. README 优先走 `raw.githubusercontent.com`，不要直接分析 `github.com/.../blob/...` 的 HTML。
4. README 首轮只分析前 16000 字符；若更短则读全文。
5. 信息不足时先做关键章节补读；仍不足时明确写 `信息不足`，禁止编造。
6. 最终输出必须是中文、规范化、可直接发送的条目结果。
7. 普通仓库条目和 Trending 条目都禁止空泛话术，如“提升效率”“降低门槛”“适用于多种场景”“赋能开发”。
8. 最终用户输出里不要混入状态码、raw URL、落盘校验日志，除非用户明确要求排障报告。

## 生产版输出目标
每日正式任务需要产出三类结果：

### 1. 频道正文版
- 只包含 `## Trending`
- 供发送到 Discord 频道
- 若过长需按条目边界分批
- 第一批必须含抓取日期、更新时间、`## Trending`

### 2. 完整归档版
- 包含全部分组规范化结果
- 末尾附：
  - 最有趣的 TOP5 仓库
  - 最具商业价值的 TOP5 仓库
- 用于写入 `trace://stream/github_trending/YYYY-MM-DD`

### 3. 元信息
- 节点日期
- 抓取日期
- 更新时间
- 是否未更新
- 失败原因（若失败）
- 供 MCP memory 写入流程引用

### 分组输出差异
- `Trending` 分组：输出 `仓库说明 + 作用详解`
- 其他分组：只输出 `仓库说明`
- 不要把 `Trending` 的 README 深读要求误套到其它分组

元信息时间约束：
- `fetch_date` 以 `llms.txt` 日期字段为准。
- `node_date` 默认应直接等于 `fetch_date`。
- 只有当 `fetch_date` 缺失或无法解析为 `YYYY-MM-DD` 时，才允许回退到 Asia/Hong_Kong 当天日期。
- 不要再把“当前日期”默认当成节点日期。

## 最终条目格式
所有仓库条目都必须以以下开头：
- `**序号. [owner/repo](repo_url) - 🌟 star数 - 语言**`
- `- 仓库说明（中文翻译）：...`

分组差异：
- `Trending` 分组：必须额外输出 `- 作用详解：...`
- 其他分组：默认不输出 `- 作用详解：...`，只保留仓库说明即可

所有分组标题统一使用二级标题，例如：
- `## Trending`
- `## Rust`

## 执行流程
### A. 抓取与落盘
1. 请求 `https://blog.0120012.xyz/github_trending/llms.txt`
2. 保存到本地工作目录
3. 从本地读回
4. 校验读回文本与响应文本一致
5. 解析抓取日期与分组

### B. 仓库处理
对于 Trending 仓库：
1. 读取仓库主页 URL
2. 查找 README raw 地址
3. 下载 raw README
4. README 落盘并读回
5. 首轮分析前 16000 字符
6. 若关键信息不足，补读关键章节或信号段落
7. 生成中文仓库说明与作用详解

对于非 Trending 仓库：
1. 基于 `llms.txt` 简介生成中文仓库说明
2. 默认不生成“作用详解”
3. 仍然必须遵守固定格式
4. 仓库说明仍然必须避免空泛话术

### C. 结果生成
脚本应生成：
- `channel.md`：只含 Trending，适合频道正文发送
- `archive.md`：全分组完整归档内容
- `metadata.json`：节点日期、抓取日期、更新时间、是否未更新、TOP5 等结构化元信息

### D. MCP 写入阶段
脚本本身负责**准备内容**，真正写入 `trace://stream/github_trending/YYYY-MM-DD` 由调用者用 MCP memory 工具完成：
1. 检查父节点存在
2. 创建或更新日期子节点
3. 过长时通过 MCP 分批写入
4. 严禁绕过 MCP 直接写 memory

## README 规则
### 适用范围
- 只有 `Trending` 分组需要深读 README。
- 其它分组默认不抓 README，不做 README 深读，不输出作用详解。

### Raw 优先
若 README 页面链接形如：
- `https://github.com/<owner>/<repo>/blob/<ref>/<path>`

必须转换为：
- `https://raw.githubusercontent.com/<owner>/<repo>/<ref>/<path>`

约束：
- 不保留 `/blob/`
- 不强行改写成 `refs/heads/...`
- `ref` 直接沿用分支 / tag / commit hash 原值
- raw 失败后，才退回主页简介、topics、目录结构等公开信息

### 16000 首轮窗口
- README 先完整下载并落盘
- 首轮只分析前 16000 字符
- 若 README 更短，则分析全文

### 关键章节补读
优先补读这些章节或近义标题：
- `Features`
- `Usage`
- `Quick Start`
- `Installation`
- `Examples`
- `FAQ`
- `Architecture`
- `Who is this for`
- `Overview`
- `Introduction`
- `Getting Started`

允许：
- 大小写差异
- Markdown 标题层级差异
- 常见近义标题

若 README 无明确结构，则补读含这些信号词的段落：
- `install`
- `usage`
- `example`
- `feature`
- `architecture`
- `for developers`
- `for teams`
- `use case`
- `getting started`

### 超长 README 降级
若“前 16000 字符 + 补读”仍不足以稳定提炼，则综合：
1. README 前 16000 字符
2. 补读章节
3. 仓库主页简介
4. topics
5. 目录结构
6. 显著文件名

允许降权或跳过：
- 徽章
- changelog
- 冗长示例
- 自动生成 API 列表
- 大段附录

若仍无法确认关键结论，必须写 `信息不足`。

## 反空话约束
### 普通条目与 Trending 条目都适用
禁止只写：
- 提升效率
- 降低门槛
- 适用于多种场景
- 赋能开发

必须尽量落到：
- 处理什么对象
- 用于什么任务
- 服务什么场景
- 面向什么用户
- 属于什么工作流

## 生产运行方式
### 方式一：抽样测试
适合：
- 单仓库验证
- 多仓库抽样
- 检查输出形状是否正确

示例：
- `python scripts/run_trending_v5.py --mode trending-test --limit 5`
- `python scripts/run_trending_v5.py --mode repo-test --repo-url https://github.com/vcvvvc/BitCoin-v0.01-ALPHA`

### 方式二：正式 daily 产出
适合：
- 定时任务
- 产出 channel/archive/metadata 三件套

示例：
- `python scripts/run_trending_v5.py --mode daily --workdir /tmp/github_trending_v5_daily`

## 调用后应检查的文件
- `channel.md`
- `archive.md`
- `metadata.json`

如果用户只要最终结果，就直接发送 `channel.md` 或对应片段；不要附带诊断信息。

## V5 补充
- V5 延续 V4 的抓取、README raw、16000 首轮窗口、关键章节补读、超长 README 降级、统一输出格式与反空话约束，本次升级不增加新的复杂分支。
- 默认输出策略：若用户没有明确要求排障、验证链路或调试报告，则只返回规范化仓库条目结果，不附带状态码、原始链接、readback 校验细节或过程日志。
- 在把规则落到 `trace://stream/github_trending` 这类 memory 节点时，不要只写“对应 skill / 对应 cron prompt”这种抽象说法；应显式写出：
  - skill 名称
  - SKILL.md 绝对路径
  - runner 脚本绝对路径
  - cron 模板绝对路径
- 这样可以避免节点、skill、模板之间名义同步但实际不可定位的问题。

## 关联文件
- `scripts/run_trending_v5.py` — 生产版 runner
- `references/output-spec.md` — 条目输出规范
- `templates/cron-prompt.md` — 可直接复用的 cron prompt 模板

## 成功标准
- 抓取、落盘、读回、解析链路完整
- README 优先使用 raw
- 最终输出全为规范化中文条目
- 普通条目与 Trending 条目都避免空泛话术
- daily 模式能直接产出 channel/archive/metadata 三件套
- `node_date` 默认直接等于 `llms.txt` 的日期字段；只有日期解析失败时才回退到当天日期
- 总结逻辑必须面向每天都会变化的新仓库，禁止依赖少量仓库名硬编码
- 后续 cron 调用只需加载本 skill + 跑脚本 + 用 MCP 写入

## 生产经验补充
- 这是定时任务，不是一次性脚本；稳定性优先于针对个别热门仓库手工优化文案。
- 如果 memory 节点里只写“对应 skill / 对应 cron prompt”而不写绝对路径，后续排障会很痛苦；在规则节点中应显式写出 skill 名、SKILL.md 路径、runner 脚本路径、cron 模板路径。
- 当用户明确说“只要结果”时，最终输出必须只保留规范化仓库条目；不要夹带状态码、原始链接、调试日志或过程报告。
- 面对每天新的数据、新的仓库时，结果质量仍应稳定；不能依赖少数仓库名的硬编码特判维持输出质量

## 生产稳定性约束（后续实现或审查时必须检查）
- 这是定时任务，不是一次性脚本；每天都会遇到新的仓库与新的 README 结构。
- 若 runner 仍依赖 `if name == ...` 这类仓库名硬编码特判，则它只算阶段性原型，不算真正可复用的生产版。
- 真正的生产版应把仓库说明与作用详解建立在通用规则上：`llms.txt` 简介、README 前 16000 字符、关键章节补读、仓库主页简介、topics、目录结构。
- 输出前应做稳定性检查：是否仍保留原始三行结构、是否缺少三项覆盖、是否掉回空泛模板句；不合格时应降级重写或明确写 `信息不足`。
- 若要把此 skill 长期用于 cron，优先继续减少硬编码、加强章节补读与结果校验，而不是继续追加仓库级特判。

## 常见失败
- 把 GitHub HTML README 当正文分析
- 没落盘就直接解析内存响应
- 保留 llms.txt 原始三行结构
- 作用详解写成抽象价值判断
- 依赖少量仓库名硬编码，导致对新仓库不稳定
- 把测试日志混到最终用户输出里
- 未区分 channel 正文与 archive 正文
- 只改 memory 节点，不同步脚本和 cron 模板
- memory 节点已经要求“节点日期以 llms.txt 为准”，但脚本仍错误地用当天日期作为默认节点日期
- 规则节点里只写“对应 skill / 对应 cron”，却不写实际 skill 名与绝对路径，导致运行时不可定位
