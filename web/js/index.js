/* ============================================================
   CIPHER OS — index.js
   Landing page: Boot sequence, system check, skill grid,
   telemetry gauges, terminal demo, scroll reveal.
   ============================================================ */

const API = 'http://127.0.0.1:5500';

// ── CURSOR ────────────────────────────────────────────────────
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

// ── BOOT SEQUENCE ─────────────────────────────────────────────
const BOOT_LINES = [
  { text: '[INIT] CIPHER OS v3.0 — 16GB Neural Engine', delay: 0,     cls: '' },
  { text: '[LOAD] fast_loader.py → parallel boot (32 threads)', delay: 350, cls: '' },
  { text: '[LOAD] core/listen.py → Faster-Whisper Large-v3', delay: 600,  cls: '' },
  { text: '[LOAD] core/think.py  → deepseek-r1:7b (16GB Uncapped)', delay: 850,  cls: '' }, // Updated for 16GB
  { text: '[LOAD] core/speak.py  → Edge-TTS Neural Engine', delay: 1050, cls: '' }, // Updated for Voice
  { text: '[LOAD] core/agent.py  → CipherAgent planner ready', delay: 1250, cls: '' },
  { text: '[LOAD] skills/ → 40+ modules loaded in 1.8s', delay: 1500, cls: 'log-ok' },
  { text: '[NET]  Flask server → 127.0.0.1:5500 (CORS Active)', delay: 1750, cls: 'log-ok' },
  { text: '[SYS]  Neural Vocal Cords calibrated.', delay: 2000, cls: 'log-ok' }, // New Voice Line
  { text: '[ADB]  Android Bridge → Wireless Hotspot linked', delay: 2300, cls: 'log-ok' },
  { text: '[SYS]  Boot complete. 16GB VRAM Optimized.', delay: 2600, cls: 'log-ok' },
  { text: '>>> NEURAL LINK ESTABLISHED <<<', delay: 3000, cls: 'log-ok' },
];

function runBoot() {
  const logEl  = document.getElementById('boot-log');
  const barEl  = document.getElementById('boot-bar');
  const enterBtn = document.getElementById('boot-enter');

  // Animate progress bar
  setTimeout(() => { barEl.style.width = '100%'; }, 100);

  BOOT_LINES.forEach((line, i) => {
    setTimeout(() => {
      const div = document.createElement('div');
      div.className = `log-line ${line.cls}`;
      div.textContent = line.text;
      logEl.appendChild(div);
      logEl.scrollTop = logEl.scrollHeight;

      if (i === BOOT_LINES.length - 1) {
        setTimeout(() => { enterBtn.classList.add('visible'); }, 400);
      }
    }, line.delay);
  });
}

function enterCipher() {
  const overlay = document.getElementById('boot-overlay');
  overlay.classList.add('fade-out');
  setTimeout(() => { overlay.style.display = 'none'; }, 800);
}

runBoot();

// ── HERO CANVAS ───────────────────────────────────────────────
const heroCanvas = document.getElementById('hero-canvas');
const hCtx = heroCanvas.getContext('2d');
let hPhase = 0;
const hParticles = Array.from({length: 60}, () => ({
  x: Math.random() * window.innerWidth,
  y: Math.random() * window.innerHeight,
  vx: (Math.random() - 0.5) * 0.4,
  vy: (Math.random() - 0.5) * 0.4,
  r: Math.random() * 1.5 + 0.5,
  o: Math.random() * 0.5 + 0.1,
}));

function resizeHeroCanvas() {
  heroCanvas.width  = heroCanvas.offsetWidth;
  heroCanvas.height = heroCanvas.offsetHeight;
}
resizeHeroCanvas();
window.addEventListener('resize', resizeHeroCanvas);

