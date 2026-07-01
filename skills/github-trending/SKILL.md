---
name: github-trending-task
description: Analyze GitHub Trending commercial value.
---

# GitHub Trending 任务

## 一、任务模版

### 目标

从固定数据源拉取 GitHub Trending JSON，按指定分组读取仓库 README，上下文交给模型生成中文分析。程序只负责取数和读取 README；仓库说明翻译、作用详解、商业价值判断、创新方向由模型完成，禁止程序写死分析结论。

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

完整归档写入归档系统，字段固定：

```text
类别：github
标题：GitHub Trending YYYY-MM-DD
关键词：github, trending
```

归档正文最低结构：

```markdown
节点日期：YYYY-MM-DD
抓取日期：YYYY-MM-DD 或 未知
更新时间：YYYY-MM-DD HH:mm:ss Asia/Hong_Kong
是否未更新：是/否

## Trending
...

## 其他分组
...

## 商业价值 TOP5
...
```

频道正文最终只输出：

```markdown
## Trending
```

如果未更新，频道正文输出：

```markdown
## Trending

内容未更新（沿用上次日期）
```

### 统一输出格式

所有分组标题统一使用二级标题，例如 `## Trending`、`## Rust`、`## Python`。

所有仓库统一改写为：

```markdown
**序号. [owner/repo](repo_url) - 🌟 star数 - 语言**
- 仓库说明（中文翻译）：...
```

字段缺失时统一写：

- star：`未知`
- 语言：`未知`
- 仓库说明：`暂无仓库说明`

`Trending` 分组额外追加：

```markdown
- 作用详解：解决的问题：...；典型使用场景：...；目标用户：...
```

`作用详解` 必须覆盖“问题 / 场景 / 用户”三项；公开信息不足时可写 `信息不足`，但不得编造。

### 商业价值 TOP5

只保留一个商业价值榜，格式固定：

```markdown
## 商业价值 TOP5
1. owner/repo
- 商业价值：具体说明它为什么有商业价值，能降低什么成本、提升什么效率、创造什么新能力。
- 可用场景：说明可落地到哪些产品、业务流程或行业场景。
- 创新方向：说明可以基于它做什么新产品、新功能或差异化方案；信息不足时写 `信息不足`。
```

### 失败门槛

以下任一成立，则本次失败：

- 无法读取或解析 `llms.json`
- 无法完成目标分组统一格式化
- `Trending` 条目缺少中文仓库说明
- `Trending` 条目缺少 `作用详解`
- `作用详解` 未覆盖“问题 / 场景 / 用户”三项
- `商业价值 TOP5` 缺少“商业价值 / 可用场景 / 创新方向”任一项
- 输出大量保留源站原始三行结构
- 日期字段缺失或解析失败但未明确写 `日期字段解析失败`

失败时不得伪造结果、不得写入最终归档、不得发送半成品频道正文，只输出失败原因和阻塞点。

## 二、程序用法

### 简洁说明

- `fetch_llms_json.py`：拉取固定 `llms.json`，默认写入 `cache/github_trending/llms.json`；会明文输出每一步。
- `gather_readmes.py`：一次传入一个 JSON 分组名，完整读取该分组仓库 README；`--max-bytes` 是单个 README 的字节上限，推荐 `120000`，`0` 表示不限制；结果写入 JSON 文件，`stdout` 返回 `README 上下文 JSON：绝对路径`，步骤输出到 `stderr`。
- `read_raw_readme.py`：读取单个 README；输入可以是 raw URL，也可以是 GitHub 仓库根 URL；README 正文输出到 `stdout`，步骤输出到 `stderr`。

### 命令举例

```bash
cd /Users/vw/git/trending

# 1. 拉取固定数据源到本地缓存，默认写入 cache/github_trending/llms.json
python3 fetch_llms_json.py

# 2. 按单个分组读取 README 上下文；分组名来自 llms.json
python3 gather_readmes.py --max-bytes 12000 Trending
python3 gather_readmes.py --max-bytes 12000 "C++"

# 3. 读取单个 README：raw URL 或仓库根 URL 均可
python3 read_raw_readme.py https://raw.githubusercontent.com/vcvvvc/CLAUDE.MD/refs/heads/main/CLAUDE_ZH.md
python3 read_raw_readme.py --max-bytes 12000 https://github.com/vcvvvc/CLAUDE.MD
```
