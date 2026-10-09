(function () {
  'use strict';

  var EMAIL = 'info@sycamoreagritech.com';
  var root = document.documentElement;
  var header = document.querySelector('.site-header');

  var META = {
    zh: {
      title: 'Sycamore Agritech Limited | 农产品采购与贸易',
      desc: 'Sycamore Agritech 专注农产品采购与贸易，提供从产地寻源、验货质检到物流交付的一站式服务。'
    },
    en: {
      title: 'Sycamore Agritech Limited | Agricultural Sourcing & Trade',
      desc: 'Sycamore Agritech sources and trades agricultural products, handling sourcing, inspection, logistics and paperwork from origin to delivery.'
    }
  };

  // ---- Language ----
  function currentLang() {
    return root.getAttribute('data-lang') === 'en' ? 'en' : 'zh';
  }

  function applyLang(lang, remember) {
    root.setAttribute('data-lang', lang);
    root.lang = lang === 'zh' ? 'zh-CN' : 'en';
    document.title = META[lang].title;
    var desc = document.querySelector('meta[name="description"]');
    if (desc) desc.setAttribute('content', META[lang].desc);

    // Text that can't hold <span lang> children (e.g. <option>)
    document.querySelectorAll('[data-zh]').forEach(function (el) {
      el.textContent = el.getAttribute('data-' + lang);
    });
    document.querySelectorAll('[data-ph-zh]').forEach(function (el) {
      el.placeholder = el.getAttribute('data-ph-' + lang);
    });

    if (remember) {
      try { localStorage.setItem('lang', lang); } catch (e) {}
    }
  }

  applyLang(currentLang(), false);

  document.getElementById('langToggle').addEventListener('click', function () {
    applyLang(currentLang() === 'zh' ? 'en' : 'zh', true);
  });

  // ---- Mobile menu ----
  var menuBtn = document.getElementById('menuToggle');

  function setMenu(open) {
    header.classList.toggle('nav-open', open);
    menuBtn.setAttribute('aria-expanded', String(open));
  }

  menuBtn.addEventListener('click', function () {
    setMenu(!header.classList.contains('nav-open'));
  });
  document.querySelectorAll('#nav a').forEach(function (a) {
    a.addEventListener('click', function () { setMenu(false); });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') setMenu(false);
  });

  // ---- Header shadow on scroll ----
  function onScroll() {
    header.classList.toggle('scrolled', window.scrollY > 8);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ---- "Get a quote" links preselect the product ----
  var form = document.getElementById('inquiry');
  var productSelect = form.elements.namedItem('product');

  document.querySelectorAll('[data-product]').forEach(function (a) {
    a.addEventListener('click', function () {
      productSelect.value = a.getAttribute('data-product');
    });
  });

  // ---- Inquiry form → opens the visitor's email app ----
  var LABELS = {
    zh: { subject: '询价', name: '姓名', company: '公司', email: '邮箱', product: '产品', qty: '数量', msg: '需求说明' },
    en: { subject: 'Inquiry', name: 'Name', company: 'Company', email: 'Email', product: 'Product', qty: 'Quantity', msg: 'Details' }
  };

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    var required = form.querySelectorAll('[required]');
    var firstInvalid = null;
    required.forEach(function (el) {
      var ok = el.checkValidity() && el.value.trim() !== '';
      el.classList.toggle('invalid', !ok);
      if (!ok && !firstInvalid) firstInvalid = el;
    });
    if (firstInvalid) { firstInvalid.focus(); return; }

    var L = LABELS[currentLang()];
    var v = function (name) { return form.elements.namedItem(name).value.trim(); };
    var product = productSelect.options[productSelect.selectedIndex].text;

    var lines = [
      L.name + ': ' + v('fullname'),
      L.company + ': ' + v('company'),
      L.email + ': ' + v('email'),
      L.product + ': ' + product,
      L.qty + ': ' + v('quantity'),
      '',
      L.msg + ':',
      v('message')
    ];
    var subject = L.subject + ' - ' + product + ' - ' + v('fullname');

    window.location.href = 'mailto:' + EMAIL +
      '?subject=' + encodeURIComponent(subject) +
      '&body=' + encodeURIComponent(lines.join('\n'));
  });

  form.querySelectorAll('[required]').forEach(function (el) {
    el.addEventListener('input', function () { el.classList.remove('invalid'); });
  });

  // ---- Footer year ----
  document.querySelectorAll('[data-year]').forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });
})();
