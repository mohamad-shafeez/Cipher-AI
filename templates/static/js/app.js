/* ============================================================
   CIPHER OS — God-Mode Dashboard  |  app.js
   1-second /api/status polling loop.
   Handles: telemetry, agent state, neural feed, console,
            memory retrievals, error/glitch detection,
            background canvas, uptime counter.
   ============================================================ */

'use strict';

// ── BOOT TIME ─────────────────────────────────────────────────
const BOOT_TIME = Date.now();

// ── AGENT CONFIG ──────────────────────────────────────────────
const AGENT_ICONS = {
  'IDLE':               'fa-circle-pause',
  'Idle':               'fa-circle-pause',
  'LISTENING':          'fa-microphone-lines',
  'ResearchAssistant':  'fa-magnifying-glass',
  'CodeAnalyst':        'fa-code',
  'SystemSentinel':     'fa-shield-halved',
  'Swarm Orchestrator': 'fa-network-wired',
  'Heavy Planner':      'fa-brain',
  'Turbo Brain':        'fa-bolt',
  'Sandbox':            'fa-flask',
  'GhostOperator':      'fa-ghost',
};
const AGENT_SUBS = {
  'IDLE':               'Awaiting command input',
  'Idle':               'Awaiting command input',
  'LISTENING':          'Neural capture active',
  'ResearchAssistant':  'Scraping and synthesizing data',
  'CodeAnalyst':        'Analyzing codebase context',
  'SystemSentinel':     'Monitoring system vitals',
  'Swarm Orchestrator': 'Coordinating sub-agents',
  'Heavy Planner':      'Decomposing multi-step task',
  'Turbo Brain':        'Streaming LLM inference',
  'Sandbox':            'Executing sandboxed patch — SELF-HEALING',
  'GhostOperator':      'Physical OS control active',
};

// ── ERROR KEYWORDS ─────────────────────────────────────────────
const ERROR_KEYWORDS = [
  'traceback', 'error', 'exception', 'failed', 'stderr',
  'attributeerror', 'typeerror', 'valueerror', 'importerror',
  'syntaxerror', 'runtimeerror', 'assertion', 'killed',
];

// ── DOM REFS ───────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const dom = {
  cpuVal:         $('cpu-val'),
  cpuFill:        $('cpu-fill'),
  cpuGlow:        $('cpu-glow'),
  ramVal:         $('ram-val'),
  ramFill:        $('ram-fill'),
  ramGlow:        $('ram-glow'),
  uptimeVal:      $('uptime-val'),
  statusChip:     $('system-status-chip'),
  statusText:     $('system-status-text'),
  chipDot:        $('chip-dot'),
  sleepBadge:     $('sleep-worker-badge'),
  agentOuter:     $('agent-orb-outer'),
  agentCenter:    $('agent-orb-center'),
  agentIcon:      $('agent-icon'),
  agentName:      $('agent-name'),
  agentSub:       $('agent-sub'),
  agentStateTag:  $('agent-state-tag'),
  pipeListen:     $('pipe-listen'),
  pipeThink:      $('pipe-think'),
  pipeSkill:      $('pipe-skill'),
  pipeSpeak:      $('pipe-speak'),
  micTag:         $('mic-tag'),
  transcript:     $('transcript-text'),
  consoleOutput:  $('console-output'),
  consolePanel:   $('panel-console'),
  errorBadge:     $('error-badge'),
  memoryList:     $('memory-list'),
  tickTime:       $('tick-time'),
  footerTime:     $('footer-time'),
  voiceViz:       $('voice-viz'),
  logoOrb:        $('logo-orb'),
};

// ── STATE ──────────────────────────────────────────────────────
let prevAgent    = null;
let prevStatus   = null;
let prevConsole  = null;
let hasError     = false;
let glitchTimer  = null;

