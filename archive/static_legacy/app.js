/* ═══════════════════════════════════════════
   Alvitur.is — Production Interactive Behaviors
   Tengist /api/chat (texti) og /api/analyze-document (skrár)
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  var tabGeneral = document.getElementById('tab-general');
  var tabConfidential = document.getElementById('tab-confidential');
  var trustStatement = document.getElementById('trust-statement');
  var intakeCard = document.getElementById('intake-card');
  var queryInput = document.getElementById('query-input');
  var fileTrigger = document.getElementById('file-trigger');
  var fileInput = document.getElementById('file-input');
  var attachedFile = document.getElementById('attached-file');
  var attachedName = document.getElementById('attached-name');
  var attachedSize = document.getElementById('attached-size');
  var removeFileBtn = document.getElementById('remove-file');
  var submitBtn = document.getElementById('submit-btn');
  var statusArea = document.getElementById('status-area');
  var resultsArea = document.getElementById('results-area');
  var resultsBody = document.getElementById('results-body');

  var currentFile = null;
  var currentMode = 'general';
  var busy = false;

  // ─── Tab toggle ───
  function setMode(mode) {
    currentMode = mode;
    [tabGeneral, tabConfidential].forEach(function (tab) {
      var isActive = tab.getAttribute('data-mode') === mode;
      tab.classList.toggle('intake-tab--active', isActive);
      tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });
    trustStatement.hidden = (mode !== 'confidential');
  }

  if (tabGeneral) tabGeneral.addEventListener('click', function () { setMode('general'); });
  if (tabConfidential) tabConfidential.addEventListener('click', function () { setMode('confidential'); });

  // ─── File handling ───
  var MAX_FILE_SIZE = 20 * 1024 * 1024;
  if (fileTrigger) fileTrigger.addEventListener('click', function () { fileInput.click(); });

  if (fileInput) {
    fileInput.addEventListener('change', function (e) {
      var file = e.target.files[0];
      if (file) handleFile(file);
    });
  }

  function handleFile(file) {
    clearStatus();
    var name = file.name.toLowerCase();
    var validTypes = ['.pdf', '.docx', '.xlsx', '.doc', '.xls'];
    var isValid = validTypes.some(function (ext) { return name.endsWith(ext); });
    if (!isValid) {
      showStatus('error', 'Skráargerð ekki studd. Styður PDF, Word og Excel.');
      fileInput.value = '';
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      showStatus('error', 'Skjalið er of stórt. Hámark 20 MB.');
      fileInput.value = '';
      return;
    }
    currentFile = file;
    attachedName.textContent = file.name;
    attachedSize.textContent = formatFileSize(file.size);
    attachedFile.hidden = false;
  }

  if (removeFileBtn) {
    removeFileBtn.addEventListener('click', function () {
      currentFile = null;
      fileInput.value = '';
      attachedFile.hidden = true;
      attachedName.textContent = '';
      attachedSize.textContent = '';
    });
  }

  function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  // ─── Submit handler ───
  if (submitBtn) {
    submitBtn.addEventListener('click', function () {
      if (busy) return;
      var query = queryInput ? queryInput.value.trim() : '';
      if (!query && !currentFile) {
        showStatus('error', 'Sláðu inn fyrirspurn eða hengdu við skjal.');
        return;
      }
      busy = true;
      submitBtn.disabled = true;
      if (resultsArea) resultsArea.hidden = true;
      showStatus('loading', 'Greining í gangi…');

      var isTextOnly = !currentFile;
      var endpoint = isTextOnly ? '/api/chat' : '/api/analyze-document';
      var tier = currentMode === 'confidential' ? 'vault' : 'general';

      var fetchOptions = {
        method: 'POST',
        headers: { 'X-Alvitur-Tier': tier }
      };

      if (isTextOnly) {
        fetchOptions.headers['Content-Type'] = 'application/json';
        fetchOptions.body = JSON.stringify({ query: query });
      } else {
        var fd = new FormData();
        fd.append('file', currentFile);
        if (query) fd.append('query', query);
        fetchOptions.body = fd;
      }

      var controller = new AbortController();
      fetchOptions.signal = controller.signal;
      var timeoutId = setTimeout(function () {
        controller.abort();
        busy = false;
        submitBtn.disabled = false;
        showStatus('error', 'Fyrirspurnin rann út á tíma. Reyndu aftur.');
      }, 180000);

      fetch(endpoint, fetchOptions)
        .then(function (r) {
          clearTimeout(timeoutId);
          if (!r.ok) return r.json().catch(function () { return {}; }).then(function (d) { throw { status: r.status, data: d }; });
          return r.json();
        })
        .then(function (d) {
          busy = false;
          submitBtn.disabled = false;
          clearStatus();
          showResults(d);
        })
        .catch(function (err) {
          clearTimeout(timeoutId);
          busy = false;
          submitBtn.disabled = false;
          if (err && err.name === 'AbortError') return;
          if (err && err.status) {
            var d = err.data || {};
            if (err.status === 422) {
              var em = d.error_code === 'no_text_extracted'
                ? 'Ekki tókst að lesa texta úr skjalinu. Reyndu annað skjal.'
                : (d.error || 'Villa við úrvinnslu. Reyndu aftur.');
              showStatus('error', em);
              return;
            }
            if (err.status === 413) { showStatus('error', 'Skráin er of stór. Hámark 20 MB.'); return; }
            if (err.status === 415) { showStatus('error', 'Ógild skráargerð.'); return; }
            if (err.status === 429) { showStatus('error', 'Of margar beiðnir. Reyndu aftur eftir stund.'); return; }
            showStatus('error', d.error || 'Villa í þjónustu. Reyndu aftur síðar.');
            return;
          }
          showStatus('error', 'Tenging mistókst. Athugaðu nettengingu og reyndu aftur.');
        });
    });
  }

  // ─── Enter key ───
  if (queryInput) {
    queryInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (submitBtn) submitBtn.click();
      }
    });
  }

  // ─── Status messages ───
  function showStatus(type, message) {
    if (!statusArea) return;
    var icon = type === 'loading' ? '<span class="spinner" aria-hidden="true"></span>' : '';
    statusArea.innerHTML = '<div class="status-message status-message--' + type + '">' + icon + '<span>' + message + '</span></div>';
  }

  function clearStatus() {
    if (statusArea) statusArea.innerHTML = '';
  }

  // ─── Show results ───
  var DOMAIN_LABELS = {
    'legal':    '📋 Lögfræðigreining',
    'finance':  '📊 Fjármálagreining',
    'writing':  '✏️ Ritvinnsla',
    'research': '🔍 Rannsókn',
    'general':  '💬 Almennt'
  };

  function showResults(data) {
    var html = '';
    if (data.domain && DOMAIN_LABELS[data.domain]) {
      html += '<div class="results-domain-tag">' + DOMAIN_LABELS[data.domain] + '</div>';
    }
    var txt = data.summary || data.response;
    if (txt) {
      html += '<div class="results-summary">' + formatSummary(txt) + '</div>';
    }
    if (data.citations && data.citations.length > 0) {
      html += '<div class="results-citations"><h4>Heimildir</h4><ul>';
      data.citations.forEach(function (c) {
        var label = c.title || c.url || String(c);
        var href = c.url || '#';
        var snippet = c.snippet ? '<br><small>' + escapeHtml(c.snippet.substring(0,120)) + '…</small>' : '';
        html += '<li><a href="' + escapeHtml(href) + '" target="_blank" rel="noopener">' + escapeHtml(label) + '</a>' + snippet + '</li>';
      });
      html += '</ul></div>';
    }
    if (data.filename) {
      html += '<p class="results-meta">Skjal: ' + escapeHtml(data.filename);
      if (data.sidur) html += ' (' + data.sidur + ' bls.)';
      html += '</p>';
    }
    if (!html) html = '<p>Engar niðurstöður fundust.</p>';
    if (resultsBody) resultsBody.innerHTML = html;
    if (resultsArea) resultsArea.hidden = false;
    if (resultsArea) resultsArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function formatSummary(text) {
    return text.split('\n').filter(function (line) { return line.trim(); }).map(function (line) { return '<p>' + escapeHtml(line) + '</p>'; }).join('');
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ─── Drag and drop ───
  var dragCounter = 0;
  if (intakeCard) {
    intakeCard.addEventListener('dragenter', function (e) { e.preventDefault(); dragCounter++; intakeCard.classList.add('intake-card--dragover'); });
    intakeCard.addEventListener('dragleave', function (e) { e.preventDefault(); dragCounter--; if (dragCounter <= 0) { dragCounter = 0; intakeCard.classList.remove('intake-card--dragover'); } });
    intakeCard.addEventListener('dragover', function (e) { e.preventDefault(); });
    intakeCard.addEventListener('drop', function (e) { e.preventDefault(); dragCounter = 0; intakeCard.classList.remove('intake-card--dragover'); var files = e.dataTransfer.files; if (files.length > 0) handleFile(files[0]); });
  }

  // ─── Smooth scroll ───
  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      var target = document.querySelector(link.getAttribute('href'));
      if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    });
  });

})();