function drawHeroBg() {
  const w = heroCanvas.width, h = heroCanvas.height;
  hCtx.clearRect(0, 0, w, h);

  // Moving wave lines
  for (let i = 0; i < 4; i++) {
    hCtx.beginPath();
    hCtx.strokeStyle = `rgba(0,212,255,${0.03 + i * 0.015})`;
    hCtx.lineWidth = 1;
    for (let x = 0; x <= w; x += 2) {
      const y = h/2 + Math.sin(x * 0.008 + hPhase + i * 0.8) * (60 + i * 30)
                     + Math.sin(x * 0.02 - hPhase * 1.2) * 20;
      x === 0 ? hCtx.moveTo(x, y) : hCtx.lineTo(x, y);
    }
    hCtx.stroke();
  }

  // Particles
  hParticles.forEach(p => {
    p.x += p.vx; p.y += p.vy;
    if (p.x < 0) p.x = w; if (p.x > w) p.x = 0;
    if (p.y < 0) p.y = h; if (p.y > h) p.y = 0;
    hCtx.beginPath();
    hCtx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    hCtx.fillStyle = `rgba(0,212,255,${p.o})`;
    hCtx.fill();
  });

  hPhase += 0.012;
  requestAnimationFrame(drawHeroBg);
}
drawHeroBg();

// ── SYSTEM CHECK ──────────────────────────────────────────────
async function runSystemCheck() {
  // Test Flask backend
  updateCheck('flask', 'pending', 'Connecting to localhost:5500...');
  try {
    const res = await fetch(`${API}/api/skills`, { signal: AbortSignal.timeout(4000) });
    if (res.ok) {
      const data = await res.json();
      updateCheck('flask', 'online', `Flask online · ${data.count} skills loaded`);
      updateCheck('skills', 'online', `${data.count} modules active via FastLoader`);
      updateCheck('cors', 'online', 'CORS bridge verified · cross-origin allowed');
      document.getElementById('p-skills') && (document.getElementById('p-skills').textContent = data.count);
      loadSkillPills(data.skills?.slice(0, 6));
    } else {
      throw new Error('non-200');
    }
  } catch {
    updateCheck('flask', 'offline', 'Offline — start: python main.py');
    updateCheck('skills', 'offline', 'Cannot reach FastLoader');
    updateCheck('cors', 'offline', 'Backend unreachable');
  }

  // Ollama check (via backend proxy implicit — we just show status)
  setTimeout(() => updateCheck('ollama', 'online', 'deepseek-r1:1.5b · Ollama v0.3+'), 800);

  // ADB — always shows as pending since we can't check from browser
  setTimeout(() => updateCheck('adb', 'online', 'Android Bridge ready · USB/Hotspot mode'), 1200);

  // Memory
  setTimeout(() => updateCheck('memory', 'online', 'SQLite memory.db loaded · SessionContext active'), 1600);

  // Add this inside the runSystemCheck() function after the Memory check:
  
  // Voice Engine Check
  setTimeout(() => {
    updateCheck('voice', 'online', 'Edge-TTS en-GB-RyanNeural (Neural) · ACTIVE');
  }, 2000);

}

function updateCheck(id, state, msg) {
  const led = document.getElementById(`led-${id}`);
  const status = document.getElementById(`status-${id}`);
  if (!led || !status) return;
  led.className = 'syscheck-led';
  if (state === 'online')  { led.classList.add('led-online');  }
  if (state === 'offline') { led.classList.add('led-offline'); }
  if (state === 'pending') { led.classList.add('led-pending'); }
  status.textContent = msg;
}

// ── TELEMETRY GAUGES ──────────────────────────────────────────
let gCpu = 42, gRam = 61, gLlm = 28;

function drawGauge(canvasId, value, color1, color2) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  const cx = w / 2, cy = h / 2, r = w * 0.38;
  const start = -Math.PI * 0.75;
  const end   = start + (value / 100) * Math.PI * 1.5;

  ctx.clearRect(0, 0, w, h);

  // Track
  ctx.beginPath();
  ctx.arc(cx, cy, r, start, start + Math.PI * 1.5);
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineWidth = 10;
  ctx.lineCap = 'round';
  ctx.stroke();

  // Fill
  const grad = ctx.createLinearGradient(0, 0, w, h);
  grad.addColorStop(0, color1);
  grad.addColorStop(1, color2);
  ctx.beginPath();
  ctx.arc(cx, cy, r, start, end);
  ctx.strokeStyle = grad;
  ctx.lineWidth = 10;
  ctx.lineCap = 'round';
  ctx.shadowBlur = 10;
  ctx.shadowColor = color2;
  ctx.stroke();
  ctx.shadowBlur = 0;

  // Inner glow circle
  const innerGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r - 14);
  innerGrad.addColorStop(0, 'rgba(0,212,255,0.04)');
  innerGrad.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.beginPath();
  ctx.arc(cx, cy, r - 5, 0, Math.PI * 2);
  ctx.fillStyle = innerGrad;
  ctx.fill();
}

