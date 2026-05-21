(function () {
  var prose = document.querySelector('[data-mv-prose]');
  var tocList = document.querySelector('[data-mv-toc]');
  if (!prose || !tocList) return;

  function slugify(s) {
    return s.toLowerCase().trim()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-');
  }

  var headings = Array.prototype.slice.call(prose.querySelectorAll('h2, h3'));
  if (headings.length === 0) {
    tocList.innerHTML = '<li><span class="mv-toc-empty">No sections</span></li>';
    return;
  }

  var seen = {};
  var items = headings.map(function (h) {
    if (!h.id) {
      var base = slugify(h.textContent);
      var id = base, n = 2;
      while (seen[id]) { id = base + '-' + n; n += 1; }
      seen[id] = true;
      h.id = id;
    } else {
      seen[h.id] = true;
    }
    return { id: h.id, text: h.textContent, level: h.tagName.toLowerCase(), el: h };
  });

  tocList.innerHTML = items.map(function (it) {
    return '<li>'
      + '<button type="button" class="mv-toc-link ' + (it.level === 'h3' ? 'is-h3' : '') + '" data-mv-toc-id="' + it.id + '">'
      +   it.text
      + '</button>'
      + '</li>';
  }).join('');

  Array.prototype.forEach.call(tocList.querySelectorAll('[data-mv-toc-id]'), function (btn) {
    btn.addEventListener('click', function () {
      var id = btn.getAttribute('data-mv-toc-id');
      var el = document.getElementById(id);
      if (!el) return;
      var top = el.getBoundingClientRect().top + window.scrollY - 80;
      window.scrollTo({ top: top, behavior: 'smooth' });
      history.replaceState(null, '', '#' + id);
    });
  });

  var links = tocList.querySelectorAll('[data-mv-toc-id]');
  function spy() {
    var top = window.scrollY + 100;
    var active = items[0].id;
    for (var i = 0; i < items.length; i++) {
      if (items[i].el.offsetTop <= top) active = items[i].id;
    }
    Array.prototype.forEach.call(links, function (l) {
      l.classList.toggle('is-active', l.getAttribute('data-mv-toc-id') === active);
    });
  }
  spy();
  window.addEventListener('scroll', spy, { passive: true });

  if (window.location.hash) {
    var target = document.getElementById(window.location.hash.slice(1));
    if (target) {
      setTimeout(function () {
        var top = target.getBoundingClientRect().top + window.scrollY - 80;
        window.scrollTo({ top: top });
      }, 50);
    }
  }
})();
