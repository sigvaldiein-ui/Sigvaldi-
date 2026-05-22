/* ═══════════════════════════════════════════
   Alvitur.is — Production Interactive Behaviors
   Tengist /api/chat (texti) og /api/analyze-document (skrár)
   Sprint 87.5: Vitinn + Hvelfingin + Starfsmaður
   ═══════════════════════════════════════════ */

(function () {
  'use strict';

  var tabGeneral = document.getElementById('tab-general');
  var tabConfidential = document.getElementById('tab-confidential');
  var tabEmployee = document.getElementById('tab-employee');
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
    var allTabs = [tabGeneral, tabConfidential, tabEmployee];
    allTabs.forEach(function (tab) {
      if (!tab) return;
      var isActive = tab.getAttribute('data-mode') === mode;
      tab.classList.toggle('intake-tab--active', isActive);
      tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    // Ef Starfsmaður: fela spjallborð, birta biðlistaform
    var employeePanel = document.getElementById('employee-panel');
    if (mode === 'employee') {
      if (intakeCard) intakeCard.style.display = 'none';
      if (employeePanel) employeePanel.hidden = false;
      if (trustStatement) trustStatement.hidden = true;
    } else {
      if (intakeCard) intakeCard.style.display = '';
      if (employeePanel) employeePanel.hidden = true;
      if (trustStatement) trustStatement.hidden = (mode !== 'confidential');
    }
  }

  if (tabGeneral) tabGeneral.addEventListener('click', function () { setMode('general'); });
  if (tabConfidential) tabConfidential.addEventListener('click', function () { setMode('confidential'); });
  if (tabEmployee) tabEmployee.addEventListener('click', function () { setMode('employee'); });

  // ─── Biðlisti (Starfsmaður) ───
  var employeeForm = document.getElementById('employee-form');
  var employeeName = document.getElementById('employee-name');
  var employeeEmail = document.getElementById('employee-email');
  var employeeSubmit = document.getElementById('employee-submit');
  var employeeSuccess = document.getElementById('employee-success');

  if (employeeSubmit) {
    employeeSubmit.addEventListener('click', function () {
      if (busy) return;
      busy = true;
      var name = employeeName ? employeeName.value.trim() : '';
      var email = employeeEmail ? employeeEmail.value.trim() : '';
      if (!name || !email) {
        employeeSuccess.textContent = 'Vinsamlegast fylltu út bæði nafn og netfang.';
        busy = false;
        return;
      }
      fetch('/api/waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, email: email })
      })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data && data.status === 'success') {
          employeeSuccess.textContent = 'Takk fyrir! Þú ert skráð(ur) á biðlistann.';
        } else {
          employeeSuccess.textContent = 'Villa kom upp. Vinsamlegast reyndu aftur síðar.';
        }
      })
      .catch(function () {
        employeeSuccess.textContent = 'Villa kom upp. Vinsamlegast reyndu aftur síðar.';
      })
      .finally(function () { busy = false; });
    });
  }

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
    var validTypes = ['.pdf', '.docx', '.xlsx', '.doc', '.xls', '.txt'];
    var isValid = validTypes.some(function (ext) { return name.endsWith(ext); });
    if (!isValid) {
      showStatus('error', 'Skráargerð ekki studd. Styður PDF, DOCX, XLSX, TXT og skjáskot.');
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
      showStatus('loading', 'Greining í gangi…');
      var formData = new FormData();
      formData.append('tier', currentMode);
      formData.append('query', query);
      if (currentFile) formData.append('file', currentFile);
      fetch('/api/analyze-document', { method: 'POST', body: formData })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          showResults(data);
          clearFile();
        })
        .catch(function (err) {
          if (r.status === 202) {
                    r.json().then(function(d) {
                        showStatus('info', '⭐ Beiðni send í samþykktarferli. Tilvísun: ' + (d.approval_id || ''));
                    });
                } else {
                    showStatus('error', 'Villa kom upp: ' + (err.message || 'Netsamband rofið.'));
                }
        })
        .finally(function () { busy = false; });
    });
  }

  function showStatus(type, message) {
    if (!statusArea) return;
    var icon = '';
    if (type === 'error') icon = '⚠️ ';
    if (type === 'loading') icon = '⏳ ';
    statusArea.innerHTML = '<div class="status-message status-message--' + type + '">' + icon + '<span>' + message + '</span></div>';
  }

  function clearStatus() {
    if (statusArea) statusArea.innerHTML = '';
  }

  function showResults(data) {
    if (!resultsArea || !resultsBody) return;
    resultsArea.hidden = false;
    var citations = data.citations || [];
    var html = '';
    html += '<div class="results-response">' + escapeHtml(data.response || '') + '</div>';
    if (citations.length > 0) {
      html += '<div class="results-citations"><h4>Heimildir</h4><ul>';
      citations.forEach(function (c) {
        html += '<li><a href="' + escapeHtml(c.url || '#') + '" target="_blank" rel="noopener">' + escapeHtml(c.title || c.url || 'Heimild') + '</a></li>';
      });
      html += '</ul></div>';
    }
    resultsBody.innerHTML = html;
  }

  function clearFile() {
    currentFile = null;
    fileInput.value = '';
    attachedFile.hidden = true;
    attachedName.textContent = '';
    attachedSize.textContent = '';
  }

  function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Set initial mode
  if (tabGeneral && tabGeneral.classList.contains('intake-tab--active')) {
    setMode('general');
  } else if (tabConfidential && tabConfidential.classList.contains('intake-tab--active')) {
    setMode('confidential');
  } else {
    setMode('general');
  }
})();