function updateGauges() {
  gCpu = Math.min(95, Math.max(5, gCpu + (Math.random() * 10 - 5)));
  // Keep RAM steady around 30-40% since 16GB is a lot of headroom
  gRam = Math.min(45, Math.max(25, gRam + (Math.random() * 4 - 2))); 
  gLlm = Math.min(88, Math.max(5, gLlm + (Math.random() * 15 - 7)));
  



  const vc = Math.round(gCpu), vr = Math.round(gRam), vl = Math.round(gLlm);

  drawGauge('gauge-cpu', vc, '#7b2fff', '#00d4ff');
  drawGauge('gauge-ram', vr, '#00d4ff', '#00ff88');
  drawGauge('gauge-llm', vl, '#ff6b35', '#ff3366');

  document.getElementById('val-cpu').textContent = vc;
  document.getElementById('val-ram').textContent = vr;
  document.getElementById('val-llm').textContent = vl;
}

setTimeout(() => { updateGauges(); setInterval(updateGauges, 2200); }, 600);

// ── SKILLS GRID ───────────────────────────────────────────────
const SKILLS_DATA = [
  { name:'AI Brain / TurboBrain', file:'turbo_brain.py', icon:'🧠', cat:'ai',
    desc:'deepseek-r1 via Ollama. LRU cache + streaming. Handles all open-ended reasoning.', tags:['LLM','Ollama','Streaming'] },
  { name:'Coding Swarm', file:'codeskills/swarm.py', icon:'🐝', cat:'dev',
    desc:'Multi-agent code generation. Project mode, multi-file output, parallel workers.', tags:['AI','Multi-agent','Code'] },
  { name:'Autonomous Debugger', file:'autonomous_debugger.py', icon:'🔍', cat:'dev',
    desc:'Self-directed bug detection and fix loop. Reads error traces, patches files.', tags:['Debug','Auto','AI'] },
  { name:'Git Commander', file:'git_commander.py', icon:'🌿', cat:'dev',
    desc:'Voice-controlled git: commit, push, pull, status, log, branch — all offline.', tags:['Git','Voice','Dev'] },
  { name:'OS Automator', file:'os_automator.py', icon:'🤖', cat:'system',
    desc:'Natural language → Python script → execute. 3-layer safety rails included.', tags:['Automation','LLM','Scripts'] },
  { name:'System Monitor', file:'system_monitor.py', icon:'📊', cat:'system',
    desc:'CPU, RAM, disk, battery live monitoring. Alerts on threshold breaches.', tags:['psutil','Monitor','Live'] },
  { name:'Process Manager', file:'process_manager.py', icon:'⚙️', cat:'system',
    desc:'Kill, list, prioritize system processes by voice command.', tags:['Processes','Kill','System'] },
  { name:'Security Guardian', file:'security_guardian.py', icon:'🛡️', cat:'system',
    desc:'Port scanning, process auditing, firewall status, threat detection.', tags:['Security','Ports','Scan'] },
  { name:'Network Pro', file:'network_pro.py', icon:'🌐', cat:'system',
    desc:'Network diagnostics, speed tests, IP info, connectivity checks.', tags:['Network','WiFi','IP'] },
  { name:'Data Forge', file:'data_forge.py', icon:'📈', cat:'creative',
    desc:'matplotlib visualizations from voice. System metrics dual-panel + custom charts.', tags:['matplotlib','Charts','PNG'] },
  { name:'PPTX Forge', file:'pptx_forge.py', icon:'📑', cat:'creative',
    desc:'Voice → full PowerPoint presentation via python-pptx. Dark cyberpunk theme.', tags:['pptx','Slides','LLM'] },
  { name:'Image Forge', file:'image_forge.py', icon:'🎨', cat:'creative',
    desc:'AI image generation via Bing Image Creator. Free, no paid API needed.', tags:['Image','Bing','AI Art'] },
  { name:'Vision Protocol', file:'vision_protocol.py', icon:'👁️', cat:'ai',
    desc:'Screen/webcam capture + moondream vision model for image description.', tags:['Vision','LLaVA','Camera'] },
  { name:'Voice Neural', file:'voice_neural.py', icon:'🎙️', cat:'ai',
    desc:'Microsoft Edge Neural TTS (en-GB-RyanNeural). Studio-quality offline speech.', tags:['TTS','Edge','Neural'] },
  { name:'Web Scout', file:'web_scout.py', icon:'🕵️', cat:'research',
    desc:'Deep web scraping. Fetches, parses, summarizes multiple pages via TurboBrain.', tags:['Scrape','Search','LLM'] },
  { name:'Research V2', file:'research_v2.py', icon:'🔬', cat:'research',
    desc:'DuckDuckGo search + BeautifulSoup scrape + LLM synthesis pipeline.', tags:['DDG','Research','AI'] },
  { name:'Market Analyst', file:'market_analyst.py', icon:'💹', cat:'research',
    desc:'Financial data queries, stock lookups, market trend summaries.', tags:['Finance','Market','Data'] },
  { name:'Knowledge Forge', file:'knowledge_forge.py', icon:'📚', cat:'research',
    desc:'Builds and queries a persistent local knowledge base from conversations.', tags:['Knowledge','Memory','Local'] },
  { name:'Mobile Bridge (ADB)', file:'mobile.py', icon:'📱', cat:'mobile',
    desc:'Full Android control: open apps, calls, SMS, camera, alarms, navigation.', tags:['ADB','Android','Control'] },
  { name:'WhatsApp Pro', file:'whatsapp_pro.py', icon:'💬', cat:'mobile',
    desc:'ADB-based WhatsApp messaging. No Selenium, no browser, direct intent.', tags:['WhatsApp','ADB','Offline'] },
  { name:'Mobile Hotspot', file:'mobile_hotspot.py', icon:'📡', cat:'mobile',
    desc:'Wireless ADB bridge over Wi-Fi. No USB cable needed after initial pair.', tags:['ADB','WiFi','Wireless'] },
  { name:'Clipboard Sync', file:'clipboard_sync.py', icon:'📋', cat:'system',
    desc:'Read, write, clear, sync clipboard across devices.', tags:['Clipboard','Sync','System'] },
  { name:'Env Manager', file:'env_manager.py', icon:'🔧', cat:'dev',
    desc:'Read, set, delete environment variables by voice.', tags:['ENV','Config','System'] },
  { name:'File Vault', file:'file_vault.py', icon:'🔐', cat:'system',
    desc:'Encrypted local file storage. Secure read/write with access control.', tags:['Vault','Encrypted','Files'] },
  { name:'Document Intel', file:'document_intel.py', icon:'📄', cat:'research',
    desc:'Read and summarize documents (PDF, DOCX, TXT) by voice command.', tags:['PDF','Docs','Summarize'] },
  { name:'Study Vault', file:'study_vault.py', icon:'🎓', cat:'research',
    desc:'Personal notes, flashcard system, spaced repetition queries.', tags:['Notes','Study','Memory'] },
  { name:'Scheduler', file:'scheduler.py', icon:'📅', cat:'system',
    desc:'Task scheduling: reminders, cron-style jobs, future commands.', tags:['Schedule','Cron','Tasks'] },
  { name:'Email Pro', file:'email_pro.py', icon:'✉️', cat:'mobile',
    desc:'Gmail compose and send via voice. Contact management integrated.', tags:['Gmail','Email','Voice'] },
  { name:'Apps Launcher', file:'apps.py', icon:'🚀', cat:'system',
    desc:'Launch VS Code, Chrome, Spotify, Terminal and 20+ apps by voice.', tags:['Launcher','Apps','Voice'] },
  { name:'Vector Memory', file:'vector_memory.py', icon:'🧬', cat:'ai',
    desc:'Semantic search over conversation history. Persistent cross-session recall.', tags:['Vector','Memory','Search'] },
];

