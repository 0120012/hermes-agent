# IMAP/SMTP Email Skill (Minimal Dependencies)

精简后的 IMAP/SMTP 工具，核心只保留邮件收发必需能力。

## 依赖（最少）

- `imapflow`：IMAP 连接与邮件检索
- `mailparser`：解析邮件正文/附件
- `nodemailer`：SMTP 发信
- `dotenv`：读取 `.env`

## 配置

在技能目录创建 `.env`：

```bash
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=your@gmail.com
IMAP_PASS=your_app_password
IMAP_TLS=true
IMAP_REJECT_UNAUTHORIZED=true
IMAP_MAILBOX=INBOX

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your@gmail.com
SMTP_PASS=your_app_password
SMTP_FROM=your@gmail.com
SMTP_REJECT_UNAUTHORIZED=true
```

## 安装

```bash
npm install
```

## IMAP 命令

```bash
# 检查未读
node scripts/imap.js check --limit 10 --recent 2h

# 搜索
node scripts/imap.js search --unseen --from "sender@example.com" --subject "invoice" --limit 20

# 读取某封邮件
node scripts/imap.js fetch <uid>

# 下载附件
node scripts/imap.js download <uid> --dir ./downloads [--file report.pdf]

# 标记已读/未读
node scripts/imap.js mark-read <uid>
node scripts/imap.js mark-unread <uid>

# 列出邮箱文件夹
node scripts/imap.js list-mailboxes
```

## SMTP 命令

```bash
# 连通性测试
node scripts/smtp.js test

# 发文本邮件
node scripts/smtp.js send --to receiver@example.com --subject "Hello" --body "World"

# 发 HTML 邮件
node scripts/smtp.js send --to receiver@example.com --subject "News" --html --body "<h1>Hi</h1>"

# 带附件
node scripts/smtp.js send --to receiver@example.com --subject "Report" --body "请查收" --attach ./report.pdf
```

## 兼容入口

历史脚本仍可用，但已转发到新实现：

- `node scripts/check-inbox.js` -> `node scripts/imap.js check --limit 5`
- `node scripts/test-conn.js` -> `node scripts/imap.js list-mailboxes`

## 安全提示

- `.env` 只放本地，不要提交到仓库。
- 附件下载会做文件名净化，避免路径穿越写文件。
- 生产环境建议保持 `*_REJECT_UNAUTHORIZED=true`。