// ── CLOCK & UPTIME ─────────────────────────────────────────────
function updateClock() {
  const now = new Date();
  const hh  = String(now.getHours()).padStart(2, '0');
  const mm  = String(now.getMinutes()).padStart(2, '0');
  const ss  = String(now.getSeconds()).padStart(2, '0');
  const timeStr = `${hh}:${mm}:${ss}`;

  if (dom.tickTime)   dom.tickTime.textContent = timeStr;
  if (dom.footerTime) dom.footerTime.textContent = `${timeStr} UTC+5:30`;

  // Uptime
  const elapsed = Math.floor((Date.now() - BOOT_TIME) / 1000);
  const uh = String(Math.floor(elapsed / 3600)).padStart(2, '0');
  const um = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0');
  const us = String(elapsed % 60).padStart(2, '0');
  if (dom.uptimeVal) dom.uptimeVal.textContent = `${uh}:${um}:${us}`;
}
setInterval(updateClock, 1000);
updateClock();

// ── TELEMETRY BARS ─────────────────────────────────────────────
function setBar(fillEl, glowEl, valEl, pct) {
  const clamped = Math.max(0, Math.min(100, pct));
  fillEl.style.width = `${clamped}%`;
  glowEl.style.left  = `${clamped}%`;
  valEl.textContent  = `${clamped}%`;

  // Color shift when critical
  if (clamped >= 85) {
    fillEl.style.background = 'linear-gradient(90deg, var(--pink), #ff4444)';
    glowEl.style.background = 'var(--pink)';
    glowEl.style.boxShadow  = 'var(--glow-pink)';
  } else if (clamped >= 60) {
    fillEl.style.background = 'linear-gradient(90deg, var(--amber), var(--pink))';
    glowEl.style.background = 'var(--amber)';
    glowEl.style.boxShadow  = '0 0 12px rgba(255,195,0,0.5)';
  } else {
    fillEl.style.background = 'linear-gradient(90deg, var(--cyan), var(--pink))';
    glowEl.style.background = 'var(--cyan)';
    glowEl.style.boxShadow  = 'var(--glow-cyan)';
  }
}

// ── SYSTEM STATUS ──────────────────────────────────────────────
function updateStatus(statusText) {
  if (statusText === prevStatus) return;
  prevStatus = statusText;
  const isOnline = ['ONLINE', 'IDLE', 'Idle', 'Active'].includes(statusText);
  dom.statusText.textContent = statusText.toUpperCase();
  dom.statusChip.className = `status-chip ${isOnline ? 'online' : 'offline'}`;
}

// ── AGENT STATE ────────────────────────────────────────────────
function updateAgent(agentName) {
  if (agentName === prevAgent) return;
  prevAgent = agentName;

  const name = agentName || 'IDLE';
  const isIdle    = name === 'IDLE' || name === 'Idle';
  const isSandbox = name === 'Sandbox';

  // Name + sub
  dom.agentName.textContent = name.toUpperCase();
  dom.agentName.className   = `agent-name ${isIdle ? 'state-idle' : isSandbox ? 'state-sandbox' : ''}`;
  dom.agentSub.textContent  = AGENT_SUBS[name] || `Running ${name}`;

  // Tag
  dom.agentStateTag.textContent = isIdle ? 'IDLE' : isSandbox ? 'HEALING' : 'ACTIVE';
  dom.agentStateTag.className   = `panel-tag ${isIdle ? '' : isSandbox ? 'tag-pink' : 'tag-green'}`;

  // Orb state
  dom.agentOuter.className = `agent-orb-outer ${isIdle ? 'state-idle' : isSandbox ? 'state-sandbox' : 'state-active'}`;

  // Icon
  const iconClass = AGENT_ICONS[name] || 'fa-microchip';
  dom.agentIcon.className = `fa ${iconClass}`;
  if (isSandbox) dom.agentIcon.style.color = 'var(--pink)';
  else if (isIdle) dom.agentIcon.style.color = 'var(--text-dim)';
  else dom.agentIcon.style.color = 'var(--cyan)';

  // Pipeline highlighting
  const pipes = [dom.pipeListen, dom.pipeThink, dom.pipeSkill, dom.pipeSpeak];
  pipes.forEach(p => p.classList.remove('active'));
  if (name === 'LISTENING') dom.pipeListen.classList.add('active');
  else if (!isIdle) {
    dom.pipeThink.classList.add('active');
    dom.pipeSkill.classList.add('active');
  }
}

