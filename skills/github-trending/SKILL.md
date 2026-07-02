---
name: github-trending-task
description: Analyze GitHub Trending commercial value.
---

# GitHub Trending 任务

## 一、任务模版

### 目标

从固定数据源拉取 GitHub Trending JSON，只读取 `Trending` 分组仓库 README，上下文交给模型生成中文商业价值分析和价值排序，并完整输出该分组全部项目。SKILL中python程序只负责取数和读取 README；第一性原理、VC视角、开发者继续开发视角、创业者视角、当前年月环境分析、业务壁垒与风险由模型完成，禁止程序写死分析结论。禁止输出、分析或写入非 `Trending` 分组内容。

### 数据源

固定使用：

```text
https://blog.0120012.xyz/github_trending/llms.json
```

抓取日期必须来自 `llms.json` 内日期字段，禁止伪造抓取日期。

### 日期规则

- 抓取日期：以 `llms.json` 内日期字段为准。
- 更新时间：以 `Asia/Hong_Kong` 时区生成。
- 节点日期：默认等于抓取日期。
- 如果日期字段缺失或解析失败，必须明确写：`日期字段解析失败`；此时节点日期才允许退回 `Asia/Hong_Kong` 当天日期。
- 若抓取日期与最近一次归档中的抓取日期相同，正文必须写：`内容未更新（沿用上次日期）`。

### 归档写入

完整归档写入mem012记忆系统，字段固定：

```text
类别：github
标题：GitHub Trending YYYY-MM-DD
关键词：github, trending
```

归档正文只写 `Trending` 分组商业价值榜，最低结构：

```markdown
节点日期：YYYY-MM-DD
抓取日期：YYYY-MM-DD 或 未知
更新时间：YYYY-MM-DD HH:mm:ss Asia/Hong_Kong
是否未更新：是/否

## Trending 分组商业价值榜
...
```

最终频道消息必须发送到频道 `1497481717018005504`，不得发送到其他频道。

频道正文最终只输出商业价值榜：

```markdown
## Trending 分组商业价值榜
...
```

如果未更新，频道正文输出：

```markdown
## Trending 分组商业价值榜

内容未更新（沿用上次日期）
```

### 统一输出格式

唯一允许的输出主体是 `## Trending 分组商业价值榜`。

### Trending 分组商业价值榜

从 `Trending` 分组全部项目中创建一个商业价值榜，必须覆盖该分组全部项目，不得只输出部分项目。按商业价值从高到低排序；排序优先看真实需求、投资吸引力、继续开发空间、创业落地路径、当前年月窗口期和业务壁垒风险，禁止按 star、热度或语言排序替代商业价值排序。格式固定：

```markdown
## Trending 分组商业价值榜
排序依据：用 1-3 句话说明本次排序最看重的商业判断标准。

1. [owner/repo](repo_url) - 🌟 star数
- 一句话定位：说明它是什么，解决了什么痛点以及最可能卖给谁。
- 仓库说明：用中文概括仓库公开说明和 README 体现的核心能力；信息不足时写 `暂无仓库说明`。
- 第一性原理：拆出真实需求、核心约束、不可替代价值，并说明为什么排在当前位置。
- VC视角：判断市场空间、增长性、可投性和为什么值得押注；信息不足时写 `信息不足`。
- 开发者继续开发视角：说明最该补齐的核心能力、工程化能力、API、生态集成或使用门槛。
- 创业者视角：说明最小可卖产品、首批客户、获客方式和定价假设。
- 当前年月环境分析：以 `更新时间` 所属年月为准，只基于 README、llms.json 和可验证上下文判断模型、开源、平台、监管、资本和企业预算环境；无法验证时写 `信息不足`。
- 业务壁垒与风险：说明可建立的壁垒、最大风险和最小验证动作。
```

### 失败门槛

以下任一成立，则本次失败：

- 无法读取或解析 `llms.json`
- 未只基于 `Trending` 分组项目创建商业价值榜
- `Trending 分组商业价值榜` 未覆盖该分组全部项目
- `Trending 分组商业价值榜` 未按商业价值从高到低排序
- `Trending 分组商业价值榜` 缺少“排序依据 / 一句话定位 / 仓库说明 / 第一性原理 / VC视角 / 开发者继续开发视角 / 创业者视角 / 当前年月环境分析 / 业务壁垒与风险”任一项
- 输出、分析或归档非 `Trending` 分组内容
- 最终频道消息未发送到频道 `1497481717018005504`
- 日期字段缺失或解析失败但未明确写 `日期字段解析失败`

失败时不得伪造结果、不得写入最终归档、不得发送半成品频道正文，只输出失败原因和阻塞点。

## 二、程序用法

### 简洁说明

- `fetch_llms_json.py`：拉取固定 `llms.json`，默认写入 `cache/github_trending/llms.json`；会明文输出每一步。
- `gather_readmes.py`：本任务只允许传入 `Trending`，完整读取该分组仓库 README；`--max-bytes` 是单个 README 的字节上限，推荐 `120000`，`0` 表示不限制；结果写入 JSON 文件，`stdout` 返回 `README 上下文 JSON：绝对路径`，步骤输出到 `stderr`。
- `read_raw_readme.py`：读取单个 README；输入可以是 raw URL，也可以是 GitHub 仓库根 URL；README 正文输出到 `stdout`，步骤输出到 `stderr`。

### 命令举例

```bash
# 1. 拉取固定数据源到本地缓存，默认写入 cache/github_trending/llms.json
python3 fetch_llms_json.py

# 2. 只读取 Trending 分组 README 上下文
python3 gather_readmes.py --max-bytes 12000 Trending

# 3. 读取单个 README：raw URL 或仓库根 URL 均可
python3 read_raw_readme.py https://raw.githubusercontent.com/vcvvvc/CLAUDE.MD/refs/heads/main/CLAUDE_ZH.md
python3 read_raw_readme.py --max-bytes 12000 https://github.com/vcvvvc/CLAUDE.MD
```
