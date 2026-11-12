// Subject page: search inside the subject, group tabs, opened-lesson marks
(function () {
  var SUBJ = window.SN_SUBJ, DATA = window.SN_DATA || [];
  var store = window.SNStore || { load: function () { return { v: {} }; }, save: function () {} };
  var byS = {};
  DATA.forEach(function (d) { byS[d.s] = d; });

  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var groups = Array.prototype.slice.call(document.querySelectorAll('.group'));

  function paint() {
    var v = store.load().v;
    cards.forEach(function (c) { c.classList.toggle('seen', !!v[SUBJ + '/' + c.dataset.s]); });
  }
  paint();
  addEventListener('pageshow', paint);

  // quizzes / animations / reviews can't record themselves: remember the click
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[data-l]');
    if (!a) return;
    var d = store.load();
    d.v[SUBJ + '/' + a.dataset.l] = 1;
    var card = a.closest('.card');
    var t = card ? card.querySelector('.card-title').textContent : '';
    var label = a.textContent.replace(/\s+/g, ' ').trim();
    d.last = { u: SUBJ + '/' + a.getAttribute('href'), t: label + ' · ' + t, s: '' };
    store.save(d);
  });

  // search + tabs
  var q = document.getElementById('sq'), filter = 'all';
  var empty = document.getElementById('sEmpty');
  function apply() {
    var term = (q ? q.value : '').trim().toLowerCase(), shown = 0;
    cards.forEach(function (c) {
      var d = byS[c.dataset.s] || { f: '', toc: [] };
      var ok = (filter === 'all' || c.dataset.g === filter) && (!term || d.f.indexOf(term) !== -1);
      c.hidden = !ok;
      if (ok) shown++;
      var hits = c.querySelector('.hits');
      hits.innerHTML = '';
      c.classList.toggle('searching', !!term && ok);
      if (term && ok) {
        d.toc.filter(function (x) { return x[1].toLowerCase().indexOf(term) !== -1; }).slice(0, 4).forEach(function (x) {
          var li = document.createElement('li'), a = document.createElement('a');
          a.href = d.s + '/index.html#' + x[0];
          a.dataset.l = d.s;
          a.textContent = '↳ ' + x[1];
          li.appendChild(a); hits.appendChild(li);
        });
      }
    });
    groups.forEach(function (g) { g.hidden = !g.querySelector('.card:not([hidden])'); });
    if (empty) empty.hidden = shown > 0;
  }
  if (q) {
    q.addEventListener('input', apply);
    q.addEventListener('keydown', function (e) { if (e.key === 'Escape') { q.value = ''; apply(); q.blur(); } });
  }
  document.querySelectorAll('.tabs button').forEach(function (b) {
    b.addEventListener('click', function () {
      document.querySelectorAll('.tabs button').forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      filter = b.dataset.f;
      apply();
    });
  });
})();