// ── NEURAL FEED ────────────────────────────────────────────────
function updateFeed(transcript) {
  const hasCommand = transcript && transcript.trim().length > 5
    && transcript !== 'No command captured yet.'
    && transcript !== 'No active neural capture...';

  dom.transcript.textContent = transcript || 'No active neural capture...';

  // Animate voice bars
  const bars = dom.voiceViz.querySelectorAll('.vbar');
  if (hasCommand) {
    bars.forEach(b => b.classList.add('active'));
    dom.micTag.textContent  = 'CAPTURED';
    dom.micTag.className    = 'panel-tag tag-green';
  } else {
    bars.forEach(b => b.classList.remove('active'));
    dom.micTag.textContent  = 'STANDBY';
    dom.micTag.className    = 'panel-tag tag-green';
  }
}

// ── CONSOLE ────────────────────────────────────────────────────
function updateConsole(logs) {
  if (!logs || logs.length === 0) {
    if (prevConsole === null) {
      dom.consoleOutput.textContent = 'SYSTEM ACTIVE. ALL SENSORS FUNCTIONAL.\nNO REFLECTION OR SELF-HEALING CYCLES TRIGGERED YET.';
      prevConsole = '';
    }
    clearError();
    return;
  }

  const text = logs.join('\n');
  if (text === prevConsole) return;
  prevConsole = text;

  // Detect errors
  const lowerText = text.toLowerCase();
  const detected  = ERROR_KEYWORDS.some(kw => lowerText.includes(kw));

  if (detected) {
    triggerError(text);
  } else {
    clearError();
    dom.consoleOutput.textContent = text;
  }

  // Auto-scroll to bottom
  requestAnimationFrame(() => {
    dom.consoleOutput.scrollTop = dom.consoleOutput.scrollHeight;
  });
}

function triggerError(text) {
  if (!hasError) {
    hasError = true;
    dom.consolePanel.classList.add('has-error');
    dom.errorBadge.classList.add('visible');

    // Stop glitch after 3 seconds to avoid seizure territory
    clearTimeout(glitchTimer);
    glitchTimer = setTimeout(() => {
      dom.consolePanel.classList.remove('has-error');
    }, 3000);
  }

  // Color-code error lines
  const lines = text.split('\n');
  dom.consoleOutput.innerHTML = lines.map(line => {
    const ll = line.toLowerCase();
    if (ERROR_KEYWORDS.some(kw => ll.includes(kw))) {
      return `<span class="log-error">${escHtml(line)}</span>`;
    }
    if (ll.includes('fixed') || ll.includes('success') || ll.includes('online')) {
      return `<span class="log-ok">${escHtml(line)}</span>`;
    }
    return `<span class="log-normal">${escHtml(line)}</span>`;
  }).join('\n');

  requestAnimationFrame(() => {
    dom.consoleOutput.scrollTop = dom.consoleOutput.scrollHeight;
  });
}

function clearError() {
  if (hasError) {
    hasError = false;
    dom.consolePanel.classList.remove('has-error');
    dom.errorBadge.classList.remove('visible');
  }
}

// ── MEMORY RETRIEVALS ──────────────────────────────────────────
let prevMemHash = '';
function updateMemory(retrievals) {
  const hash = JSON.stringify(retrievals);
  if (hash === prevMemHash) return;
  prevMemHash = hash;

  if (!retrievals || retrievals.length === 0) {
    dom.memoryList.innerHTML = `
      <div class="memory-item">
        <div class="mem-icon"><i class="fa fa-database"></i></div>
        <div class="mem-text">No active memory query.</div>
      </div>`;
    return;
  }

  dom.memoryList.innerHTML = retrievals.map((r, i) => `
    <div class="memory-item" style="animation-delay:${i * 0.05}s">
      <div class="mem-icon"><i class="fa fa-brain"></i></div>
      <div class="mem-text">${escHtml(String(r))}</div>
    </div>
  `).join('');
}

// ── SLEEP-WORKER BADGE ─────────────────────────────────────────
function updateSleepWorker(running) {
  if (running) dom.sleepBadge.classList.add('visible');
  else         dom.sleepBadge.classList.remove('visible');
}

