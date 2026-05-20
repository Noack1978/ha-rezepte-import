/**
 * Rezepte Import – UI-Erweiterung für ha-rezepte
 * Wird automatisch geladen wenn ha-rezepte-import installiert ist.
 * Benötigt globale Variablen aus index.html: HA_TOKEN, HA_URL,
 * RECIPES, saveToHA, renderHome, showView, esc, showToast,
 * fEditId, fStep, fEmoji, fIngs, fSteps, fNotes, showFStep
 */
(function () {
  'use strict';

  /* ── CSS ──────────────────────────────────────────────────────────────── */
  const css = `
    .imp-modal{position:fixed;inset:0;background:var(--bg);z-index:300;display:flex;flex-direction:column;transform:translateY(100%);transition:transform .3s cubic-bezier(.4,0,.2,1)}
    .imp-modal.open{transform:translateY(0)}
    .imp-header{background:var(--card);border-bottom:1px solid var(--border);padding:13px 17px;display:flex;align-items:center;gap:11px;flex-shrink:0}
    .imp-header h2{font-family:'Playfair Display',serif;font-size:1.15rem;flex:1}
    .imp-body{flex:1;overflow-y:auto;padding:18px;display:flex;flex-direction:column;gap:14px}
    .imp-footer{background:var(--card);border-top:1px solid var(--border);padding:12px 17px;display:flex;gap:9px;flex-shrink:0}
    .imp-tabs{display:flex;gap:3px;background:var(--bg2);border-radius:var(--r-sm);padding:4px}
    .imp-tab{flex:1;background:none;border:none;border-radius:7px;padding:8px 4px;font-size:.8rem;font-family:'Source Sans 3',sans-serif;color:var(--text3);cursor:pointer;transition:background .15s,color .15s;font-weight:500}
    .imp-tab.active{background:var(--card);color:var(--accent);font-weight:600;box-shadow:var(--shadow)}
    .imp-panel{display:none}
    .imp-panel.active{display:flex;flex-direction:column;gap:12px}
    .imp-textarea{width:100%;min-height:200px;background:var(--card);border:1.5px solid var(--border);border-radius:var(--r-sm);padding:12px 14px;font-size:.88rem;font-family:'Source Sans 3',sans-serif;color:var(--text);resize:vertical;line-height:1.55}
    .imp-textarea:focus{outline:none;border-color:var(--accent)}
    .imp-hint{font-size:.8rem;color:var(--text3);line-height:1.45}
    .imp-upload-label{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;border:2px dashed var(--border);border-radius:var(--r-sm);padding:30px 20px;cursor:pointer;color:var(--text3);font-size:.88rem;text-align:center;transition:border-color .15s}
    .imp-upload-label:hover{border-color:var(--accent);color:var(--accent)}
    .imp-upload-label .imp-upload-icon{font-size:2.2rem}
    .imp-preview-img{max-height:180px;border-radius:var(--r-sm);object-fit:contain;align-self:center}
    .imp-url-input{width:100%;background:var(--card);border:1.5px solid var(--border);border-radius:var(--r-sm);padding:10px 13px;font-size:.91rem;font-family:'Source Sans 3',sans-serif;color:var(--text)}
    .imp-url-input:focus{outline:none;border-color:var(--accent)}
    .imp-spinner{width:34px;height:34px;border:3px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:imp-spin .8s linear infinite;margin:0 auto}
    @keyframes imp-spin{to{transform:rotate(360deg)}}
    .imp-loading{text-align:center;padding:28px 0}
    .imp-loading p{margin-top:13px;font-size:.88rem;color:var(--text3)}
    .imp-result-card{background:var(--card);border:1.5px solid var(--border);border-radius:var(--r);padding:18px;display:flex;gap:14px;align-items:flex-start}
    .imp-result-emoji{font-size:2.3rem;flex-shrink:0}
    .imp-result-info h3{font-family:'Playfair Display',serif;font-size:1.05rem;margin-bottom:3px}
    .imp-result-sub{font-size:.76rem;color:var(--accent);font-weight:600;text-transform:uppercase;letter-spacing:.04em;margin-bottom:5px}
    .imp-result-meta{font-size:.8rem;color:var(--text3)}
    .imp-result-desc{font-size:.82rem;color:var(--text2);margin-top:5px;line-height:1.45}
    .imp-error-box{background:#fee;border:1px solid #f5c5c5;border-radius:var(--r-sm);padding:14px;font-size:.84rem;color:#7a1f1f;line-height:1.5}
    .istat{display:none}
    .istat.on{display:block}
    .btn-imp-back{background:var(--bg2);border:none;border-radius:var(--r-sm);padding:10px 20px;font-size:.9rem;font-family:'Source Sans 3',sans-serif;color:var(--text2);cursor:pointer;flex-shrink:0}
    .btn-imp-back:hover{background:var(--border)}
    .btn-imp{background:var(--accent);color:#fff;border:none;border-radius:var(--r-sm);padding:10px 20px;font-size:.9rem;font-weight:600;font-family:'Source Sans 3',sans-serif;cursor:pointer;flex:1;display:flex;align-items:center;justify-content:center;gap:6px;transition:background .2s}
    .btn-imp:hover{background:var(--accent2)}
    .btn-imp:disabled{opacity:.5;pointer-events:none}
    .btn-imp.sec{background:var(--text2)}
    .btn-imp.sec:hover{background:var(--text)}
  `;
  const styleEl = document.createElement('style');
  styleEl.textContent = css;
  document.head.appendChild(styleEl);

  /* ── HTML ─────────────────────────────────────────────────────────────── */
  const html = `
    <div id="imp-modal" class="imp-modal">
      <div class="imp-header">
        <button class="btn-icon" onclick="impClose()">✕</button>
        <h2>Rezept importieren</h2>
      </div>
      <div class="imp-body">
        <div class="imp-tabs">
          <button class="imp-tab active" onclick="impTab(0)">✏️ Text</button>
          <button class="imp-tab"        onclick="impTab(1)">📁 Datei</button>
          <button class="imp-tab"        onclick="impTab(2)">🔗 Link</button>
        </div>

        <!-- Zustand: Eingabe -->
        <div id="imp-input" class="istat on">
          <!-- Tab 0: Text -->
          <div id="imp-panel-0" class="imp-panel active">
            <p class="imp-hint">Rezepttext einfügen – beliebiges Format (Fließtext, strukturiert, aus Webseite kopiert …).</p>
            <textarea id="imp-textarea" class="imp-textarea" placeholder="Rezepttext hier einfügen …"></textarea>
          </div>
          <!-- Tab 1: Datei -->
          <div id="imp-panel-1" class="imp-panel">
            <p class="imp-hint">TXT-Dateien werden als Text analysiert, Bilder (JPG, PNG, WEBP) via LLM Vision.</p>
            <label class="imp-upload-label" for="imp-file-input">
              <span class="imp-upload-icon">📂</span>
              <span id="imp-file-label">Datei auswählen oder hier ablegen</span>
            </label>
            <input id="imp-file-input" type="file" accept=".txt,image/jpeg,image/png,image/webp" style="display:none" onchange="impFileSelected(this)">
            <img id="imp-img-preview" class="imp-preview-img" style="display:none" alt="Vorschau">
          </div>
          <!-- Tab 2: Link -->
          <div id="imp-panel-2" class="imp-panel">
            <p class="imp-hint">URL einer Rezept-Webseite einfügen. HA ruft die Seite serverseitig ab.</p>
            <input id="imp-url" type="url" class="imp-url-input" placeholder="https://www.beispiel.de/rezept/...">
          </div>
        </div>

        <!-- Zustand: Laden -->
        <div id="imp-loading" class="istat">
          <div class="imp-loading">
            <div class="imp-spinner"></div>
            <p id="imp-loading-msg">Analysiere …</p>
          </div>
        </div>

        <!-- Zustand: Ergebnis -->
        <div id="imp-result" class="istat">
          <p style="font-size:.83rem;color:var(--text2)">Erkanntes Rezept – direkt importieren oder im Formular bearbeiten:</p>
          <div class="imp-result-card" id="imp-result-card"></div>
        </div>

        <!-- Zustand: Fehler -->
        <div id="imp-error" class="istat">
          <div class="imp-error-box" id="imp-error-msg"></div>
        </div>
      </div>

      <div class="imp-footer" id="imp-footer"></div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', html);

  /* ── Import-Button in Home-Hero einfügen ─────────────────────────────── */
  const hero = document.querySelector('#home-view .home-hero > div');
  if (hero) {
    const btn = document.createElement('button');
    btn.title = 'Rezept importieren';
    btn.textContent = '📋';
    btn.style.cssText = 'background:rgba(255,255,255,.18);border:none;border-radius:50%;width:36px;height:36px;font-size:1rem;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:2px;margin-right:6px';
    btn.onclick = impOpen;
    // Vor dem ⚙️-Button einfügen
    const gear = hero.querySelector('button');
    if (gear) hero.insertBefore(btn, gear);
    else hero.appendChild(btn);
  }

  /* ── State ────────────────────────────────────────────────────────────── */
  let _activeTab    = 0;
  let _fileData     = null; // {type:'text'|'image', content, mimeType}
  let _importedRecipe = null;

  /* ── Tab-Steuerung ────────────────────────────────────────────────────── */
  window.impTab = function(idx) {
    _activeTab = idx;
    document.querySelectorAll('.imp-tab').forEach((t, i) =>
      t.classList.toggle('active', i === idx));
    document.querySelectorAll('.imp-panel').forEach((p, i) =>
      p.classList.toggle('active', i === idx));
    _fileData = null;
    document.getElementById('imp-img-preview').style.display = 'none';
    document.getElementById('imp-file-label').textContent = 'Datei auswählen oder hier ablegen';
    impSetState('input');
  };

  /* ── Datei-Auswahl ────────────────────────────────────────────────────── */
  window.impFileSelected = function(input) {
    const file = input.files[0];
    if (!file) return;
    document.getElementById('imp-file-label').textContent = file.name;

    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = e => {
        const dataUrl = e.target.result;
        const b64 = dataUrl.split(',')[1];
        _fileData = { type: 'image', content: b64, mimeType: file.type };
        const prev = document.getElementById('imp-img-preview');
        prev.src = dataUrl;
        prev.style.display = 'block';
      };
      reader.readAsDataURL(file);
    } else {
      const reader = new FileReader();
      reader.onload = e => {
        _fileData = { type: 'text', content: e.target.result };
      };
      reader.readAsText(file);
    }
  };

  /* ── Modal öffnen / schließen ─────────────────────────────────────────── */
  window.impOpen = function() {
    _importedRecipe = null;
    _fileData = null;
    _activeTab = 0;
    document.querySelectorAll('.imp-tab').forEach((t, i) => t.classList.toggle('active', i === 0));
    document.querySelectorAll('.imp-panel').forEach((p, i) => p.classList.toggle('active', i === 0));
    document.getElementById('imp-textarea').value = '';
    document.getElementById('imp-url').value = '';
    document.getElementById('imp-img-preview').style.display = 'none';
    document.getElementById('imp-file-label').textContent = 'Datei auswählen oder hier ablegen';
    document.getElementById('imp-file-input').value = '';
    impSetState('input');
    document.getElementById('imp-modal').classList.add('open');
  };
  window.impClose = function() {
    document.getElementById('imp-modal').classList.remove('open');
  };

  /* ── Zustand steuern ──────────────────────────────────────────────────── */
  function impSetState(state) {
    ['input','loading','result','error'].forEach(s =>
      document.getElementById('imp-' + s).classList.toggle('on', s === state));

    const footer = document.getElementById('imp-footer');
    if (state === 'input') {
      footer.innerHTML = `
        <button class="btn-imp-back" onclick="impClose()">Abbrechen</button>
        <button class="btn-imp" onclick="impAnalyze()">🔍 Analysieren</button>`;
    } else if (state === 'result') {
      footer.innerHTML = `
        <button class="btn-imp-back" onclick="impSetState('input')">← Zurück</button>
        <button class="btn-imp sec" onclick="impEdit()">✏️ Bearbeiten</button>
        <button class="btn-imp" onclick="impSave()">💾 Importieren</button>`;
    } else if (state === 'error') {
      footer.innerHTML = `
        <button class="btn-imp-back" onclick="impSetState('input')">← Zurück</button>
        <button class="btn-imp" onclick="impAnalyze()">↺ Erneut</button>`;
    } else {
      footer.innerHTML = '';
    }
  }

  /* ── Analysieren ──────────────────────────────────────────────────────── */
  window.impAnalyze = async function() {
    const startTs = Math.floor(Date.now() / 1000);
    let service, payload, loadingMsg;

    if (_activeTab === 0) {
      // Text
      const text = document.getElementById('imp-textarea').value.trim();
      if (!text) { window.showToast('Bitte Text einfügen', 'err'); return; }
      service    = 'parse_text';
      payload    = { text };
      loadingMsg = 'Text wird analysiert …';

    } else if (_activeTab === 1) {
      // Datei
      if (!_fileData) { window.showToast('Bitte eine Datei auswählen', 'err'); return; }
      if (_fileData.type === 'text') {
        service    = 'parse_text';
        payload    = { text: _fileData.content };
        loadingMsg = 'Dateiinhalt wird analysiert …';
      } else {
        service    = 'parse_image';
        payload    = { image_data: _fileData.content, mime_type: _fileData.mimeType };
        loadingMsg = 'Bild wird analysiert …';
      }

    } else {
      // Link
      const url = document.getElementById('imp-url').value.trim();
      if (!url) { window.showToast('Bitte eine URL eingeben', 'err'); return; }
      service    = 'parse_url';
      payload    = { url };
      loadingMsg = 'Webseite wird abgerufen …';
    }

    document.getElementById('imp-loading-msg').textContent = loadingMsg;
    impSetState('loading');

    try {
      const resp = await fetch(`${window.HA_URL}/api/services/rezepte_import/${service}`, {
        method:  'POST',
        headers: { 'Authorization': `Bearer ${window.HA_TOKEN}`, 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      });
      if (!resp.ok) throw new Error('HA-Fehler HTTP ' + resp.status);

      // Ergebnis pollen
      const result = await impPoll(startTs);
      if (result.status !== 'ok') throw new Error(result.error || 'Unbekannter Fehler');

      _importedRecipe = result.recipe;
      _importedRecipe.id = Date.now();
      impShowResult(_importedRecipe);
      impSetState('result');
    } catch(e) {
      document.getElementById('imp-error-msg').textContent = 'Fehler: ' + e.message;
      impSetState('error');
    }
  };

  async function impPoll(startTs, maxWait = 45000) {
    const deadline = Date.now() + maxWait;
    while (Date.now() < deadline) {
      await new Promise(r => setTimeout(r, 1500));
      try {
        const r = await fetch('/local/rezepte/import_result.json?_=' + Date.now());
        if (!r.ok) continue;
        const data = await r.json();
        if (data.ts >= startTs) return data;
      } catch(e) { /* noch nicht fertig */ }
    }
    throw new Error('Timeout – kein Ergebnis nach 45 Sekunden.');
  }

  function impShowResult(r) {
    const meta = [
      (r.ingredients?.length || 0) + ' Zutaten',
      (r.steps?.length || 0) + ' Schritte',
      r.category,
    ].filter(Boolean).join(' · ');

    document.getElementById('imp-result-card').innerHTML = `
      <div class="imp-result-emoji">${window.esc(r.emoji || '🍳')}</div>
      <div class="imp-result-info">
        <h3>${window.esc(r.title)}</h3>
        ${r.subtitle ? `<div class="imp-result-sub">${window.esc(r.subtitle)}</div>` : ''}
        <div class="imp-result-meta">${window.esc(meta)}</div>
        ${r.description ? `<div class="imp-result-desc">${window.esc(r.description)}</div>` : ''}
      </div>`;
  }

  /* ── Importieren ──────────────────────────────────────────────────────── */
  window.impSave = async function() {
    if (!_importedRecipe) return;
    window.RECIPES.push(_importedRecipe);
    const btn = document.querySelector('#imp-footer .btn-imp:last-child');
    if (btn) { btn.disabled = true; btn.textContent = '💾 Speichern …'; }
    try {
      await window.saveToHA();
      window.showToast('✓ Rezept importiert', 'ok');
      impClose();
      window.renderHome();
      window.showView('home');
    } catch(e) {
      window.RECIPES = window.RECIPES.filter(r => r.id !== _importedRecipe.id);
      window.showToast('❌ ' + e.message, 'err');
      if (btn) { btn.disabled = false; btn.textContent = '💾 Importieren'; }
    }
  };

  /* ── Im Formular bearbeiten ────────────────────────────────────────────── */
  window.impEdit = function() {
    if (!_importedRecipe) return;
    const r = _importedRecipe;
    impClose();
    window.fEditId = null;
    window.fStep   = 0;
    window.fEmoji  = r.emoji || '🍳';
    window.fIngs   = (r.ingredients || []).map(x => ({...x}));
    window.fSteps  = (r.steps       || []).map(x => ({...x}));
    window.fNotes  = [...(r.notes   || [''])];
    document.getElementById('f-title').value    = r.title        || '';
    document.getElementById('f-subtitle').value = r.subtitle     || '';
    document.getElementById('f-cat').value      = r.category     || '';
    document.getElementById('f-servings').value = r.baseServings || 4;
    document.getElementById('f-slabel').value   = r.servingLabel || 'Portionen';
    document.getElementById('f-desc').value     = r.description  || '';
    document.getElementById('emoji-box').textContent      = window.fEmoji;
    document.getElementById('form-heading').textContent   = 'Rezept bearbeiten';
    document.getElementById('emoji-picker-panel').style.display = 'none';
    document.getElementById('emoji-box').classList.remove('open');
    window.showFStep();
    document.getElementById('form-modal').classList.add('open');
  };

})();
