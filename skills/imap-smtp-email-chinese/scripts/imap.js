#!/usr/bin/env node

// Why: 统一走 imapflow + mailparser，替换老旧 imap/imap-simple，减少依赖面并降低维护风险。
const { ImapFlow } = require('imapflow');
const { simpleParser } = require('mailparser');
const fs = require('fs');
const path = require('path');
require('dotenv').config({ path: path.resolve(__dirname, '../.env') });

const DEFAULT_MAILBOX = process.env.IMAP_MAILBOX || 'INBOX';
const DEFAULT_LIMIT = 20;

function parseArgs(argv = process.argv.slice(2)) {
  const command = argv[0];
  const positional = [];
  const options = {};

  for (let i = 1; i < argv.length; i++) {
    const token = argv[i];
    if (!token.startsWith('--')) {
      positional.push(token);
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

  return { command, options, positional };
}

function parseBool(v, fallback = false) {
  if (v === undefined) return fallback;
  return String(v).toLowerCase() === 'true';
}

function parseLimit(v, fallback = DEFAULT_LIMIT) {
  const n = Number(v);
  if (!Number.isInteger(n) || n <= 0) return fallback;
  return n;
}

// Why: 所有 UID 输入统一走一个校验入口，避免不同命令出现边界行为漂移。
function parseRequiredUid(v, commandName) {
  const uid = Number(v);
  if (!Number.isInteger(uid) || uid <= 0) {
    throw new Error(`UID required: ${commandName} <uid>`);
  }
  return uid;
}

// Why: 批量 UID 的校验与转换集中处理，减少 mark-read/mark-unread 重复分支。
function parseUidList(values) {
  if (!values.length) throw new Error('UID(s) required');
  const ids = values.map((v) => Number(v));
  if (ids.some((v) => !Number.isInteger(v) || v <= 0)) {
    throw new Error('Invalid UID(s)');
  }
  return ids;
}

function formatImapDate(input) {
  const d = new Date(input);
  if (Number.isNaN(d.getTime())) throw new Error(`Invalid date: ${input}`);
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const day = String(d.getUTCDate()).padStart(2, '0');
  return `${day}-${months[d.getUTCMonth()]}-${d.getUTCFullYear()}`;
}

function parseRelativeTime(v) {
  const m = String(v || '').match(/^(\d+)(m|h|d)$/);
  if (!m) throw new Error('Invalid --recent format. Use 30m / 2h / 7d');
  const amount = Number(m[1]);
  const unit = m[2];
  const now = Date.now();
  const unitMs = unit === 'm' ? 60_000 : unit === 'h' ? 3_600_000 : 86_400_000;
  return formatImapDate(now - amount * unitMs);
}

function buildSearchCriteria(options) {
  const criteria = {};
  if (options.unseen) criteria.seen = false;
  if (options.seen) criteria.seen = true;
  if (options.from) criteria.from = String(options.from);
  if (options.to) criteria.to = String(options.to);
  if (options.subject) criteria.subject = String(options.subject);
  if (options.uid) criteria.uid = String(options.uid);

  if (options.recent) {
    criteria.since = parseRelativeTime(options.recent);
  } else {
    if (options.since) criteria.since = formatImapDate(options.since);
    if (options.before) criteria.before = formatImapDate(options.before);
  }

  if (Object.keys(criteria).length === 0) return { all: true };
  return criteria;
}

function makeClient() {
  const host = process.env.IMAP_HOST;
  const user = process.env.IMAP_USER;
  const pass = process.env.IMAP_PASS;
  if (!host || !user || !pass) {
    throw new Error('Missing IMAP config: IMAP_HOST / IMAP_USER / IMAP_PASS');
  }

  return new ImapFlow({
    host,
    port: Number(process.env.IMAP_PORT || 993),
    secure: parseBool(process.env.IMAP_TLS, true),
    auth: { user, pass },
    tls: { rejectUnauthorized: parseBool(process.env.IMAP_REJECT_UNAUTHORIZED, true) },
    enableUTF8Accept: true,
    connectionTimeout: 10_000,
    authTimeout: 10_000,
    logger: false,
  });
}

async function withMailbox(mailbox, readOnly, fn) {
  const client = makeClient();
  await client.connect();
  const lock = await client.getMailboxLock(mailbox || DEFAULT_MAILBOX, { readOnly });
  try {
    return await fn(client);
  } finally {
    lock.release();
    await client.logout();
  }
}

async function parseMessageFromSource(source, includeAttachments = false) {
  const parsed = await simpleParser(source);
  const text = parsed.text || '';
  return {
    from: parsed.from?.text || '',
    to: parsed.to?.text || '',
    subject: parsed.subject || '(no subject)',
    date: parsed.date || null,
    text,
    html: parsed.html || null,
    snippet: text ? text.slice(0, 200) : '',
    attachments: (parsed.attachments || []).map((a) => ({
      filename: a.filename || 'attachment.bin',
      contentType: a.contentType,
      size: a.size,
      cid: a.cid,
      content: includeAttachments ? a.content : undefined,
    })),
  };
}

async function fetchSummaryByUids(client, uids, limit) {
  const out = [];
  for (const uid of uids) {
    const msg = await client.fetchOne(uid, { uid: true, flags: true, envelope: true, source: true }, { uid: true });
    if (!msg || !msg.source) continue;
    const parsed = await parseMessageFromSource(msg.source, false);
    out.push({ uid: msg.uid, flags: msg.flags, ...parsed });
  }
  out.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));
  return out.slice(0, limit);
}

function sanitizeFilename(name) {
  const safe = path.basename(String(name || 'attachment.bin')).replace(/[^\w.\- ]/g, '_').trim();
  return safe || 'attachment.bin';
}

