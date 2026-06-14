/* ═══════════════════════════════════════════
   Alvitur.is — Production Interactive Behaviors
   Sprettur 102.5a — Hrein endurskrifun (Master Override)
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  // ─── DOM references ───
  var tabGeneral    = document.getElementById('tab-general');
  var tabConfidential = document.getElementById('tab-confidential');
  var tabEmployee   = document.getElementById('tab-employee');
  var tabInbox      = document.getElementById('tab-inbox');
  var trustStatement = document.getElementById('trust-statement');
  var intakeCard    = document.getElementById('intake-card');
  var queryInput    = document.getElementById('query-input');
  var submitBtn     = document.getElementById('submit-btn');
  var statusArea    = document.getElementById('status-area');
  var resultsArea   = document.getElementById('results-area');
  var resultsBody   = document.getElementById('results-body');
  var employeePanel = document.getElementById('employee-panel');
  var inboxContent  = document.getElementById('inbox-content');

  var currentMode = 'general';
  var busy = false;

  function getToken() {
    return localStorage.getItem('alvitur_token') || '';
  }

  // ─── Mode switching ───
  function setMode(mode) {
    currentMode = mode;
    [tabGeneral, tabConfidential, tabEmployee, tabInbox].forEach(function (t) {
      if (!t) return;
      var active = t.getAttribute('data-mode') === mode;
      t.classList.toggle('intake-tab--active', active);
      t.setAttribute('aria-selected', active ? 'true' : 'false');
    });

    if (mode === 'inbox') {
      if (intakeCard) intakeCard.style.display = 'none';
      if (employeePanel) { employeePanel.hidden = false; employeePanel.style.display = 'block'; }
      if (trustStatement) trustStatement.hidden = true;
      loadInbox();
      return;
    }

    if (intakeCard) intakeCard.style.display = '';
    if (employeePanel) { employeePanel.hidden = true; employeePanel.style.display = 'none'; }
    if (trustStatement) trustStatement.hidden = (mode !== 'confidential');
  }

  if (tabGeneral)    tabGeneral.addEventListener('click', function () { setMode('general'); });
  if (tabConfidential) tabConfidential.addEventListener('click', function () { setMode('confidential'); });
  if (tabEmployee)   tabEmployee.addEventListener('click', function () { setMode('employee'); });
  if (tabInbox)      tabInbox.addEventListener('click', function () { setMode('inbox'); });

  // ─── Submit handler ───
  if (submitBtn) {
    submitBtn.addEventListener('click', function () {
      if (busy) return;
      var query = queryInput ? queryInput.value.trim() : '';
      if (!query) { showStatus('error', 'Sláðu inn fyrirspurn.'); return; }
      busy = true;
      showStatus('loading', 'Greining í gangi…');

      fetch('/api/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + getToken()
        },
        body: JSON.stringify({ query: query })
      })
      .then(function (r) {
        if (r.status === 202) {
          return r.json().then(function (d) { showHITLWidget(d); });
        }
        if (r.status === 401) { showStatus('error', 'Aðgangur óheimill.'); return; }
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.text().then(function (text) { renderStream(text); });
      })
      .catch(function (err) {
        showStatus('error', 'Villa: ' + (err.message || 'Óþekkt villa'));
      })
      .finally(function () { busy = false; });
    });
  }

  // ─── SSE stream parser ───
  function renderStream(text) {
    if (!resultsArea || !resultsBody) return;
    resultsArea.hidden = false;
    var chunks = text.split('\n').filter(function (l) { return l.startsWith('data: '); });
    var output = '';
    chunks.forEach(function (line) {
      var payload = line.substring(6);
      if (payload === '[DONE]') return;
      if (payload.indexOf('"stage"') !== -1) {
        try { var s = JSON.parse(payload); output += '<p style="color:#94A3B8;">' + escapeHtml(s.stage) + '</p>'; } catch (e) {}
        return;
      }
      try {
        var obj = JSON.parse(payload);
        var delta = obj.choices && obj.choices[0] && obj.choices[0].delta;
        if (delta && delta.content) output += escapeHtml(delta.content);
        if (delta && delta.content === '') output += ' ';
      } catch (e) {}
    });
    if (output) {
      resultsBody.innerHTML = '<div style="white-space:pre-wrap;line-height:1.6;">' + output + '</div>';
    }
  }

  // ─── HITL widget ───
  function showHITLWidget(data) {
    if (!resultsBody || !resultsArea) return;
    resultsArea.hidden = false;
    var approvalId = data.approval_id || '';
    var html = '<div style="background:#1a1a2e;border:1px solid #e94560;border-radius:8px;padding:1rem;">';
    html += '<h4 style="color:#e94560;">🔒 Bíður samþykktar</h4>';
    html += '<p style="color:#ccc;">Þessi aðgerð krefst staðfestingar.</p>';
    html += '<p style="color:#94A3B8;">Tilvísun: ' + escapeHtml(approvalId) + '</p>';
    html += '<button onclick="approveTask(\'' + approvalId + '\')" style="padding:0.5rem 1rem;background:#0f3460;color:#e2e8f0;border:none;border-radius:4px;cursor:pointer;margin-right:0.5rem;">✅ Samþykkja</button>';
    html += '<button onclick="alert(\'Hafnað\')" style="padding:0.5rem 1rem;background:#1a1a2e;color:#e94560;border:1px solid #e94560;border-radius:4px;cursor:pointer;">❌ Hafna</button>';
    html += '</div>';
    resultsBody.innerHTML = html;
  }

  window.approveTask = function (id) {
    fetch('/api/approve/' + id, {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + getToken() }
    })
    .then(function (r) { return r.json(); })
    .then(function () { showStatus('success', '✅ Samþykkt!'); })
    .catch(function () { showStatus('error', 'Villa við samþykki.'); });
  };

  // ─── Inbox ───
  function loadInbox() {
    if (!inboxContent) return;
    inboxContent.innerHTML = '<p style="color:#94A3B8;">Sæki beiðnir…</p>';
    fetch('/api/pending_tasks', {
      headers: { 'Authorization': 'Bearer ' + getToken() }
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var tasks = data.pending_tasks || [];
      if (tasks.length === 0) {
        inboxContent.innerHTML = '<p style="color:#94A3B8;">Engar beiðnir í biðröð.</p>';
        return;
      }
      var html = '';
      tasks.forEach(function (t) {
        html += '<div style="background:#1a1a2e;border:1px solid #334155;border-radius:8px;padding:1rem;margin-bottom:0.5rem;">';
        html += '<strong style="color:#e2e8f0;">' + escapeHtml(t.tool_name) + '</strong> ';
        html += '<span style="color:#94A3B8;">- ' + escapeHtml(t.status) + '</span>';
        html += '<div style="margin-top:0.5rem;">';
        html += '<button onclick="approveTask(\'' + t.task_id + '\')" style="padding:0.3rem 0.8rem;background:#0f3460;color:#e2e8f0;border:none;border-radius:4px;cursor:pointer;margin-right:0.5rem;">Samþykkja</button>';
        html += '<button onclick="alert(\'Hafnað\')" style="padding:0.3rem 0.8rem;background:#1a1a2e;color:#e94560;border:1px solid #e94560;border-radius:4px;cursor:pointer;">Hafna</button>';
        html += '</div></div>';
      });
      inboxContent.innerHTML = html;
    })
    .catch(function () {
      inboxContent.innerHTML = '<p style="color:#e94560;">Villa við að sækja beiðnir.</p>';
    });
  }

  // ─── Helpers ───
  function showStatus(type, message) {
    if (!statusArea) return;
    var icon = type === 'error' ? '⚠️ ' : type === 'loading' ? '⏳ ' : type === 'success' ? '✅ ' : '';
    statusArea.innerHTML = '<div class="status-message">' + icon + message + '</div>';
  }

  function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Init
  if (tabGeneral && tabGeneral.classList.contains('intake-tab--active')) setMode('general');
  else if (tabConfidential && tabConfidential.classList.contains('intake-tab--active')) setMode('confidential');
  else setMode('general');
})();

document.addEventListener('DOMContentLoaded',function(){
var token=localStorage.getItem('alvitur_token')||'';
var box=document.getElementById('loginbox');
var intake=document.getElementById('main-intake');
 if(box)box.style.display='none';
 if(intake)intake.style.display='';
var sBtn=document.getElementById('sidebar-login-btn');
if(sBtn){sBtn.addEventListener('click',function(){window.location.href='/login';});}
var lBtn=document.getElementById('loginbtn');
if(lBtn){lBtn.addEventListener('click',function(){
var tok=document.getElementById('logintok');
if(tok){var val=tok.value.trim();
if(val){localStorage.setItem('alvitur_token',val);location.reload();}
else{alert('Limdu token fyrst');}}
});}
});
// === V5: Vitinn tvö-hök + /api/vitinn ===
document.addEventListener('DOMContentLoaded', function() {
    var wsToggle = document.getElementById('web-search-toggle');
    var smToggle = document.getElementById('stormeistari-toggle');
    var approvalPanel = document.getElementById('approval-panel');
    var approvalQuery = document.getElementById('approval-query');
    var approvalConfirm = document.getElementById('approval-confirm');
    var approvalCancel = document.getElementById('approval-cancel');
    var statusArea = document.getElementById('status-area');
    var resultsArea = document.getElementById('results-area');
    var resultsBody = document.getElementById('results-body');
    var submitBtn = document.getElementById('submit-btn');

    submitBtn.addEventListener('click', function(e) {
        var query = (document.getElementById('query-input') || {}).value || '';
        if (smToggle.checked) {
            approvalQuery.textContent = '"' + query.substring(0,80) + '"';
            approvalPanel.removeAttribute('hidden');
        } else if (wsToggle.checked) {
            sendVitinn(query, true, false);
        } else {
            sendVitinn(query, false, false);
        }
    });

    if (approvalConfirm) approvalConfirm.addEventListener('click', function() {
        approvalPanel.setAttribute('hidden','');
        var query = (document.getElementById('query-input') || {}).value || '';
        sendVitinn(query, wsToggle.checked, true);
    });

    if (approvalCancel) approvalCancel.addEventListener('click', function() {
        approvalPanel.setAttribute('hidden','');
        smToggle.checked = false;
    });

    function esc(t){var d=document.createElement('div');d.textContent=(t==null?'':String(t));return d.innerHTML;}
    function badgeHtml(s){
        if (s.stormeistari) return '<span style="background:var(--color-accent-light);color:var(--color-accent);font-size:.7rem;padding:2px 8px;border-radius:99px;font-weight:500">Stórmeistari</span>';
        if (s.web_search) return '<span style="background:#e0f0ff;color:#0066cc;font-size:.7rem;padding:2px 8px;border-radius:99px;font-weight:500">+Vefur</span>';
        return '<span style="background:#e6f4ea;color:#1a7a3c;font-size:.7rem;padding:2px 8px;border-radius:99px;font-weight:500">Sovereign</span>';
    }
    function sendVitinn(query, webSearch, stormeistari) {
        var token = localStorage.getItem('alvitur_token') || '';
        if (statusArea) statusArea.textContent = 'Greini...';
        wsToggle.checked = false;
        smToggle.checked = false;
        approvalPanel.setAttribute('hidden','');
        // Undirbua nidurstodu-svaedi fyrir streymi
        if (resultsBody) resultsBody.innerHTML = '<p id="vitinn-stream" style="font-size:.875rem;white-space:pre-wrap"></p>';
        if (resultsArea) resultsArea.hidden = false;
        var streamP = document.getElementById('vitinn-stream');
        var acc = '';
        var hvToggle = document.getElementById('hvelfingin-search-toggle');
        var hvelfinginSearch = hvToggle ? hvToggle.checked : false;
        var url = '/api/vitinn/stream?query=' + encodeURIComponent(query)
                + '&web_search=' + (webSearch?'true':'false')
                + '&stormeistari=' + (stormeistari?'true':'false')
                + '&hvelfingin_search=' + (hvelfinginSearch?'true':'false');
        fetch(url, {headers:{'Authorization':'Bearer '+token}}).then(function(resp){
            if (!resp.ok) throw new Error('HTTP '+resp.status);
            var reader = resp.body.getReader();
            var decoder = new TextDecoder();
            var buffer = '';
            function pump(){
                return reader.read().then(function(res){
                    if (res.done) return;
                    buffer += decoder.decode(res.value, {stream:true});
                    var lines = buffer.split('\n');
                    buffer = lines.pop();
                    lines.forEach(function(line){
                        line = line.trim();
                        if (!line || line.indexOf('data:')!==0) return;
                        var payload = line.slice(5).trim();
                        if (payload === '[DONE]') return;
                        try {
                            var obj = JSON.parse(payload);
                            if (obj.chunk != null) {
                                acc += obj.chunk;
                                if (streamP) streamP.textContent = acc;
                                if (statusArea) statusArea.textContent = '';
                            } else if (obj.metadata) {
                                var s = obj.metadata.sources || {};
                                var cits = (obj.metadata.citations||[]).map(function(c){
                                    return '<li style="font-size:.75rem;color:var(--color-text-muted);margin:.2rem 0">'+esc(c.title||c.citation_full||'')+'</li>';
                                }).join('');
                                if (resultsBody) resultsBody.innerHTML =
                                    '<div style="margin-bottom:.5rem">'+badgeHtml(s)+'</div>'
                                    +'<p style="font-size:.875rem;white-space:pre-wrap">'+esc(acc)+'</p>'
                                    +(cits?'<ul style="padding-left:1rem;margin-top:.5rem">'+cits+'</ul>':'');
                            }
                        } catch(e) {}
                    });
                    return pump();
                });
            }
            return pump();
        }).catch(function(e){
            if (statusArea) statusArea.textContent = 'Tengivilla: '+e.message;
        });
    }
});
// Fela hok a Hvelfingin/confidential flipa
document.addEventListener('DOMContentLoaded', function() {
    var tabs = document.querySelectorAll('[data-mode]');
    var toggles = document.getElementById('intake-toggles');
    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            var mode = tab.getAttribute('data-mode');
            if (mode === 'confidential' || mode === 'employee' || mode === 'inbox') {
                toggles.style.display = 'none';
                var ap = document.getElementById('approval-panel');
                if (ap) ap.setAttribute('hidden','');
                var ws = document.getElementById('web-search-toggle');
                var sm = document.getElementById('stormeistari-toggle');
                if (ws) ws.checked = false;
                if (sm) sm.checked = false;
            } else {
                toggles.style.display = '';
            }
        });
    });
});
document.addEventListener('DOMContentLoaded', function() {
    var tabs = document.querySelectorAll('[data-mode]');
    var toggles = document.getElementById('intake-toggles');
    if (!toggles) return;
    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            var mode = tab.getAttribute('data-mode');
            if (mode === 'confidential' || mode === 'employee' || mode === 'inbox') {
                toggles.style.display = 'none';
                var ap = document.getElementById('approval-panel');
                if (ap) ap.setAttribute('hidden','');
                var ws = document.getElementById('web-search-toggle');
                var sm = document.getElementById('stormeistari-toggle');
                if (ws) ws.checked = false;
                if (sm) sm.checked = false;
            } else {
                toggles.style.display = '';
            }
        });
    });
});

// Styrkja-spjald
document.addEventListener('DOMContentLoaded', function() {
    var trigger = document.getElementById('support-trigger');
    var overlay = document.getElementById('support-overlay');
    var closeBtn = document.getElementById('support-close');
    if (!trigger || !overlay) return;
    trigger.addEventListener('click', function() { overlay.removeAttribute('hidden'); });
    if (closeBtn) closeBtn.addEventListener('click', function() { overlay.setAttribute('hidden',''); });
    overlay.addEventListener('click', function(e) { if (e.target === overlay) overlay.setAttribute('hidden',''); });
});

// H5: Hvelfingin-leitarrofi — default-AF, synileiki, endurstilling per fyrirspurn
document.addEventListener('DOMContentLoaded', function() {
    var toggle = document.getElementById('hvelfingin-search-toggle');
    var vis = document.getElementById('hvelfingin-search-visibility');
    if (!toggle || !vis) return;
    // Default-AF tryggt
    toggle.checked = false;
    vis.setAttribute('hidden','');
    toggle.addEventListener('change', function() {
        if (toggle.checked) { vis.removeAttribute('hidden'); }
        else { vis.setAttribute('hidden',''); }
    });
    // Endurstilla i AF thegar skipt er um flipa (privacy-by-default)
    var tabs = document.querySelectorAll('[data-mode]');
    tabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            toggle.checked = false;
            vis.setAttribute('hidden','');
        });
    });
});


// === V6: TIER-GATING (v2) - Verk 2+3+4 ===
document.addEventListener('DOMContentLoaded', function() {
    function getTier() {
        var tok = localStorage.getItem('alvitur_token') || '';
        if (!tok) return null;
        try {
            var p = tok.split('.');
            if (p.length < 2) return null;
            var pl = JSON.parse(atob(p[1].replace(/-/g,'+').replace(/_/g,'/')));
            return (pl.tier || '').toLowerCase();
        } catch(e) { return null; }
    }
    function showGateTip(anchor, msg) {
        var old = document.getElementById('gate-tip');
        if (old) old.remove();
        var tip = document.createElement('div');
        tip.id = 'gate-tip';
        tip.style.cssText = 'position:fixed;background:#1a2a1a;color:#fff;font-size:.75rem;padding:6px 10px;border-radius:6px;max-width:240px;line-height:1.5;z-index:9999;pointer-events:none;box-shadow:0 2px 8px rgba(0,0,0,.25)';
        tip.textContent = msg;
        document.body.appendChild(tip);
        var r = anchor.getBoundingClientRect();
        tip.style.top = Math.min(r.bottom + 6, window.innerHeight - 60) + 'px';
        tip.style.left = Math.max(8, r.left) + 'px';
        setTimeout(function() { if (tip.parentNode) tip.remove(); }, 2500);
        document.addEventListener('click', function rm() { if (tip.parentNode) tip.remove(); document.removeEventListener('click', rm); });
    }
    function makeStep(icon, tool, result) {
        return '<div style="display:flex;gap:.5rem;align-items:flex-start;padding:.5rem .625rem;background:var(--color-bg,#f5f7f5);border-radius:.375rem">' +
               '<span style="font-size:.95rem;flex-shrink:0;margin-top:1px">' + icon + '</span>' +
               '<div style="flex:1;min-width:0"><div style="font-size:.8rem;font-weight:500;color:var(--color-text,#111)">' + tool + '</div>' +
               '<div style="font-size:.72rem;color:var(--color-text-muted,#666);margin-top:1px;line-height:1.4">' + result + '</div></div>' +
               '<span style="color:#1a7a3c;font-size:.85rem;flex-shrink:0">&#x2713;</span></div>';
    }
    function showAgentShowcase() {
        var old = document.getElementById('agt-ov');
        if (old) { old.remove(); return; }
        var ov = document.createElement('div');
        ov.id = 'agt-ov';
        ov.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:200;display:flex;align-items:center;justify-content:center;padding:1rem;box-sizing:border-box';
        ov.innerHTML =
            '<div style="background:var(--color-surface,#fff);border-radius:.875rem;padding:1.5rem;max-width:400px;width:100%;box-shadow:0 8px 32px rgba(0,0,0,.15);position:relative;box-sizing:border-box">' +
            '<button id="agt-cl" style="position:absolute;top:.75rem;right:.75rem;background:none;border:none;cursor:pointer;font-size:1.2rem;color:var(--color-text-muted,#999)">&#xd7;</button>' +
            '<div style="font-size:.65rem;text-transform:uppercase;letter-spacing:.08em;color:var(--color-text-muted,#999);margin-bottom:.25rem">Sýnidæmi</div>' +
            '<div style="font-size:1rem;font-weight:600;color:var(--color-text,#111);margin-bottom:.25rem">Erindrekinn leysir lögfræðiverkefni</div>' +
            '<div style="font-size:.78rem;color:var(--color-text-muted,#666);margin-bottom:.875rem;line-height:1.5">Lögfræðingur bað um aðstoð við að greina og semja greinargerð.</div>' +
            '<div style="display:flex;flex-direction:column;gap:.375rem;margin-bottom:.75rem">' +
            makeStep('&#x1F50D;','Lagarannsókn','Fann 3 lög: Stjórnarskrá 1944 nr. 33, Þingsköp Alþingis 1991 nr. 55, Persónuvernd 2018 nr. 90') +
            makeStep('&#x1F4DD;','Skjalasmiður','Drög tilbúin — 3 blaðsíður, 12 tilvísanir í lagaheimildir') +
            makeStep('&#x1F52C;','Textagreining','2 ábendingar: bæta við tilvísun í 36. gr. stjórnarskrár, laga málfar í 3. mgr.') +
            makeStep('&#x1F4E8;','Póstsending (HITL)','Samþykkt af stjórnanda. Greinargerð send til viðtakanda.') +
            '</div>' +
            '<div style="font-size:.72rem;color:var(--color-text-muted,#888);margin-bottom:.75rem">&#x23F1; 2 mín 34 sek • 4 skref lokið</div>' +
            '<div style="border:0.5px solid var(--color-border,#e0e0e0);border-radius:.5rem;padding:.875rem;text-align:center">' +
            '<div style="font-size:.78rem;color:var(--color-text-muted,#666);margin-bottom:.5rem">&#x1F512; Þessi virkni krefst Erindreka-aðgangs eða áskriftar</div>' +
            '<button onclick="window.location.href=&#39;/um&#39;" style="background:var(--color-accent,#1a5c3a);color:#fff;border:none;border-radius:.5rem;padding:.5rem 1.25rem;font-size:.875rem;font-weight:500;cursor:pointer;font-family:inherit">Styðja verkefnið</button>' +
            '</div></div>';
        document.body.appendChild(ov);
        ov.addEventListener('click', function(e) { if (e.target === ov) ov.remove(); });
        var cl = document.getElementById('agt-cl');
        if (cl) cl.addEventListener('click', function() { ov.remove(); });
    }
    var tier = getTier();
    var fullAccess = tier && tier !== 'vitinn';
    if (!fullAccess) {
        ['confidential','employee'].forEach(function(mode) {
            var tab = document.querySelector('[data-mode="' + mode + '"]');
            if (!tab) return;
            tab.style.opacity = '0.4';
            tab.style.cursor = 'not-allowed';
            tab.setAttribute('aria-disabled','true');
            tab.addEventListener('click', function(e) {
                e.stopImmediatePropagation();
                e.preventDefault();
                if (mode === 'employee') { showAgentShowcase(); }
                else { showGateTip(tab, 'Þessi hluti krefst innskráningar eða boðsaðgangs.'); }
            }, true);
        });
    }
    var smCb = document.getElementById('stormeistari-toggle');
    var smLabel = smCb ? (smCb.closest('label') || smCb.parentElement) : null;
    if (smLabel) {
        if (!tier) { smLabel.style.display = 'none'; }
        else if (tier === 'vitinn') {
            smCb.disabled = true;
            smLabel.style.opacity = '0.4';
            smLabel.style.cursor = 'not-allowed';
            smLabel.addEventListener('click', function(e) {
                e.preventDefault();
                showGateTip(smLabel, 'Stórmeistari krefst Hvelfingin-aðgangs.');
            });
        }
    }
});