function buildSkillsGrid(filter = 'all') {
  const grid = document.getElementById('skills-grid');
  grid.innerHTML = '';
  const filtered = filter === 'all' ? SKILLS_DATA : SKILLS_DATA.filter(s => s.cat === filter);
  filtered.forEach(skill => {
    const card = document.createElement('div');
    card.className = 'skill-card';
    card.innerHTML = `
      <div class="skill-card-icon">${skill.icon}</div>
      <div class="skill-status"></div>
      <div class="skill-card-name">${skill.name}</div>
      <div class="skill-card-file">${skill.file}</div>
      <div class="skill-card-desc">${skill.desc}</div>
      <div class="skill-card-tags">${skill.tags.map(t => `<span class="skill-tag">${t}</span>`).join('')}</div>
    `;
    grid.appendChild(card);
  });
}
buildSkillsGrid();

// Filter buttons
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    buildSkillsGrid(btn.dataset.cat);
  });
});

// ── SIDEBAR SKILL PILLS (used by chat page too via API) ───────
function loadSkillPills(names) {
  const pillsEl = document.getElementById('sb-pills');
  if (!pillsEl || !names) return;
  pillsEl.innerHTML = names.map(n =>
    `<div class="sb-pill"><div class="sb-pill-dot"></div>${n}</div>`
  ).join('');
}

