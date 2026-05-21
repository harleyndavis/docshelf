(function () {
  var tagBtns = document.querySelectorAll('[data-tag]');
  var items = document.querySelectorAll('[data-tags]');

  Array.prototype.forEach.call(tagBtns, function (btn) {
    btn.addEventListener('click', function () {
      var tag = btn.getAttribute('data-tag');
      Array.prototype.forEach.call(tagBtns, function (b) {
        b.classList.toggle('is-active', b === btn);
      });
      Array.prototype.forEach.call(items, function (item) {
        if (!tag) {
          item.style.display = '';
        } else {
          var tags = item.getAttribute('data-tags');
          item.style.display = tags && tags.split(',').indexOf(tag) !== -1 ? '' : 'none';
        }
      });
    });
  });
})();
