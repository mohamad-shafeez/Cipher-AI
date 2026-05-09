/* ============================================================
   CIPHER OS — chat.js
   Full dashboard: messaging, skill-aware output rendering,
   image gallery, file cards, code blocks, telemetry, voice.
   API: POST /api/command → { response, code }
   ============================================================ */

const API = 'http://127.0.0.1:5500';

// ── STATE ──────────────────────────────────────────────────────
const S = {
  loading:       false,
  micOn:         false,
  voiceEnabled:  true,
  neuralVoice:   false,
  autoScroll:    true,
  msgCount:      0,
  sessionNum:    1,
  uploadedFile:  null,
  scanlines:     true,
};

// ── DOM REFS ───────────────────────────────────────────────────
const chatArea = document.getElementById('chat-area');
const msgWrap  = document.getElementById('msg-wrap');
const prompt   = document.getElementById('prompt');
const sendBtn  = document.getElementById('send-btn');
const micBtn   = document.getElementById('mic-btn');
const statusTxt= document.getElementById('status-text');
const statusDot= document.getElementById('status-dot');

// ── CURSOR ─────────────────────────────────────────────────────
const cur = document.getElementById('cursor');
const curR = document.getElementById('cursor-ring');
document.addEventListener('mousemove', e => {
  cur.style.left  = e.clientX - 4 + 'px';
  cur.style.top   = e.clientY - 4 + 'px';
  curR.style.left = e.clientX - 14 + 'px';
  curR.style.top  = e.clientY - 14 + 'px';
});
document.addEventListener('mousedown', () => curR.classList.add('click'));
document.addEventListener('mouseup',   () => curR.classList.remove('click'));

// ── TEXTAREA AUTO-RESIZE ───────────────────────────────────────
prompt.addEventListener('input', () => {
  prompt.style.height = 'auto';
  prompt.style.height = Math.min(prompt.scrollHeight, 180) + 'px';
  sendBtn.classList.toggle('ready', prompt.value.trim().length > 0);
});
prompt.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

