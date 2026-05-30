说明：本文件记录 `hermes-v0.15.2` 分支在 `v0.15.2` 标签之后的本地补充修改，按 commit 对应整理，便于核对代码、文档和本地裁剪项。

# Update

- `6c83e4632` `chore: remove github automation and plans`
  - 删除 `.github/` 下的 GitHub 模板、Actions、Dependabot 配置。
  - 删除 `.plans/` 下的计划文档。
- `c8fdf808f` `chore: ignore local debug artifacts`
  - 忽略本地调试输出 `init.md`。
  - 忽略 JetBrains 项目目录 `.idea/`。
- `d8a7654dc` `docs: update Chinese README setup notes`
  - 在 `README.zh-CN.md` 补充编译安装说明。
  - 补充 initial system prompt dump 说明。
- `0e0694db6` `debug: dump initial system prompt`
  - 首轮构建 system prompt 后输出到终端。
  - 同步写入当前目录 `init.md`，避免终端截断导致无法获取完整内容。
