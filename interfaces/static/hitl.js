(function() {
  'use strict';

  // Nota localStorage beint - óháð app_v3.js
  function _hitlToken() {
    try { return localStorage.getItem('alvitur_token') || ''; } catch(e) { return ''; }
  }

  // Eigin escape - ekkert nafnaárekstur
  function _htEsc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g,'&amp;').replace(/</g,'&lt;')
      .replace(/>/g,'&gt;').replace(/"/g,'&quot;')
      .replace(/'/g,'&#39;');
  }

  var TIER = {
    1: {label:'Lítil áhætta',   bg:'#f0fdf4', border:'#16a34a', txt:'#14532d'},
    2: {label:'Miðlungs áhætta', bg:'#fffbeb', border:'#d97706', txt:'#78350f'},
    3: {label:'Há áhætta',       bg:'#fef2f2', border:'#dc2626', txt:'#7f1d1d'}
  };

  function _renderItem(item) {
    var t   = TIER[item.risk_tier] || TIER[1];
    var id  = _htEsc(item.id || item.item_id || '');
    var tol = _htEsc(item.tool_name || '');
    var pre = _htEsc(item.preview || '');
    var ts  = _htEsc(item.created_at || '');

    var h = '<div id="hi-' + id + '" style="background:' + t.bg + ';border:1.5px solid ' + t.border + ';border-radius:.625rem;padding:.75rem;display:flex;flex-direction:column;gap:.5rem;margin-bottom:.5rem">';
    h += '<div style="display:flex;justify-content:space-between;align-items:center">';
    h += '<strong style="font-size:.85rem;color:' + t.txt + '">' + tol + '</strong>';
    h += '<span style="font-size:.7rem;padding:2px 8px;border-radius:99px;background:' + t.border + ';color:#fff">' + t.label + '</span>';
    h += '</div>';
    if (pre) h += '<p style="font-size:.8rem;color:#64748b;margin:0;white-space:pre-wrap">' + pre + '</p>';
    if (ts)  h += '<p style="font-size:.7rem;color:#94a3b8;margin:0">Tími: ' + ts + '</p>';

    if (item.risk_tier === 3) {
      h += '<div style="display:flex;flex-direction:column;gap:.35rem;padding:.5rem;background:#fee2e2;border-radius:.375rem">';
      h += '<label style="font-size:.8rem;color:#7f1d1d;display:flex;align-items:center;gap:.4rem">';
      h += '<input type="checkbox" id="hr-' + id + '" style="margin:0"> Ég hef lesið og skilið aðgerðina</label>';
      h += '<label style="font-size:.8rem;color:#7f1d1d;display:flex;align-items:center;gap:.4rem">';
      h += '<input type="checkbox" id="hc-' + id + '" style="margin:0"> Ég samþykki að aðgerðin verði framkvæmd</label>';
      h += '</div>';
    }
    h += '<div style="display:flex;gap:.5rem">';
    h += '<button onclick="hitlApprove(\'' + id + '\',' + (item.risk_tier||1) + ')" style="flex:1;padding:.45rem;background:' + t.border + ';color:#fff;border:none;border-radius:.5rem;font-size:.82rem;cursor:pointer">Samþykkja</button>';
    h += '<button onclick="hitlReject(\'' + id + '\')" style="flex:1;padding:.45rem;background:none;border:1.5px solid ' + t.border + ';color:' + t.txt + ';border-radius:.5rem;font-size:.82rem;cursor:pointer">Hafna</button>';
    h += '</div>';
    h += '</div>';
    return h;
  }

  function _showPanel(items) {
    var panel = document.getElementById('hitl-panel');
    var box   = document.getElementById('hitl-items');
    if (!panel || !box) return;
    if (!items || items.length === 0) {
      panel.hidden = true;
      panel.style.display = 'none';
      box.innerHTML = '';
      return;
    }
    box.innerHTML = items.map(_renderItem).join('');
    panel.hidden = false;
    panel.style.display = 'flex';
  }

  function _poll() {
    var tok = _hitlToken();
    if (!tok) return;
    fetch('/api/hitl/queue', {
      headers: {'Authorization': 'Bearer ' + tok}
    }).then(function(r) {
      return r.ok ? r.json() : null;
    }).then(function(d) {
      if (d && d.items) _showPanel(d.items);
    }).catch(function() {});
  }

  // Opinber föll — kallað úr onclick í HTML
  window.hitlApprove = function(id, tier) {
    if (tier === 3) {
      var r = document.getElementById('hr-' + id);
      var c = document.getElementById('hc-' + id);
      if (!r || !r.checked || !c || !c.checked) {
        alert('Þú verður að haka við báðar staðfestingar fyrir há-áhættu aðgerð.');
        return;
      }
    }
    var tok = _hitlToken();
    if (!tok) return;
    fetch('/api/hitl/approve/' + encodeURIComponent(id), {
      method: 'POST',
      headers: {'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'}
    }).then(function(r) { return r.json(); }).then(function() {
      var el = document.getElementById('hi-' + id);
      if (el) el.remove();
      _poll();
    }).catch(function() {});
  };

  window.hitlReject = function(id) {
    var tok = _hitlToken();
    if (!tok) return;
    fetch('/api/hitl/reject/' + encodeURIComponent(id), {
      method: 'POST',
      headers: {'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'}
    }).then(function(r) { return r.json(); }).then(function() {
      var el = document.getElementById('hi-' + id);
      if (el) el.remove();
      _poll();
    }).catch(function() {});
  };

  // Byrja polling 3 sek eftir load - app_v3.js þarf tíma til að ræsast
  setTimeout(function() {
    try { _poll(); } catch(e) {}
    setInterval(function() { try { _poll(); } catch(e) {} }, 10000);
  }, 3000);

})();
