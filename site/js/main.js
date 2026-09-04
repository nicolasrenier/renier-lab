/* ========================================
   Renier Lab — Main JavaScript
   ======================================== */

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* --- Mobile navigation toggle --- */
const navToggle = document.querySelector('.nav-toggle');
const navLinks = document.querySelector('.nav-links');

if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => {
    const open = navLinks.classList.toggle('open');
    navToggle.setAttribute('aria-expanded', String(open));
  });

  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      navLinks.classList.remove('open');
      navToggle.setAttribute('aria-expanded', 'false');
    });
  });
}

/* --- Scroll-triggered fade-in animations --- */
const fadeElements = document.querySelectorAll('.fade-in');

if (fadeElements.length > 0) {
  if (reduceMotion || !('IntersectionObserver' in window)) {
    fadeElements.forEach(el => el.classList.add('visible'));
  } else {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    fadeElements.forEach(el => observer.observe(el));
  }
}

/* --- Navbar opacity on scroll --- */
const nav = document.querySelector('.nav');
if (nav) {
  const setNav = () => {
    nav.style.background = window.scrollY > 50
      ? 'rgba(8, 9, 13, 0.95)'
      : 'rgba(8, 9, 13, 0.85)';
  };
  setNav();
  window.addEventListener('scroll', setNav, { passive: true });
}

/* --- Gallery lightbox --- */
const lightbox = document.getElementById('lightbox');

if (lightbox) {
  const items = Array.from(document.querySelectorAll('.gallery-item'));
  const imgEl = document.getElementById('lightbox-img');
  const capEl = document.getElementById('lightbox-caption');
  const btnClose = lightbox.querySelector('.lightbox-close');
  const btnPrev = lightbox.querySelector('.lightbox-prev');
  const btnNext = lightbox.querySelector('.lightbox-next');
  let index = 0;
  let lastFocus = null;

  const show = i => {
    index = (i + items.length) % items.length;
    const el = items[index];
    const title = el.dataset.title || '';
    const caption = el.dataset.caption || '';
    imgEl.src = el.dataset.full;
    imgEl.alt = caption || title;
    capEl.innerHTML = '';
    if (title) {
      const strong = document.createElement('strong');
      strong.textContent = title;
      capEl.appendChild(strong);
    }
    if (caption) capEl.appendChild(document.createTextNode(caption));
    // Warm the neighbours so arrow navigation feels instant.
    [items[(index + 1) % items.length], items[(index - 1 + items.length) % items.length]]
      .forEach(n => { if (n) new Image().src = n.dataset.full; });
  };

  const open = i => {
    lastFocus = document.activeElement;
    lightbox.hidden = false;
    document.body.classList.add('lightbox-open');
    show(i);
    requestAnimationFrame(() => lightbox.classList.add('open'));
    btnClose.focus();
  };

  const close = () => {
    lightbox.classList.remove('open');
    document.body.classList.remove('lightbox-open');
    const finish = () => { lightbox.hidden = true; imgEl.src = ''; };
    reduceMotion ? finish() : setTimeout(finish, 250);
    if (lastFocus) lastFocus.focus();
  };

  items.forEach((el, i) => el.addEventListener('click', () => open(i)));
  btnClose.addEventListener('click', close);
  btnPrev.addEventListener('click', () => show(index - 1));
  btnNext.addEventListener('click', () => show(index + 1));
  lightbox.addEventListener('click', e => { if (e.target === lightbox) close(); });

  document.addEventListener('keydown', e => {
    if (lightbox.hidden) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowRight') show(index + 1);
    else if (e.key === 'ArrowLeft') show(index - 1);
    else if (e.key === 'Tab') {
      // Keep focus inside the dialog.
      const focusable = [btnClose, btnPrev, btnNext];
      const pos = focusable.indexOf(document.activeElement);
      e.preventDefault();
      focusable[(pos + (e.shiftKey ? -1 : 1) + focusable.length) % focusable.length].focus();
    }
  });

  // Swipe on touch devices.
  let touchX = null;
  lightbox.addEventListener('touchstart', e => { touchX = e.changedTouches[0].clientX; }, { passive: true });
  lightbox.addEventListener('touchend', e => {
    if (touchX === null) return;
    const dx = e.changedTouches[0].clientX - touchX;
    if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
    touchX = null;
  }, { passive: true });
}

/* --- Publication filter --- */
const pubSearch = document.getElementById('pub-search');

if (pubSearch) {
  const groups = Array.from(document.querySelectorAll('.pub-year-group'));
  const sections = Array.from(document.querySelectorAll('.pub-section, .pub-subsection'));
  const pubs = Array.from(document.querySelectorAll('.pub-item'));
  const countEl = document.getElementById('pub-count');
  const total = pubs.length;

  pubs.forEach(p => { p.dataset.haystack = p.textContent.toLowerCase(); });

  const apply = () => {
    const q = pubSearch.value.trim().toLowerCase();
    let shown = 0;
    pubs.forEach(p => {
      const match = !q || p.dataset.haystack.includes(q);
      p.hidden = !match;
      if (match) shown++;
    });
    groups.forEach(g => {
      g.hidden = !g.querySelector('.pub-item:not([hidden])');
    });
    sections.forEach(s => {
      s.hidden = !s.querySelector('.pub-item:not([hidden])');
    });
    if (countEl) {
      countEl.textContent = q
        ? `${shown} of ${total} publications match “${pubSearch.value.trim()}”`
        : `${total} publications`;
    }
  };

  pubSearch.addEventListener('input', apply);
  apply();
}

// --- News type filters -------------------------------------------------
// Each .news-filter names the items it controls via data-filter-target.
document.querySelectorAll('.news-filter').forEach(bar => {
  const items = Array.from(document.querySelectorAll(bar.dataset.filterTarget));
  const chips = Array.from(bar.querySelectorAll('.news-filter-chip'));
  if (!items.length) return;

  bar.addEventListener('click', event => {
    const chip = event.target.closest('.news-filter-chip');
    if (!chip) return;
    const wanted = chip.dataset.filter;
    chips.forEach(c => {
      const on = c === chip;
      c.classList.toggle('is-active', on);
      c.setAttribute('aria-pressed', String(on));
    });
    items.forEach(item => {
      item.hidden = wanted !== 'all' && item.dataset.type !== wanted;
    });
  });

  chips.forEach(c => c.setAttribute('aria-pressed', String(c.classList.contains('is-active'))));
});
