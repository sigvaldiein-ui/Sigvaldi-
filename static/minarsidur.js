// minarsidur.js v1 — Minimal web chat (engin markdown parsing)
// Alvitur ehf — Sprint 16
console.log('minarsidur.js v1 loaded successfully');

document.addEventListener('DOMContentLoaded', function() {
  var chatHistory = document.getElementById('chat-history');
  var chatForm = document.getElementById('chat-form');
  var chatInput = document.getElementById('chat-input');
  var sendBtn = document.getElementById('send-btn');
  var sending = false;

  function scrollDown() {
    chatHistory.scrollTop = chatHistory.scrollHeight;
  }

  function addMsg(text, isUser) {
    var div = document.createElement('div');
    div.style.cssText = isUser
      ? 'text-align:right;margin:8px 0;'
      : 'text-align:left;margin:8px 0;';

    var bubble = document.createElement('div');
    bubble.style.cssText = isUser
      ? 'display:inline-block;background:#3730A3;color:#fff;padding:10px 14px;border-radius:12px 0 12px 12px;max-width:80%;text-align:left;'
      : 'display:inline-block;background:#1a1f2e;border:1px solid #2d3348;color:#e2e8f0;padding:10px 14px;border-radius:0 12px 12px 12px;max-width:80%;text-align:left;';

    bubble.textContent = text;
    div.appendChild(bubble);
    chatHistory.appendChild(div);
    scrollDown();
    return bubble;
  }

  function addLoading() {
    var div = document.createElement('div');
    div.style.cssText = 'text-align:left;margin:8px 0;';
    var bubble = document.createElement('div');
    bubble.style.cssText = 'display:inline-block;background:#1a1f2e;border:1px solid #2d3348;color:#818cf8;padding:10px 14px;border-radius:0 12px 12px 12px;';
    bubble.textContent = 'Alvitur hugsar...';
    bubble.id = 'loading-msg';
    div.appendChild(bubble);
    div.id = 'loading-row';
    chatHistory.appendChild(div);
    scrollDown();
  }

  function removeLoading() {
    var el = document.getElementById('loading-row');
    if (el) el.remove();
  }

  async function doSend() {
    if (sending) return;
    var text = chatInput.value.trim();
    if (!text) return;

    sending = true;
    sendBtn.disabled = true;
    chatInput.value = '';

    addMsg(text, true);
    addLoading();

    try {
      var resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, user_id: 'web_user' })
      });

      removeLoading();

      if (resp.ok) {
        var data = await resp.json();
        addMsg(data.response || 'Ekkert svar.', false);
      } else {
        addMsg('Villa: ' + resp.status, false);
      }
    } catch (err) {
      removeLoading();
      addMsg('Tengivilla. Reyndu aftur.', false);
    }

    sending = false;
    sendBtn.disabled = false;
    chatInput.focus();
  }

  // Form submit
  chatForm.addEventListener('submit', function(e) {
    e.preventDefault();
    doSend();
  });

  // Enter sendir
  chatInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      doSend();
    }
  });

  // Click
  sendBtn.addEventListener('click', function(e) {
    e.preventDefault();
    doSend();
  });

  // Velkomin
  addMsg('Velkomin! Ég er Alvitur, íslenskur gervigreindaraðstoðarmaður. Spyrðu mig um skjalagreiningu, lögfræði eða fjárhag.', false);
});
