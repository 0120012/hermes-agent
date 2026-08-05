## 快速安装



## 上手指南

```bash
hermes              # 交互式 CLI — 开始对话
hermes model        # 选择大模型提供商与具体模型
hermes tools        # 配置启用的工具集
hermes config set   # 设置单个配置项参数
hermes config get   # 查看单个配置项参数
hermes gateway      # 启动消息网关（支持 Telegram、Discord 等）
hermes setup        # 运行完整设置向导（一次性配置所有选项）
hermes claw migrate # 从 OpenClaw 进行数据迁移（针对 OpenClaw 老用户）
hermes update       # 更新至最新版本
hermes doctor       # 环境与故障诊断
```

📖 **[完整文档入口 →](https://hermes-agent.nousresearch.com/docs/)**

---

## 文档指引

所有文档均存放在 **[hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/)**：

| 板块                                                                                             | 包含内容                                             |
| --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| [快速开始](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart)                 | 2 分钟完成安装 → 设置 → 开启首次对话          |
| [CLI 使用指南](https://hermes-agent.nousresearch.com/docs/user-guide/cli)                              | 命令、快捷键、人格配置、会话管理             |
| [配置说明](https://hermes-agent.nousresearch.com/docs/user-guide/configuration)                | 配置文件、提供商、模型及全量选项                |
| [消息网关](https://hermes-agent.nousresearch.com/docs/user-guide/messaging)                | Telegram、Discord、Slack、WhatsApp、Signal、Home Assistant |
| [安全规范](https://hermes-agent.nousresearch.com/docs/user-guide/security)                          | 命令审批、私信配对、容器隔离机制          |
| [工具与工具集](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools)            | 40+ 款工具、工具集系统、终端后端               |
| [技能系统](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)              | 程序化记忆、技能中心（Skills Hub）、技能创建指南             |
| [记忆机制](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)                     | 持久化记忆、用户画像、最佳实践           |
| [MCP 扩展集成](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp)               | 连接任意 MCP 服务器以扩展系统能力           |
| [Cron 定时任务](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron)              | 支持平台推送的定时自动化任务                     |
| [上下文文件](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files)       | 影响每一轮对话的项目上下文定义             |
| [系统架构](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture)             | 项目结构、Agent 核心循环、关键类分析                 |
| [贡献指南](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing)             | 开发环境搭建、PR 流程、代码规范                  |
| [CLI 参考手册](https://hermes-agent.nousresearch.com/docs/reference/cli-commands)                  | 全量命令与参数 Flags 详解                                     |
| [环境变量参考](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) | 完整环境变量手册                                 |

---

## 开源许可证

MIT 许可证 — 详情请参阅 [LICENSE](LICENSE)。

由 [Nous Research](https://nousresearch.com) 开发构建。