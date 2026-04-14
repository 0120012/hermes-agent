---
name: ai-news-collector
description: AI news aggregation and popularity ranking tool. Trigger when users ask for the latest AI updates, such as "What AI news is there today?", "Summarize this week's AI updates", "What AI products are trending recently?", or "What is the AI community discussing lately?". Coverage includes new product launches, research papers, industry updates, funding news, open-source project updates, community viral phenomena, and trending AI tool/Agent projects. Output a Chinese summary list sorted by popularity, with source links.
---

# AI News Collector

Collect, aggregate, and rank AI news by popularity.

## Core Principle

**Do not only search "AI news today".** Generic searches mostly return SEO aggregator pages and trend-prediction articles, and will systematically miss community-level viral signals (such as exploding open-source tools or meme-level events). You must use a multi-dimensional, layered search strategy.

## Workflow

### 1. Multi-dimensional layered search (minimum 8 searches, recommended 10-12)

Search across the following **6 dimensions** in sequence, with at least 1 search per dimension:

#### Dimension A: Weekly roundups/newsletters (top priority 🔑)

This is the highest-density source; one article can cover 10+ news items.

```
Search terms:
- "last week in AI" [当前月份年份]
- "AI weekly roundup" [当前月份年份]
- "the batch AI newsletter"
- site:substack.com AI news [当前月份]
```

After finding a roundup, use `web_fetch` to get the full text and extract all news leads from it.

#### Dimension B: Community heat/viral spread (key dimension 🔑)

Capture bottom-up community breakouts; generic search can barely reach this type of signal.

```
Search terms:
- "viral AI tool" OR "viral AI agent"
- "AI trending" site:reddit.com OR site:news.ycombinator.com
- "GitHub trending AI" OR "AI open source trending"
- AI buzzing OR "everyone is talking about" AI
- "most popular AI" this week
```

#### Dimension C: Product launches and model updates

```
Search terms:
- "AI model release" OR "LLM launch" [当前月份]
- "AI product launch" [当前月份年份]
- OpenAI OR Anthropic OR Google OR Meta AI announcement
- "大模型 发布" OR "AI 新产品"
```

#### Dimension D: Funding and business

```
Search terms:
- "AI startup funding" [当前月份年份]
- "AI acquisition" OR "AI IPO"
- "AI 融资" OR "人工智能投资"
```

#### Dimension E: Research breakthroughs

```
Search terms:
- "AI breakthrough" OR "AI paper" [当前月份]
- "state of the art" machine learning
- "AI 论文" OR "机器学习突破"
```

#### Dimension F: Regulation and policy

```
Search terms:
- "AI regulation" OR "AI policy" [当前月份年份]
- "AI law" OR "AI governance" 
- "AI 监管" OR "人工智能法案"
```

### 2. Cross-validation and gap filling

After the first search round, check for missing coverage:

- If a newsletter mentions a project/event not covered in round one -> run a focused search on that project.
- If the same event is mentioned by 3+ different sources -> it is likely a hotspot; do deeper searches for more detail.
- If Chinese and English media are highlighting different hotspots -> cover both sides.

### 3. Search keyword design principles (anti-pattern checklist)

| ❌ Do not search like this | ✅ Search like this | Reason |
|---|---|---|
| "AI news today February 2026" | "AI weekly roundup February 2026" | The former returns aggregator pages; the latter returns curated content |
| "AI news today" | Search separately with "viral AI tool" + "AI model release" | Generic search cannot cover community phenomena |
| "artificial intelligence breaking news" | Search by dimensions | Too broad; returns noisy results |
| Add exact date (YYYY-MM-DD) in query | Use "this week", "today", "latest" | Exact dates often bias toward forecast/outlook articles |
| Start writing after only 3 searches | At least 8 searches across 6 dimensions | 3 searches cover less than 30% |

### 4. Popularity scoring

Evaluate each item's heat (1-5 stars) using the following signals:

| Signal | Weight | Notes |
|------|------|------|
| Same event covered by multiple media outlets | ⭐⭐⭐ High | 3+ sources = confirmed hotspot |
| Evidence of community viral spread | ⭐⭐⭐ High | GitHub stars surging, Twitter flooding, HN front page |
| From authoritative sources (top conferences, major vendor announcements) | ⭐⭐⭐ High | But major-vendor PR does not always mean true heat |
| Real user experience sharing | ⭐⭐ Medium | Actually being used > just announced |
| Technical breakthrough / impact scope | ⭐⭐ Medium | |
| Controversy (safety, ethics debates) | ⭐⭐ Medium | Controversy often indicates high impact |
| Recency (newer = hotter) | ⭐ Low-Medium | Auxiliary sorting signal |

### 5. Output format

Sort by heat descending, and output **15-25** news items:

```
## 🔥 AI 新闻速递（YYYY-MM-DD）

### ⭐⭐⭐⭐⭐ 热度最高

1. **[新闻标题]**
   > 一句话摘要（不超过 50 字）
   > 🔗 [来源名称](URL)

### ⭐⭐⭐⭐ 高热度

2. ...

### ⭐⭐⭐ 中等热度

...

---
📊 本次共收集 XX 条新闻 | 搜索 XX 次 | 覆盖维度：A/B/C/D/E/F | 更新时间：HH:MM
```

### 6. Deduplication and merging

- If multiple outlets report the same event, merge into one item and keep the most authoritative/detailed source.
- Mark "reported by multiple media outlets" in the summary to reflect heat.

## Recommended news sources

See [references/sources.md](references/sources.md).

## Notes

- Prefer HTTPS links.
- If content is paywalled/unreachable, label it as "subscription required".
- Stay objective and do not add subjective judgments about news content.
- Do not start output before completing at least 8 searches.
- If one dimension returns empty results, change keywords and search again.
