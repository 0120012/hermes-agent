#!/usr/bin/env node

// Why: 仅保留 nodemailer 做 SMTP，减少额外依赖，接口保持 send/test 两个核心能力。
const nodemailer = require('nodemailer');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });

function parseArgs(argv = process.argv.slice(2)) {
  const command = argv[0];
  const options = {};

  for (let i = 1; i < argv.length; i++) {
    const token = argv[i];
    if (!token.startsWith('--')) {
      continue;
    }
    const key = token.slice(2);
    const maybeValue = argv[i + 1];
    if (!maybeValue || maybeValue.startsWith('--')) {
      options[key] = true;
      continue;
    }
    options[key] = maybeValue;
    i += 1;
  }

  return { command, options };
}

function parseBool(v, fallback = false) {
  if (v === undefined) return fallback;
  return String(v).toLowerCase() === 'true';
}

function requireFile(filePath) {
  const abs = path.resolve(filePath);
  if (!fs.existsSync(abs)) throw new Error(`File not found: ${filePath}`);
  return abs;
}

// Why: 附件参数在 send 路径反复出现，集中解析可降低分支噪音并保持行为一致。
function parseAttachmentList(attachValue) {
  if (!attachValue) return [];
  return String(attachValue)
    .split(',')
    .map((v) => v.trim())
    .filter(Boolean)
    .map((filePath) => {
      const abs = requireFile(filePath);
      return { filename: path.basename(abs), path: abs };
    });
}

// Why: 文本/HTML/文件输入的优先级集中在一个函数里，避免后续修改时出现覆盖顺序错误。
function resolveBodyOptions(options) {
  if (options['body-file']) {
    const content = fs.readFileSync(requireFile(options['body-file']), 'utf8');
    if (String(options['body-file']).endsWith('.html') || options.html) {
      return { html: content, text: undefined };
    }
    return { text: content, html: undefined };
  }

  if (options['html-file']) {
    return { html: fs.readFileSync(requireFile(options['html-file']), 'utf8'), text: undefined };
  }

  if (options.body) {
    if (options.html) return { html: options.body, text: undefined };
    return { text: options.body, html: undefined };
  }

  return { text: '', html: undefined };
}

function createTransporter() {
  const host = process.env.SMTP_HOST;
  const user = process.env.SMTP_USER;
  const pass = process.env.SMTP_PASS;
  if (!host || !user || !pass) {
    throw new Error('Missing SMTP config: SMTP_HOST / SMTP_USER / SMTP_PASS');
  }

  return nodemailer.createTransport({
    host,
    port: Number(process.env.SMTP_PORT || 587),
    secure: parseBool(process.env.SMTP_SECURE, false),
    auth: { user, pass },
    tls: { rejectUnauthorized: parseBool(process.env.SMTP_REJECT_UNAUTHORIZED, true) },
  });
}

function buildMailOptions(options) {
  if (!options.to) throw new Error('Missing required option: --to <email>');
  if (!options.subject && !options['subject-file']) {
    throw new Error('Missing required option: --subject <text> or --subject-file <file>');
  }

  const body = resolveBodyOptions(options);
  const mail = {
    from: options.from || process.env.SMTP_FROM || process.env.SMTP_USER,
    to: options.to,
    cc: options.cc || undefined,
    bcc: options.bcc || undefined,
    subject: options.subject || '',
    text: body.text,
    html: body.html,
    attachments: parseAttachmentList(options.attach),
  };

  if (options['subject-file']) {
    mail.subject = fs.readFileSync(requireFile(options['subject-file']), 'utf8').trim();
  }

  return mail;
}

async function cmdSend(options) {
  const transporter = createTransporter();
  await transporter.verify();
  const info = await transporter.sendMail(buildMailOptions(options));
  return {
    success: true,
    messageId: info.messageId,
    response: info.response,
  };
}

async function cmdTest() {
  const transporter = createTransporter();
  await transporter.verify();
  const info = await transporter.sendMail({
    from: process.env.SMTP_FROM || process.env.SMTP_USER,
    to: process.env.SMTP_USER,
    subject: 'SMTP Connection Test',
    text: 'SMTP test message from minimal IMAP/SMTP skill',
  });

  return {
    success: true,
    message: 'SMTP connection successful',
    messageId: info.messageId,
  };
}

function printUsageAndExit() {
  console.error('Usage:');
  console.error('  node scripts/smtp.js send --to a@x.com --subject "Hello" [--body "text"]');
  console.error('  node scripts/smtp.js send --to a@x.com --subject-file s.txt --body-file body.txt [--attach a.pdf,b.pdf]');
  console.error('  node scripts/smtp.js test');
  process.exit(1);
}

async function main() {
  const { command, options } = parseArgs();
  try {
    let result;
    if (command === 'send') result = await cmdSend(options);
    else if (command === 'test') result = await cmdTest();
    else printUsageAndExit();

    console.log(JSON.stringify(result, null, 2));
  } catch (err) {
    console.error('Error:', err.message);
    process.exit(1);
  }
}

main();
