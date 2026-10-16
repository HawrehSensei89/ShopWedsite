(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const isFa = document.documentElement.lang === 'fa';
  const fmt = n => n.toLocaleString(isFa ? 'fa-IR' : 'en-US');

  if (window.AOS) AOS.init({ duration: 700, once: true, offset: 40 });

  // theme
  $('#themeBtn')?.addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem('theme', next); } catch (e) {}
  });
  $('#burger')?.addEventListener('click', () => $('#links').classList.toggle('open'));

  // banner slider
  const slider = $('#slider');
  if (slider) {
    const slides = $$('.slide', slider), dots = $('#dots');
    let i = 0, timer;
    slides.forEach((_, n) => {
      const d = document.createElement('button');
      d.className = 'dot'; d.setAttribute('aria-label', 'slide ' + (n + 1));
      d.onclick = () => { go(n); restart(); };
      dots.appendChild(d);
    });
    const go = n => {
      i = (n + slides.length) % slides.length;
      slides.forEach((s, k) => s.classList.toggle('active', k === i));
      $$('.dot', dots).forEach((d, k) => d.classList.toggle('on', k === i));
    };
    const restart = () => { clearInterval(timer); timer = setInterval(() => go(i + 1), 5000); };
    $('#nextBtn').onclick = () => { go(i + 1); restart(); };
    $('#prevBtn').onclick = () => { go(i - 1); restart(); };
    go(0); restart();
  }

  // cart
  const form = $('#cartForm');
  if (form) {
    const csrf = $('meta[name=csrf]').content;
    const rows = $$('.cart-row', form), all = $('#selectAll');
    const toInt = t => parseInt(t.replace(/[۰-۹]/g, d => '۰۱۲۳۴۵۶۷۸۹'.indexOf(d)), 10) || 1;
    const recalc = () => {
      let total = 0, n = 0;
      rows.forEach(r => {
        if ($('.sel', r).checked) { total += +r.dataset.price * +$('.q', r).dataset.v; n++; }
      });
      $('#total').textContent = fmt(total);
      $('#payBtn').disabled = n === 0;
      all.checked = n === rows.length;
    };
    rows.forEach(r => {
      const q = $('.q', r);
      q.dataset.v = toInt(q.textContent);
      q.textContent = fmt(+q.dataset.v);
      const set = v => {
        v = Math.max(1, Math.min(99, v));
        q.dataset.v = v; q.textContent = fmt(v);
        fetch(window.UPDATE_URL + r.dataset.id + '/', {
          method: 'POST',
          headers: { 'X-CSRFToken': csrf, 'Content-Type': 'application/x-www-form-urlencoded' },
          body: 'qty=' + v
        });
        recalc();
      };
      $('.plus', r).onclick = () => set(+q.dataset.v + 1);
      $('.minus', r).onclick = () => set(+q.dataset.v - 1);
      $('.sel', r).onchange = recalc;
    });
    all.onchange = () => { rows.forEach(r => ($('.sel', r).checked = all.checked)); recalc(); };
    recalc();
  }
})();
