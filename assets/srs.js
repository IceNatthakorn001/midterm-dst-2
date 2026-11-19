// Spaced-repetition hub for quiz-pro sets (skills/quiztest/template_pro.html).
// Every quiz-pro page stores its Leitner boxes in localStorage under 'sn-srs:<bank id>'
// ({v, items: {qid: {b, d, n, w, l, c, r}}, ...}); all pages share one origin on the site,
// so this file can count what is due today across every set listed in window.SN_SRS (srs-catalog.js).
//  - home / subject page: the "ทบทวนที่ถึงรอบ" banner (#srsDue)
//  - review.html: the list of every set + "start reviewing" (#srsList)
//  - quiz-pro pages opened with #sn-due[=<subject>|all]: start the due mode, then offer the next set
(function () {
  var CAT = window.SN_SRS || [];
  var BASE = window.SN_BASE || '';
  var pad = function (n) { return (n < 10 ? '0' : '') + n; };
  var iso = function (d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); };
  function today() { // same rule as the quiz: #today=YYYY-MM-DD simulates another day (testing)
    var m = /today=(\d{4}-\d{2}-\d{2})/.exec(location.hash);
    return m ? m[1] : iso(new Date());
  }
  var TH_MON = ['ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.', 'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.'];
  function thDate(s) { var p = s.split('-').map(Number); return p[2] + ' ' + TH_MON[p[1] - 1]; }
  function dayDiff(a, b) {
    var pa = a.split('-').map(Number), pb = b.split('-').map(Number);
    return Math.round((new Date(pb[0], pb[1] - 1, pb[2]) - new Date(pa[0], pa[1] - 1, pa[2])) / 864e5);
  }
  function rel(s) {
    var n = dayDiff(today(), s);
    return n <= 0 ? 'วันนี้' : n === 1 ? 'พรุ่งนี้' : 'อีก ' + n + ' วัน (' + thDate(s) + ')';
  }
  function read(id) {
    try { var v = JSON.parse(localStorage.getItem('sn-srs:' + id) || 'null'); return v && v.items ? v : null; } catch (e) { return null; }
  }
  function status(e) {
    var S = read(e.id), t = today(), due = 0, seen = 0, next = null;
    if (S) Object.keys(S.items).forEach(function (k) {
      var it = S.items[k]; if (!it || !it.d) return;
      seen++;
      if (it.d <= t) due++; else if (!next || it.d < next) next = it.d;
    });
    return { due: due, seen: seen, total: e.n || seen, next: next, started: seen > 0 };
  }
  function list(subj) {
    return CAT.filter(function (e) { return !subj || subj === 'all' || e.s === subj; })
      .map(function (e) { var s = status(e); s.e = e; return s; });
  }
  function sum(rows) {
    var r = { due: 0, sets: 0, started: 0, next: null, n: rows.length };
    rows.forEach(function (x) {
      r.due += x.due; if (x.due) r.sets++; if (x.started) r.started++;
      if (x.next && (!r.next || x.next < r.next)) r.next = x.next;
    });
    return r;
  }
  // links carry the #today= test hook along so a simulated day survives the hand-off
  var href = function (e, tag) {
    var tm = /today=\d{4}-\d{2}-\d{2}/.exec(location.hash), h = [];
    if (tag) h.push('sn-due=' + tag);
    if (tm) h.push(tm[0]);
    return BASE + e.u + (h.length ? '#' + h.join('&') : '');
  };
  var rv = function (subj) {
    var tm = /today=\d{4}-\d{2}-\d{2}/.exec(location.hash), h = [];
    if (subj) h.push('s=' + subj);
    if (tm) h.push(tm[0]);
    return BASE + 'review.html' + (h.length ? '#' + h.join('&') : '');
  };
  window.SNSrs = { status: status, list: list, sum: sum, today: today };
  if (!CAT.length) return;

  // ---------- home / subject banner ----------
  var box = document.getElementById('srsDue');
  function paintBox() {
    if (!box) return;
    var subj = box.dataset.subj || '';
    var rows = list(subj), s = sum(rows);
    if (!rows.length) { box.hidden = true; return; }
    var strong = box.querySelector('strong'), small = box.querySelector('small'), n = box.querySelector('.srs-n');
    box.classList.toggle('is-due', s.due > 0);
    if (s.due) {
      strong.textContent = 'วันนี้ถึงรอบ ' + s.due + ' ข้อ จาก ' + s.sets + ' ชุด';
      small.textContent = 'ทบทวนตามรอบ · Quiz Pro';
      n.textContent = 'เริ่ม →';
      var first = rows.filter(function (x) { return x.due; })[0].e;
      box.href = href(first, subj || 'all');
    } else {
      small.textContent = 'ทบทวนตามรอบ · Quiz Pro ' + rows.length + ' ชุด';
      strong.textContent = s.started ? 'ยังไม่มีข้อถึงรอบวันนี้' + (s.next ? ' · รอบถัดไป' + (rel(s.next) === 'พรุ่งนี้' ? 'พรุ่งนี้' : ' ' + rel(s.next)) : '')
        : 'ทำ Quiz Pro ครั้งแรกแล้วระบบจะนัดวันทวนให้';
      n.textContent = 'ดูทั้งหมด';
      box.href = rv(subj);
    }
    box.hidden = false;
  }
  paintBox();
  addEventListener('pageshow', paintBox);

  // ---------- review.html ----------
  var host = document.getElementById('srsList');
  function paintReview() {
    if (!host) return;
    var m = /(?:^|[#&])s=([\w-]+)/.exec(location.hash), only = m ? m[1] : '';
    var rows = list(), s = sum(rows);
    var tot = document.getElementById('srsTotal'), start = document.getElementById('srsStart'), note = document.getElementById('srsNote');
    tot.innerHTML = '<div class="srs-stat"><b>' + s.due + '</b><span>ข้อถึงรอบวันนี้</span></div>' +
      '<div class="srs-stat"><b>' + s.sets + '</b><span>ชุดที่มีข้อถึงรอบ</span></div>' +
      '<div class="srs-stat"><b>' + s.started + '/' + s.n + '</b><span>ชุดที่เคยทำ</span></div>' +
      '<div class="srs-stat"><b>' + (s.due ? 'วันนี้' : s.next ? (dayDiff(today(), s.next) === 1 ? 'พรุ่งนี้' : thDate(s.next)) : '–') + '</b><span>รอบถัดไป</span></div>';
    var firstDue = rows.filter(function (x) { return x.due; })[0];
    start.hidden = !firstDue;
    if (firstDue) { start.href = href(firstDue.e, 'all'); start.querySelector('span').textContent = 'เริ่มทบทวนทั้งหมด ' + s.due + ' ข้อ'; }
    note.textContent = s.due ? 'ระบบจะเปิดทีละชุดในโหมด “ทบทวนที่ถึงรอบ” ทำจบแล้วกดไปชุดถัดไปได้เลย'
      : s.started ? 'ยังไม่มีข้อถึงรอบวันนี้ ทำได้ดีมาก — ข้อที่ตอบถูกแบบมั่นใจจะถูกนัดห่างขึ้นเรื่อย ๆ (1 · 3 · 7 · 16 · 35 วัน)'
      : 'ยังไม่เคยทำ Quiz Pro ชุดไหนในเบราว์เซอร์นี้ เลือกชุดด้านล่างแล้วทำทั้งชุดก่อน ระบบจะนัดวันทวนให้เอง';
    var groups = {}, order = [];
    rows.forEach(function (x) { if (!groups[x.e.s]) { groups[x.e.s] = []; order.push(x.e.s); } groups[x.e.s].push(x); });
    host.innerHTML = '';
    order.forEach(function (k) {
      var g = groups[k], gs = sum(g), e0 = g[0].e;
      var sec = document.createElement('section'); sec.className = 'srs-group'; sec.id = 's-' + k;
      if (only && only === k) sec.classList.add('is-focus');
      sec.innerHTML = '<h2><span>' + e0.i + '</span>' + e0.c + '<small>' + (gs.due ? 'ถึงรอบ ' + gs.due + ' ข้อ' : g.length + ' ชุด') + '</small></h2>';
      var ol = document.createElement('ol'); ol.className = 'srs-rows';
      g.forEach(function (x) {
        var li = document.createElement('li'); li.className = 'srs-row' + (x.due ? ' is-due' : '');
        var info = document.createElement('div'); info.className = 'srs-info';
        var t = document.createElement('a'); t.className = 'srs-title'; t.href = href(x.e); t.textContent = x.e.t;
        var meta = document.createElement('div'); meta.className = 'srs-meta';
        meta.textContent = !x.started ? 'ยังไม่เริ่ม · ' + x.total + ' ข้อ'
          : 'เคยทำ ' + x.seen + '/' + x.total + ' ข้อ · ' + (x.due ? 'ถึงรอบ ' + x.due + ' ข้อ' : x.next ? 'รอบถัดไป ' + rel(x.next) : 'ครบแล้ว');
        info.appendChild(t); info.appendChild(meta);
        var go = document.createElement('a'); go.className = 'btn ' + (x.due ? 'btn-primary' : 'btn-ghost');
        go.href = x.due ? href(x.e, 'all') : href(x.e);
        go.textContent = x.due ? '↻ ทบทวน ' + x.due + ' ข้อ' : x.started ? 'เปิดชุดนี้' : 'เริ่มทำ';
        li.appendChild(info); li.appendChild(go); ol.appendChild(li);
      });
      sec.appendChild(ol); host.appendChild(sec);
    });
    if (only) { var f = document.getElementById('s-' + only); if (f && f.scrollIntoView) f.scrollIntoView({ block: 'start' }); }
  }
  paintReview();
  addEventListener('pageshow', paintReview);

  // ---------- quiz-pro page: #sn-due hand-off ----------
  var app = document.getElementById('qp-app');
  var hm = /(?:^|[#&])sn-due(?:=([\w-]+))?/.exec(location.hash);
  if (!app || !hm) return;
  var scope = hm[1] || 'all';
  var here = CAT.filter(function (e) { return location.pathname.slice(-e.u.length) === e.u; })[0];
  var btn = app.querySelector('[data-act="mode"][data-m="due"]');
  var started = false;
  if (btn && !btn.disabled) { btn.click(); started = true; }
  try {
    var rest = location.hash.slice(1).split('&').filter(function (x) { return x && !/^sn-due(=|$)/.test(x); }).join('&');
    history.replaceState(null, '', location.pathname + location.search + (rest ? '#' + rest : ''));
  } catch (e) {}

  function nextSet() {
    return list(scope).filter(function (x) { return x.due && (!here || x.e.id !== here.id); })[0];
  }
  function banner(final) {
    var nx = nextSet(), d = document.createElement('div');
    d.className = 'snq-next' + (nx ? '' : ' is-done');
    var txt = document.createElement('div');
    if (nx) txt.innerHTML = '<small>' + (final ? 'ทบทวนชุดนี้ครบแล้ว · ' : 'ชุดนี้ยังไม่มีข้อถึงรอบ · ') + 'ชุดถัดไปที่ถึงรอบ</small><strong></strong>';
    else txt.innerHTML = '<small>' + (final ? 'ทบทวนชุดนี้ครบแล้ว' : 'ชุดนี้ยังไม่มีข้อถึงรอบ') + '</small><strong>ไม่มีชุดอื่นถึงรอบวันนี้แล้ว 🌿</strong>';
    if (nx) txt.querySelector('strong').textContent = nx.e.c + ' · ' + nx.e.t + ' (' + nx.due + ' ข้อ)';
    d.appendChild(txt);
    var acts = document.createElement('div'); acts.className = 'snq-next-acts';
    var back = document.createElement('a'); back.className = 'snq-next-btn is-quiet'; back.href = rv(); back.textContent = 'หน้าทบทวนรวม';
    acts.appendChild(back);
    if (nx) { var a = document.createElement('a'); a.className = 'snq-next-btn'; a.href = href(nx.e, scope); a.textContent = 'ไปชุดถัดไป →'; acts.appendChild(a); }
    d.appendChild(acts);
    return d;
  }
  // the quiz re-renders #qp-app with innerHTML, so the banner lives in a holder just above it
  var holder = document.createElement('div'); holder.className = 'snq-next-holder';
  app.parentNode.insertBefore(holder, app);
  function sync() {
    var onStart = !!app.querySelector('[data-act="mode"][data-m="due"]'), onResults = !!app.querySelector('.qp-score');
    var want = onResults && started ? 'final' : onStart && !started ? 'none' : '';
    if (holder.dataset.v === want) return;
    holder.dataset.v = want; holder.innerHTML = '';
    if (want) holder.appendChild(banner(want === 'final'));
  }
  sync();
  new MutationObserver(sync).observe(app, { childList: true });
})();
