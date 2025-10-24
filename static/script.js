// script.js — UI behaviour for MultiDocChat
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

let sessionId = localStorage.getItem('mdc_session_id') || '';
let stagedFiles = []; // File objects selected but not yet uploaded

// DOM refs
const fileInput = document.getElementById('file-input');
const dropzone = document.getElementById('dropzone');
const fileListEl = document.getElementById('file-list');
const ingestedListEl = document.getElementById('ingested-list');
const sessionIdEl = document.getElementById('session-id');
const indexStatusEl = document.getElementById('index-status');
const indexedAtEl = document.getElementById('indexed-at');
const metaFilesEl = document.getElementById('meta-files');
const metaSizeEl = document.getElementById('meta-size');
const indexingEl = document.getElementById('indexing');
const indexProgressEl = document.getElementById('index-progress');
const uploadBtn = document.getElementById('upload-btn');
const clearBtn = document.getElementById('clear-btn');
const messagesEl = document.getElementById('messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const thinkingEl = document.getElementById('thinking');
const toastEl = document.getElementById('toast');

function formatBytes(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B','KB','MB','GB','TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function setIndexStatus(text, cls = 'idle') {
  indexStatusEl.textContent = text;
  indexStatusEl.className = 'status ' + cls;
}

function setSessionId(id) {
  sessionId = id;
  sessionIdEl.textContent = id || '—';
  if (id) localStorage.setItem('mdc_session_id', id);
}

function showToast(msg) {
  toastEl.textContent = msg;
  toastEl.style.opacity = '1';
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => toastEl.style.opacity = '0', 3000);
}

function renderFileList() {
  fileListEl.innerHTML = '';
  if (!stagedFiles.length) {
    fileListEl.innerHTML = '<div class="empty muted">No files selected</div>';
    return;
  }
  const ul = document.createElement('div');
  ul.className = 'file-list-grid';
  let total = 0;
  stagedFiles.forEach((f, idx) => {
    total += f.size || 0;
    const item = document.createElement('div');
    item.className = 'file-item';
    item.innerHTML = `
      <div class="file-main">
        <div class="file-name">${escapeHtml(f.name)}</div>
        <div class="file-meta muted">${f.type || '—'} • ${formatBytes(f.size || 0)}</div>
      </div>
      <div class="file-actions">
        <button class="btn small remove" data-idx="${idx}">Remove</button>
      </div>
    `;
    ul.appendChild(item);
  });
  fileListEl.appendChild(ul);
  metaFilesEl.textContent = stagedFiles.length;
  metaSizeEl.textContent = formatBytes(total);
}

function renderIngested(docs) {
  ingestedListEl.innerHTML = '';
  if (!docs || docs.length === 0) {
    ingestedListEl.innerHTML = '<div class="muted">No documents indexed yet.</div>';
    return;
  }
  const list = document.createElement('div');
  list.className = 'ingested-grid';
  docs.forEach(d => {
    const card = document.createElement('div');
    card.className = 'ingested-item';
    card.innerHTML = `
      <div class="ingested-title">${escapeHtml(d.name || d.source || 'Document')}</div>
      <div class="ingested-meta muted">${escapeHtml(d.type || '')} • ${formatBytes(d.size || 0)}</div>
      <div class="ingested-foot muted">Indexed: ${d.indexed_at || '—'}</div>
    `;
    list.appendChild(card);
  });
  ingestedListEl.appendChild(list);
}

function appendMessage(role, text) {
  const bubble = document.createElement('div');
  bubble.className = 'bubble ' + (role === 'user' ? 'user' : 'assistant');
  bubble.textContent = text;
  messagesEl.appendChild(bubble);
  messagesEl.classList.remove('empty');
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

// Safety helper to avoid XSS from filenames
function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, (m) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

// Event handlers
fileInput.addEventListener('change', (e) => {
  const files = Array.from(e.target.files || []);
  stagedFiles = stagedFiles.concat(files);
  renderFileList();
});

dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('hover'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('hover'));
dropzone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropzone.classList.remove('hover');
  const files = Array.from(e.dataTransfer.files || []);
  stagedFiles = stagedFiles.concat(files);
  fileInput.files = createFileList(stagedFiles);
  renderFileList();
});

// Create a FileList from array (for convenience)
function createFileList(files) {
  const dataTransfer = new DataTransfer();
  files.forEach(f => dataTransfer.items.add(f));
  return dataTransfer.files;
}

fileListEl.addEventListener('click', (ev) => {
  const btn = ev.target.closest('button.remove');
  if (!btn) return;
  const idx = Number(btn.dataset.idx);
  if (!Number.isFinite(idx)) return;
  stagedFiles.splice(idx, 1);
  fileInput.files = createFileList(stagedFiles);
  renderFileList();
});

clearBtn.addEventListener('click', () => {
  stagedFiles = [];
  fileInput.value = '';
  renderFileList();
});

// Upload & index
document.getElementById('upload-form').addEventListener('submit', async (ev) => {
  ev.preventDefault();
  if (!stagedFiles.length) {
    showToast('Please select files to upload');
    return;
  }

  setIndexStatus('Indexing', 'working');
  indexingEl.style.display = 'inline-block';
  indexProgressEl.textContent = '0%';
  uploadBtn.disabled = true;
  clearBtn.disabled = true;

  try {
    const fd = new FormData();
    stagedFiles.forEach(f => fd.append('files', f));
    const res = await fetch('/upload', { method: 'POST', body: fd });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Upload failed');
    }
    const data = await res.json();
    setSessionId(data.session_id || '');
    setIndexStatus('Indexed', 'ok');
    indexedAtEl.textContent = new Date().toLocaleString();
    indexProgressEl.textContent = '100%';
    showToast('Indexing completed');

    // Render ingested docs using local stagedFiles as best-effort metadata
    const ingestedDocs = stagedFiles.map(f => ({
      name: f.name,
      type: f.type,
      size: f.size,
      indexed_at: new Date().toLocaleString()
    }));
    renderIngested(ingestedDocs);

    // clear staged files (they are now indexed)
    stagedFiles = [];
    fileInput.value = '';
    renderFileList();

  } catch (e) {
    console.error(e);
    setIndexStatus('Error', 'error');
    showToast('Indexing failed');
  } finally {
    indexingEl.style.display = 'none';
    uploadBtn.disabled = false;
    clearBtn.disabled = false;
  }
});

// Chat send
sendBtn.addEventListener('click', async () => {
  await sendMessage();
});
messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

async function sendMessage() {
  const text = messageInput.value.trim();
  if (!text) return;
  if (!sessionId) { showToast('Please upload documents first'); return; }

  appendMessage('user', text);
  messageInput.value = '';
  thinkingEl.style.display = 'inline-block';
  sendBtn.disabled = true;

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ session_id: sessionId, message: text })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Chat failed');
    }
    const data = await res.json();
    appendMessage('assistant', data.answer || '(no answer)');
  } catch (e) {
    console.error(e);
    appendMessage('assistant', 'Error: failed to get answer. Check server logs.');
    showToast('Chat error');
  } finally {
    thinkingEl.style.display = 'none';
    sendBtn.disabled = false;
  }
}

// On load: restore session if present
window.addEventListener('DOMContentLoaded', () => {
  if (sessionId) {
    setSessionId(sessionId);
    setIndexStatus('Indexed', 'ok');
    // optionally show chat pane if you prefer
  }
  renderFileList();
  renderIngested([]);
});

// Utility: escape for safety in HTML (already used above)
