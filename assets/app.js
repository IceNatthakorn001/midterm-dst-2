(function () {
  var root = document.documentElement;
  var BASE = window.SN_BASE || '';
  var PKEY = 'sn-progress';

  // ---------- progress store: {v: {"subj/lesson": 1}, last: {u, t, s}} ----------
  function load() {
    var d;
    try { d = JSON.parse(localStorage.getItem(PKEY) || '{}'); } catch (e) { d = {}; }
    d.v = d.v || {};
    // migrate the old ITDS211-only store once
    try {
      var old = localStorage.getItem('itds211-progress');
      if (old && !d.m) {
        var o = JSON.parse(old);
        Object.keys(o.v || {}).forEach(function (k) { d.v['architecture/' + k] = 1; });
        if (!d.last && o.last && o.last.h) d.last = { u: 'architecture/' + o.last.h, t: o.last.t, s: 'ITDS211' };
        d.m = 1; save(d);
      }
    } catch (e) {}
    return d;
  }
  function save(d) { try { localStorage.setItem(PKEY, JSON.stringify(d)); } catch (e) {} }
  window.SNStore = { load: load, save: save };

  // lesson pages record themselves
  if (window.SN_TRACK) {
    var d0 = load(), tr = window.SN_TRACK;
    d0.v[tr.k] = 1;
    d0.last = { u: tr.u, t: tr.t, s: tr.s };
    save(d0);
  }

  // "continue reading" banner (home + subject pages)
  var cont = document.getElementById('cont');
  function paintContinue() {
    if (!cont) return;
    var d = load(), last = d.last;
    if (!last || !last.u) return;
    if (window.SN_SUBJ && last.u.indexOf(window.SN_SUBJ + '/') !== 0) return;
    cont.href = BASE + last.u;
    document.getElementById('contTitle').textContent = (last.s && !window.SN_SUBJ ? last.s + ' · ' : '') + last.t;
    cont.hidden = false;
  }
  paintContinue();

  // home: per-subject progress bars
  function paintHome() {
    if (!window.SN_LESSONS) return;
    var v = load().v;
    document.querySelectorAll('.subject-card[data-subj]').forEach(function (c) {
      var list = window.SN_LESSONS[c.dataset.subj] || [];
      if (!list.length) return;
      var n = list.filter(function (s) { return v[c.dataset.subj + '/' + s]; }).length;
      var box = c.querySelector('.sc-progress');
      if (!n || !box) return;
      box.hidden = false;
      box.querySelector('i').style.width = Math.round(n / list.length * 100) + '%';
      box.querySelector('span').textContent = 'เปิดอ่านแล้ว ' + n + '/' + list.length + ' บท';
    });
  }
  paintHome();
  addEventListener('pageshow', function () { paintContinue(); paintHome(); });

  // ---------- theme ----------
  var themeBtn = document.getElementById('themeBtn');
  if (themeBtn) themeBtn.addEventListener('click', function () {
    var next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('theme', next); } catch (e) {}
  });

  // ---------- reading progress ----------
  var bar = document.getElementById('progress');
  if (bar && document.body.classList.contains('is-lesson')) {
    var onScroll = function () {
      var h = document.documentElement.scrollHeight - innerHeight;
      bar.style.width = (h > 0 ? Math.min(100, scrollY / h * 100) : 0) + '%';
    };
    addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // ---------- lesson list collapse (desktop) ----------
  function setNav(hidden) {
    root.classList.toggle('nav-hidden', hidden);
    try { localStorage.setItem('sn-nav', hidden ? '0' : '1'); } catch (e) {}
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('[data-nav-toggle]');
    if (b) setNav(!root.classList.contains('nav-hidden'));
  });
  var lcur = document.querySelector('.lnav li.cur');
  if (lcur && lcur.offsetParent) {
    var ln = document.querySelector('.lnav');
    ln.scrollTop = lcur.offsetTop - ln.clientHeight / 3;
  }

  // ---------- section sheet (mobile) ----------
  function sheet(open) { document.body.classList.toggle('sheet-open', open); }
  [['sheetBtn', true], ['sheetClose', false], ['sheetBackdrop', false]].forEach(function (x) {
    var el = document.getElementById(x[0]);
    if (el) el.addEventListener('click', function () { sheet(x[1]); });
  });
  var topBtn = document.getElementById('topBtn');
  if (topBtn) topBtn.addEventListener('click', function () { scrollTo({ top: 0, behavior: 'smooth' }); });

  // ---------- "on this page" highlight ----------
  var toc = document.getElementById('toc');
  var links = toc ? Array.prototype.slice.call(toc.querySelectorAll('ol a')) : [];
  links.forEach(function (a) { a.addEventListener('click', function () { sheet(false); }); });
  if (links.length && 'IntersectionObserver' in window) {
    var map = {};
    links.forEach(function (a) { map[decodeURIComponent(a.hash.slice(1))] = a; });
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var a = map[en.target.id];
        if (en.isIntersecting && a) {
          links.forEach(function (l) { l.classList.remove('active'); });
          a.classList.add('active');
          if (innerWidth >= 900) {
            var box = toc.getBoundingClientRect(), r = a.getBoundingClientRect();
            if (r.top < box.top || r.bottom > box.bottom) toc.scrollTop += r.top - box.top - 80;
          }
        }
      });
    }, { rootMargin: '-70px 0px -70% 0px' });
    document.querySelectorAll('.prose h2[id]').forEach(function (h) { obs.observe(h); });
  }

  // ---------- quiz menus: close when clicking elsewhere ----------
  document.addEventListener('click', function (e) {
    document.querySelectorAll('details.qm[open]').forEach(function (d) { if (!d.contains(e.target)) d.open = false; });
  });

  // ---------- image lightbox ----------
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (t.tagName === 'IMG' && t.closest('.prose')) {
      var lb = document.createElement('div');
      lb.className = 'lightbox';
      var img = document.createElement('img');
      img.src = t.src; img.alt = t.alt;
      lb.appendChild(img);
      lb.addEventListener('click', function () { lb.remove(); });
      document.body.appendChild(lb);
    }
  });

  // ---------- keyboard ----------
  document.addEventListener('keydown', function (e) {
    var tag = (e.target.tagName || '').toUpperCase();
    var typing = tag === 'INPUT' || tag === 'TEXTAREA';
    if (e.key === 'Escape') {
      var lb = document.querySelector('.lightbox'); if (lb) lb.remove();
      sheet(false);
    }
    if (typing || e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key === '[' && document.querySelector('.lnav')) setNav(!root.classList.contains('nav-hidden'));
    if (e.key === '/') {
      var box = document.getElementById('q') || document.getElementById('sq');
      if (box) { e.preventDefault(); box.focus(); }
    }
  });

  // ---------- home search ----------
  var q = document.getElementById('q'), results = document.getElementById('results');
  if (q && results && window.SEARCH_INDEX) {
    var render = function () {
      var term = q.value.trim().toLowerCase();
      results.innerHTML = '';
      if (!term) return;
      var hits = [];
      window.SEARCH_INDEX.forEach(function (l) {
        if (l.t.toLowerCase().indexOf(term) !== -1) hits.push({ l: l, h: null });
        l.h.forEach(function (h) { if (h && h.toLowerCase().indexOf(term) !== -1) hits.push({ l: l, h: h }); });
      });
      hits.slice(0, 30).forEach(function (x) {
        var li = document.createElement('li'), a = document.createElement('a');
        a.href = x.l.u;
        a.textContent = x.h || x.l.t;
        var small = document.createElement('small');
        small.textContent = x.l.s + ' · ' + x.l.t;
        a.appendChild(small);
        li.appendChild(a); results.appendChild(li);
      });
      if (!hits.length) results.innerHTML = '<li><a>ไม่พบหัวข้อที่ค้นหา ลองคำอื่นดูนะ</a></li>';
    };
    q.addEventListener('input', render);
    q.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { q.value = ''; render(); q.blur(); }
      if (e.key === 'ArrowDown') { var f = results.querySelector('a[href]'); if (f) { e.preventDefault(); f.focus(); } }
    });
    results.addEventListener('keydown', function (e) {
      var items = Array.prototype.slice.call(results.querySelectorAll('a[href]'));
      var i = items.indexOf(document.activeElement);
      if (e.key === 'ArrowDown' && i < items.length - 1) { e.preventDefault(); items[i + 1].focus(); }
      if (e.key === 'ArrowUp') { e.preventDefault(); (i > 0 ? items[i - 1] : q).focus(); }
    });
  }
})();