// --- UPDATED SEND MESSAGE (FOR NEURAL VOICE) ---
async function sendMessage() {
  const text = prompt.value.trim();
  if (!text || S.loading) return;

  hideWelcome();
  appendUser(text);
  prompt.value = '';
  prompt.style.height = 'auto';

  const thinkId = appendThinking();
  setStatus('PROCESSING', 'amber');
  S.loading = true;

  try {
    const res = await fetch(`${API}/api/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        command: text, 
        voice: S.voiceEnabled // Tells backend to trigger voice_neural.py
      }),
      signal: AbortSignal.timeout(45000),
    });
    
    const data = await res.json();
    removeThinking(thinkId);
    appendAI(data.response || '(No response)', data.code || null, text);
    setStatus('ONLINE', 'green');

    // NOTE: Your backend (communication.py) should already be calling 
    // voice_neural.py directly. If it is, the sound will come out 
    // of your speakers automatically. We don't need JS speech!
    
  } catch (err) {
    removeThinking(thinkId);
    appendAI('⚠ Connection failed.', null, text, true);
    setStatus('OFFLINE', 'red');
  }

  S.loading = false;
  updateSessionMeta();
}

// --- DISABLE ROBOTIC VOICE ---
function speakText(text) {
  // We disable the browser's robotic voice.
  // Instead, we let the Python backend handle the high-quality Neural voice.
  console.log("Neural Voice handled by backend: " + text.substring(0, 50));
}

// Direct send (bypasses input field)
function sendDirect(cmd) {
  prompt.value = cmd;
  prompt.dispatchEvent(new Event('input'));
  sendMessage();
}

// ── APPEND USER MSG ────────────────────────────────────────────
function appendUser(text) {
  S.msgCount++;
  const now = fmtTime();
  const g = document.createElement('div');
  g.className = 'msg-group';
  g.innerHTML = `
    <div class="msg-label user"><i class="fa fa-user"></i> YOU · ${now}</div>
    <div class="msg-row user">
      <div class="msg-actions">
        <button class="msg-action" onclick="copyBubble(this)" title="Copy"><i class="fa fa-copy"></i></button>
      </div>
      <div class="msg-bubble user">${esc(text)}</div>
      <div class="msg-avatar user"><i class="fa fa-user"></i></div>
    </div>
  `;
  msgWrap.appendChild(g);
  scrollBottom();
}

// ── APPEND AI MSG — SKILL-AWARE OUTPUT ────────────────────────
function appendAI(text, code, originalCmd, isErr) {
  S.msgCount++;
  const now = fmtTime();
  const g = document.createElement('div');
  g.className = 'msg-group';

  // Detect what kind of output this is
  const lowerText = text.toLowerCase();
  const lowerCmd  = (originalCmd || '').toLowerCase();

  let extraHTML = '';

  // Code block from swarm/executor (explicit code field OR code fence in response)
  if (code) {
    extraHTML += buildCodeBlock(code, 'python');
  }

  // Check for inline code fences in response
  let displayText = formatText(text);

  // PPTX output — show download card
  if (lowerText.includes('.pptx') && (lowerText.includes('saved') || lowerText.includes('created') || lowerText.includes('generated'))) {
    const match = text.match(/generated_code[\/\\][\w\-. ]+\.pptx/i) || text.match(/([\w\-. ]+\.pptx)/i);
    const fname = match ? match[0] : 'presentation.pptx';
    extraHTML += buildFileCard(fname, 'PowerPoint Presentation', '📑', fname);
  }

  // Image output — show gallery
  if ((lowerText.includes('image') || lowerText.includes('generated')) &&
      (lowerText.includes('.jpg') || lowerText.includes('.png') || lowerText.includes('generated_code/images'))) {
    extraHTML += buildImageGallery(text);
  }

  // Chart/graph output — show inline image viewer
  if (lowerText.includes('.png') && (lowerText.includes('saved') || lowerText.includes('graph') || lowerText.includes('chart'))) {
    const match = text.match(/(temp_data\/[\w\-. ]+\.png)/i) || text.match(/([\w\-./]+\.png)/i);
    if (match) {
      extraHTML += buildInlineImage(`${API}/${match[0]}`, 'System Chart');
    }
  }

  // Script output from OS Automator — styled pre block
  if (lowerCmd.includes('automate') || lowerText.includes('task completed') || lowerText.includes('script')) {
    // already handled by code block if code field present
  }

  g.innerHTML = `
    <div class="msg-label ai"><i class="fa fa-microchip"></i> CIPHER · ${now}</div>
    <div class="msg-row">
      <div class="msg-avatar ai"><i class="fa fa-robot"></i></div>
      <div class="msg-bubble ai${isErr ? ' err' : ''}">
        ${displayText}
        ${extraHTML}
      </div>
      <div class="msg-actions">
        <button class="msg-action" onclick="copyBubble(this)" title="Copy"><i class="fa fa-copy"></i></button>
        <button class="msg-action" onclick="speakBubble(this)" title="Speak"><i class="fa fa-volume-high"></i></button>
      </div>
    </div>
  `;
  msgWrap.appendChild(g);
  scrollBottom();
}

// ── OUTPUT BUILDERS ────────────────────────────────────────────
function buildCodeBlock(code, lang) {
  const id = 'cb_' + Date.now();
  return `
    <div class="code-block">
      <div class="code-block-header">
        <span class="code-lang"><i class="fa fa-code"></i> ${lang.toUpperCase()}</span>
        <button class="code-copy" id="${id}" onclick="copyCode('${id}')">
          <i class="fa fa-copy"></i> Copy
        </button>
      </div>
      <pre class="code-body" id="${id}_body">${esc(code)}</pre>
    </div>`;
}

function buildFileCard(filename, label, icon, path) {
  return `
    <div class="file-card">
      <div class="file-card-icon">${icon}</div>
      <div class="file-card-info">
        <div class="file-card-name">${filename}</div>
        <div class="file-card-meta">${label} · Ready to open</div>
      </div>
      <button class="file-card-btn" onclick="openFile('${path}')">
        <i class="fa fa-folder-open"></i> OPEN
      </button>
    </div>`;
}

function buildImageGallery(text) {
  // Extract image paths from response text
  const matches = [...text.matchAll(/(generated_code\/images\/[\w\-. ]+\.(?:jpg|png|webp))/gi)];
  if (!matches.length) return '';
  const imgs = matches.map(m =>
    `<img src="${API}/${m[0]}" alt="AI Generated" onclick="openImgModal('${API}/${m[0]}')" loading="lazy">`
  ).join('');
  return `<div class="img-gallery">${imgs}</div>`;
}

function buildInlineImage(src, label) {
  return `
    <div style="margin:10px 0 3px;">
      <img src="${src}" alt="${label}"
           style="max-width:100%;border:1px solid rgba(0,212,255,0.2);border-radius:6px;cursor:pointer;"
           onclick="openImgModal('${src}')"
           onerror="this.style.display='none'"
           loading="lazy">
    </div>`;
}

// ── TEXT FORMATTER ─────────────────────────────────────────────
function formatText(text) {
  // Code fences
  let out = esc(text).replace(
    /```(\w*)\n?([\s\S]*?)```/g,
    (_, lang, code) => buildCodeBlock(code, lang || 'code')
  );
  // **bold**
  out = out.replace(/\*\*(.*?)\*\*/g, '<strong style="color:var(--cyan)">$1</strong>');
  // `inline code`
  out = out.replace(/`([^`]+)`/g, '<code style="background:rgba(0,212,255,0.08);border:1px solid rgba(0,212,255,0.15);border-radius:3px;padding:1px 6px;font-family:var(--font-mono);font-size:0.8em;color:var(--cyan)">$1</code>');
  // newlines
  out = out.replace(/\n/g, '<br>');
  return out;
}

// ── THINKING BUBBLE ────────────────────────────────────────────
function appendThinking() {
  const id = 'think_' + Date.now();
  const g = document.createElement('div');
  g.id = id;
  g.className = 'msg-group';
  g.innerHTML = `
    <div class="msg-label ai"><i class="fa fa-microchip"></i> CIPHER · thinking...</div>
    <div class="msg-row">
      <div class="msg-avatar ai"><i class="fa fa-robot"></i></div>
      <div class="typing-bubble">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>`;
  msgWrap.appendChild(g);
  scrollBottom();
  return id;
}
function removeThinking(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ── COPY HANDLERS ──────────────────────────────────────────────
function copyCode(id) {
  const body = document.getElementById(id + '_body');
  if (!body) return;
  navigator.clipboard.writeText(body.innerText);
  const btn = document.getElementById(id);
  if (btn) {
    btn.innerHTML = '<i class="fa fa-check"></i> Copied';
    btn.classList.add('copied');
    setTimeout(() => { btn.innerHTML = '<i class="fa fa-copy"></i> Copy'; btn.classList.remove('copied'); }, 2000);
  }
  toast('Code copied', 'success');
}
function copyBubble(btn) {
  const bubble = btn.closest('.msg-row').querySelector('.msg-bubble');
  if (bubble) navigator.clipboard.writeText(bubble.innerText);
  toast('Copied', 'info');
}

// ── IMAGE MODAL ────────────────────────────────────────────────
function openImgModal(src) {
  document.getElementById('img-modal-src').src = src;
  document.getElementById('img-modal').classList.add('open');
}
function closeImgModal() {
  document.getElementById('img-modal').classList.remove('open');
}
document.getElementById('img-modal').addEventListener('click', e => {
  if (e.target === document.getElementById('img-modal')) closeImgModal();
});

// ── OPEN FILE ──────────────────────────────────────────────────
function openFile(path) {
  // Tell Cipher to open the file via a command
  sendDirect(`open file ${path}`);
}

// ── SPEECH ─────────────────────────────────────────────────────
function speakText(text) {
  if (!S.voiceEnabled || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text.substring(0, 300));
  u.rate = 1.1;
  window.speechSynthesis.speak(u);
}
function speakBubble(btn) {
  const b = btn.closest('.msg-row').querySelector('.msg-bubble');
  if (b) speakText(b.innerText);
}

// ── MIC ────────────────────────────────────────────────────────
const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;
if (SpeechRec) {
  recognition = new SpeechRec();
  recognition.continuous = false;
  recognition.lang = 'en-US';
  recognition.interimResults = false;
  recognition.onresult = e => {
    const t = e.results[0][0].transcript;
    prompt.value = t;
    prompt.dispatchEvent(new Event('input'));
    stopMic();
    sendMessage();
  };
  recognition.onerror = stopMic;
  recognition.onend   = stopMic;
}
function toggleMic() {
  if (!recognition) { toast('Voice input not supported in this browser', 'error'); return; }
  if (!S.micOn) {
    recognition.start();
    S.micOn = true;
    micBtn.classList.add('listening');
    document.getElementById('voice-overlay').classList.add('active');
  } else { cancelVoice(); }
}
function stopMic() {
  S.micOn = false;
  micBtn.classList.remove('listening');
  document.getElementById('voice-overlay').classList.remove('active');
}
function cancelVoice() {
  if (recognition) recognition.stop();
  stopMic();
}

// ── TOOLS TRAY ─────────────────────────────────────────────────
function toggleChips() {
  const tray = document.getElementById('dock-chips');
  const btn  = document.getElementById('chips-toggle');
  tray.classList.toggle('open');
  btn.classList.toggle('active');
}
function insertCmd(prefix) {
  prompt.value = prefix;
  prompt.focus();
  prompt.dispatchEvent(new Event('input'));
  document.getElementById('dock-chips').classList.remove('open');
  document.getElementById('chips-toggle').classList.remove('active');
}

// ── SUGGESTION CHIPS ───────────────────────────────────────────
function useChip(cmd) {
  prompt.value = cmd;
  prompt.dispatchEvent(new Event('input'));
  prompt.focus();
}

// ── FILE UPLOAD ────────────────────────────────────────────────
function handleFile(input) {
  const file = input.files[0];
  if (!file) return;
  S.uploadedFile = file;
  document.getElementById('upload-name').textContent = file.name;
  document.getElementById('upload-preview').classList.add('visible');
  toast(`Attached: ${file.name}`, 'info');
}
function removeUpload() {
  S.uploadedFile = null;
  document.getElementById('upload-preview').classList.remove('visible');
  document.getElementById('file-input').value = '';
}

// ── SIDEBAR ────────────────────────────────────────────────────
let sbCollapsed = false;
function toggleSidebar() {
  sbCollapsed = !sbCollapsed;
  document.getElementById('sidebar').classList.toggle('collapsed', sbCollapsed);
  document.getElementById('sb-toggle-icon').className =
    sbCollapsed ? 'fa fa-chevron-right' : 'fa fa-chevron-left';
}
function newSession() {
  clearChat();
  S.sessionNum++;
  S.msgCount = 0;
  const list = document.getElementById('sb-sessions');
  list.querySelectorAll('.sb-session').forEach(s => s.classList.remove('active'));
  const item = document.createElement('div');
  item.className = 'sb-session active';
  item.innerHTML = `
    <i class="fa fa-terminal sb-session-icon"></i>
    <div>
      <div class="sb-session-title">Session ${S.sessionNum}</div>
      <div class="sb-session-meta">Just now · 0 msgs</div>
    </div>`;
  list.insertBefore(item, list.firstChild);
}
function updateSessionMeta() {
  const first = document.querySelector('#sb-sessions .sb-session');
  if (first) {
    const meta = first.querySelector('.sb-session-meta');
    if (meta) meta.textContent = `${fmtTime()} · ${S.msgCount} msgs`;
  }
  const pm = document.getElementById('p-msgs');
  if (pm) pm.textContent = S.msgCount;
}

// ── RIGHT PANEL ────────────────────────────────────────────────
function toggleRightPanel() {
  document.getElementById('right-panel').classList.toggle('open');
}

// ── CLEAR / EXPORT ─────────────────────────────────────────────
function clearChat() {
  msgWrap.innerHTML = '';
  S.msgCount = 0;
  const pm = document.getElementById('p-msgs');
  if (pm) pm.textContent = '0';
  // Re-add welcome
  const w = document.createElement('div');
  w.className = 'welcome';
  w.id = 'welcome';
  w.innerHTML = `
    <div class="welcome-orb">⚡</div>
    <div class="welcome-title">CIPHER OS</div>
    <div class="welcome-sub">Multi-Agent · 40+ Skills · Fully Offline · 16GB Engine</div>
    <div class="suggestions">
      <div class="chip" onclick="useChip('build a flask REST API')"><span class="chip-icon">💻</span><span class="chip-title">Generate code</span><span class="chip-desc">build · fix · debug · swarm</span></div>
      <div class="chip" onclick="useChip('open instagram')"><span class="chip-icon">📱</span><span class="chip-title">Control my phone</span><span class="chip-desc">apps · calls · WhatsApp</span></div>
      <div class="chip" onclick="useChip('create presentation about machine learning')"><span class="chip-icon">📊</span><span class="chip-title">Create presentation</span><span class="chip-desc">pptx forge · slides · export</span></div>
      <div class="chip" onclick="useChip('security check')"><span class="chip-icon">🛡️</span><span class="chip-title">Security scan</span><span class="chip-desc">guardian · process · network</span></div>
    </div>`;
  msgWrap.appendChild(w);
}
function exportChat() {
  const lines = [];
  msgWrap.querySelectorAll('.msg-group').forEach(g => {
    const lbl = g.querySelector('.msg-label')?.innerText || '';
    const bbl = g.querySelector('.msg-bubble')?.innerText || '';
    if (bbl) lines.push(`[${lbl}]\n${bbl}`);
  });
  if (!lines.length) { toast('No messages to export', 'info'); return; }
  const blob = new Blob([lines.join('\n\n---\n\n')], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `cipher_session_${Date.now()}.txt`;
  a.click();
  toast('Chat exported', 'success');
}

// ── WELCOME ────────────────────────────────────────────────────
function hideWelcome() {
  const w = document.getElementById('welcome');
  if (w) {
    w.style.opacity = '0'; w.style.transform = 'translateY(-10px)';
    w.style.transition = '0.3s';
    setTimeout(() => w.remove(), 300);
  }
}

// ── SETTINGS ──────────────────────────────────────────────────
function openSettings()  { document.getElementById('settings-modal').classList.add('open'); }
function closeSettings() { document.getElementById('settings-modal').classList.remove('open'); }
document.getElementById('settings-modal').addEventListener('click', e => {
  if (e.target.id === 'settings-modal') closeSettings();
});
function toggleSetting(el, key) {
  el.classList.toggle('on');
  const on = el.classList.contains('on');
  if (key === 'voice')  S.voiceEnabled  = on;
  if (key === 'neural') {
    S.neuralVoice = on;
    sendDirect(on ? 'switch to neural voice' : 'disable neural voice');
  }
  if (key === 'scroll') S.autoScroll    = on;
  if (key === 'panel')  { if (on) document.getElementById('right-panel').classList.add('open'); else document.getElementById('right-panel').classList.remove('open'); }
  if (key === 'scan')   { document.body.style.setProperty('--scanline-opacity', on ? '1' : '0'); }
}

// ── TOAST ──────────────────────────────────────────────────────
function toast(msg, type = 'info') {
  const area = document.getElementById('toast-area');
  const icons = { success: 'fa-check-circle', error: 'fa-circle-xmark', info: 'fa-circle-info' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<i class="fa ${icons[type]} toast-i"></i><span>${msg}</span>`;
  area.appendChild(t);
  setTimeout(() => {
    t.style.opacity = '0'; t.style.transform = 'translateX(16px)';
    t.style.transition = '0.3s';
    setTimeout(() => t.remove(), 300);
  }, 2800);
}

// ── STATUS ─────────────────────────────────────────────────────
function setStatus(text, color) {
  statusTxt.textContent = text;
  const colors = { green: 'var(--green)', red: 'var(--red)', amber: 'var(--amber)' };
  statusDot.style.background  = colors[color];
  statusDot.style.boxShadow   = `0 0 8px ${colors[color]}`;
  statusTxt.style.color       = colors[color];
  const pb = document.getElementById('p-backend');
  if (pb) { pb.textContent = color === 'green' ? 'ONLINE' : 'OFFLINE'; pb.style.color = colors[color]; }
}

// ── RIGHT PANEL TELEMETRY ──────────────────────────────────────
let ptCpu = 45, ptRam = 62;
function updateTelemetry() {
  ptCpu = Math.min(94, Math.max(5, ptCpu + (Math.random() * 16 - 7)));
  ptRam = Math.min(90, Math.max(15, ptRam + (Math.random() * 10 - 4)));
  const vc = Math.round(ptCpu), vr = Math.round(ptRam);
  const pc = document.getElementById('p-cpu');
  const pr = document.getElementById('p-ram');
  if (pc) { pc.textContent = vc + '%'; document.getElementById('p-cpu-bar').style.width = vc + '%'; }
  if (pr) { pr.textContent = vr + '%'; document.getElementById('p-ram-bar').style.width = vr + '%'; }
}
setInterval(updateTelemetry, 2500);
updateTelemetry();

// ── LOAD SKILL PILLS FROM API ──────────────────────────────────
async function loadSkillsFromAPI() {
  try {
    const res = await fetch(`${API}/api/skills`, { signal: AbortSignal.timeout(4000) });
    if (!res.ok) return;
    const data = await res.json();
    const pillsEl = document.getElementById('sb-pills');
    if (pillsEl && data.skills) {
      pillsEl.innerHTML = data.skills.slice(0, 12).map(n =>
        `<div class="sb-pill"><div class="sb-pill-dot"></div>${n}</div>`
      ).join('');
    }
    const ps = document.getElementById('p-skills');
    if (ps) ps.textContent = data.count;
  } catch { /* offline — pills stay as-is */ }
}

// ── BACKEND CHECK ──────────────────────────────────────────────
async function checkBackend() {
  try {
    const res = await fetch(`${API}/api/skills`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      setStatus('ONLINE', 'green');
      loadSkillsFromAPI();
    } else throw new Error();
  } catch {
    setStatus('OFFLINE', 'red');
    toast('Backend offline — start: python main.py', 'error');
  }
}

// ── KEYBOARD SHORTCUTS ─────────────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    closeSettings();
    closeImgModal();
    document.getElementById('dock-chips').classList.remove('open');
    document.getElementById('chips-toggle').classList.remove('active');
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); prompt.focus(); }
  if ((e.ctrlKey || e.metaKey) && e.key === 'l') { e.preventDefault(); clearChat(); }
});

// ── HELPERS ────────────────────────────────────────────────────
function esc(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
function fmtTime() {
  return new Date().toLocaleTimeString('en-US', { hour:'2-digit', minute:'2-digit' });
}
function scrollBottom() {
  if (S.autoScroll) setTimeout(() => chatArea.scrollTo({ top: chatArea.scrollHeight, behavior: 'smooth' }), 40);
}


/* ============================================================
   CIPHER OS — Autonomous Coder Kill-Switch Diff Card
   ADD THIS BLOCK to the bottom of chat.js
   Polls /api/patch/pending every 2s.
   When a patch is waiting, injects a diff card into the chat.
   ============================================================ */

// ── DIFF CARD POLLER ──────────────────────────────────────────
let _diffPollerActive = false;

function startDiffPoller() {
  if (_diffPollerActive) return;
  _diffPollerActive = true;

  setInterval(async () => {
    try {
      const res = await fetch(`${API}/api/patch/pending`);
      if (!res.ok) return;
      const data = await res.json();
      if (data.status === 'pending' && !document.getElementById('diff-card')) {
        injectDiffCard(data);
      }
    } catch { /* backend offline — silent */ }
  }, 2000);
}

// ── INJECT DIFF CARD INTO CHAT ────────────────────────────────
function injectDiffCard(patch) {
  hideWelcome();

  const card = document.createElement('div');
  card.id = 'diff-card';
  card.style.cssText = `
    background: #060f18;
    border: 1px solid rgba(255,170,0,0.5);
    border-radius: 8px;
    padding: 0;
    margin: 12px 0;
    overflow: hidden;
    animation: msg-in 0.4s ease forwards;
    box-shadow: 0 0 20px rgba(255,170,0,0.15);
  `;

  const fname = patch.file.split(/[/\\]/).pop();
  const diffLines = (patch.diff || '').split('\n');
  const diffHtml = diffLines.map(line => {
    let color = '#9ab8cc';
    if (line.startsWith('+++') || line.startsWith('---')) color = '#4a6a80';
    else if (line.startsWith('+')) color = '#00ff88';
    else if (line.startsWith('-')) color = '#ff3366';
    else if (line.startsWith('@@')) color = '#7b2fff';
    return `<span style="color:${color};display:block;">${escHtml(line)}</span>`;
  }).join('');

  card.innerHTML = `
    <div style="background:rgba(255,170,0,0.08);border-bottom:1px solid rgba(255,170,0,0.3);padding:12px 16px;display:flex;align-items:center;gap:10px;">
      <span style="font-size:1.1rem;">⚡</span>
      <div>
        <div style="font-family:var(--font-hud);font-size:0.75rem;color:#ffaa00;letter-spacing:3px;font-weight:700;">KILL SWITCH — PATCH APPROVAL REQUIRED</div>
        <div style="font-family:var(--font-mono);font-size:0.6rem;color:var(--text-dim);margin-top:3px;letter-spacing:1px;">${fname} · ${new Date(patch.timestamp).toLocaleTimeString()}</div>
      </div>
    </div>

    <div style="padding:12px 16px;">
      <div style="font-family:var(--font-mono);font-size:0.65rem;color:var(--text-dim);margin-bottom:8px;letter-spacing:1px;">
        ERROR: <span style="color:#ffaa00;">${escHtml((patch.error || '').substring(0, 120))}</span>
      </div>

      <div style="background:#020d14;border:1px solid rgba(0,212,255,0.15);border-radius:5px;padding:12px;max-height:280px;overflow-y:auto;font-family:var(--font-mono);font-size:0.72rem;line-height:1.7;margin-bottom:14px;">
        <div style="font-family:var(--font-hud);font-size:0.55rem;color:var(--text-dim);letter-spacing:2px;margin-bottom:8px;">// UNIFIED DIFF</div>
        ${diffHtml || '<span style="color:var(--text-dim);">No diff available.</span>'}
      </div>

      <div style="display:flex;gap:10px;">
        <button onclick="submitPatchDecision('approved')" style="
          flex:1;background:linear-gradient(135deg,#00ff88,#00d4aa);
          border:none;color:#000;padding:10px;border-radius:5px;cursor:pointer;
          font-family:var(--font-hud);font-size:0.7rem;font-weight:700;
          letter-spacing:3px;transition:all 0.2s;
          clip-path:polygon(6px 0%,100% 0%,calc(100% - 6px) 100%,0% 100%);
        " onmouseover="this.style.boxShadow='0 0 16px rgba(0,255,136,0.5)'"
          onmouseout="this.style.boxShadow='none'">
          ✓ &nbsp; APPROVE
        </button>
        <button onclick="submitPatchDecision('rejected')" style="
          flex:1;background:rgba(255,51,102,0.1);
          border:1px solid rgba(255,51,102,0.4);color:#ff3366;
          padding:10px;border-radius:5px;cursor:pointer;
          font-family:var(--font-hud);font-size:0.7rem;font-weight:700;
          letter-spacing:3px;transition:all 0.2s;
        " onmouseover="this.style.background='rgba(255,51,102,0.2)'"
          onmouseout="this.style.background='rgba(255,51,102,0.1)'">
          ✕ &nbsp; REJECT
        </button>
      </div>
    </div>
  `;

  const wrap = document.getElementById('msg-wrap');
  wrap.appendChild(card);
  scrollBottom();

  // Also show a toast
  toast(`Patch ready for ${fname} — approval required`, 'info');
}

// ── SUBMIT DECISION ───────────────────────────────────────────
async function submitPatchDecision(decision) {
  const card = document.getElementById('diff-card');

  try {
    const res = await fetch(`${API}/api/patch/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision }),
    });

    if (res.ok) {
      const data = await res.json();
      if (card) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(-8px)';
        card.style.transition = '0.3s';
        setTimeout(() => card.remove(), 300);
      }

      const msg = decision === 'approved'
        ? `✅ Patch APPROVED for ${data.file?.split(/[/\\]/).pop() || 'file'}. Applying now...`
        : `❌ Patch REJECTED. Skipping this fix.`;

      appendAI(msg, null, '');
      toast(decision === 'approved' ? 'Patch approved and applied' : 'Patch rejected', decision === 'approved' ? 'success' : 'error');
    }
  } catch {
    toast('Could not reach backend to submit decision', 'error');
  }
}

// ── HTML escape helper (local, avoids conflict with main esc()) ──
function escHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Start polling when page loads
startDiffPoller();

let _plagMode = 'internet';
let _plagPoller = null;
 
function openPlagPanel() {
  document.getElementById('plag-modal').style.display = 'flex';
}
function closePlagPanel() {
  document.getElementById('plag-modal').style.display = 'none';
  if (_plagPoller) { clearInterval(_plagPoller); _plagPoller = null; }
}
function setPlagMode(mode) {
  _plagMode = mode;
  document.getElementById('mode-internet').style.background =
    mode === 'internet' ? 'rgba(0,212,255,0.15)' : 'transparent';
  document.getElementById('mode-internet').style.color =
    mode === 'internet' ? '#00d4ff' : '#4a6a80';
  document.getElementById('mode-document').style.background =
    mode === 'document' ? 'rgba(0,212,255,0.15)' : 'transparent';
  document.getElementById('mode-document').style.color =
    mode === 'document' ? '#00d4ff' : '#4a6a80';
}
 
async function runPlagCheck() {
  const text    = document.getElementById('plag-text').value.trim();
  const file    = document.getElementById('plag-file').value.trim();
  const compare = document.getElementById('plag-compare').value.trim();
 
  if (!text && !file) {
    alert('Please paste text or enter a file path.');
    return;
  }
 
  document.getElementById('plag-status').style.display = 'block';
  document.getElementById('plag-results').style.display = 'none';
 
  try {
    await fetch('http://127.0.0.1:5500/api/plagiarism/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, file_path: file, compare_file: compare, mode: _plagMode }),
    });
 
    // Poll for result every 3 seconds
    _plagPoller = setInterval(async () => {
      try {
        const res  = await fetch('http://127.0.0.1:5500/api/plagiarism/result');
        const data = await res.json();
        if (data.status === 'ready') {
          clearInterval(_plagPoller);
          _plagPoller = null;
          document.getElementById('plag-status').style.display = 'none';
          renderPlagResults(data.report);
        }
      } catch {}
    }, 3000);
 
  } catch (e) {
    document.getElementById('plag-status').textContent = '⚠ Backend connection failed.';
  }
}
 
