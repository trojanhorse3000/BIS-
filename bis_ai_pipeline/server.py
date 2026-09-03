"""
server.py
Production-ready Web Server for BIS AI Pipeline.
Serves a high-aesthetic UI and REST API for real-time interactive inference.
"""

import os
import sys
import json
import time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Ensure bis_ai_pipeline is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(CURRENT_DIR, "pipeline")):
    sys.path.insert(0, CURRENT_DIR)
else:
    sys.path.insert(0, os.path.join(CURRENT_DIR, "bis_ai_pipeline"))

from pipeline.normalize import normalize_query, extract_entities
from pipeline.intent import classify_intent
from pipeline.retrieve import HybridRetriever
from pipeline.generate import AnswerGenerator

# Global Singletons
retriever = None
generator = None


def get_pipeline():
    global retriever, generator
    if retriever is None:
        retriever = HybridRetriever()
    if generator is None:
        generator = AnswerGenerator()
    return retriever, generator


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BIS AI Regulatory & Standards Engine</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0d14;
            --bg-secondary: #111726;
            --bg-card: rgba(18, 24, 40, 0.75);
            --border-color: rgba(255, 255, 255, 0.08);
            --border-glow: rgba(212, 175, 55, 0.3);
            --accent-gold: #d4af37;
            --accent-gold-hover: #f3cf5f;
            --accent-blue: #3b82f6;
            --accent-teal: #0ea5e9;
            --accent-emerald: #10b981;
            --accent-red: #ef4444;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(circle at 50% 0%, #172033 0%, var(--bg-primary) 70%);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }

        /* Ambient Glow Backdrop */
        .ambient-glow {
            position: fixed;
            top: -150px;
            left: 50%;
            transform: translateX(-50%);
            width: 800px;
            height: 400px;
            background: radial-gradient(circle, rgba(212, 175, 55, 0.12) 0%, rgba(59, 130, 246, 0.08) 50%, transparent 80%);
            filter: blur(80px);
            pointer-events: none;
            z-index: 0;
        }

        /* Top Header */
        header {
            position: relative;
            z-index: 10;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 18px 36px;
            border-bottom: 1px solid var(--border-color);
            backdrop-filter: blur(12px);
            background: rgba(10, 13, 20, 0.6);
        }

        .brand-container {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .brand-logo {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: linear-gradient(135deg, #d4af37, #b8860b);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            color: #0a0d14;
            font-size: 20px;
            box-shadow: 0 4px 16px rgba(212, 175, 55, 0.35);
        }

        .brand-text h1 {
            font-size: 18px;
            font-weight: 700;
            letter-spacing: -0.02em;
            background: linear-gradient(90deg, #ffffff, #d4af37);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-text p {
            font-size: 12px;
            color: var(--text-secondary);
        }

        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            color: var(--accent-emerald);
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            background: var(--accent-emerald);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--accent-emerald);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.9); opacity: 0.8; }
            50% { transform: scale(1.3); opacity: 1; }
            100% { transform: scale(0.9); opacity: 0.8; }
        }

        /* Main Workspace Layout */
        main {
            position: relative;
            z-index: 10;
            flex: 1;
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            gap: 24px;
            max-width: 1560px;
            width: 100%;
            margin: 0 auto;
            padding: 24px 32px;
        }

        /* Left Chat Panel */
        .chat-panel {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            backdrop-filter: blur(16px);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 12px 36px rgba(0, 0, 0, 0.4);
            height: calc(100vh - 140px);
        }

        .chat-header {
            padding: 16px 22px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .chat-header h2 {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-primary);
        }

        .sample-chips {
            padding: 12px 20px;
            display: flex;
            gap: 8px;
            overflow-x: auto;
            border-bottom: 1px solid var(--border-color);
            background: rgba(10, 13, 20, 0.4);
        }

        .sample-chips::-webkit-scrollbar {
            height: 4px;
        }

        .sample-chips::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }

        .chip {
            white-space: nowrap;
            padding: 6px 12px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            font-size: 11.5px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .chip:hover {
            background: rgba(212, 175, 55, 0.12);
            border-color: rgba(212, 175, 55, 0.4);
            color: var(--accent-gold);
            transform: translateY(-1px);
        }

        /* Message Stream */
        .chat-stream {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .chat-stream::-webkit-scrollbar {
            width: 6px;
        }

        .chat-stream::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }

        .message-bubble {
            display: flex;
            gap: 14px;
            max-width: 88%;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message-bubble.user {
            align-self: flex-end;
            flex-direction: row-reverse;
        }

        .avatar {
            width: 34px;
            height: 34px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 13px;
            flex-shrink: 0;
        }

        .avatar.user-avatar {
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: #fff;
        }

        .avatar.bot-avatar {
            background: linear-gradient(135deg, #d4af37, #b8860b);
            color: #0a0d14;
        }

        .message-content {
            padding: 14px 18px;
            border-radius: 16px;
            font-size: 13.5px;
            line-height: 1.6;
        }

        .message-bubble.user .message-content {
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: #f1f5f9;
            border-top-right-radius: 4px;
        }

        .message-bubble.bot .message-content {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            color: #f8fafc;
            border-top-left-radius: 4px;
        }

        .message-content h3 {
            font-size: 14px;
            font-weight: 700;
            color: var(--accent-gold);
            margin-bottom: 8px;
        }

        .message-content ul {
            padding-left: 18px;
            margin-top: 6px;
        }

        .message-content li {
            margin-bottom: 4px;
        }

        .source-tag {
            display: inline-block;
            margin-top: 10px;
            padding: 3px 8px;
            background: rgba(212, 175, 55, 0.1);
            border: 1px solid rgba(212, 175, 55, 0.25);
            border-radius: 6px;
            font-size: 10.5px;
            color: var(--accent-gold);
            font-family: 'JetBrains Mono', monospace;
        }

        /* Chat Input Bar */
        .chat-input-bar {
            padding: 16px 20px;
            border-top: 1px solid var(--border-color);
            background: rgba(10, 13, 20, 0.5);
            display: flex;
            gap: 12px;
        }

        .chat-input-bar input {
            flex: 1;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 12px 18px;
            color: #fff;
            font-size: 14px;
            font-family: 'Inter', sans-serif;
            outline: none;
            transition: all 0.2s ease;
        }

        .chat-input-bar input:focus {
            border-color: var(--accent-gold);
            box-shadow: 0 0 16px rgba(212, 175, 55, 0.2);
            background: rgba(255, 255, 255, 0.08);
        }

        .send-button {
            background: linear-gradient(135deg, #d4af37, #b8860b);
            color: #0a0d14;
            border: none;
            border-radius: 12px;
            padding: 0 24px;
            font-weight: 700;
            font-size: 13.5px;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 14px rgba(212, 175, 55, 0.3);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .send-button:hover {
            background: linear-gradient(135deg, #f3cf5f, #d4af37);
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4);
        }

        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Right Inspector Panel */
        .inspect-panel {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            backdrop-filter: blur(16px);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 12px 36px rgba(0, 0, 0, 0.4);
            height: calc(100vh - 140px);
        }

        .inspect-header {
            padding: 16px 22px;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .inspect-header h2 {
            font-size: 15px;
            font-weight: 600;
        }

        .inspect-body {
            flex: 1;
            padding: 22px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }

        .inspect-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            border-radius: 14px;
            padding: 16px;
        }

        .inspect-card h4 {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
        }

        .badge-intent {
            padding: 4px 10px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 12px;
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.4);
            color: #60a5fa;
            display: inline-block;
        }

        .badge-refusal {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.4);
            color: #f87171;
        }

        .entity-tag {
            display: inline-block;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            padding: 3px 8px;
            font-size: 11px;
            margin: 2px;
            font-family: 'JetBrains Mono', monospace;
            color: #cbd5e1;
        }

        pre.code-view {
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 8px;
            padding: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 11.5px;
            color: #94a3b8;
            max-height: 180px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 14px;
        }

        .stat-box {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 10px;
            text-align: center;
        }

        .stat-val {
            font-size: 18px;
            font-weight: 700;
            color: var(--accent-gold);
            font-family: 'JetBrains Mono', monospace;
        }

        .stat-lbl {
            font-size: 10.5px;
            color: var(--text-muted);
            margin-top: 2px;
        }
    </style>
</head>
<body>
    <div class="ambient-glow"></div>

    <header>
        <div class="brand-container">
            <div class="brand-logo">BIS</div>
            <div class="brand-text">
                <h1>Bureau of Indian Standards &bull; AI Regulatory Pipeline</h1>
                <p>Hybrid RAG Architecture &bull; SQLite Structured Engine &bull; ChromaDB Vector Knowledge</p>
            </div>
        </div>
        <div class="status-badge">
            <div class="pulse-dot"></div>
            <span>MODEL ACTIVE &bull; DEMO READY</span>
        </div>
    </header>

    <main>
        <!-- Left Chat Stream -->
        <section class="chat-panel">
            <div class="chat-header">
                <h2>Regulatory Assistant & Verification Terminal</h2>
                <span style="font-size: 12px; color: var(--text-muted);">Real-Time Inference</span>
            </div>

            <div class="sample-chips">
                <div class="chip" onclick="askPreset('Please verify gold hallmark HUID code AB1234')">✨ Verify HUID AB1234</div>
                <div class="chip" onclick="askPreset('What are the specifications under IS 1293:2019?')">🔌 IS 1293 Plugs & Sockets</div>
                <div class="chip" onclick="askPreset('What standard and QCO applies to Sulphate Resisting Portland Cement?')">🏗️ Cement QCO Order</div>
                <div class="chip" onclick="askPreset('How do domestic manufacturers apply for Scheme I ISI mark on MANAK Online?')">📜 Scheme I (ISI) Procedure</div>
                <div class="chip" onclick="askPreset('क्या भारत में सोने के आभूषणों पर 6 अंकों का HUID हॉलमार्क अनिवार्य है?')">🇮🇳 Hindi: HUID Mandate</div>
                <div class="chip" onclick="askPreset('Can you give me a recipe to cook butter chicken with ingredients?')">🛑 Refusal Policy Demo</div>
            </div>

            <div class="chat-stream" id="chatStream">
                <div class="message-bubble bot">
                    <div class="avatar bot-avatar">BIS</div>
                    <div class="message-content">
                        <h3>Bureau of Indian Standards AI Assistant Ready</h3>
                        <p>Welcome! I am specialized in verified Indian Standards (IS), mandatory Quality Control Orders (QCO), Hallmark Unique Identification (HUID), and BIS certification schemes.</p>
                        <ul>
                            <li><strong>Standards Query</strong>: Inquire about specifications, editions, and categories (e.g., <em>IS 1293</em>, <em>IS 694</em>).</li>
                            <li><strong>QCO Crosswalk</strong>: Check mandatory compliance for products (e.g., <em>Cement, Cables, Iron, Tyres</em>).</li>
                            <li><strong>HUID Verification</strong>: Authenticate 6-digit hallmark codes or check karatage fineness.</li>
                            <li><strong>Multilingual Support</strong>: Query directly in Hindi (हिंदी).</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="chat-input-bar">
                <input type="text" id="queryInput" placeholder="Ask about an Indian Standard, product QCO, HUID code, or scheme..." onkeydown="handleKey(event)" autofocus />
                <button class="send-button" id="sendBtn" onclick="submitQuery()">
                    <span>Send</span>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                </button>
            </div>
        </section>

        <!-- Right Pipeline Inspector -->
        <section class="inspect-panel">
            <div class="inspect-header">
                <h2>Pipeline Telemetry & Diagnostics</h2>
                <span id="latencyBadge" style="font-size: 11.5px; color: var(--accent-gold); font-family: 'JetBrains Mono', monospace;">Ready</span>
            </div>

            <div class="inspect-body">
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-val" id="statStandards">10</div>
                        <div class="stat-lbl">Standards Master</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-val" id="statCrosswalk">817</div>
                        <div class="stat-lbl">Crosswalk Rows</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-val" id="statVectors">12</div>
                        <div class="stat-lbl">Vector Chunks</div>
                    </div>
                </div>

                <div class="inspect-card">
                    <h4><span>1. Query Normalizer & Entities</span> <span id="tagLang" style="color:var(--text-secondary)">ENG</span></h4>
                    <div id="entitiesBox">
                        <span style="color:var(--text-muted); font-size:12px;">Awaiting user query...</span>
                    </div>
                </div>

                <div class="inspect-card">
                    <h4><span>2. Intent Classification</span> <span id="confBadge">--</span></h4>
                    <div id="intentBox">
                        <span class="badge-intent">IDLE</span>
                    </div>
                </div>

                <div class="inspect-card">
                    <h4><span>3. Hybrid Retrieval Facts</span> <span id="retrievalCount" style="color:var(--accent-teal)">0 matches</span></h4>
                    <pre class="code-view" id="retrievalBox">// Structured SQLite rows and ChromaDB embeddings will render here...</pre>
                </div>

                <div class="inspect-card">
                    <h4><span>4. Verification & Source Layer</span> <span id="sourceTag" style="color:var(--accent-gold)">STANDBY</span></h4>
                    <pre class="code-view" id="rawOutputBox">// Raw response payload logs here...</pre>
                </div>
            </div>
        </section>
    </main>

    <script>
        const chatStream = document.getElementById('chatStream');
        const queryInput = document.getElementById('queryInput');
        const sendBtn = document.getElementById('sendBtn');

        function handleKey(e) {
            if (e.key === 'Enter') submitQuery();
        }

        function askPreset(text) {
            queryInput.value = text;
            submitQuery();
        }

        async function submitQuery() {
            const query = queryInput.value.trim();
            if (!query) return;

            // Append User Bubble
            appendMessage('user', query);
            queryInput.value = '';
            queryInput.disabled = true;
            sendBtn.disabled = true;

            const t0 = performance.now();

            try {
                const res = await fetch('/api/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query })
                });

                const data = await res.json();
                const latency = Math.round(performance.now() - t0);

                // Update Inspector
                updateInspector(data, latency);

                // Append Bot Bubble
                appendBotMessage(data);

            } catch (err) {
                appendMessage('bot', 'Error contacting BIS pipeline server: ' + err.message);
            } finally {
                queryInput.disabled = false;
                sendBtn.disabled = false;
                queryInput.focus();
            }
        }

        function appendMessage(role, text) {
            const bubble = document.createElement('div');
            bubble.className = `message-bubble ${role}`;
            bubble.innerHTML = `
                <div class="avatar ${role}-avatar">${role === 'user' ? 'YOU' : 'BIS'}</div>
                <div class="message-content">${escapeHtml(text)}</div>
            `;
            chatStream.appendChild(bubble);
            chatStream.scrollTop = chatStream.scrollHeight;
        }

        function appendBotMessage(data) {
            const bubble = document.createElement('div');
            bubble.className = 'message-bubble bot';

            let formatted = data.answer
                .replace(/^### (.*$)/gim, '<h3>$1</h3>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\[(.*?)\]\((https?:\/\/[^\s\)]+)\)/gi, '<a href="$2" target="_blank" rel="noopener noreferrer" style="color:var(--accent-gold); text-decoration:underline; font-weight:600;">$1</a>')
                .replace(/^- (.*$)/gim, '<li>$1</li>');

            if (formatted.includes('<li>')) {
                formatted = formatted.replace(/(<li>[\s\S]*?<\/li>)/g, '<ul>$1</ul>');
            }

            bubble.innerHTML = `
                <div class="avatar bot-avatar">BIS</div>
                <div class="message-content">
                    ${formatted}
                    <div class="source-tag">${data.source} &bull; ${data.verified ? 'VERIFIED' : 'UNVERIFIED'}</div>
                </div>
            `;
            chatStream.appendChild(bubble);
            chatStream.scrollTop = chatStream.scrollHeight;
        }

        function updateInspector(data, latency) {
            document.getElementById('latencyBadge').innerText = `${latency} ms`;

            // 1. Entities
            document.getElementById('tagLang').innerText = data.entities.is_hindi ? 'HINDI (हिंदी)' : 'ENG';
            const eb = document.getElementById('entitiesBox');
            eb.innerHTML = '';

            if (data.entities.is_numbers.length) {
                data.entities.is_numbers.forEach(n => eb.innerHTML += `<span class="entity-tag">IS: ${n}</span>`);
            }
            if (data.entities.huid_codes.length) {
                data.entities.huid_codes.forEach(h => eb.innerHTML += `<span class="entity-tag">HUID: ${h}</span>`);
            }
            if (data.entities.hs_codes.length) {
                data.entities.hs_codes.forEach(hs => eb.innerHTML += `<span class="entity-tag">HS: ${hs}</span>`);
            }
            if (data.entities.search_keywords && data.entities.search_keywords.length) {
                data.entities.search_keywords.forEach(k => eb.innerHTML += `<span class="entity-tag">KW: ${k}</span>`);
            }
            if (!eb.innerHTML) {
                eb.innerHTML = '<span style="color:var(--text-muted); font-size:12px;">General text query</span>';
            }

            // 2. Intent
            const ib = document.getElementById('intentBox');
            const isRefusal = data.is_refusal;
            ib.innerHTML = `<span class="badge-intent ${isRefusal ? 'badge-refusal' : ''}">${data.intent.intent}</span>`;
            document.getElementById('confBadge').innerText = `${Math.round(data.intent.confidence * 100)}% conf`;

            // 3. Retrieval
            const st = data.retrieved.structured_results || [];
            const vc = data.retrieved.vector_results || [];
            document.getElementById('retrievalCount').innerText = `${st.length} SQL, ${vc.length} Vectors`;
            document.getElementById('retrievalBox').innerText = JSON.stringify({
                structured_count: st.length,
                structured_sample: st.slice(0, 2),
                vector_chunks_retrieved: vc.map(v => ({ id: v.id, meta: v.metadata }))
            }, null, 2);

            // 4. Source
            document.getElementById('sourceTag').innerText = data.source;
            document.getElementById('rawOutputBox').innerText = JSON.stringify({
                source: data.source,
                verified: data.verified,
                is_refusal: data.is_refusal
            }, null, 2);
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.innerText = text;
            return div.innerHTML;
        }
    </script>
</body>
</html>
"""


class BISHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif parsed.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "pipeline": "ready"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/query":
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len)
            try:
                payload = json.loads(post_body.decode("utf-8"))
                query = payload.get("query", "")

                retriever_inst, generator_inst = get_pipeline()

                t0 = time.time()
                cleaned = normalize_query(query)
                entities = extract_entities(query)
                is_hindi = entities.get("is_hindi", False)

                intent_data = classify_intent(cleaned, entities)
                retrieved = retriever_inst.retrieve(cleaned, intent_data, entities)
                response = generator_inst.generate(cleaned, intent_data, retrieved, is_hindi=is_hindi)
                elapsed_ms = round((time.time() - t0) * 1000, 2)

                result_data = {
                    "query": query,
                    "cleaned_query": cleaned,
                    "entities": entities,
                    "intent": {
                        "intent": intent_data["intent"].value if hasattr(intent_data["intent"], "value") else str(intent_data["intent"]),
                        "confidence": intent_data.get("confidence", 1.0)
                    },
                    "retrieved": {
                        "structured_results": retrieved.get("structured_results", []),
                        "vector_results": retrieved.get("vector_results", [])
                    },
                    "answer": response.get("answer", ""),
                    "citations": response.get("citations", []),
                    "source": response.get("source", "UNKNOWN"),
                    "verified": response.get("verified", False),
                    "is_refusal": response.get("is_refusal", False),
                    "latency_ms": elapsed_ms
                }

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(result_data, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write(f"[BIS Server] {self.address_string()} - {format % args}\n")


def run_server(port=8000):
    server_address = ("0.0.0.0", port)
    try:
        httpd = ThreadingHTTPServer(server_address, BISHTTPHandler)
    except OSError:
        # Try fallback port
        port = 8080
        server_address = ("0.0.0.0", port)
        httpd = ThreadingHTTPServer(server_address, BISHTTPHandler)

    print(f"\n{'='*70}")
    print(f" BIS AI Pipeline Web Server Launched Successfully!")
    print(f" Local URL:    http://localhost:{port}")
    print(f" Network URL:  http://127.0.0.1:{port}")
    print(f"{'='*70}\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully.")
        httpd.server_close()


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port=port_arg)