// ── ISOLATED EXECUTION LANES UPDATER ───────────────────────────
function updateWorkerLanes(health) {
  const lanes = ['vision', 'coding', 'automation', 'swarm'];
  lanes.forEach(lane => {
    const el = document.getElementById(`status-${lane}`);
    if (el) {
      const status = (health[lane] || 'OFFLINE').toUpperCase();
      el.textContent = status;
      
      // Update styling dynamically based on live health status
      if (status === 'ONLINE') {
        el.style.color = '#39ff14'; // Neon matrix green
        el.style.background = 'rgba(57,255,20,0.1)';
        el.style.border = '1px solid rgba(57,255,20,0.2)';
      } else if (status === 'DEAD') {
        el.style.color = '#ff0055'; // Neon vibrant pink/red
        el.style.background = 'rgba(255,0,85,0.1)';
        el.style.border = '1px solid rgba(255,0,85,0.2)';
      } else {
        el.style.color = '#ff9d00'; // Amber warning offline state
        el.style.background = 'rgba(255,157,0,0.1)';
        el.style.border = '1px solid rgba(255,157,0,0.2)';
      }
    }
  });
}

// ── SERVER-SENT EVENTS (SSE) STREAMING ────────────────────────
let eventSource = null;

function connectStream() {
  if (eventSource) {
    eventSource.close();
  }

  // Hook into the high-frequency streaming endpoint
  eventSource = new EventSource('/api/stream');

  eventSource.onopen = () => {
    updateStatus('ONLINE');
    console.log('⚡ [HUD STREAM]: Connected to high-performance SSE stream.');
  };

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);

      // CPU Total tracks all cores, CPU Main tracks parent process
      setBar(dom.cpuFill, dom.cpuGlow, dom.cpuVal, Math.round(data.cpu_total || 0));
      setBar(dom.ramFill, dom.ramGlow, dom.ramVal, Math.round(data.ram_usage || 0));

      updateStatus(data.system_status || 'ONLINE');
      updateAgent(data.current_agent  || 'IDLE');
      updateFeed(data.last_transcript || '');
      updateConsole(data.reflection_logs || []);
      updateMemory(data.memory_retrievals || []);
      updateSleepWorker(data.background_tasks_running || false);

      if (data.worker_health) {
        updateWorkerLanes(data.worker_health);
      }
    } catch (err) {
      console.error('💥 [HUD STREAM ERROR]: Failed to parse stream event:', err);
    }
  };

  eventSource.onerror = (err) => {
    updateStatus('OFFLINE');
    dom.consoleOutput.textContent = `[CONNECTION LOST]\nTelemetry stream interrupted.\n\nRe-establishing connection pipeline in 2 seconds...`;
    clearError();
    eventSource.close();
    setTimeout(connectStream, 2000);
  };
}

// Establish the stream pipeline
connectStream();

// ── BACKGROUND CANVAS (ambient particles) ─────────────────────
const canvas = document.getElementById('bg-canvas');
const ctx    = canvas.getContext('2d');
const particles = [];
const PARTICLE_COUNT = 50;

function resizeCanvas() {
  canvas.width  = window.innerWidth;
  canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

for (let i = 0; i < PARTICLE_COUNT; i++) {
  particles.push({
    x: Math.random() * window.innerWidth,
    y: Math.random() * window.innerHeight,
    vx: (Math.random() - 0.5) * 0.3,
    vy: (Math.random() - 0.5) * 0.3,
    r: Math.random() * 1.2 + 0.3,
    o: Math.random() * 0.5 + 0.1,
  });
}

function drawParticles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  particles.forEach(p => {
    p.x += p.vx; p.y += p.vy;
    if (p.x < 0) p.x = canvas.width;
    if (p.x > canvas.width)  p.x = 0;
    if (p.y < 0) p.y = canvas.height;
    if (p.y > canvas.height) p.y = 0;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(0,240,255,${p.o})`;
    ctx.fill();
  });
  requestAnimationFrame(drawParticles);
}
drawParticles();

// ── UTILITY ────────────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}