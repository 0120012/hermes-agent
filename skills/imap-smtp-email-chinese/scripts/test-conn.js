#!/usr/bin/env node

// Why: 兼容旧入口，统一走新实现，避免维护两套 IMAP 客户端代码。
const { spawnSync } = require('child_process');
const path = require('path');

const target = path.resolve(__dirname, 'imap.js');
const result = spawnSync(process.execPath, [target, 'list-mailboxes'], { stdio: 'inherit' });
process.exit(result.status || 0);
