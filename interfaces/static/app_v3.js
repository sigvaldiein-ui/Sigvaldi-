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
if(token){if(box)box.style.display='none';if(intake)intake.style.display='';}
else{if(box)box.style.display='flex';}
var sBtn=document.getElementById('sidebar-login-btn');
if(sBtn){sBtn.addEventListener('click',function(){if(box)box.style.display='flex';});}
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

    function sendVitinn(query, webSearch, stormeistari) {
        var token = localStorage.getItem('alvitur_token') || '';
        if (statusArea) statusArea.textContent = 'Greini...';
        if (resultsArea) resultsArea.hidden = true;
        wsToggle.checked = false;
        smToggle.checked = false;
        approvalPanel.setAttribute('hidden','');
        fetch('/api/vitinn', {
            method: 'POST',
            headers: {'Content-Type':'application/json','Authorization':'Bearer '+token},
            body: JSON.stringify({query:query, web_search:webSearch, stormeistari:stormeistari})
        }).then(function(r){return r.json();}).then(function(data){
            if (statusArea) statusArea.textContent = '';
            if (data.success) {
                var s = data.sources || {};
                var badge = s.stormeistari ? '<span style="background:var(--color-accent-light);color:var(--color-accent);font-size:.7rem;padding:2px 8px;border-radius:99px;font-weight:500">Stórmeistari</span>'
                    : s.web_search ? '<span style="background:#e0f0ff;color:#0066cc;font-size:.7rem;padding:2px 8px;border-radius:99px;font-weight:500">+Vefur</span>'
                    : '<span style="background:#e6f4ea;color:#1a7a3c;font-size:.7rem;padding:2px 8px;border-radius:99px;font-weight:500">Sovereign</span>';
                var cits = (data.citations||[]).map(function(c){
                    return '<li style="font-size:.75rem;color:var(--color-text-muted);margin:.2rem 0">'+(c.citation_full||c.title||'')+'</li>';
                }).join('');
                resultsBody.innerHTML = '<div style="margin-bottom:.5rem">'+badge+'</div><p style="font-size:.875rem">'+data.response+'</p>'+(cits?'<ul style="padding-left:1rem;margin-top:.5rem">'+cits+'</ul>':'');
                resultsArea.hidden = false;
            } else {
                if (statusArea) statusArea.textContent = 'Villa: '+(data.error||'Óþekkt');
            }
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