function renderPlagResults(report) {
  const panel  = document.getElementById('plag-results');
  const risk   = report.risk_level;
  const score  = report.plagiarism_score;
  const colors = { CLEAN:'#00ff88', LOW:'#00d4ff', MEDIUM:'#ffaa00', HIGH:'#ff3366' };
  const color  = colors[risk] || '#00d4ff';
 
  let rewriteHtml = '';
  if (report.rewrites && report.rewrites.length > 0) {
    rewriteHtml = '<div style="margin-top:16px;">'
      + '<div style="font-family:JetBrains Mono,monospace;font-size:0.6rem;color:#4a6a80;letter-spacing:2px;margin-bottom:10px;">// CIPHER SURGICAL REWRITES</div>';
    report.rewrites.forEach((rw, i) => {
      rewriteHtml += `
        <div style="background:#060f18;border:1px solid rgba(0,212,255,0.12);
                    border-radius:5px;padding:12px;margin-bottom:8px;">
          <div style="font-family:JetBrains Mono,monospace;font-size:0.58rem;
                      color:#ff3366;margin-bottom:6px;">FLAGGED:</div>
          <div style="font-size:0.82rem;color:#9ab8cc;margin-bottom:10px;
                      font-style:italic;">"${escH(rw.original)}"</div>
          <div style="font-family:JetBrains Mono,monospace;font-size:0.58rem;
                      color:#00ff88;margin-bottom:6px;">✓ CIPHER REWRITE:</div>
          <div style="font-size:0.82rem;color:#c8dde8;margin-bottom:8px;">"${escH(rw.rewritten)}"</div>
          <button onclick="applyRewrite(${i})"
                  data-original="${escH(rw.original)}"
                  data-rewritten="${escH(rw.rewritten)}"
                  style="background:#00ff88;border:none;color:#000;padding:5px 14px;
                         border-radius:4px;cursor:pointer;font-family:Orbitron,monospace;
                         font-size:0.58rem;font-weight:700;letter-spacing:2px;">
            ✦ APPLY REWRITE
          </button>
        </div>`;
    });
    rewriteHtml += '</div>';
  }
 
  let sourcesHtml = '';
  const flaggedSources = (report.internet_sources || []).filter(s => s.flagged);
  if (flaggedSources.length > 0) {
    sourcesHtml = '<div style="margin-top:14px;">'
      + '<div style="font-family:JetBrains Mono,monospace;font-size:0.6rem;color:#4a6a80;letter-spacing:2px;margin-bottom:8px;">// MATCHED INTERNET SOURCES</div>';
    flaggedSources.slice(0,5).forEach(s => {
      sourcesHtml += `
        <div style="display:flex;align-items:center;gap:10px;padding:7px 10px;
                    background:#060f18;border:1px solid rgba(255,51,102,0.2);
                    border-radius:4px;margin-bottom:5px;">
          <span style="color:#ff3366;font-family:JetBrains Mono,monospace;font-size:0.7rem;
                       font-weight:700;">${Math.round(s.similarity * 100)}%</span>
          <a href="${s.url}" target="_blank"
             style="font-family:JetBrains Mono,monospace;font-size:0.62rem;
                    color:#00d4ff;word-break:break-all;">${s.url.substring(0,60)}...</a>
        </div>`;
    });
    sourcesHtml += '</div>';
  }
 
  panel.style.display = 'block';
  panel.innerHTML = `
    <div style="text-align:center;padding:20px;background:#060f18;
                border:2px solid ${color};border-radius:8px;margin-bottom:14px;">
      <div style="font-family:Orbitron,monospace;font-size:2.5rem;font-weight:900;
                  color:${color};text-shadow:0 0 20px ${color};">${score}%</div>
      <div style="font-family:Orbitron,monospace;font-size:0.8rem;color:${color};
                  letter-spacing:4px;margin-top:4px;">${risk} RISK</div>
      <div style="font-family:JetBrains Mono,monospace;font-size:0.65rem;color:#4a6a80;
                  margin-top:10px;">${report.summary}</div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:14px;">
      <div style="background:#060f18;border:1px solid rgba(0,212,255,0.12);
                  border-radius:5px;padding:12px;text-align:center;">
        <div style="font-family:Orbitron,monospace;font-size:1.2rem;color:#00d4ff;">
          ${report.flagged_sentences}</div>
        <div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;
                    color:#4a6a80;margin-top:3px;">FLAGGED</div>
      </div>
      <div style="background:#060f18;border:1px solid rgba(0,212,255,0.12);
                  border-radius:5px;padding:12px;text-align:center;">
        <div style="font-family:Orbitron,monospace;font-size:1.2rem;color:#7b2fff;">
          ${report.total_sentences}</div>
        <div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;
                    color:#4a6a80;margin-top:3px;">TOTAL SENTENCES</div>
      </div>
      <div style="background:#060f18;border:1px solid rgba(0,212,255,0.12);
                  border-radius:5px;padding:12px;text-align:center;">
        <div style="font-family:Orbitron,monospace;font-size:1.2rem;color:#00ff88;">
          ${report.rewrites ? report.rewrites.length : 0}</div>
        <div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;
                    color:#4a6a80;margin-top:3px;">REWRITES READY</div>
      </div>
    </div>
    ${sourcesHtml}
    ${rewriteHtml}
  `;
}
 
function applyRewrite(idx) {
  const btn      = document.querySelectorAll('[data-original]')[idx];
  const original = btn.getAttribute('data-original');
  const rewrite  = btn.getAttribute('data-rewritten');
  const textarea = document.getElementById('plag-text');
  if (textarea && original) {
    textarea.value = textarea.value.replace(original, rewrite);
    btn.textContent = '✓ APPLIED';
    btn.style.background = '#4a6a80';
    btn.disabled = true;
  }
}
 
function escH(str) {
  return String(str||'').replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

// ── INIT ───────────────────────────────────────────────────────
setTimeout(checkBackend, 800);
setTimeout(() => prompt.focus(), 300);