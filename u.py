from datetime import datetime
import email
from email import policy
from email.header import decode_header
from html import unescape
import imaplib
from pathlib import Path
import random
import re
import socket
import threading
import time

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

# ============= قالب الواجهة (HTML / CSS / JS) =============

TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>صندوق الوارد</title>
    <style>
        :root {
            --bg: #0a0e1a;
            --card: #161e2f;
            --card-hover: #1d2739;
            --border: #283349;
            --text: #e8ecf5;
            --text-dim: #8b95ab;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --success: #10b981;
            --danger: #ef4444;
            --accent: #06b6d4;
        }
        * { box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: radial-gradient(ellipse at top, #131b2e 0%, #0a0e1a 60%);
            background-attachment: fixed;
            color: var(--text);
            margin: 0;
            min-height: 100vh;
            padding: 24px 16px;
            -webkit-font-smoothing: antialiased;
        }
        .container { max-width: 900px; margin: 0 auto; }

        /* ===== الهيدر ===== */
        .top-bar {
            background: linear-gradient(135deg, #1a2438 0%, #16203a 100%);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px 22px;
            margin-bottom: 18px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.35);
        }
        .top-bar h2 {
            margin: 0 0 6px;
            font-size: 17px;
            font-weight: 600;
            color: var(--text-dim);
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        .email-badge {
            color: var(--accent);
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 16px;
            background: rgba(6,182,212,0.08);
            padding: 4px 12px;
            border-radius: 8px;
            border: 1px solid rgba(6,182,212,0.2);
            word-break: break-all;
        }
        .hint {
            font-size: 12.5px;
            color: var(--text-dim);
            margin-bottom: 14px;
        }
        .actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .btn {
            background: var(--card-hover);
            color: var(--text);
            border: 1px solid var(--border);
            padding: 9px 15px;
            border-radius: 9px;
            cursor: pointer;
            font-size: 13.5px;
            font-weight: 600;
            font-family: inherit;
            transition: all 0.15s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            white-space: nowrap;
        }
        .btn:hover { background: var(--primary); border-color: var(--primary); transform: translateY(-1px); }
        .btn:active { transform: translateY(0); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .btn-primary { background: var(--primary); border-color: var(--primary); }
        .btn-primary:hover { background: var(--primary-hover); }
        .btn-danger { background: rgba(239,68,68,0.12); border-color: rgba(239,68,68,0.35); color: #fca5a5; }
        .btn-danger:hover { background: var(--danger); border-color: var(--danger); color: white; }
        .btn .spin {
            width: 13px; height: 13px;
            border: 2px solid currentColor;
            border-top-color: transparent;
            border-radius: 50%;
            animation: spin 0.7s linear infinite;
            display: none;
        }
        .btn.loading .spin { display: inline-block; }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* ===== إحصائيات ===== */
        .stats {
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 12px;
            margin-bottom: 18px;
            align-items: stretch;
        }
        .stat-box {
            background: var(--card);
            border: 1px solid var(--border);
            padding: 14px 18px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .stat-num {
            font-size: 24px;
            font-weight: 800;
            color: var(--accent);
            line-height: 1;
        }
        .stat-label { font-size: 13px; color: var(--text-dim); }
        .status-dot {
            width: 9px; height: 9px;
            border-radius: 50%;
            background: var(--success);
            box-shadow: 0 0 8px var(--success);
            animation: pulse 2s infinite;
            display: inline-block;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }

        /* ===== شريط البحث ===== */
        .search-wrap {
            display: flex;
            gap: 8px;
            margin-bottom: 14px;
            align-items: center;
        }
        .search-input {
            flex: 1;
            background: var(--card);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 11px 16px;
            border-radius: 10px;
            font-size: 14px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.15s, box-shadow 0.15s;
        }
        .search-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(59,130,246,0.15);
        }
        .search-input::placeholder { color: var(--text-dim); }
        .search-count {
            font-size: 12.5px;
            color: var(--text-dim);
            white-space: nowrap;
            padding: 0 6px;
            min-width: 70px;
            text-align: center;
            font-variant-numeric: tabular-nums;
        }
        .search-clear {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-dim);
            width: 40px;
            height: 40px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 16px;
            display: none;
            transition: all 0.15s;
        }
        .search-clear:hover {
            color: var(--danger);
            border-color: var(--danger);
        }
        .search-clear.show {
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }

        /* ===== قائمة الرسائل ===== */
        .section-title {
            font-size: 15px;
            font-weight: 700;
            color: var(--text-dim);
            margin: 0 0 12px;
            padding: 0 4px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .message-item {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-bottom: 10px;
            overflow: hidden;
            transition: all 0.2s ease;
            border-right: 3px solid var(--border);
        }
        .message-item.unread { border-right-color: var(--primary); }
        .message-item:hover { background: var(--card-hover); border-color: rgba(59,130,246,0.4); }
        .message-header {
            padding: 15px 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            cursor: pointer;
            user-select: none;
        }
        .message-header .left {
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
            min-width: 0;
        }
        .unread-dot {
            width: 8px; height: 8px;
            border-radius: 50%;
            background: var(--primary);
            flex-shrink: 0;
            box-shadow: 0 0 6px var(--primary);
        }
        .message-item:not(.unread) .unread-dot { background: transparent; box-shadow: none; }
        .msg-main { min-width: 0; flex: 1; }
        .subject-title {
            font-size: 14.5px;
            font-weight: 600;
            color: var(--text);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .meta-small {
            font-size: 12px;
            color: var(--text-dim);
            margin-top: 3px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .folder-tag {
            display: inline-block;
            font-size: 10.5px;
            background: rgba(139,149,171,0.15);
            color: var(--text-dim);
            padding: 1px 7px;
            border-radius: 4px;
            margin-right: 6px;
            vertical-align: middle;
        }
        .time-badge {
            font-size: 11.5px;
            color: var(--text-dim);
            background: rgba(255,255,255,0.04);
            padding: 4px 9px;
            border-radius: 6px;
            flex-shrink: 0;
            font-variant-numeric: tabular-nums;
        }
        .codes-row {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
        }
        .code-chip {
            background: rgba(6,182,212,0.1);
            color: var(--accent);
            border: 1px solid rgba(6,182,212,0.25);
            padding: 3px 10px;
            border-radius: 6px;
            font-size: 12.5px;
            font-weight: 700;
            font-family: 'Consolas', monospace;
            cursor: pointer;
            transition: all 0.15s;
        }
        .code-chip:hover { background: var(--accent); color: #0a0e1a; }

        .message-body {
            display: none;
            padding: 16px 18px;
            border-top: 1px solid var(--border);
            background: rgba(0,0,0,0.15);
            animation: slideDown 0.2s ease;
        }
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-4px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .meta-info {
            font-size: 12.5px;
            color: var(--text-dim);
            margin-bottom: 12px;
            line-height: 1.7;
            padding: 10px 12px;
            background: rgba(255,255,255,0.02);
            border-radius: 8px;
            border-right: 2px solid var(--accent);
        }
        .meta-info strong { color: var(--text); font-weight: 600; }
        .email-text {
            font-size: 13.5px;
            color: var(--text);
            white-space: pre-wrap;
            line-height: 1.7;
            background: rgba(0,0,0,0.25);
            padding: 14px;
            border-radius: 10px;
            max-height: 420px;
            overflow-y: auto;
            word-wrap: break-word;
        }
        .email-text::-webkit-scrollbar { width: 8px; }
        .email-text::-webkit-scrollbar-track { background: transparent; }
        .email-text::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

        .empty {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-dim);
        }
        .empty-icon { font-size: 44px; margin-bottom: 12px; opacity: 0.4; }

        /* ===== Toast ===== */
        .toast {
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%) translateY(80px);
            padding: 12px 22px;
            border-radius: 10px;
            background: var(--success);
            color: white;
            font-size: 14px;
            font-weight: 600;
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            z-index: 1000;
            opacity: 0;
            transition: all 0.3s ease;
            pointer-events: none;
        }
        .toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }
        .toast.error { background: var(--danger); }

        /* ===== موبايل ===== */
        @media (max-width: 600px) {
            body { padding: 12px 10px; }
            .top-bar { padding: 16px; }
            .email-badge { font-size: 14px; }
            .btn { padding: 8px 12px; font-size: 13px; }
            .stats { grid-template-columns: 1fr; }
            .subject-title { font-size: 13.5px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="top-bar">
            <h2>
                📬 الحساب الحالي:
                <span class="email-badge" id="currentEmail">{{ current_email or 'لا يوجد' }}</span>
            </h2>
            <p class="hint">اضغط على أي رسالة لعرض محتواها • اضغط على أي كود لنسخه • Ctrl+F للبحث</p>
            <div class="actions">
                <button class="btn btn-primary" onclick="copyEmail()">📋 نسخ البريد</button>
                <button class="btn" onclick="newEmail(this)">🔄 حساب عشوائي</button>
                <button class="btn" onclick="refreshMessages(this)">↻ تحديث الآن</button>
                <button class="btn btn-danger" onclick="clearMessages(this)">🗑 مسح الشاشة</button>
            </div>
        </div>

        <div class="stats">
            <div class="stat-box">
                <div class="stat-num">{{ codes_count }}</div>
                <div>
                    <div class="stat-label">كود مستخرج</div>
                    <div style="font-size:11.5px; color: var(--text-dim); margin-top:2px;">
                        <span class="status-dot"></span> المراقبة نشطة
                    </div>
                </div>
            </div>
            <button class="btn" onclick="copyAllCodes(this)">📋 نسخ كل الأكواد</button>
        </div>

        <div class="search-wrap">
            <input type="text" id="searchInput" class="search-input"
                   placeholder="🔎 ابحث في الموضوع أو المُرسل أو المحتوى... (Ctrl+F)"
                   autocomplete="off">
            <button class="search-clear" id="searchClear" onclick="clearSearch()" title="مسح البحث">✕</button>
            <span class="search-count" id="searchCount"></span>
        </div>

        <div class="section-title">
            <span>صندوق الرسائل</span>
            <span style="font-weight:400; font-size:12.5px;" id="msgTotal">{{ messages|length }} رسالة</span>
        </div>

        <div id="messagesList">
            {% for msg in messages %}
            <div class="message-item {% if msg.unread %}unread{% endif %}"
                 data-search="{{ msg.subject }} {{ msg.from }} {{ msg.body }} {{ msg.codes|join(' ') }}">
                <div class="message-header" onclick="toggleDetails('details-{{ loop.index }}', this)">
                    <div class="left">
                        <span class="unread-dot"></span>
                        <div class="msg-main">
                            <div class="subject-title">
                                {% if msg.folder and msg.folder|upper != 'INBOX' %}
                                <span class="folder-tag">{{ msg.folder }}</span>
                                {% endif %}
                                📌 {{ msg.subject }}
                            </div>
                            <div class="meta-small">من: {{ msg.from }}</div>
                            {% if msg.codes %}
                            <div class="codes-row">
                                {% for code in msg.codes %}
                                <span class="code-chip" onclick="event.stopPropagation(); copyCode(this, '{{ code }}')">{{ code }}</span>
                                {% endfor %}
                            </div>
                            {% endif %}
                        </div>
                    </div>
                    <span class="time-badge">{{ msg.received_at }}</span>
                </div>

                <div id="details-{{ loop.index }}" class="message-body" onclick="event.stopPropagation()">
                    <div class="meta-info">
                        <div><strong>من:</strong> {{ msg.from }}</div>
                        <div><strong>التاريخ:</strong> {{ msg.date }}</div>
                        {% if msg.folder %}<div><strong>المجلد:</strong> {{ msg.folder }}</div>{% endif %}
                    </div>
                    <div class="email-text">{{ msg.body }}</div>
                </div>
            </div>
            {% else %}
            <div class="empty">
                <div class="empty-icon">📭</div>
                <div>في انتظار وصول رسائل جديدة...</div>
            </div>
            {% endfor %}
        </div>
    </div>

    <div id="toast" class="toast"></div>

    <script>
        const pageRevision = {{ revision | tojson }};
        let pollBusy = false;
        let actionBusy = false;

        function toggleDetails(id, header) {
            const el = document.getElementById(id);
            const item = header.closest('.message-item');
            const isOpen = el.style.display === 'block';
            el.style.display = isOpen ? 'none' : 'block';
            if (!isOpen) item.classList.remove('unread');
        }

        function showToast(message, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = 'toast ' + type;
            void toast.offsetWidth;
            toast.classList.add('show');
            clearTimeout(toast._timer);
            toast._timer = setTimeout(() => toast.classList.remove('show'), 2600);
        }

        async function api(url, method = 'GET') {
            const options = { method, cache: 'no-store' };
            if (method !== 'GET') {
                options.headers = { 'Content-Type': 'application/json' };
                options.body = '{}';
            }
            const response = await fetch(url, options);
            const data = await response.json();
            if (!response.ok || !data.success) throw new Error(data.error || 'تعذر تنفيذ الطلب');
            return data;
        }

        async function copyText(text) {
            if (navigator.clipboard && window.isSecureContext) {
                try { await navigator.clipboard.writeText(text); return; } catch (_) {}
            }
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            try {
                ta.focus(); ta.select();
                if (!document.execCommand('copy')) throw new Error('النسخ غير مدعوم');
            } finally { ta.remove(); }
        }

        async function copyEmail() {
            const address = document.getElementById('currentEmail').textContent.trim();
            if (!address.includes('@')) return showToast('لا يوجد بريد متاح', 'error');
            try { await copyText(address); showToast('✅ تم نسخ البريد'); }
            catch (e) { showToast(e.message, 'error'); }
        }

        async function copyCode(el, code) {
            try {
                await copyText(code);
                showToast('✅ تم نسخ: ' + code);
                el.style.transform = 'scale(1.15)';
                setTimeout(() => el.style.transform = '', 180);
            } catch (e) { showToast(e.message, 'error'); }
        }

        async function copyAllCodes(btn) {
            const codes = Array.from(document.querySelectorAll('.code-chip')).map(el => el.textContent.trim());
            if (!codes.length) return showToast('لا توجد أكواد', 'error');
            try { await copyText(codes.join('\\n')); showToast('✅ تم نسخ ' + codes.length + ' كود'); }
            catch (e) { showToast(e.message, 'error'); }
        }

        async function runAction(url, btn) {
            if (actionBusy) return;
            actionBusy = true;
            if (btn) btn.classList.add('loading');
            try {
                await api(url, 'POST');
                location.reload();
            } catch (e) {
                showToast(e.message, 'error');
                actionBusy = false;
                if (btn) btn.classList.remove('loading');
            }
        }

        function newEmail(btn) { return runAction('/new_email', btn); }
        function clearMessages(btn) {
            if (confirm('مسح الرسائل من الشاشة فقط؟')) return runAction('/clear_messages', btn);
        }

        async function refreshMessages(btn) {
            if (pollBusy || actionBusy) return;
            pollBusy = true;
            if (btn) btn.classList.add('loading');
            try {
                const data = await api('/get_messages?since=' + pageRevision);
                if (data.new_messages) location.reload();
                else showToast('لا توجد رسائل جديدة');
            } catch (e) { showToast(e.message, 'error'); }
            finally {
                pollBusy = false;
                if (btn) btn.classList.remove('loading');
            }
        }

        async function pollMessages() {
            if (pollBusy || actionBusy) return;
            pollBusy = true;
            try {
                const data = await api('/get_messages?since=' + pageRevision);
                if (data.new_messages) location.reload();
            } catch (_) {}
            finally { pollBusy = false; }
        }

        // ===== البحث الفوري =====
        function filterMessages() {
            const input = document.getElementById('searchInput');
            const q = input.value.trim().toLowerCase();
            const items = document.querySelectorAll('.message-item');
            const clearBtn = document.getElementById('searchClear');
            const countEl = document.getElementById('searchCount');
            const totalEl = document.getElementById('msgTotal');
            const emptyEl = document.querySelector('.empty');

            clearBtn.classList.toggle('show', q.length > 0);

            if (!q) {
                items.forEach(it => it.style.display = '');
                countEl.textContent = '';
                countEl.style.color = '';
                if (emptyEl) emptyEl.style.display = '';
                if (totalEl) totalEl.textContent = items.length + ' رسالة';
                return;
            }

            let visible = 0;
            items.forEach(it => {
                const hay = (it.dataset.search || '').toLowerCase();
                if (hay.includes(q)) {
                    it.style.display = '';
                    visible++;
                } else {
                    it.style.display = 'none';
                }
            });

            if (visible === 0) {
                countEl.textContent = 'لا نتائج';
                countEl.style.color = 'var(--danger)';
            } else {
                countEl.textContent = visible + ' / ' + items.length;
                countEl.style.color = 'var(--success)';
            }
            if (totalEl) totalEl.textContent = visible + ' من ' + items.length + ' رسالة';
            if (emptyEl) emptyEl.style.display = 'none';
        }

        function clearSearch() {
            const input = document.getElementById('searchInput');
            input.value = '';
            sessionStorage.removeItem('inboxSearch');
            filterMessages();
            input.focus();
        }

        (function restoreSearch() {
            const saved = sessionStorage.getItem('inboxSearch');
            if (saved) {
                document.getElementById('searchInput').value = saved;
                filterMessages();
            }
        })();

        document.getElementById('searchInput').addEventListener('input', (e) => {
            sessionStorage.setItem('inboxSearch', e.target.value);
            filterMessages();
        });

        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'f') {
                e.preventDefault();
                document.getElementById('searchInput').focus();
                document.getElementById('searchInput').select();
            }
            if (e.key === 'Escape' && document.activeElement === document.getElementById('searchInput')) {
                clearSearch();
            }
        });

        setInterval(pollMessages, 8000);
        document.addEventListener('visibilitychange', () => { if (!document.hidden) pollMessages(); });
    </script>
</body>
</html>
"""

# ============= الإعدادات العامة =============

HITS_FILE = Path(__file__).resolve().parent / "hits.txt"
POLL_SECONDS = 8
MAX_MESSAGES = 100
MAX_FETCH_PER_CHECK = 30
MAX_VISIBLE = 50

state_lock = threading.RLock()
accounts = []
current_email = None
current_password = None
inbox_messages = []
seen_ids = set()
revision = 0
monitoring = False
monitor_thread = None
wake_event = threading.Event()

KNOWN_IMAP = {
    "gmail.com": "imap.gmail.com",
    "googlemail.com": "imap.gmail.com",
    "outlook.com": "outlook.office365.com",
    "hotmail.com": "outlook.office365.com",
    "live.com": "outlook.office365.com",
    "msn.com": "outlook.office365.com",
    "yahoo.com": "imap.mail.yahoo.com",
    "ymail.com": "imap.mail.yahoo.com",
    "aol.com": "imap.aol.com",
    "icloud.com": "imap.mail.me.com",
    "me.com": "imap.mail.me.com",
    "suddenlink.net": "mail.suddenlink.net",
    "ufamts.ru": "mail.ufamts.ru",
    "interia.eu": "imap.interia.eu",
    "interia.pl": "imap.interia.pl",
    "wp.pl": "imap.wp.pl",
    "o2.pl": "imap.o2.pl",
    "onet.pl": "imap.poczta.onet.pl",
    "onet.eu": "imap.poczta.onet.pl",
    "gazeta.pl": "imap.gazeta.pl",
    "op.pl": "imap.op.pl",
    "tlen.pl": "imap.tlen.pl",
    "zoho.com": "imap.zoho.com",
    "yandex.com": "imap.yandex.com",
    "yandex.ru": "imap.yandex.ru",
    "mail.ru": "imap.mail.ru",
    "rambler.ru": "imap.rambler.ru",
}

# ============= التحميل والمعالجة =============

def load_accounts():
    global accounts
    loaded = []
    try:
        with HITS_FILE.open("r", encoding="utf-8-sig") as file:
            for raw in file:
                line = raw.rstrip("\r\n").strip()
                if not line or line.startswith("#"):
                    continue

                custom_server = None
                if "|" in line:
                    main_part, extra_part = line.split("|", 1)
                    match = re.search(r"(?:server|imap)\s*:\s*([^\s]+)", extra_part, re.IGNORECASE)
                    if match:
                        custom_server = match.group(1).strip()
                else:
                    main_part = line

                address, separator, password = main_part.partition(":")
                address = address.strip()
                password = password.strip()

                if not separator or not re.fullmatch(r"[^@]+@[^@]+", address) or not password:
                    continue

                loaded.append({"email": address, "password": password, "server": custom_server})
    except OSError:
        print("❌ تعذر العثور على hits.txt أو قراءته.")
    accounts = loaded
    print(f"✅ تم تحميل {len(accounts)} حساب بنجاح")
    return accounts


def get_random_account():
    global current_email, current_password
    if not accounts:
        load_accounts()
    if not accounts:
        return None
    alternatives = [acc for acc in accounts if acc["email"].casefold() != (current_email or "").casefold()]
    account = random.choice(alternatives or accounts)
    current_email = account["email"]
    current_password = account["password"]
    return account


def decode_bytes(value, charset=None):
    if isinstance(value, str):
        return value
    if not value:
        return ""
    try:
        return value.decode(charset or "utf-8", errors="replace")
    except LookupError:
        return value.decode("utf-8", errors="replace")


def clean_text(value):
    if not value:
        return ""
    try:
        return "".join(decode_bytes(part, charset) for part, charset in decode_header(str(value)))
    except (TypeError, ValueError):
        return str(value)


def get_message_body(message):
    part = message.get_body(preferencelist=("plain", "html"))
    if part is None:
        return ""
    payload = part.get_payload(decode=True)
    if payload is None:
        payload = part.get_payload()
        body = payload if isinstance(payload, str) else ""
    else:
        body = decode_bytes(payload, part.get_content_charset())

    if part.get_content_type() == "text/html":
        body = re.sub(r"(?is)<script[^>]*>.*?</script>", "", body)
        body = re.sub(r"(?is)<style[^>]*>.*?</style>", "", body)
        body = re.sub(r"(?i)<(?:br|/p|/div|/tr)\b[^>]*>", "\n", body)
        body = re.sub(r"<[^>]+>", " ", body)
        body = unescape(body)

    return body.strip()


def extract_codes(text):
    return list(dict.fromkeys(re.findall(r"\b[0-9]{4,8}\b", text or "")))

# ============= فحص البريد (كل المجلدات + آخر 30 رسالة) =============

def check_inbox():
    global revision

    with state_lock:
        email_addr = current_email
        password = current_password
        acc_info = next(
            (acc for acc in accounts if acc["email"].casefold() == (email_addr or "").casefold()),
            None,
        )
        server_override = acc_info.get("server") if acc_info else None
        seen_snapshot = set(seen_ids)

    if not email_addr or not password:
        return

    domain = email_addr.rsplit("@", 1)[1].lower()
    server = server_override or KNOWN_IMAP.get(domain, f"imap.{domain}")

    try:
        with imaplib.IMAP4_SSL(server, timeout=25) as mail:
            mail.login(email_addr, password)

            # ===== 1) اكتشاف كل المجلدات =====
            folder_names = []
            status, folders = mail.list()
            if status == "OK" and folders:
                for f in folders:
                    try:
                        decoded = f.decode("utf-8", errors="replace") if isinstance(f, bytes) else str(f)
                        matches = re.findall(r'"([^"]+)"', decoded)
                        if matches:
                            folder_names.append(matches[-1])
                    except Exception:
                        pass

            if not folder_names:
                folder_names = ["INBOX"]

            # ===== 2) ترتيب الأولويات: INBOX + Spam/Junk أولاً =====
            folder_names.sort(
                key=lambda f: (
                    0 if f.upper() == "INBOX" else
                    1 if any(k in f.lower() for k in ("spam", "junk", "bulk")) else
                    2
                )
            )
            folder_names = folder_names[:6]

            print(f"📂 فحص المجلدات: {folder_names}")

            for folder in folder_names:
                try:
                    safe_folder = folder.replace('"', '\\"')
                    status, _ = mail.select(f'"{safe_folder}"', readonly=True)
                    if status != "OK":
                        continue

                    _, validity_data = mail.response("UIDVALIDITY")
                    validity = decode_bytes(validity_data[0], "ascii") if validity_data and validity_data[0] else "0"
                    prefix = f"{email_addr.casefold()}:{folder}:{validity}:"

                    # غير المقروء
                    unread_uids = set()
                    status_unread, unread_data = mail.uid("search", None, "UNSEEN")
                    if status_unread == "OK":
                        unread_uids = set((unread_data[0] or b"").split())

                    # كل الرسائل
                    status, data = mail.uid("search", None, "ALL")
                    if status != "OK":
                        continue

                    all_uids = (data[0] or b"").split()
                    recent_uids = all_uids[-30:]

                    # تحديث حالة "غير مقروء" للرسائل القديمة
                    unread_ids = {prefix + u.decode("ascii") for u in unread_uids}
                    with state_lock:
                        status_changed = False
                        for item in inbox_messages:
                            if item["id"].startswith(prefix):
                                unread = item["id"] in unread_ids
                                if item["unread"] != unread:
                                    item["unread"] = unread
                                    status_changed = True
                        if status_changed:
                            revision += 1
                        seen_snapshot = set(seen_ids)

                    pending = [u for u in recent_uids if prefix + u.decode("ascii") not in seen_snapshot]
                    if not pending:
                        continue

                    new_items = []
                    for uid in pending[:MAX_FETCH_PER_CHECK]:
                        status, fetched = mail.uid("fetch", uid, "(BODY.PEEK[])")
                        if status != "OK":
                            continue

                        raw_message = next(
                            (it[1] for it in fetched if isinstance(it, tuple) and isinstance(it[1], bytes)),
                            None,
                        )
                        if raw_message is None:
                            continue

                        uid_str = uid.decode("ascii")
                        message_id = prefix + uid_str
                        try:
                            message = email.message_from_bytes(raw_message, policy=policy.default)
                            subject = clean_text(message.get("Subject", "بدون عنوان"))
                            sender = clean_text(message.get("From", "غير معروف"))
                            body = get_message_body(message)

                            new_items.append({
                                "id": message_id,
                                "subject": subject,
                                "from": sender,
                                "date": clean_text(message.get("Date", "")),
                                "body": body if body else "(رسالة فارغة)",
                                "codes": extract_codes(subject + "\n" + body),
                                "received_at": datetime.now().strftime("%H:%M:%S"),
                                "unread": uid in unread_uids,
                                "folder": folder,
                            })
                            print(f"  ✉️ [{folder}] {subject[:60]} — من: {sender[:40]}")
                        except Exception as e:
                            print(f"  ⚠️ خطأ معالجة رسالة: {e}")
                            continue

                    if new_items:
                        with state_lock:
                            for item in new_items:
                                if item["id"] in seen_ids:
                                    continue
                                inbox_messages.append(item)
                                seen_ids.add(item["id"])
                            del inbox_messages[:-MAX_MESSAGES]
                            revision += 1

                except Exception as folder_exc:
                    print(f"  ⚠️ تعذر فحص مجلد [{folder}]: {folder_exc}")
                    continue

    except Exception as exc:
        print(f"⚠️ خطأ في الاتصال بالسيرفر ({server}): {exc}")


def monitor_inbox():
    while True:
        check_inbox()
        wake_event.wait(POLL_SECONDS)
        wake_event.clear()


def start_monitoring():
    global monitoring, monitor_thread
    with state_lock:
        if monitor_thread is not None and monitor_thread.is_alive():
            return
        monitor_thread = threading.Thread(target=monitor_inbox, daemon=True)
        monitor_thread.start()
        monitoring = True

# ============= مسارات Flask =============

@app.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.route("/")
def index():
    with state_lock:
        if not current_email:
            get_random_account()
        if current_email:
            start_monitoring()
        visible = list(inbox_messages[-MAX_VISIBLE:])
        visible.reverse()
        return render_template_string(
            TEMPLATE,
            current_email=current_email,
            messages=visible,
            codes_count=sum(len(item["codes"]) for item in visible),
            monitoring=monitoring,
            revision=revision,
        )


@app.route("/new_email", methods=["POST"])
def new_email():
    global revision
    if not request.is_json:
        return jsonify(success=False, error="نوع الطلب غير مدعوم"), 415
    with state_lock:
        account = get_random_account()
        if account is None:
            return jsonify(success=False, error="لا توجد حسابات متاحة"), 400
        inbox_messages.clear()
        seen_ids.clear()
        revision += 1
        start_monitoring()
    wake_event.set()
    return jsonify(success=True, email=current_email)


@app.route("/get_messages")
def get_messages():
    client_revision = request.args.get("since", default=-1, type=int)
    with state_lock:
        visible = list(inbox_messages[-MAX_VISIBLE:])
        visible.reverse()
        return jsonify(
            success=True,
            messages=visible,
            revision=revision,
            new_messages=(client_revision != revision),
        )


@app.route("/clear_messages", methods=["POST"])
def clear_messages():
    global revision
    with state_lock:
        inbox_messages.clear()
        revision += 1
    return jsonify(success=True)


# ============= مسار التشخيص =============

@app.route("/debug")
def debug_inbox():
    """يفحص كل المجلدات ويطبع محتواها — للتشخيص فقط."""
    with state_lock:
        email_addr = current_email
        password = current_password
        acc_info = next(
            (acc for acc in accounts if acc["email"].casefold() == (email_addr or "").casefold()),
            None,
        )
        server_override = acc_info.get("server") if acc_info else None

    if not email_addr:
        return jsonify(success=False, error="لا يوجد حساب"), 400

    domain = email_addr.rsplit("@", 1)[1].lower()
    server = server_override or KNOWN_IMAP.get(domain, f"imap.{domain}")

    result = {"server": server, "email": email_addr, "folders": []}

    try:
        with imaplib.IMAP4_SSL(server, timeout=25) as mail:
            mail.login(email_addr, password)

            status, folders = mail.list()
            folder_names = []
            if status == "OK" and folders:
                for f in folders:
                    decoded = f.decode("utf-8", errors="replace") if isinstance(f, bytes) else str(f)
                    matches = re.findall(r'"([^"]+)"', decoded)
                    if matches:
                        folder_names.append(matches[-1])

            for folder in folder_names:
                info = {"name": folder, "total": 0, "unread": 0, "recent_subjects": []}
                try:
                    safe_folder = folder.replace('"', '\\"')
                    status, _ = mail.select(f'"{safe_folder}"', readonly=True)
                    if status != "OK":
                        info["error"] = "select failed"
                        result["folders"].append(info)
                        continue

                    _, total_data = mail.uid("search", None, "ALL")
                    all_uids = []
                    if total_data and total_data[0]:
                        all_uids = total_data[0].split()
                        info["total"] = len(all_uids)

                    _, unread_data = mail.uid("search", None, "UNSEEN")
                    if unread_data and unread_data[0]:
                        info["unread"] = len(unread_data[0].split())

                    if info["total"] > 0:
                        for uid in all_uids[-5:]:
                            st, fetched = mail.uid("fetch", uid, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])")
                            if st == "OK" and fetched:
                                raw = next((it[1] for it in fetched if isinstance(it, tuple) and isinstance(it[1], bytes)), None)
                                if raw:
                                    msg = email.message_from_bytes(raw, policy=policy.default)
                                    info["recent_subjects"].append({
                                        "from": clean_text(msg.get("From", ""))[:80],
                                        "subject": clean_text(msg.get("Subject", ""))[:80],
                                        "date": clean_text(msg.get("Date", ""))[:60],
                                    })
                except Exception as e:
                    info["error"] = str(e)
                result["folders"].append(info)

    except Exception as exc:
        return jsonify(success=False, error=str(exc)), 500

    return jsonify(success=True, **result)


# ============= التشغيل =============

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


if __name__ == "__main__":
    with state_lock:
        if not load_accounts():
            raise SystemExit("خطأ: يرجى وضع الحسابات في hits.txt")
        get_random_account()
        start_monitoring()

    local_ip = get_local_ip()
    port = 5000

    print("\n" + "=" * 50)
    print(f"🌐 الموقع يعمل الآن على الشبكة كلها:")
    print(f"💻 من هذا الجهاز: http://127.0.0.1:{port}")
    print(f"📱 من أي جهاز آخر في الواي فاي: http://{local_ip}:{port}")
    print(f"🔍 للتشخيص: http://127.0.0.1:{port}/debug")
    print("=" * 50 + "\n")

    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)