// Why: IMAP 搜索 + 摘要提取是 check/search 共用路径，集中后更容易维护与测试。
async function searchAndFetchSummary(client, criteria, limit) {
  const uids = await client.search(criteria, { uid: true });
  return fetchSummaryByUids(client, Array.isArray(uids) ? uids : [], limit);
}

async function cmdCheck(options) {
  return withMailbox(options.mailbox || DEFAULT_MAILBOX, true, async (client) => {
    const criteria = { seen: false };
    if (options.recent) criteria.since = parseRelativeTime(options.recent);
    return searchAndFetchSummary(client, criteria, parseLimit(options.limit, 10));
  });
}

async function cmdSearch(options) {
  return withMailbox(options.mailbox || DEFAULT_MAILBOX, true, async (client) => {
    const criteria = buildSearchCriteria(options);
    return searchAndFetchSummary(client, criteria, parseLimit(options.limit, DEFAULT_LIMIT));
  });
}

async function cmdFetch(uid, mailbox) {
  const parsedUid = parseRequiredUid(uid, 'fetch');
  return withMailbox(mailbox || DEFAULT_MAILBOX, true, async (client) => {
    const msg = await client.fetchOne(parsedUid, { uid: true, flags: true, envelope: true, source: true }, { uid: true });
    if (!msg || !msg.source) throw new Error(`Message not found: ${parsedUid}`);
    const parsed = await parseMessageFromSource(msg.source, false);
    return [{ uid: msg.uid, flags: msg.flags, ...parsed }];
  });
}

async function cmdDownload(uid, options) {
  const parsedUid = parseRequiredUid(uid, 'download');
  return withMailbox(options.mailbox || DEFAULT_MAILBOX, true, async (client) => {
    const msg = await client.fetchOne(parsedUid, { uid: true, source: true }, { uid: true });
    if (!msg || !msg.source) throw new Error(`Message not found: ${parsedUid}`);

    const parsed = await parseMessageFromSource(msg.source, true);
    if (!parsed.attachments.length) {
      return { uid: parsedUid, downloaded: [], message: 'No attachments found' };
    }

    const outputDirAbs = path.resolve(options.dir || '.');
    if (!fs.existsSync(outputDirAbs)) fs.mkdirSync(outputDirAbs, { recursive: true });

    const onlyFile = options.file ? String(options.file) : null;
    const downloaded = [];
    for (const attachment of parsed.attachments) {
      if (onlyFile && attachment.filename !== onlyFile) continue;
      if (!attachment.content) continue;
      const safeName = sanitizeFilename(attachment.filename);
      const filePath = path.resolve(outputDirAbs, safeName);
      if (!filePath.startsWith(outputDirAbs + path.sep) && filePath !== outputDirAbs) {
        throw new Error(`Invalid attachment filename: ${attachment.filename}`);
      }
      fs.writeFileSync(filePath, attachment.content);
      downloaded.push({ filename: safeName, path: filePath, size: attachment.size });
    }

    if (onlyFile && downloaded.length === 0) {
      return { uid: parsedUid, downloaded: [], message: `File not found: ${onlyFile}` };
    }

    return { uid: parsedUid, downloaded, message: `Downloaded ${downloaded.length} attachment(s)` };
  });
}

async function cmdUpdateSeen(uids, mailbox, addSeen) {
  const idList = parseUidList(uids);
  return withMailbox(mailbox || DEFAULT_MAILBOX, false, async (client) => {
    const range = idList.join(',');
    if (addSeen) {
      await client.messageFlagsAdd(range, ['\\Seen'], { uid: true });
      return { success: true, action: 'mark-read', uids: idList };
    }
    await client.messageFlagsRemove(range, ['\\Seen'], { uid: true });
    return { success: true, action: 'mark-unread', uids: idList };
  });
}

async function cmdListMailboxes() {
  const client = makeClient();
  await client.connect();
  try {
    const list = await client.list();
    return list.map((m) => ({
      name: m.path,
      delimiter: m.delimiter,
      flags: Array.from(m.flags || []),
      specialUse: m.specialUse || null,
    }));
  } finally {
    await client.logout();
  }
}

function printUsageAndExit() {
  console.error('Usage:');
  console.error('  node scripts/imap.js check [--limit 10] [--recent 2h] [--mailbox INBOX]');
  console.error('  node scripts/imap.js search [--unseen] [--from a@x.com] [--subject text] [--limit 20]');
  console.error('  node scripts/imap.js fetch <uid> [--mailbox INBOX]');
  console.error('  node scripts/imap.js download <uid> [--dir .] [--file name] [--mailbox INBOX]');
  console.error('  node scripts/imap.js mark-read <uid> [uid2 ...] [--mailbox INBOX]');
  console.error('  node scripts/imap.js mark-unread <uid> [uid2 ...] [--mailbox INBOX]');
  console.error('  node scripts/imap.js list-mailboxes');
  process.exit(1);
}

async function main() {
  const { command, options, positional } = parseArgs();
  try {
    let result;
    if (command === 'check') result = await cmdCheck(options);
    else if (command === 'search') result = await cmdSearch(options);
    else if (command === 'fetch') result = await cmdFetch(positional[0], options.mailbox);
    else if (command === 'download') result = await cmdDownload(positional[0], options);
    else if (command === 'mark-read') result = await cmdUpdateSeen(positional, options.mailbox, true);
    else if (command === 'mark-unread') result = await cmdUpdateSeen(positional, options.mailbox, false);
    else if (command === 'list-mailboxes') result = await cmdListMailboxes();
    else printUsageAndExit();

    console.log(JSON.stringify(result, null, 2));
  } catch (err) {
    console.error('Error:', err.message);
    process.exit(1);
  }
}

main();
