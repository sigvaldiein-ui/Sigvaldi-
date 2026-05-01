/* ═══════════════════════════════════════════
   Alvitur.is — Production Interactive Behaviors
   Tengist /api/analyze-document endpoint
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  // ─── DOM refs ───
  var cardVitinn = document.getElementById('card-vitinn');
  var cardHvelfing = document.getElementById('card-hvelfing');
  var trustStatementVitinn = document.getElementById('trust-statement-vitinn');
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
    var cards = [cardVitinn, cardHvelfing];
    cards.forEach(function (card) {
      var isActive = card.getAttribute('data-mode') === mode;
      if (isActive) {
        card.classList.add('intake-card-option--active');
        card.setAttribute('aria-checked', 'true');
      } else {
        card.classList.remove('intake-card-option--active');
        card.setAttribute('aria-checked', 'false');
      }
    });
    if (mode === 'confidential') {
      trustStatement.hidden = false;
      trustStatementVitinn.hidden = true;
    } else {
      trustStatement.hidden = true;
      trustStatementVitinn.hidden = false;
    }
  }

  cardVitinn.addEventListener('click', function () { setMode('general'); });
  cardHvelfing.addEventListener('click', function () { setMode('confidential'); });

  // Keyboard nav between cards
  [cardVitinn, cardHvelfing].forEach(function (tab, i, tabs) {
    tab.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        e.preventDefault();
        var next = e.key === 'ArrowRight' ? tabs[(i + 1) % tabs.length] : tabs[(i - 1 + tabs.length) % tabs.length];
        next.focus();
        next.click();
      }
    });
  });

  // ─── File handling ───
  var MAX_FILE_SIZE = 20 * 1024 * 1024; // 20 MB

  fileTrigger.addEventListener('click', function () { fileInput.click(); });

  fileInput.addEventListener('change', function (e) {
    var file = e.target.files[0];
    if (file) handleFile(file);
  });

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

  function removeFile() {
    currentFile = null;
    fileInput.value = '';
    attachedFile.hidden = true;
    attachedName.textContent = '';
    attachedSize.textContent = '';
  }

  removeFileBtn.addEventListener('click', removeFile);

  function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  // ─── Drag and drop ───
  var dragCounter = 0;

  intakeCard.addEventListener('dragenter', function (e) {
    e.preventDefault();
    dragCounter++;
    intakeCard.classList.add('intake-card--dragover');
  });

  intakeCard.addEventListener('dragleave', function (e) {
    e.preventDefault();
    dragCounter--;
    if (dragCounter <= 0) {
      dragCounter = 0;
      intakeCard.classList.remove('intake-card--dragover');
    }
  });

  intakeCard.addEventListener('dragover', function (e) { e.preventDefault(); });

  intakeCard.addEventListener('drop', function (e) {
    e.preventDefault();
    dragCounter = 0;
    intakeCard.classList.remove('intake-card--dragover');
    var files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
  });

  // ─── Status messages ───
  function showStatus(type, message) {
    var icon = '';
    if (type === 'loading') {
      icon = '<span class="spinner" aria-hidden="true"></span>';
    }
    statusArea.innerHTML = '<div class="status-message status-message--' + type + '">' + icon + '<span>' + message + '</span></div>';
  }

  function clearStatus() {
    statusArea.innerHTML = '';
  }

  // ─── Submit — real API call ───
  submitBtn.addEventListener('click', function () {
    if (busy) return;

    var query = queryInput.value.trim();
    if (!query && !currentFile) {
      showStatus('error', 'Sláðu inn fyrirspurn eða hengdu við skjal.');
      return;
    }

  var currentController = null;
    if (currentController) { try { currentController.abort(); } catch (e) {} }
    var ctrl = new AbortController();
    currentController = ctrl;
    busy = true;
    submitBtn.disabled = true;
    resultsArea.hidden = true;
    showStatus('loading', 'Greining í gangi\u2026');

    var fd = new FormData();
    if (currentFile) fd.append('file', currentFile);
    if (query) fd.append('query', query);

    var tier = currentMode === 'confidential' ? 'vault' : 'general';

    var timeoutId = setTimeout(function () {
      ctrl.abort();
      busy = false;
      submitBtn.disabled = false;
      currentController = null;
      showStatus('error', 'Fyrirspurnin rann út á tíma. Reyndu aftur.');
    }, 180000);

    fetch('/api/analyze-document', {
      method: 'POST',
      body: fd,
      headers: { 'X-Alvitur-Tier': tier },
      signal: ctrl.signal
    })
    .then(function (r) {
      clearTimeout(timeoutId);
      if (!r.ok) {
        return r.json().catch(function () { return {}; }).then(function (d) {
          throw { status: r.status, data: d };
        });
      }
      return r.json();
    })
    .then(function (d) {
      busy = false;
      submitBtn.disabled = false;
      currentController = null;
      clearStatus();
      showResults(d);
    })
    .catch(function (err) {
      clearTimeout(timeoutId);
      busy = false;
      submitBtn.disabled = false;
      clearStatus();
      resultsArea.hidden = false;
      if (currentController === ctrl) { currentController = null; }

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

  // ─── Show results ───
  // Sprint 47: domain label map
  var DOMAIN_LABELS = {
    'legal':    '\uD83D\uDCCB Lögfræðigreining',
    'finance':  '\uD83D\uDCCA Fjármálagreining',
    'writing':  '\u270D\uFE0F Ritvinnsla',
    'research': '\uD83D\uDD0D Rannsókn',
    'general':  '\uD83D\uDCAC Almennt'
  };

  function showResults(data) {
    var html = '';

    if (data.domain && DOMAIN_LABELS[data.domain]) {
      html += '<div class="results-domain-tag">' + DOMAIN_LABELS[data.domain] + '</div>';
    }

    // Sprint 63 Fasa 0.3c: robust — accept both 'summary' (text-only) and 'response' (file-upload)
    var _txt = data.summary || data.response;
    if (_txt) {
      html += '<div class="results-summary">' + formatSummary(_txt) + '</div>';
    }

    if (data.citations && data.citations.length > 0) {
      html += '<div class="results-citations"><h4>Heimildir</h4><ul>';
      data.citations.forEach(function (c) {
        html += '<li>' + escapeHtml(c) + '</li>';
      });
      html += '</ul></div>';
    }

    if (data.filename) {
      html += '<p class="results-meta">Skjal: ' + escapeHtml(data.filename);
      if (data.sidur) html += ' (' + data.sidur + ' bls.)';
      html += '</p>';
    }

    var ragIndicator = buildPipelineIndicator(data.pipeline_source, data.rag_metadata);
    if (ragIndicator) {
      html += '<div class="rag-indicator ' + ragIndicator.className + '">' +
              '<span class="rag-icon">' + ragIndicator.icon + '</span> ' +
              '<span class="rag-label">' + escapeHtml(ragIndicator.label) + '</span>' +
              '</div>';
    }

    if (!html) {
      html = '<p>Engar niðurstöður fundust.</p>';
    }

    resultsBody.innerHTML = html;
    resultsArea.hidden = false;
    resultsArea.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function formatSummary(text) {
    return text
      .split(/\r?\n/)
      .filter(function (line) { return line.trim(); })
      .map(function (line) { return '<p>' + escapeHtml(line) + '</p>'; })
      .join('');
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ─── Smooth scroll for CTA ───
  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      var target = document.querySelector(link.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

})();

// Sprint 70 Track E — RAG pipeline indicator
function buildPipelineIndicator(pipelineSource, ragMetadata) {
    if (!pipelineSource) return null;
    if (pipelineSource.startsWith('rag_grounded')) {
        var meta = ragMetadata || {};
        var count = meta.chunks_count || 0;
        var label = 'Sótti ' + count + ' málsgreinar úr íslenskum lögum';
        if (meta.source_laws && meta.source_laws.length) {
            label += ' — ' + meta.source_laws.join(', ');
        }
        if (meta.low_confidence) {
            label += ' (lág sannfæring)';
            return { icon: '⚠️', label: label, className: 'rag-indicator--warning' };
        }
        return { icon: '📚', label: label, className: 'rag-indicator--grounded' };
    }
    if (pipelineSource.startsWith('rag_refusal')) {
        return { icon: '🚫', label: 'Engin lagatilvitnun fannst í gagnagrunni Alvitur', className: 'rag-indicator--refusal' };
    }
    if (pipelineSource === 'rag_fallback_general') {
        return { icon: '⚠️', label: 'Engin lagatilvitnun — almennt svar', className: 'rag-indicator--fallback' };
    }
    return null;
}
