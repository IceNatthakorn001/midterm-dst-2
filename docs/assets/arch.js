// ITDS211 subject page: search, group filter, "continue reading", opened-chapter marks
(function () {
  var KEY = window.ARCH_KEY, DATA = window.ARCH || [];
  var byS = {};
  DATA.forEach(function (d) { byS[d.s] = d; });

  function load() { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; } }
  function save(d) { try { localStorage.setItem(KEY, JSON.stringify(d)); } catch (e) {} }

  var cards = Array.prototype.slice.call(document.querySelectorAll('.ax-card'));
  var groups = Array.prototype.slice.call(document.querySelectorAll('.ax-group'));

  // opened marks + continue banner
  function paint() {
    var d = load(), v = d.v || {};
    cards.forEach(function (c) { c.classList.toggle('seen', !!v[c.dataset.s]); });
    var cont = document.getElementById('axContinue');
    if (cont && d.last && d.last.h) {
      cont.href = d.last.h;
      document.getElementById('axContTitle').textContent = d.last.t || d.last.h;
      cont.hidden = false;
    }
  }
  paint();

  // remember clicks (quiz + animation pages can't record themselves)
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[data-l]');
    if (!a) return;
    var d = load();
    d.v = d.v || {};
    d.v[a.dataset.l] = 1;
    var card = a.closest('.ax-card');
    var t = card ? card.querySelector('.ax-title').textContent : '';
    d.last = { h: a.getAttribute('href'), t: a.textContent.trim() + ' · ' + t };
    save(d);
  });

  // filter + search
  var q = document.getElementById('axQ'), filter = 'all';
  var empty = document.getElementById('axEmpty');
  function apply() {
    var term = (q.value || '').trim().toLowerCase(), shown = 0;
    cards.forEach(function (c) {
      var d = byS[c.dataset.s];
      var ok = (filter === 'all' || c.dataset.g === filter) && (!term || d.f.indexOf(term) !== -1);
      c.hidden = !ok;
      if (ok) shown++;
      var hits = c.querySelector('.ax-hits');
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
    groups.forEach(function (g) {
      g.hidden = !g.querySelector('.ax-card:not([hidden])');
    });
    empty.hidden = shown > 0;
  }
  q.addEventListener('input', apply);
  document.querySelectorAll('.ax-tabs button').forEach(function (b) {
    b.addEventListener('click', function () {
      document.querySelectorAll('.ax-tabs button').forEach(function (x) { x.classList.remove('on'); });
      b.classList.add('on');
      filter = b.dataset.f;
      apply();
    });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && document.activeElement !== q) { e.preventDefault(); q.focus(); }
    if (e.key === 'Escape' && document.activeElement === q) { q.value = ''; apply(); q.blur(); }
  });
  addEventListener('pageshow', paint);
})();
