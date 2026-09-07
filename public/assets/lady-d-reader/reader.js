(() => {
  'use strict';
  const leaves = [...document.querySelectorAll('.journal-page')];
  if (!leaves.length) return;
  const select = document.querySelector('#day-select');
  const panel = document.querySelector('.reading-panel');
  const previous = document.querySelector('#previous-day');
  const next = document.querySelector('#next-day');
  const status = document.querySelector('#page-status');
  const modes = [...document.querySelectorAll('[data-view]')];
  let current = 0;
  let mode = 'page';
  const movements = ['Held', 'Led', 'Filled', 'Carried Forward'];
  const savedKey = 'lady-d-mornings-last-day';

  function fromHash() {
    const match = location.hash.match(/^#day-(\d{1,2})$/);
    return match && Number(match[1]) >= 1 && Number(match[1]) <= leaves.length ? Number(match[1]) - 1 : null;
  }

  function sizePage() {
    const available = Math.max(600, window.innerHeight - 220);
    const width = Math.max(240, Math.min(576, window.innerWidth - 24, mode === 'page' ? available * 2 / 3 : 430));
    document.documentElement.style.setProperty('--stage-width', `${width}px`);
    document.documentElement.style.setProperty('--stage-height', `${width * 1.5}px`);
    document.documentElement.style.setProperty('--page-scale', width / 576);
  }

  function focusReading() {
    const heading = panel.querySelector('h2');
    heading.tabIndex = -1;
    heading.focus({preventScroll: true});
    heading.scrollIntoView({block: 'start', behavior: 'instant'});
  }

  function show(index, updateHistory = true) {
    current = Math.max(0, Math.min(leaves.length - 1, index));
    leaves.forEach((leaf, i) => {
      leaf.classList.toggle('is-current', i === current);
      if (i === current) leaf.removeAttribute('aria-hidden');
      else leaf.setAttribute('aria-hidden', 'true');
    });
    select.value = String(current + 1);
    previous.disabled = current === 0;
    next.disabled = current === leaves.length - 1;
    status.textContent = `Day ${String(current + 1).padStart(2, '0')} of 31 · ${movements[current < 8 ? 0 : current < 16 ? 1 : current < 24 ? 2 : 3]}`;
    panel.replaceChildren(...[...leaves[current].querySelector('.copy').children].map(child => child.cloneNode(true)));
    try { localStorage.setItem(savedKey, String(current)); } catch { /* Reading works without storage. */ }
    if (updateHistory) history.replaceState(null, '', `#day-${String(current + 1).padStart(2, '0')}`);
    sizePage();
    if (updateHistory && mode === 'text') focusReading();
  }

  previous.addEventListener('click', () => show(current - 1));
  next.addEventListener('click', () => show(current + 1));
  select.addEventListener('change', () => show(Number(select.value) - 1));
  modes.forEach(button => button.addEventListener('click', () => {
    mode = button.dataset.view;
    document.body.classList.toggle('text-view', mode === 'text');
    modes.forEach(option => option.setAttribute('aria-pressed', String(option === button)));
    panel.hidden = mode !== 'text';
    sizePage();
    if (mode === 'text') focusReading();
  }));
  document.addEventListener('keydown', event => {
    if (event.altKey || event.ctrlKey || event.metaKey || /INPUT|TEXTAREA|SELECT/.test(event.target.tagName) || event.target.isContentEditable) return;
    if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
      event.preventDefault();
      show(current + (event.key === 'ArrowRight' ? 1 : -1));
    }
  });
  window.addEventListener('resize', sizePage);
  window.addEventListener('hashchange', () => {
    const day = fromHash();
    if (day !== null) show(day, false);
  });
  window.addEventListener('beforeprint', () => leaves.forEach(leaf => leaf.removeAttribute('aria-hidden')));
  window.addEventListener('afterprint', () => show(current, false));
  document.querySelectorAll('.reader-controls,.page-turner').forEach(element => { element.hidden = false; });
  document.body.classList.add('reader-ready');
  let initial = fromHash();
  if (initial === null) {
    try {
      const saved = Number(localStorage.getItem(savedKey));
      initial = Number.isInteger(saved) && saved >= 0 && saved < leaves.length ? saved : 0;
    } catch { initial = 0; }
  }
  show(initial, false);
})();
