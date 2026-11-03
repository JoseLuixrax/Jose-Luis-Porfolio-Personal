/* Portfolio · interacción mínima, sin dependencias. */
(function () {
  "use strict";

  var root = document.documentElement;

  /* Textos de la interfaz según el idioma de la página */
  var TEXT = root.lang === "en"
    ? { copy: "Copy", copied: "Copied", emailCopied: "Email copied to clipboard" }
    : { copy: "Copiar", copied: "Copiado", emailCopied: "Email copiado al portapapeles" };

  function store(key, value) {
    try {
      if (value === undefined) return localStorage.getItem(key);
      localStorage.setItem(key, value);
    } catch (e) {
      return null;
    }
  }

  /* Tema claro / oscuro */
  var themeBtn = document.querySelector("[data-theme-toggle]");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
      root.setAttribute("data-theme", next);
      store("theme", next);
    });
  }

  /* Navegación: menú móvil */
  var nav = document.querySelector(".nav");
  if (nav) {
    var toggle = nav.querySelector(".nav__toggle");
    if (toggle) {
      toggle.addEventListener("click", function () {
        var open = nav.classList.toggle("is-open");
        toggle.setAttribute("aria-expanded", String(open));
      });
      nav.querySelectorAll(".nav__links a").forEach(function (a) {
        a.addEventListener("click", function () {
          nav.classList.remove("is-open");
          toggle.setAttribute("aria-expanded", "false");
        });
      });
    }
  }

  /* Filtros de proyectos */
  var filters = document.querySelectorAll("[data-filter]");
  var cards = document.querySelectorAll(".pcard[data-filters]");
  if (filters.length && cards.length) {
    filters.forEach(function (btn) {
      var f = btn.getAttribute("data-filter");
      var n = f === "all" ? cards.length : document.querySelectorAll('.pcard[data-filters~="' + f + '"]').length;
      var count = btn.querySelector(".count");
      if (count) count.textContent = n;
      if (n === 0) btn.hidden = true;

      btn.addEventListener("click", function () {
        filters.forEach(function (b) { b.setAttribute("aria-pressed", String(b === btn)); });
        cards.forEach(function (card) {
          var tags = (card.getAttribute("data-filters") || "").split(" ");
          var show = f === "all" || tags.indexOf(f) !== -1;
          card.hidden = !show;
        });
      });
    });
  }

  /* Copiar al portapapeles (email y fragmentos de código) */
  function copy(text, done) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, function () {});
      return;
    }
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "absolute";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand("copy"); done(); } catch (e) { /* sin soporte */ }
    document.body.removeChild(ta);
  }

  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var feedback = document.querySelector(btn.getAttribute("data-feedback") || "");
      copy(btn.getAttribute("data-copy"), function () {
        if (feedback) {
          feedback.textContent = TEXT.emailCopied;
          setTimeout(function () { feedback.textContent = ""; }, 2500);
        }
      });
    });
  });

  document.querySelectorAll(".code").forEach(function (block) {
    var btn = block.querySelector(".code__copy");
    var code = block.querySelector("code");
    if (!btn || !code) return;
    var label = btn.querySelector("span");
    btn.addEventListener("click", function () {
      copy(code.textContent, function () {
        label.textContent = TEXT.copied;
        setTimeout(function () { label.textContent = TEXT.copy; }, 2000);
      });
    });
  });

  /* Índice lateral: resaltar la sección visible */
  var tocLinks = document.querySelectorAll(".toc a");
  if (tocLinks.length && "IntersectionObserver" in window) {
    var byId = {};
    tocLinks.forEach(function (a) { byId[a.getAttribute("href").slice(1)] = a; });
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        tocLinks.forEach(function (a) { a.classList.remove("is-active"); });
        var link = byId[e.target.id];
        if (link) link.classList.add("is-active");
      });
    }, { rootMargin: "-20% 0px -70% 0px" });
    document.querySelectorAll(".p-section[id]").forEach(function (s) { spy.observe(s); });
  }

  /* Año del footer */
  var year = document.querySelector("[data-year]");
  if (year) year.textContent = new Date().getFullYear();
})();
