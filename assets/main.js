(function () {
  'use strict';

  var root = document.documentElement;
  var header = document.querySelector('.site-header');
  var I18N = window.I18N || {};
  var lang = I18N.lang || 'en';
  var LANG_TAGS = { zh: 'zh-CN', en: 'en-GB', fr: 'fr', pt: 'pt' };

  // Old links used ?lang=xx on one page; each language now has its own URL.
  var asked = new URLSearchParams(location.search).get('lang');
  if (asked && asked !== lang && I18N.suggest && I18N.suggest[asked]) {
    location.replace(I18N.suggest[asked].url + location.hash);
    return;
  }

  // Enquiries go to the team that handles them
  var EMAILS = {
    wheat: 'sales@sycamoreagritech.com',
    sorghum: 'sales@sycamoreagritech.com',
    seed: 'sales@sycamoreagritech.com',
    hire: 'hire@sycamoreagritech.com',
    other: 'info@sycamoreagritech.com'
  };

  function store(key, value) {
    try { localStorage.setItem(key, value); } catch (e) {}
  }
  function stored(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  // ---- Language menu (links to the same page in other languages) ----
  var langBtn = document.getElementById('langBtn');
  var langMenu = document.getElementById('langMenu');

  function setLangMenu(open) {
    langMenu.hidden = !open;
    langBtn.setAttribute('aria-expanded', String(open));
  }
  langBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    setLangMenu(langMenu.hidden);
  });
  document.addEventListener('click', function (e) {
    if (!langMenu.hidden && !langMenu.contains(e.target)) setLangMenu(false);
  });
  document.querySelectorAll('a[hreflang]').forEach(function (a) {
    a.addEventListener('click', function () { store('lang', a.getAttribute('hreflang').slice(0, 2)); });
  });

  // ---- Suggest the visitor's own language (never redirects automatically) ----
  var suggest = document.getElementById('langSuggest');
  var preferred = stored('lang') || (navigator.language || '').slice(0, 2).toLowerCase();
  if (suggest && preferred !== lang && I18N.suggest && I18N.suggest[preferred] && stored('langSuggestClosed') !== lang) {
    var s = I18N.suggest[preferred];
    var text = document.getElementById('langSuggestText');
    var link = document.getElementById('langSuggestLink');
    text.textContent = s.text;
    text.lang = LANG_TAGS[preferred];
    link.textContent = s.go;
    link.lang = LANG_TAGS[preferred];
    link.href = s.url + location.hash;
    suggest.hidden = false;
    document.getElementById('langSuggestClose').addEventListener('click', function () {
      suggest.hidden = true;
      store('langSuggestClosed', lang);
    });
  }

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
    if (e.key !== 'Escape') return;
    setMenu(false);
    if (!langMenu.hidden) { setLangMenu(false); langBtn.focus(); }
  });

  // ---- Header shadow on scroll ----
  function onScroll() {
    header.classList.toggle('scrolled', window.scrollY > 8);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ---- Month names on the farming calendar ----
  var months = document.getElementById('scMonths');
  if (months && window.Intl) {
    var fmt = new Intl.DateTimeFormat(LANG_TAGS[lang], { month: lang === 'zh' ? 'numeric' : 'short' });
    Array.prototype.forEach.call(months.children, function (el, i) {
      el.textContent = fmt.format(new Date(2026, i, 15)).replace('.', '');
    });
  }

  // ---- Gallery lightbox ----
  var lb = document.getElementById('lightbox');
  var lbImg = document.getElementById('lbImg');
  var lbCap = document.getElementById('lbCap');
  var items = Array.prototype.slice.call(document.querySelectorAll('.g-item'));
  var current = 0;

  function show(i) {
    current = (i + items.length) % items.length;
    var cap = items[current].querySelector('.g-cap');
    lbImg.src = items[current].getAttribute('data-full');
    lbImg.alt = cap ? cap.textContent : '';
    lbCap.textContent = cap ? cap.textContent : '';
  }

  if (lb && lb.showModal && items.length) {
    items.forEach(function (item, i) {
      item.addEventListener('click', function () {
        show(i);
        lb.showModal();
        document.body.classList.add('lb-lock');
      });
    });
    lb.addEventListener('close', function () {
      document.body.classList.remove('lb-lock');
      items[current].focus();
    });
    lb.querySelector('.lb-close').addEventListener('click', function () { lb.close(); });
    lb.querySelector('.lb-prev').addEventListener('click', function () { show(current - 1); });
    lb.querySelector('.lb-next').addEventListener('click', function () { show(current + 1); });
    lb.addEventListener('click', function (e) {
      if (e.target === lb || e.target.classList.contains('lb-figure')) lb.close();
    });
    lb.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') show(current - 1);
      if (e.key === 'ArrowRight') show(current + 1);
    });
  }

  // ---- Footer year ----
  document.querySelectorAll('[data-year]').forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });

  // ---- "Get a quote" / "Book" links preselect the enquiry type ----
  var form = document.getElementById('inquiry');
  if (!form) return;
  var productSelect = form.elements.namedItem('product');

  document.querySelectorAll('[data-product]').forEach(function (a) {
    a.addEventListener('click', function () {
      productSelect.value = a.getAttribute('data-product');
    });
  });

  // ---- Inquiry form → opens the visitor's email app ----
  form.addEventListener('submit', function (e) {
    e.preventDefault();

    var firstInvalid = null;
    form.querySelectorAll('[required]').forEach(function (el) {
      var ok = el.checkValidity() && el.value.trim() !== '';
      el.classList.toggle('invalid', !ok);
      if (!ok && !firstInvalid) firstInvalid = el;
    });
    if (firstInvalid) { firstInvalid.focus(); return; }

    var L = I18N.mail || {};
    var v = function (name) { return form.elements.namedItem(name).value.trim(); };
    var product = productSelect.options[productSelect.selectedIndex].text;
    var to = EMAILS[productSelect.value] || EMAILS.other;

    var lines = [
      L.name + ': ' + v('fullname'),
      L.company + ': ' + v('company'),
      L.email + ': ' + v('email'),
      L.phone + ': ' + v('phone'),
      L.interest + ': ' + product,
      L.qty + ': ' + v('quantity'),
      '',
      L.msg + ':',
      v('message')
    ];
    var subject = L.subject + ' - ' + product + ' - ' + v('fullname');

    window.location.href = 'mailto:' + to +
      '?subject=' + encodeURIComponent(subject) +
      '&body=' + encodeURIComponent(lines.join('\n'));
  });

  form.querySelectorAll('[required]').forEach(function (el) {
    el.addEventListener('input', function () { el.classList.remove('invalid'); });
  });
})();
