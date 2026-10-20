(() => {
  const picker = document.querySelector('#reading-day');
  if (!picker) return;
  picker.addEventListener('change', () => {
    const target = document.getElementById(picker.value);
    if (!target) return;
    target.tabIndex = -1;
    target.focus({preventScroll:true});
    target.scrollIntoView({block:'start',behavior:'instant'});
    history.replaceState(null,'','#'+target.id);
  });
  const syncReading = () => {
    const reading = location.hash.slice(1).replace(/^dB/, 'dA');
    if ([...picker.options].some(option => option.value === reading)) picker.value = reading;
  };
  window.addEventListener('hashchange', syncReading);
  document.querySelector('.interior-skip')?.addEventListener('click', event => {
    const target = document.querySelector(event.currentTarget.hash);
    if (target) {
      target.tabIndex = -1;
      target.focus({preventScroll:true});
    }
  });
  syncReading();
})();
