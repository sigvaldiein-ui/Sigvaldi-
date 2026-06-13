(function(){
  function $(id){ return document.getElementById(id); }
  var msg = $('msg');

  function switchTab(which){
    $('tab-magic').classList.toggle('tab--active', which==='magic');
    $('tab-token').classList.toggle('tab--active', which==='token');
    $('panel-magic').classList.toggle('panel--active', which==='magic');
    $('panel-token').classList.toggle('panel--active', which==='token');
    msg.textContent='';
  }

  function sendMagic(){
    var email = $('email').value.trim();
    var btn = $('magic-btn');
    if (!email || email.indexOf('@')<0){ msg.className='msg err'; msg.textContent='Sláðu inn gilt netfang'; return; }
    btn.disabled = true;
    fetch('/api/auth/magic/request', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({email: email})
    }).then(function(r){ return r.json(); }).then(function(){
      msg.className='msg info';
      msg.textContent='Ef netfangið er skráð hefur þú fengið sendan innskráningartengil. Athugaðu pósthólfið.';
      btn.disabled = false;
    }).catch(function(){
      msg.className='msg err'; msg.textContent='Villa kom upp. Reyndu aftur.';
      btn.disabled = false;
    });
  }

  function loginToken(){
    var t = $('t').value.trim();
    if (!t){ msg.className='msg err'; msg.textContent='Límdu aðgangslykil í reitinn'; return; }
    try {
      var p = JSON.parse(atob(t.split('.')[1]));
      if (p.exp && p.exp < Math.floor(Date.now()/1000)){ msg.className='msg err'; msg.textContent='Aðgangslykill er útrunninn.'; return; }
      localStorage.setItem('alvitur_token', t);
      msg.className='msg ok'; msg.textContent='Innskráning tókst. Flyt á Vitann...';
      setTimeout(function(){ location.href='/'; }, 1000);
    } catch(e){ msg.className='msg err'; msg.textContent='Ógilt snið á aðgangslykli.'; }
  }

  $('tab-magic').addEventListener('click', function(){ switchTab('magic'); });
  $('tab-token').addEventListener('click', function(){ switchTab('token'); });
  $('magic-btn').addEventListener('click', sendMagic);
  $('token-btn').addEventListener('click', loginToken);

  // Magic-link verify ur URL
  var token = new URLSearchParams(window.location.search).get('token');
  if (token){
    msg.className='msg info'; msg.textContent='Staðfesti innskráningartengil...';
    fetch('/api/auth/magic/verify?token=' + encodeURIComponent(token))
      .then(function(r){ if(!r.ok) throw new Error('401'); return r.json(); })
      .then(function(data){
        if (data.access_token){
          localStorage.setItem('alvitur_token', data.access_token);
          msg.className='msg ok'; msg.textContent='Innskráning tókst. Flyt á Vitann...';
          setTimeout(function(){ location.href='/'; }, 1000);
        } else { throw new Error('no token'); }
      })
      .catch(function(){
        msg.className='msg err'; msg.textContent='Innskráningartengill er ógildur eða útrunninn.';
      });
  }
})();
