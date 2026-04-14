#!/usr/bin/env node

// Why: 兼容旧入口，内部转发到新 imap.js，避免历史命令失效。
const { spawnSync } = require('child_process');
const path = require('path');

const target = path.resolve(__dirname, 'imap.js');
const result = spawnSync(process.execPath, [target, 'check', '--limit', '5'], { stdio: 'inherit' });
process.exit(result.status || 0);