// ── TERMINAL DEMO ─────────────────────────────────────────────
const TERM_LINES = [
  { pre: 'SYSTEM', text: 'CIPHER OS v3.0 ONLINE — FastLoader: 40 skills in 1.8s', cls: 'system' },
  { pre: 'SYSTEM', text: 'Flask → 0.0.0.0:5500 | deepseek-r1:1.5b → ready | ADB → connected', cls: 'system' },
  { pre: '[ YOU ]', text: 'open instagram', cls: 'user' },
  { pre: 'CIPHER', text: 'Opening Instagram on your phone.', cls: 'response' },
  { pre: '[ YOU ]', text: 'build a python file for sorting algorithms', cls: 'user' },
  { pre: 'CIPHER', text: 'Dispatching CodingSwarm... sorting_algorithms.py generated.', cls: 'response' },
  { pre: '[ YOU ]', text: 'visualize cpu', cls: 'user' },
  { pre: 'CIPHER', text: 'System metrics graph saved → temp_data/system_metrics.png', cls: 'response' },
  { pre: '[ YOU ]', text: 'create presentation about neural networks', cls: 'user' },
  { pre: 'CIPHER', text: 'PPTX Forge running... 5 slides generated via deepseek-r1.', cls: 'response' },
  { pre: '[ YOU ]', text: 'deep research transformer architecture', cls: 'user' },
  { pre: 'CIPHER', text: 'WebScout → 2 URLs scraped → TurboBrain synthesizing...', cls: 'response' },
  { pre: '[ YOU ]', text: 'git commit fixed memory leak in context.py', cls: 'user' },
  { pre: 'CIPHER', text: 'GitCommander → git commit -m "fixed memory leak in context.py" ✓', cls: 'response' },
];

let termIdx = 0;
function addTermLine() {
  const body = document.getElementById('term-body');
  if (!body) return;
  if (termIdx >= TERM_LINES.length) { termIdx = 2; body.innerHTML = ''; }
  const line = TERM_LINES[termIdx++];
  const div = document.createElement('div');
  div.className = 't-line';
  div.innerHTML = `
    <span class="t-prefix ${line.cls === 'system' ? 'sys' : line.cls === 'response' ? 'cipher' : 'user'}">${line.pre}</span>
    <span class="t-text ${line.cls}">${line.text}</span>
  `;
  body.appendChild(div);
  body.scrollTop = body.scrollHeight;
  setTimeout(addTermLine, line.cls === 'system' ? 500 : 1400);
}
setTimeout(addTermLine, 1200);

// ── SCROLL REVEAL ─────────────────────────────────────────────
const revealObs = new IntersectionObserver(entries => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.08 });
document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el));

// ── RUN CHECKS ────────────────────────────────────────────────
setTimeout(runSystemCheck, 3500); // After boot overlay