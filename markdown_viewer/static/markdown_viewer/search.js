(function () {
  var docs = [];
  try {
    var raw = document.getElementById('mv-doc-index');
    if (raw) docs = JSON.parse(raw.textContent.trim() || '[]');
  } catch (e) { docs = []; }

  var backdrop = document.querySelector('[data-mv-palette]');
  var inner = document.querySelector('[data-mv-palette-inner]');
  var input = document.querySelector('[data-mv-palette-input]');
  var results = document.querySelector('[data-mv-palette-results]');
  var triggers = document.querySelectorAll('[data-mv-search-open]');
  var highlight = 0;
  var current = [];

  function fuzzyScore(needle, hay) {
    if (!needle) return 0;
    var n = needle.toLowerCase();
    var h = hay.toLowerCase();
    if (h.indexOf(n) !== -1) return 100 - h.indexOf(n);
    var i = 0, j = 0, score = 0, streak = 0;
    while (i < n.length && j < h.length) {
      if (n[i] === h[j]) { score += 2 + streak; streak += 1; i += 1; }
      else { streak = 0; }
      j += 1;
    }
    return i === n.length ? score : 0;
  }

  function search(q) {
    if (!q.trim()) return docs.slice(0, 8);
    return docs
      .map(function (d) {
        var tagScore = (d.tags || []).reduce(function (best, tag) {
          return Math.max(best, fuzzyScore(q, tag));
        }, 0);
        return { doc: d, score: Math.max(fuzzyScore(q, d.title || d.slug), fuzzyScore(q, d.slug), tagScore) };
      })
      .filter(function (r) { return r.score > 0; })
      .sort(function (a, b) { return b.score - a.score; })
      .slice(0, 8)
      .map(function (r) { return r.doc; });
  }

  function render(q) {
    current = search(q);
    highlight = 0;
    if (current.length === 0) {
      results.innerHTML = '<div class="mv-palette-empty">No matches for <em>"' + escapeHtml(q) + '"</em></div>';
      return;
    }
    var label = q.trim()
      ? '<div class="mv-palette-section-label">' + current.length + (current.length === 1 ? ' match' : ' matches') + '</div>'
      : '<div class="mv-palette-section-label">All documents</div>';
    results.innerHTML = label + current.map(function (d, i) {
      return '<button class="mv-palette-row ' + (i === 0 ? 'is-active' : '') + '" data-mv-row="' + i + '" type="button">'
        + '<div class="mv-palette-row-main">'
        +   '<div class="mv-palette-row-title">' + escapeHtml(d.title || d.slug) + '</div>'
        +   '<div class="mv-palette-row-summary">' + escapeHtml(d.slug) + '</div>'
        + '</div>'
        + '<span class="mv-palette-row-arrow">↵</span>'
        + '</button>';
    }).join('');

    Array.prototype.forEach.call(results.querySelectorAll('[data-mv-row]'), function (el) {
      el.addEventListener('mouseenter', function () { setHighlight(parseInt(el.getAttribute('data-mv-row'), 10)); });
      el.addEventListener('click', function () { open(current[parseInt(el.getAttribute('data-mv-row'), 10)]); });
    });
  }

  function setHighlight(i) {
    highlight = Math.max(0, Math.min(current.length - 1, i));
    Array.prototype.forEach.call(results.querySelectorAll('[data-mv-row]'), function (el, idx) {
      el.classList.toggle('is-active', idx === highlight);
    });
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c];
    });
  }

  function openPalette() {
    backdrop.classList.add('is-open');
    input.value = '';
    render('');
    setTimeout(function () { input.focus(); }, 30);
  }

  function closePalette() { backdrop.classList.remove('is-open'); }

  function open(doc) { if (doc) window.location.href = doc.url; }

  Array.prototype.forEach.call(triggers, function (t) { t.addEventListener('click', openPalette); });

  backdrop.addEventListener('click', function (e) { if (e.target === backdrop) closePalette(); });

  input.addEventListener('input', function () { render(input.value); });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowDown') { e.preventDefault(); setHighlight(highlight + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setHighlight(highlight - 1); }
    else if (e.key === 'Enter') { e.preventDefault(); open(current[highlight]); }
  });

  document.addEventListener('keydown', function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); openPalette(); }
    else if (e.key === 'Escape' && backdrop.classList.contains('is-open')) { closePalette(); }
  });
})();
