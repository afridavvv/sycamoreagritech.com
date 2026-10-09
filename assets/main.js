(function () {
  'use strict';

  var EMAIL = 'info@sycamoreagritech.com';
  var root = document.documentElement;
  var header = document.querySelector('.site-header');

  var LANG_TAGS = { zh: 'zh-CN', en: 'en', fr: 'fr', pt: 'pt' };

  var META = {
    zh: {
      title: 'Sycamore Agritech Limited | 马拉维小麦与玉米种植',
      desc: 'Sycamore Agritech Limited 在马拉维规模化种植小麦和玉米，采用中心支轴式喷灌，并为面粉、饮料、饲料和食品企业稳定供应粮食。'
    },
    en: {
      title: 'Sycamore Agritech Limited | Wheat & Maize Farming in Malawi',
      desc: 'Sycamore Agritech Limited grows wheat and maize at scale in Malawi under centre-pivot irrigation, and supplies grain to millers, beverage, feed and food companies.'
    },
    fr: {
      title: 'Sycamore Agritech Limited | Culture de blé et de maïs au Malawi',
      desc: "Sycamore Agritech Limited cultive du blé et du maïs à grande échelle au Malawi sous irrigation à pivot central, et approvisionne meuniers, brasseurs, fabricants d'aliments pour animaux et industriels de l'agroalimentaire."
    },
    pt: {
      title: 'Sycamore Agritech Limited | Cultivo de trigo e milho no Malawi',
      desc: 'A Sycamore Agritech Limited cultiva trigo e milho em grande escala no Malawi com rega por pivô central e fornece cereais a moageiras, indústrias de bebidas, fábricas de rações e empresas alimentares.'
    }
  };

  // ---- Language ----
  function currentLang() {
    var l = root.getAttribute('data-lang');
    return LANG_TAGS[l] ? l : 'en';
  }

  function applyLang(lang, remember) {
    root.setAttribute('data-lang', lang);
    root.lang = LANG_TAGS[lang];
    document.title = META[lang].title;
    var desc = document.querySelector('meta[name="description"]');
    if (desc) desc.setAttribute('content', META[lang].desc);

    // Text that can't hold <span lang> children (e.g. <option>)
    document.querySelectorAll('[data-en]').forEach(function (el) {
      el.textContent = el.getAttribute('data-' + lang);
    });
    document.querySelectorAll('[data-ph-en]').forEach(function (el) {
      el.placeholder = el.getAttribute('data-ph-' + lang);
    });

    if (remember) {
      try { localStorage.setItem('lang', lang); } catch (e) {}
    }
  }

  applyLang(currentLang(), false);

  // Language menu in the header
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

  // Header menu items and footer links both switch language in place
  document.querySelectorAll('[data-set-lang]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      e.preventDefault();
      applyLang(el.getAttribute('data-set-lang'), true);
      setLangMenu(false);
    });
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
    en: { subject: 'Inquiry', name: 'Name', company: 'Company', email: 'Email', product: 'Product', qty: 'Quantity', msg: 'Details' },
    fr: { subject: 'Demande de devis', name: 'Nom', company: 'Entreprise', email: 'E-mail', product: 'Produit', qty: 'Quantité', msg: 'Détails' },
    pt: { subject: 'Pedido de cotação', name: 'Nome', company: 'Empresa', email: 'E-mail', product: 'Produto', qty: 'Quantidade', msg: 'Detalhes' }
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
