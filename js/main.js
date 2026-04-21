/* ============================================================
   Dr. Fadhl Alakwaa Library — Main script
   Pure vanilla JS, no dependencies, no build step.
   ============================================================ */

(function () {
  'use strict';

  // -----------------------------------------------------------
  // State
  // -----------------------------------------------------------
  const state = {
    site: null,
    categories: [],
    books: [],
    filteredBooks: [],
    activeCategory: 'all',
    searchQuery: '',
    sortBy: 'newest',
    lang: 'ar',
  };

  // Books that are excluded from display no matter what
  // (per author instruction — never displayed or referenced)
  const ALWAYS_EXCLUDED_IDS = new Set([
    'salman-al-awda', // never list the Salman al-Awda book under any circumstances
  ]);

  // -----------------------------------------------------------
  // Utilities
  // -----------------------------------------------------------
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function escHtml(str) {
    if (str == null) return '';
    return String(str).replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  function tr(book, field) {
    // Pick Arabic or English variant of a book field based on current lang
    const suffix = state.lang === 'ar' ? '_ar' : '_en';
    return book[field + suffix] || book[field + '_ar'] || '';
  }

  function catLabel(catId) {
    const c = state.categories.find((x) => x.id === catId);
    if (!c) return catId;
    return state.lang === 'ar' ? c.ar : c.en;
  }

  function normalize(str) {
    return String(str || '')
      .toLowerCase()
      .normalize('NFKD')
      .replace(/[\u064B-\u0652\u0670\u0640]/g, '') // strip Arabic tashkeel + tatweel
      .replace(/\s+/g, ' ')
      .trim();
  }

  // -----------------------------------------------------------
  // Load manifest
  // -----------------------------------------------------------
  async function loadManifest() {
    try {
      const resp = await fetch('data/books.json', { cache: 'no-cache' });
      if (!resp.ok) throw new Error('Manifest load failed');
      const data = await resp.json();
      state.site = data.site;
      state.categories = (data.categories || []).sort((a, b) => (a.order || 0) - (b.order || 0));
      state.books = (data.books || []).filter((b) => !ALWAYS_EXCLUDED_IDS.has(b.id));
      state.filteredBooks = [...state.books];
      return true;
    } catch (err) {
      console.error('Failed to load books.json:', err);
      const grid = $('#book-grid');
      if (grid) {
        grid.innerHTML = `<p style="padding:32px;text-align:center;color:var(--muted);">تعذّر تحميل المكتبة. يرجى التحديث.</p>`;
      }
      return false;
    }
  }

  // -----------------------------------------------------------
  // Render: stats
  // -----------------------------------------------------------
  function renderStats() {
    const total = state.books.length;
    const cats = new Set(state.books.map((b) => b.category)).size;
    const latestYear = Math.max(...state.books.map((b) => b.year || 0));
    $('#stat-total').textContent = total;
    $('#stat-categories').textContent = cats;
    $('#stat-year').textContent = latestYear || '—';
  }

  // -----------------------------------------------------------
  // Render: category chips
  // -----------------------------------------------------------
  function renderCategoryChips() {
    const container = $('.filter-group');
    if (!container) return;
    // keep the "All" chip, append the rest
    const all = container.querySelector('[data-category="all"]');
    container.innerHTML = '';
    container.appendChild(all);

    state.categories.forEach((cat) => {
      const count = state.books.filter((b) => b.category === cat.id).length;
      if (count === 0) return;
      const chip = document.createElement('button');
      chip.className = 'chip';
      chip.dataset.category = cat.id;
      chip.dataset.ar = cat.ar;
      chip.dataset.en = cat.en;
      chip.innerHTML = `${escHtml(state.lang === 'ar' ? cat.ar : cat.en)}<span class="chip-count">(${count})</span>`;
      container.appendChild(chip);
    });
  }

  // -----------------------------------------------------------
  // Render: spotlight (featured books)
  // -----------------------------------------------------------
  function renderSpotlight() {
    const grid = $('#spotlight-grid');
    if (!grid) return;
    const featured = state.books.filter((b) => b.featured).slice(0, 4);
    if (featured.length === 0) {
      $('#spotlight').hidden = true;
      return;
    }
    grid.innerHTML = featured.map(bookSpotlightCardHTML).join('');
    grid.querySelectorAll('.spotlight-card').forEach((el) => {
      el.addEventListener('click', () => openBookModal(el.dataset.id));
    });
  }

  function bookSpotlightCardHTML(book) {
    const title = tr(book, 'title');
    const sub = tr(book, 'subtitle') || tr(book, 'description').slice(0, 90) + '…';
    return `
      <article class="spotlight-card" data-id="${escHtml(book.id)}" role="listitem">
        <div class="spotlight-card-cover">
          <img src="${escHtml(book.cover)}" alt="${escHtml(title)}" loading="lazy">
        </div>
        <div class="spotlight-card-body">
          <span class="spotlight-card-cat">${escHtml(catLabel(book.category))}</span>
          <h3 class="spotlight-card-title">${escHtml(title)}</h3>
          <p class="spotlight-card-sub">${escHtml(sub)}</p>
          <div class="spotlight-card-meta">
            <span>${escHtml(book.year)}</span>
            <span class="dot">·</span>
            <span>${book.pages ? `${book.pages} ${state.lang === 'ar' ? 'صفحة' : 'pages'}` : '—'}</span>
          </div>
        </div>
      </article>
    `;
  }

  // -----------------------------------------------------------
  // Render: book grid
  // -----------------------------------------------------------
  function renderGrid() {
    applyFilters();
    const grid = $('#book-grid');
    const empty = $('#empty-state');
    if (!grid) return;
    if (state.filteredBooks.length === 0) {
      grid.hidden = true;
      empty.hidden = false;
      return;
    }
    grid.hidden = false;
    empty.hidden = true;
    grid.innerHTML = state.filteredBooks.map(bookCardHTML).join('');
    grid.querySelectorAll('.book-card').forEach((el) => {
      el.addEventListener('click', () => openBookModal(el.dataset.id));
    });
    updateResultCount();
  }

  function bookCardHTML(book) {
    const title = tr(book, 'title');
    const sub = tr(book, 'subtitle');
    const inProd = book.status === 'in-production';
    const prodLabel = state.lang === 'ar' ? 'قيد الإعداد' : 'In production';
    const pagesLabel = state.lang === 'ar' ? 'صفحة' : 'pages';
    return `
      <article class="book-card" data-id="${escHtml(book.id)}" role="listitem" tabindex="0">
        ${inProd ? `<span class="badge-in-production">${escHtml(prodLabel)}</span>` : ''}
        <div class="book-card-cover">
          <img src="${escHtml(book.cover)}" alt="${escHtml(title)}" loading="lazy">
        </div>
        <div class="book-card-body">
          <span class="book-card-cat">${escHtml(catLabel(book.category))}</span>
          <h3 class="book-card-title">${escHtml(title)}</h3>
          ${sub ? `<p class="book-card-sub">${escHtml(sub)}</p>` : ''}
          <div class="book-card-meta">
            <span>${escHtml(book.year)}</span>
            <span class="pages">${book.pages || '—'} ${escHtml(pagesLabel)}</span>
          </div>
        </div>
      </article>
    `;
  }

  function updateResultCount() {
    const el = $('#result-count');
    if (!el) return;
    const n = state.filteredBooks.length;
    if (state.lang === 'ar') {
      el.textContent = n === 0 ? 'لا توجد نتائج'
        : n === 1 ? 'مؤلف واحد'
        : n === 2 ? 'مؤلفان اثنان'
        : `${n} مؤلفاً`;
    } else {
      el.textContent = n === 0 ? 'No results' : `${n} ${n === 1 ? 'book' : 'books'}`;
    }
  }

  // -----------------------------------------------------------
  // Filter + sort pipeline
  // -----------------------------------------------------------
  function applyFilters() {
    let out = [...state.books];

    // Category filter
    if (state.activeCategory && state.activeCategory !== 'all') {
      out = out.filter((b) => b.category === state.activeCategory);
    }

    // Search filter
    const q = normalize(state.searchQuery);
    if (q) {
      out = out.filter((b) => {
        const hay = [
          normalize(b.title_ar),
          normalize(b.title_en),
          normalize(b.subtitle_ar),
          normalize(b.subtitle_en),
          normalize(b.description_ar),
          normalize(b.description_en),
          normalize(catLabel(b.category)),
        ].join(' | ');
        return hay.includes(q);
      });
    }

    // Sort
    const s = state.sortBy;
    out.sort((a, b) => {
      if (s === 'newest') {
        return (b.year || 0) - (a.year || 0);
      }
      if (s === 'title-ar') {
        return (a.title_ar || '').localeCompare(b.title_ar || '', 'ar');
      }
      if (s === 'pages-desc') {
        return (b.pages || 0) - (a.pages || 0);
      }
      if (s === 'pages-asc') {
        return (a.pages || 0) - (b.pages || 0);
      }
      return 0;
    });

    state.filteredBooks = out;
  }

  // -----------------------------------------------------------
  // Modal — book detail
  // -----------------------------------------------------------
  function openBookModal(id) {
    const book = state.books.find((b) => b.id === id);
    if (!book) return;
    const modal = $('#book-modal');
    const inner = $('#modal-inner');
    inner.innerHTML = bookModalHTML(book);
    if (typeof modal.showModal === 'function') {
      modal.showModal();
    } else {
      modal.setAttribute('open', '');
    }
  }

  function closeBookModal() {
    const modal = $('#book-modal');
    if (typeof modal.close === 'function') {
      modal.close();
    } else {
      modal.removeAttribute('open');
    }
  }

  function bookModalHTML(book) {
    const title = tr(book, 'title');
    const sub = tr(book, 'subtitle');
    const desc = tr(book, 'description');
    const pagesLabel = state.lang === 'ar' ? 'صفحة' : 'pages';
    const downloadLabel = state.lang === 'ar' ? 'تحميل' : 'Download';
    const inProd = book.status === 'in-production';
    const comingSoon = state.lang === 'ar' ? 'قريباً' : 'Coming soon';

    const formats = Array.isArray(book.formats) ? book.formats : [];
    const formatLabels = { pdf: 'PDF', epub: 'ePub', docx: 'Word' };
    const downloadsHtml = formats.length === 0 || inProd
      ? `<span style="color:var(--muted);font-size:14px;">${escHtml(comingSoon)}</span>`
      : formats.map((fmt, idx) => {
          const url = book.files && book.files[fmt] ? book.files[fmt] : '#';
          const cls = idx === 0 ? 'download-btn' : 'download-btn alt';
          return `<a class="${cls}" href="${escHtml(url)}" download>
            <span>${escHtml(downloadLabel)}</span>
            <span class="download-btn-ext">${escHtml(formatLabels[fmt] || fmt.toUpperCase())}</span>
          </a>`;
        }).join('');

    return `
      <div class="modal-cover">
        <img src="${escHtml(book.cover)}" alt="${escHtml(title)}">
      </div>
      <div class="modal-body">
        <div class="modal-meta">
          <span class="modal-cat">${escHtml(catLabel(book.category))}</span>
          <span>${escHtml(book.year)}</span>
          ${book.pages ? `<span>${book.pages} ${escHtml(pagesLabel)}</span>` : ''}
        </div>
        <h3 id="modal-title">${escHtml(title)}</h3>
        ${sub ? `<p class="modal-sub">${escHtml(sub)}</p>` : ''}
        <p class="modal-description">${escHtml(desc)}</p>
        <div class="modal-downloads">${downloadsHtml}</div>
      </div>
    `;
  }

  // -----------------------------------------------------------
  // Language toggle
  // -----------------------------------------------------------
  function setLanguage(lang) {
    if (lang !== 'ar' && lang !== 'en') return;
    state.lang = lang;
    document.documentElement.setAttribute('lang', lang);
    document.documentElement.setAttribute('dir', lang === 'ar' ? 'rtl' : 'ltr');

    // localStorage is available on GitHub Pages (this is NOT a Claude artifact)
    try { localStorage.setItem('fadhl-library-lang', lang); } catch (_) {}

    // Toggle every element that carries data-ar / data-en
    $$('[data-ar][data-en]').forEach((el) => {
      // Skip input placeholders — handled separately
      if (el.matches('input[data-placeholder-ar]')) return;
      const val = el.dataset[lang];
      if (val != null) el.textContent = val;
    });

    // Block-level AR/EN switcher
    $$('[data-lang-block]').forEach((wrap) => {
      const arBlock = wrap.querySelector('[data-ar]');
      const enBlock = wrap.querySelector('[data-en]');
      if (arBlock) arBlock.hidden = (lang !== 'ar');
      if (enBlock) enBlock.hidden = (lang !== 'en');
    });

    // Input placeholders
    $$('input[data-placeholder-ar][data-placeholder-en]').forEach((inp) => {
      inp.placeholder = lang === 'ar' ? inp.dataset.placeholderAr : inp.dataset.placeholderEn;
    });

    // Button pressed state
    $$('.lang-btn').forEach((btn) => {
      const isActive = btn.dataset.lang === lang;
      btn.classList.toggle('active', isActive);
      btn.setAttribute('aria-pressed', isActive);
    });

    // Sort select options
    $$('#sort-select option').forEach((opt) => {
      const val = opt.dataset[lang];
      if (val) opt.textContent = val;
    });

    // Re-render dynamic content
    renderCategoryChips();
    renderSpotlight();
    renderGrid();
  }

  // -----------------------------------------------------------
  // Event wiring
  // -----------------------------------------------------------
  function wireEvents() {
    // Language toggle
    $$('.lang-btn').forEach((btn) => {
      btn.addEventListener('click', () => setLanguage(btn.dataset.lang));
    });

    // Category chips (event delegation)
    $('.filter-group').addEventListener('click', (e) => {
      const chip = e.target.closest('.chip');
      if (!chip) return;
      state.activeCategory = chip.dataset.category;
      $$('.chip').forEach((c) => c.classList.toggle('chip-active', c === chip));
      renderGrid();
    });

    // Search
    const searchInput = $('#search-input');
    const searchClear = $('#search-clear');
    let searchTimer = null;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        state.searchQuery = e.target.value;
        searchClear.hidden = !e.target.value;
        renderGrid();
      }, 80);
    });
    searchClear.addEventListener('click', () => {
      searchInput.value = '';
      state.searchQuery = '';
      searchClear.hidden = true;
      renderGrid();
      searchInput.focus();
    });

    // Sort
    $('#sort-select').addEventListener('change', (e) => {
      state.sortBy = e.target.value;
      renderGrid();
    });

    // Reset filters
    $('#reset-filters').addEventListener('click', () => {
      state.activeCategory = 'all';
      state.searchQuery = '';
      searchInput.value = '';
      searchClear.hidden = true;
      $$('.chip').forEach((c) => c.classList.toggle('chip-active', c.dataset.category === 'all'));
      renderGrid();
    });

    // Modal close
    $('#modal-close').addEventListener('click', closeBookModal);
    $('#book-modal').addEventListener('click', (e) => {
      if (e.target === e.currentTarget) closeBookModal();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeBookModal();
    });

    // Keyboard accessibility for cards
    document.addEventListener('keydown', (e) => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      const card = document.activeElement;
      if (card && card.classList.contains('book-card')) {
        e.preventDefault();
        openBookModal(card.dataset.id);
      }
    });

    // Copyright year
    $('#copyright-year').textContent = new Date().getFullYear();
  }

  // -----------------------------------------------------------
  // Init
  // -----------------------------------------------------------
  async function init() {
    const ok = await loadManifest();
    if (!ok) return;

    // Remember previous language choice (safe: not in artifacts)
    let savedLang = 'ar';
    try {
      const stored = localStorage.getItem('fadhl-library-lang');
      if (stored === 'ar' || stored === 'en') savedLang = stored;
    } catch (_) {}
    state.lang = savedLang;

    renderStats();
    renderCategoryChips();
    renderSpotlight();
    renderGrid();
    wireEvents();
    setLanguage(savedLang); // ensures everything aligns to the remembered lang
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
