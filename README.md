<p align="center">
  <img src="assets/banner.png" alt="Hermes Agent" width="100%">
</p>

# Hermes Agent ☤

<p align="center">
  <a href="https://hermes-agent.nousresearch.com/docs/"><img src="https://img.shields.io/badge/Docs-hermes--agent.nousresearch.com-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/NousResearch/hermes-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://nousresearch.com"><img src="https://img.shields.io/badge/Built%20by-Nous%20Research-blueviolet?style=for-the-badge" alt="Built by Nous Research"></a>
</p>

**由 [Nous Research](https://nousresearch.com) 构建的自我进化的 AI Agent。** 它是唯一具备内置学习闭环的 Agent —— 能够从经验中创建技能并在使用中改进，自主提示固化知识，搜索自身过往对话，并在多次会话中构建不断加深的用户模型。您可以在 5 美元的 VPS、GPU 集群或闲置时成本几乎为零的 Serverless 基础设施上运行它。它不局限于您的笔记本电脑 —— 当它在云端虚拟机上工作时，您可以通过 Telegram 与它交谈。

使用您想要的任何模型 —— [Nous Portal](https://portal.nousresearch.com)、[OpenRouter](https://openrouter.ai)（200+ 模型）、[z.ai/GLM](https://z.ai)、[Kimi/Moonshot](https://platform.moonshot.ai)、[MiniMax](https://www.minimax.io)、OpenAI，或您自建的端点。只需使用 `hermes model` 即可切换 —— 无需更改代码，拒绝供应商锁定。

<table>
<tr><td><b>真正的终端界面</b></td><td>完整的 TUI (终端用户界面)，支持多行编辑、斜杠命令自动补全、对话历史记录、中断与重定向，以及流式工具输出。</td></tr>
<tr><td><b>与您同在</b></td><td>Telegram、Discord、Slack、WhatsApp、Signal 和 CLI —— 均由单一网关进程提供支持。支持语音备忘录转录，跨平台对话连贯性。</td></tr>
<tr><td><b>闭环学习系统</b></td><td>由 Agent 整理的记忆系统，配有定期提示。在复杂任务后自动创建技能。技能在使用过程中自我改进。结合 LLM 总结的 FTS5 会话搜索实现跨会话召回。支持 Honcho 辩证用户建模。兼容 <a href="https://agentskills.io">agentskills.io</a> 开放标准。</td></tr>
<tr><td><b>定时自动化</b></td><td>内置 Cron 调度器，支持投递到任何平台。每日报告、每夜备份、每周审计 —— 全部使用自然语言配置，无人值守运行。</td></tr>
<tr><td><b>委托与并行化</b></td><td>派生隔离的子 Agent 用于并行的工作流。编写通过 RPC 调用工具的 Python 脚本，将多步流水线折叠为零上下文成本的回合。</td></tr>
<tr><td><b>无处不在，不仅限于您的笔记本</b></td><td>六种终端后端 —— 本地 (local)、Docker、SSH、Daytona、Singularity 和 Modal。Daytona 和 Modal 提供 Serverless 的持久化 —— 您的 Agent 环境在空闲时休眠并在按需时唤醒，在会话之间几乎零成本。您可以在 5 美元的 VPS 或 GPU 集群上运行它。</td></tr>
<tr><td><b>面向研究</b></td><td>批处理轨迹生成、Atropos 强化学习 (RL) 环境、轨迹压缩，用于训练下一代工具调用模型。</td></tr>
</table>

---

## 快速安装

```bash
curl -fsSL [https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh](https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh) | bash
```

支持 Linux、macOS、WSL2，以及通过 Termux 运行的 Android。安装程序会自动为您处理特定平台的设置。

> **Android / Termux:** 经过测试的手动安装路径记录在 [Termux 指南](https://hermes-agent.nousresearch.com/docs/getting-started/termux) 中。在 Termux 上，Hermes 会安装一个精简的 `.[termux]` extra 包，因为完整的 `.[all]` 目前会拉取与 Android 不兼容的语音依赖。
>
> **Windows:** 不支持原生 Windows。请安装 [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) 并运行上述命令。

安装后：

```bash
source ~/.bashrc    # 重载 shell (或: source ~/.zshrc)
hermes              # 开始对话！
```

---

## 快速上手

```bash
hermes              # 交互式 CLI — 开始对话
hermes model        # 选择您的 LLM 提供商和模型
hermes tools        # 配置启用的工具
hermes config set   # 设置单独的配置值
hermes gateway      # 启动消息网关 (Telegram, Discord 等)
hermes setup        # 运行完整的设置向导 (一次性配置所有内容)
hermes claw migrate # 从 OpenClaw 迁移 (如果您原先使用 OpenClaw)
hermes update       # 更新至最新版本
hermes doctor       # 诊断任何问题
```

📖 **[完整文档 →](https://hermes-agent.nousresearch.com/docs/)**

## CLI 与消息平台快速参考

Hermes 有两个入口点：使用 `hermes` 启动终端 UI，或运行网关并通过 Telegram、Discord、Slack、WhatsApp、Signal 或电子邮件与它交谈。一旦进入对话，大部分斜杠命令在两个界面中都是通用的。

| 操作 | CLI (命令行) | 消息平台 |
|---------|-----|---------------------|
| 开始对话 | `hermes` | 运行 `hermes gateway setup` + `hermes gateway start`，然后向机器人发送消息 |
| 开启新对话 | `/new` 或 `/reset` | `/new` 或 `/reset` |
| 切换模型 | `/model [provider:model]` | `/model [provider:model]` |
| 设置人格 | `/personality [name]` | `/personality [name]` |
| 重试或撤销上一轮 | `/retry`, `/undo` | `/retry`, `/undo` |
| 压缩上下文 / 检查使用量 | `/compress`, `/usage`, `/insights [--days N]` | `/compress`, `/usage`, `/insights [days]` |
| 浏览技能 | `/skills` 或 `/<skill-name>` | `/skills` 或 `/<skill-name>` |
| 中断当前工作 | `Ctrl+C` 或发送新消息 | `/stop` 或发送新消息 |
| 平台特定状态 | `/platforms` | `/status`, `/sethome` |

完整命令列表请参见 [CLI 指南](https://hermes-agent.nousresearch.com/docs/user-guide/cli) 和 [消息网关指南](https://hermes-agent.nousresearch.com/docs/user-guide/messaging)。

---

## 文档

所有文档均位于 **[hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/)**：

| 章节 | 涵盖内容 |
|---------|---------------|
| [快速入门 (Quickstart)](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart) | 安装 → 设置 → 2 分钟开启第一次对话 |
| [CLI 用法 (CLI Usage)](https://hermes-agent.nousresearch.com/docs/user-guide/cli) | 命令、快捷键、人格、会话 |
| [配置 (Configuration)](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) | 配置文件、提供商、模型、所有选项 |
| [消息网关 (Messaging Gateway)](https://hermes-agent.nousresearch.com/docs/user-guide/messaging) | Telegram, Discord, Slack, WhatsApp, Signal, Home Assistant |
| [安全 (Security)](https://hermes-agent.nousresearch.com/docs/user-guide/security) | 命令审批、私信配对、容器隔离 |
| [工具与工具集 (Tools & Toolsets)](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools) | 40+ 工具、工具集系统、终端后端 |
| [技能系统 (Skills System)](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) | 过程记忆、技能中心、创建技能 |
| [记忆 (Memory)](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) | 持久记忆、用户画像、最佳实践 |
| [MCP 集成 (MCP Integration)](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) | 连接任何 MCP 服务器以扩展能力 |
| [Cron 调度 (Cron Scheduling)](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron) | 定时任务与平台投递 |
| [上下文文件 (Context Files)](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files) | 塑造每次对话的项目上下文 |
| [架构 (Architecture)](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture) | 项目结构、Agent 循环、核心类 |
| [贡献 (Contributing)](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing) | 开发设置、PR 流程、代码风格 |
| [CLI 参考 (CLI Reference)](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) | 所有命令与参数标志 |
| [环境变量 (Environment Variables)](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) | 完整的环境变量参考 |

---

## 从 OpenClaw 迁移

如果您之前使用的是 OpenClaw，Hermes 可以自动导入您的设置、记忆、技能和 API 密钥。

**首次设置期间：** 设置向导 (`hermes setup`) 会自动检测 `~/.openclaw` 并在开始配置前提示迁移。

**安装后的任何时间：**

```bash
hermes claw migrate              # 交互式迁移 (完整预设)
hermes claw migrate --dry-run    # 预览将被迁移的内容
hermes claw migrate --preset user-data   # 迁移但不包含敏感凭据
hermes claw migrate --overwrite  # 覆盖现有的冲突内容
```

导入的内容：
- **SOUL.md** — 人格文件
- **记忆 (Memories)** — MEMORY.md 和 USER.md 条目
- **技能 (Skills)** — 用户创建的技能 → `~/.hermes/skills/openclaw-imports/`
- **命令白名单 (Command allowlist)** — 审批模式
- **消息设置 (Messaging settings)** — 平台配置、允许的用户、工作目录
- **API 密钥 (API keys)** — 在白名单内的凭据 (Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs)
- **TTS 资产 (TTS assets)** — 工作区音频文件
- **工作区指令 (Workspace instructions)** — AGENTS.md (通过 `--workspace-target`)

运行 `hermes claw migrate --help` 查看所有选项，或使用 `openclaw-migration` 技能通过 Agent 引导式交互进行带有试运行预览的迁移。

---

## 贡献

我们欢迎各种贡献！请参阅 [贡献指南](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing) 获取开发设置、代码风格和 PR 流程。

贡献者快速入门：

```bash
git clone [https://github.com/NousResearch/hermes-agent.git](https://github.com/NousResearch/hermes-agent.git)
cd hermes-agent
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
uv venv venv --python 3.11
source venv/bin/activate
uv pip install -e ".[all,dev]"
python -m pytest tests/ -q
```

> **RL 训练（可选）：** 如果需要进行 RL/Tinker-Atropos 集成开发：
> ```bash
> git submodule update --init tinker-atropos
> uv pip install -e "./tinker-atropos"
> ```

---

## 社区

- 💬 [Discord](https://discord.gg/NousResearch)
- 📚 [技能中心 (Skills Hub)](https://agentskills.io)
- 🐛 [Issues](https://github.com/NousResearch/hermes-agent/issues)
- 💡 [讨论 (Discussions)](https://github.com/NousResearch/hermes-agent/discussions)
- 🔌 [HermesClaw](https://github.com/AaronWong1999/hermesclaw) — 社区微信桥接：在同一个微信账号上运行 Hermes Agent 和 OpenClaw。

---

## 许可证

MIT — 详见 [LICENSE](LICENSE)。

由 [Nous Research](https://nousresearch.com) 构建。