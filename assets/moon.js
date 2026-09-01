/* SHOPCIENTY — THE MOON THAT NIGHT configurator (04.08.2026).
   Sister of starmap.js: same state/controls/checkout grammar, but the preview is a
   photographic moon (NASA GSFC/LRO texture, assets/starmap/moon-texture.jpg) with the
   TRUE phase of the chosen night. Print file is rendered server-side by
   starmap_v3.render_moon_poster from the same MN2 design code. */
(function () {
'use strict';

/* ── astronomy (mirror of starmap_v3) ── */
function julianDate(y, mo, d, utHours) {
  return 367 * y - Math.floor(7 * (y + Math.floor((mo + 9) / 12)) / 4)
       + Math.floor(275 * mo / 9) + d + 1721013.5 + utHours / 24.0;
}
const CYCLE = 29.530588853;
function moonAge(dateStr, timeStr, tzOffset) {
  const [y, mo, d] = dateStr.split('-').map(Number);
  const [hh, mm]   = timeStr.split(':').map(Number);
  const jd = julianDate(y, mo, d, hh + mm / 60 - tzOffset);
  return ((jd - 2451550.1) % CYCLE + CYCLE) % CYCLE;
}
function illumOf(age)  { return (1 - Math.cos(2 * Math.PI * age / CYCLE)) / 2; }
function moonTitle(age) {
  const lit = illumOf(age), wax = age < CYCLE / 2;
  let name;
  if (lit > 0.96) name = 'FULL MOON';
  else if (lit < 0.04) name = 'NEW MOON';
  else if (Math.abs(lit - 0.5) < 0.07) name = (wax ? 'FIRST' : 'LAST') + ' QUARTER';
  else name = (wax ? 'WAXING ' : 'WANING ') + (lit < 0.5 ? 'CRESCENT' : 'GIBBOUS');
  return `${Math.round(lit * 100)}% ILLUMINATED · ${name}`;
}

/* ── themes: то же семейство, что starmap.js/starmap_v3 ── */
const THEMES = {
  midnight: { page:'#0b1733', sky:'#0a1430', ink:'#eaf0ff', sub:'#8fb0e6', faint:'#6f8bc0',
              star:'#ffffff', accent:'#8fb0e6', label:'Midnight' },
  luxegold: { page:'#0b1733', sky:'#0a1430', ink:'#eaf0ff', sub:'#8fb0e6', faint:'#6f8bc0',
              star:'#ffffff', accent:'#c9a961', label:'Luxe · Gold' },
  luxesilver:{ page:'#0b1733', sky:'#0a1430', ink:'#eaf0ff', sub:'#8fb0e6', faint:'#6f8bc0',
              star:'#ffffff', accent:'#c3ccd8', label:'Luxe · Silver' },
  porcelain:{ page:'#f5f2ea', sky:'#f5f2ea', ink:'#0d1830', sub:'#33496e', faint:'#5f7396',
              star:'#0d1830', accent:'#243a63', label:'Porcelain' },
  noir:     { page:'#060608', sky:'#060608', ink:'#e8dcc0', sub:'#c9a961', faint:'#8a7845',
              star:'#f5efe0', accent:'#c9a961', label:'Noir' },
};
function mixThemes(A, B, p) {
  const out = Object.assign({}, B);
  const ch = (h, i) => parseInt(h.slice(i, i + 2), 16);
  for (const k of ['page','sky','ink','sub','faint','star','accent']) {
    out[k] = '#' + [1, 3, 5].map(i =>
      Math.round(ch(A[k], i) + (ch(B[k], i) - ch(A[k], i)) * p).toString(16).padStart(2, '0')).join('');
  }
  return out;
}

const PRINT_SIZES = { '30x40': 4 / 3, '40x50': 5 / 4, '50x70': 7 / 5 };
const SIZE_CM = { '3040': '30x40', '4050': '40x50', '5070': '50x70' };
const TEX = 'assets/starmap/moon-texture.jpg';

/* детерминированные звёзды фона (один и тот же узор на всех перерисовках) */
function bgStars(seedCount, W, Hmax, cx, cy, R, color) {
  let s = 0x2F6E2B1;
  const rnd = () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
  const out = [];
  for (let i = 0; i < seedCount; i++) {
    const x = 70 + rnd() * (W - 140), y = 70 + rnd() * (Hmax - 70);
    if ((x - cx) ** 2 + (y - cy) ** 2 < (R * 1.15) ** 2) continue;
    out.push(`<circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="${(0.6 + rnd() * 1.1).toFixed(1)}" fill="${color}" opacity="${(0.15 + rnd() * 0.45).toFixed(2)}"/>`);
  }
  return out.join('');
}

function renderSvg(o) {
  const t = o._themeMix || THEMES[o.theme] || THEMES.midnight;
  const age = o._age !== undefined ? o._age : moonAge(o.dateStr, o.timeStr, o.tz);
  const W = 1200;
  const H = Math.round(W * PRINT_SIZES[SIZE_CM[o.size] || '30x40']);
  const porcelain = o.theme === 'porcelain';

  const brandPad = 58, textBlock = 236, gap = 96;
  const region = H - brandPad - textBlock - gap;
  const R = Math.min(0.317 * W, region * 0.40);
  const cx = W / 2, cy = 118 + region * 0.44;
  const ty0 = cy + R + gap;

  const s = [`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}">`];
  s.push(`<rect width="${W}" height="${H}" fill="${t.page}"/>`);
  s.push(`<rect x="34" y="34" width="${W-68}" height="${H-68}" fill="none" stroke="${t.accent}" stroke-width="1.4" opacity="0.9"/>`);
  s.push(`<rect x="44" y="44" width="${W-88}" height="${H-88}" fill="none" stroke="${t.accent}" stroke-width="0.6" opacity="0.7"/>`);

  if (!porcelain) s.push(bgStars(96, W, cy + R * 0.5, cx, cy, R, t.star));

  const phase = 2 * Math.PI * age / CYCLE;
  const k = Math.cos(phase);
  const wax = age < CYCLE / 2;
  const lit = 1 - (k + 1) / 2;
  const blur = Math.max(2.5, R * 0.025);

  s.push('<defs>');
  s.push(`<clipPath id="mnclip"><circle cx="${cx}" cy="${cy}" r="${R}"/></clipPath>`);
  s.push(`<filter id="mnterm" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="${blur.toFixed(1)}"/></filter>`);
  if (porcelain) {
    const c = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16) / 255);
    const ink = c(t.sub), page = c(t.page);
    const row = (i) => {
      const a = (ink[i] - page[i]).toFixed(4), b = page[i].toFixed(4);
      return i === 0 ? `${a} 0 0 0 ${b}` : i === 1 ? `0 ${a} 0 0 ${b}` : `0 0 ${a} 0 ${b}`;
    };
    s.push(`<filter id="mnduo"><feColorMatrix type="matrix" values="${row(0)} ${row(1)} ${row(2)} 0 0 0 1 0"/></filter>`);
  } else {
    s.push(`<radialGradient id="mngl" cx="50%" cy="50%" r="50%"><stop offset="70%" stop-color="${t.accent}" stop-opacity="0.13"/><stop offset="100%" stop-color="${t.accent}" stop-opacity="0"/></radialGradient>`);
  }
  s.push('</defs>');
  if (!porcelain) s.push(`<circle cx="${cx}" cy="${cy}" r="${(R*1.28).toFixed(0)}" fill="url(#mngl)"/>`);
  s.push(`<g clip-path="url(#mnclip)">`);
  s.push(`<image href="${TEX}" x="${(cx-R*1.005).toFixed(0)}" y="${(cy-R*1.005).toFixed(0)}" width="${(R*2.01).toFixed(0)}" height="${(R*2.01).toFixed(0)}"${porcelain ? ' filter="url(#mnduo)"' : ''}/>`);
  if (lit < 0.985) {
    /* Свипы выверены матрицей фаз 06.08 (экранные координаты, y вниз):
       waxing: внешняя дуга тени слева (sweep 0); waning: справа (sweep 1);
       терминатор повторяет out при k>0 (crescent) и инвертирует при k<0 (gibbous). */
    const big = R * 1.02, rx = Math.abs(k) * big;
    const sweepOut = wax ? 0 : 1;
    const sweepIn = k > 0 ? sweepOut : 1 - sweepOut;
    const shade = porcelain ? t.page : '#04060f';
    s.push(`<path d="M ${cx} ${cy-big} A ${big} ${big} 0 0 ${sweepOut} ${cx} ${cy+big} A ${rx.toFixed(1)} ${big} 0 0 ${sweepIn} ${cx} ${cy-big} Z" fill="${shade}" opacity="${porcelain ? 0.93 : 0.96}" filter="url(#mnterm)"/>`);
  }
  s.push('</g>');
  s.push(`<circle cx="${cx}" cy="${cy}" r="${R}" fill="none" stroke="${t.accent}" stroke-width="1.2" opacity="${porcelain ? 0.75 : 0.5}"/>`);

  /* типографика — грамматика звёздного постера */
  const esc = x => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const ctext = (txt, yy, size, fill, ls) =>
    s.push(`<text x="${cx}" y="${yy}" fill="${fill}" font-family="'EB Garamond',Georgia,serif" font-size="${size}" letter-spacing="${ls}" text-anchor="middle">${esc(txt)}</text>`);
  const months = ['','JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE','JULY','AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER'];
  const [Y, MO, D] = o.dateStr.split('-').map(Number);
  const ded = (o.dedication || 'The Moon That Night').toUpperCase();
  const dsize = ded.length <= 26 ? 34 : Math.max(19, Math.round(34 * 26 / ded.length));
  ctext(ded, ty0, dsize, t.ink, ded.length <= 26 ? '4' : '2');
  const oy = ty0 + 26;
  s.push(`<line x1="${cx-130}" y1="${oy}" x2="${cx-14}" y2="${oy}" stroke="${t.accent}" stroke-width="0.8" opacity="0.7"/>`);
  s.push(`<line x1="${cx+14}" y1="${oy}" x2="${cx+130}" y2="${oy}" stroke="${t.accent}" stroke-width="0.8" opacity="0.7"/>`);
  s.push(`<path d="M ${cx} ${oy-5} L ${cx+4} ${oy} L ${cx} ${oy+5} L ${cx-4} ${oy} Z" fill="${t.accent}"/>`);
  ctext(moonTitle(age), oy + 34, 20, t.sub, '4');
  ctext(o.place.toUpperCase(), oy + 66, 21, t.sub, '6');
  ctext(`${months[MO]} ${D}, ${Y}  ·  ${o.timeStr}`, oy + 100, 19,
        porcelain ? t.ink : (o.theme === 'midnight' ? '#c9d6f2' : t.sub), '1');
  const la = `${Math.abs(o.lat).toFixed(4)}°${o.lat >= 0 ? 'N' : 'S'}`;
  const lo = `${Math.abs(o.lon).toFixed(4)}°${o.lon >= 0 ? 'E' : 'W'}`;
  ctext(`${la}   ${lo}`, oy + 132, 16, t.faint, '2');
  ctext('S K Y ,  T H A T  N I G H T', H - 58, 14, t.faint, '3');
  s.push('</svg>');
  return { svg: s.join(''), age };
}

/* ── configurator UI (грамматика starmap.js; цены и линки ОБЩИЕ со звёздным) ── */
const FRAME_TYPES = {
  print:   { label: 'Print only',    note: 'Museum-grade giclée, shipped rolled',  colors: null },
  framed:  { label: 'Framed',        note: 'Handmade wood frame, ready to hang',   colors: { white: 'White', natural: 'Natural wood' } },
  classic: { label: 'Classic frame', note: 'Gallery classic frame, ready to hang', colors: { black: 'Black', gold: 'Gold', silver: 'Silver' } },
};
const PRICES = {
  print:   { '3040': 26.99, '4050': 29.99, '5070': 32.99 },
  framed:  { '3040': 44.99, '4050': 52.99, '5070': 59.99 },
  classic: { '3040': 59.99, '4050': 69.99, '5070': 79.99 },
};
const PAYMENT_LINKS = {
  PRINT3040: 'https://buy.stripe.com/6oU5kE0kueuF0MrcRW7g409', PRINT4050: 'https://buy.stripe.com/28EbJ2aZ85Y9an1dW07g40a', PRINT5070: 'https://buy.stripe.com/aFa7sM3wG1HT52H2di7g40b',
  FRAMED3040: 'https://buy.stripe.com/5kQdRa0ku1HT7aPdW07g40c', FRAMED4050: 'https://buy.stripe.com/9B6bJ27MWgCN7aP6ty7g40d', FRAMED5070: 'https://buy.stripe.com/7sY6oI0ku3Q13YD4lq7g40e',
  CLASSIC3040: 'https://buy.stripe.com/eVqaEY7MWaep52H8BG7g40f', CLASSIC4050: 'https://buy.stripe.com/14A14o3wGfyJan119e7g40g', CLASSIC5070: 'https://buy.stripe.com/7sY3cw3wG0DP2Uz05a7g40h',
};

const state = {
  dateStr: '2021-06-19', timeStr: '21:45',
  place: 'London, United Kingdom', lat: 51.5074, lon: -0.1278, tz: 1, iana: 'Europe/London',
  dedication: 'The Moon That Night',
  theme: 'midnight', frameType: 'framed', size: '3040', frameColor: 'white',
};

function formatToken() { return state.frameType.toUpperCase() + state.size; }

function tzOffsetHours(iana, dateStr, timeStr) {
  try {
    const [y, mo, d] = dateStr.split('-').map(Number);
    const [hh, mm]   = timeStr.split(':').map(Number);
    const probe = new Date(Date.UTC(y, mo - 1, d, hh, mm));
    const part = new Intl.DateTimeFormat('en-US', { timeZone: iana, timeZoneName: 'shortOffset' })
      .formatToParts(probe).find(p => p.type === 'timeZoneName').value;
    const m = part.match(/GMT([+-]\d+)(?::(\d+))?/);
    if (!m) return 0;
    return parseInt(m[1], 10) + (m[2] ? Math.sign(parseInt(m[1],10)) * parseInt(m[2],10) / 60 : 0);
  } catch (e) { return Math.round(state.lon / 15); }
}

/* ── ГЕЙТ МЕСТА ПЕРЕД ЧЕКАУТОМ (25.08.2026, кейс Emily) — зеркало starmap.js:
   generic-дефолт (Лондон) не уезжает в оплату молча; подробный разбор в starmap.js. */
let placeConfirmed = false;
let placeGateBox = null, placeGateGo = null;

function hidePlaceGate() { if (placeGateBox) placeGateBox.hidden = true; }

function askPlaceConfirm(onKeep) {
  const echo = document.getElementById('sm-place-echo');
  const input = document.getElementById('sm-place');
  const anchor = echo || input;
  if (!anchor) { placeConfirmed = true; onKeep(); return; }   // разметки нет — покупку не запираем
  placeGateGo = onKeep;
  if (!placeGateBox) {
    placeGateBox = document.createElement('div');
    placeGateBox.className = 'sm-place-gate';
    placeGateBox.style.cssText =
      'margin:.55rem 0;padding:.7rem .9rem;border:1px solid #c9a961;border-radius:6px;' +
      'font-size:.9rem;line-height:1.5;';
    placeGateBox.innerHTML =
      'One check before payment — the moon is calculated for <strong></strong>. Is that your place?' +
      '<div style="margin-top:.55rem;display:flex;gap:.6rem;flex-wrap:wrap">' +
      '<button type="button" class="sm-gate-keep" style="background:#c9a961;color:#111;border:0;' +
      'padding:.45rem .95rem;border-radius:4px;cursor:pointer;font:inherit">Yes — that’s right</button>' +
      '<button type="button" class="sm-gate-change" style="background:transparent;color:inherit;' +
      'border:1px solid currentColor;padding:.45rem .95rem;border-radius:4px;cursor:pointer;' +
      'font:inherit;opacity:.85">No — let me type it</button></div>';
    anchor.insertAdjacentElement('afterend', placeGateBox);
    placeGateBox.querySelector('.sm-gate-keep').addEventListener('click', () => {
      placeConfirmed = true; hidePlaceGate();
      if (placeGateGo) placeGateGo();
    });
    placeGateBox.querySelector('.sm-gate-change').addEventListener('click', () => {
      hidePlaceGate();
      if (input) { input.focus(); input.select(); }
    });
  }
  placeGateBox.querySelector('strong').textContent = state.place;
  placeGateBox.hidden = false;
  placeGateBox.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/* MN2 = лунный продукт; остальная грамматика идентична SM2 — их парсит один fulfil.parse_code. */
function designCode() {
  const d = state.dateStr.replace(/-/g, '');
  const t = state.timeStr.replace(':', '');
  const la = (state.lat >= 0 ? 'N' : 'S') + Math.abs(Math.round(state.lat * 10000));
  const lo = (state.lon >= 0 ? 'E' : 'W') + Math.abs(Math.round(state.lon * 10000));
  const z = 'Z' + Math.round(state.tz * 60);
  return `MN2-${d}-${t}-${la}-${lo}-${z}-${state.theme.toUpperCase()}-${formatToken()}-${state.frameColor.toUpperCase()}`;
}

function refresh() {
  state.tz = tzOffsetHours(state.iana, state.dateStr, state.timeStr);
  const { svg, age } = renderSvg(state);
  const pv = document.getElementById('sm-preview');
  /* Анимация: терминатор ПОЛЗЁТ по луне — интерполяция возраста фазы по кратчайшей
     дуге цикла (та же механика данных, что вращение неба в starmap.js). */
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const cut = (refresh._key || '|').indexOf('|');
  const prevSize = (refresh._key || '').slice(0, cut);
  const prevTheme = (refresh._key || '').slice(cut + 1);
  const wasAnim = state._age !== undefined;
  const prevAge = wasAnim ? state._age : refresh._age;
  const fromTheme = state._themeMix || (THEMES[prevTheme] ? THEMES[prevTheme] : null);
  delete state._age; delete state._themeMix;
  if (refresh._anim) { cancelAnimationFrame(refresh._anim); refresh._anim = null; }
  if (refresh._xf) refresh._xf();
  let dA = prevAge === undefined ? 0 : age - prevAge;
  dA = ((dA + CYCLE / 2) % CYCLE + CYCLE) % CYCLE - CYCLE / 2;   // кратчайший путь по циклу
  const moonMoves = prevAge !== undefined && Math.abs(dA) > 0.01;
  const themeMoves = fromTheme && prevTheme !== state.theme;

  if (prevSize && prevSize !== state.size && !reduced) {
    const h0 = pv.offsetHeight;
    const oldSvg = pv.querySelector('svg');
    pv.innerHTML = svg;
    const h1 = pv.offsetHeight;
    if (oldSvg && Math.abs(h1 - h0) > 1) {
      pv.style.position = 'relative'; pv.style.overflow = 'hidden';
      pv.style.height = h0 + 'px';
      oldSvg.style.cssText = 'position:absolute;left:0;top:0;width:100%;transition:opacity .45s ease';
      pv.appendChild(oldSvg);
      void pv.offsetWidth;
      pv.style.transition = 'height .55s cubic-bezier(.3,.6,.2,1)';
      pv.style.height = h1 + 'px';
      oldSvg.style.opacity = '0';
      const done = () => { clearTimeout(tm); oldSvg.remove();
        for (const k of ['position','overflow','height','transition']) pv.style.removeProperty(k);
        refresh._xf = null; };
      const tm = setTimeout(done, 660);
      refresh._xf = done;
    }
  } else if ((moonMoves || themeMoves) && !reduced) {
    /* малый сдвиг даты — фаза почти та же; прокатываем терминатор через ближайшую
       выразительную дугу: минимум 6 «дней» фазы, финал всегда честный */
    if (moonMoves && Math.abs(dA) < 6) dA = (dA < 0 ? -1 : 1) * 6;
    const DUR = moonMoves ? 1800 : 900, THEME_DUR = 900, t0 = performance.now();
    const ease = p => p < 0.5 ? 4*p*p*p : 1 - Math.pow(-2*p + 2, 3) / 2;
    const toTheme = THEMES[state.theme] || THEMES.midnight;
    const target = age, from = prevAge;
    const step = now => {
      const p = Math.min(1, (now - t0) / DUR);
      if (p < 1) {
        const e = ease(p);
        if (moonMoves) state._age = ((from + dA * e) % CYCLE + CYCLE) % CYCLE;
        if (themeMoves) state._themeMix = mixThemes(fromTheme, toTheme,
          ease(Math.min(1, (now - t0) / THEME_DUR)));
        pv.innerHTML = renderSvg(state).svg;
        refresh._anim = requestAnimationFrame(step);
      } else {
        delete state._age; delete state._themeMix;
        pv.innerHTML = renderSvg(state).svg;
        refresh._anim = null;
      }
    };
    if (moonMoves) state._age = from;
    if (themeMoves) state._themeMix = mixThemes(fromTheme, toTheme, 0);
    pv.innerHTML = renderSvg(state).svg;
    refresh._anim = requestAnimationFrame(step);
  } else {
    pv.innerHTML = svg;
  }
  refresh._age = age; refresh._key = state.size + '|' + state.theme;

  const chip = document.getElementById('sm-moon');
  if (chip) chip.textContent = `☾ ${moonTitle(age).toLowerCase()} — exactly as it hung that night`;
  const ft = FRAME_TYPES[state.frameType];
  if (ft.colors && !(state.frameColor in ft.colors)) state.frameColor = Object.keys(ft.colors)[0];
  document.getElementById('sm-price').textContent = `£${PRICES[state.frameType][state.size].toFixed(2)}`;
  document.getElementById('sm-price-note').textContent = ft.note + ' · free UK delivery included';
  document.getElementById('sm-code').textContent = designCode();
  document.querySelectorAll('.sm-format').forEach(b => {
    b.querySelector('.f-price').textContent = `£${PRICES[b.dataset.frametype][state.size].toFixed(2)}`;
  });
  renderFrameColors();
  applyPreviewFrame();
}

const FRAME_ASSETS = {
  framed:  { white: 'frame-budget-white.png',  natural: 'frame-budget-natural.png' },
  classic: { black: 'frame-classic-black.png', gold: 'frame-classic-gold.png', silver: 'frame-classic-silver.png' },
};
function applyPreviewFrame() {
  const pv = document.getElementById('sm-preview');
  if (!pv) return;
  const asset = (FRAME_ASSETS[state.frameType] || {})[state.frameColor];
  if (asset) {
    const bw = Math.max(12, Math.round((pv.clientWidth || 560) * 0.06));
    pv.style.border = bw + 'px solid transparent';
    pv.style.borderImage = `url(assets/starmap/${asset}) 80 stretch`;
    pv.style.background = '#0b1220';
  } else {
    pv.style.border = 'none';
    pv.style.borderImage = 'none';
    pv.style.background = '';
  }
}
let _rsz = null;
window.addEventListener('resize', () => { clearTimeout(_rsz); _rsz = setTimeout(applyPreviewFrame, 120); });

function renderFrameColors() {
  const field = document.getElementById('sm-frame-colors');
  const row = document.getElementById('sm-frame-color-row');
  const colors = FRAME_TYPES[state.frameType].colors;
  field.style.display = colors ? '' : 'none';
  if (!colors) return;
  if (!(state.frameColor in colors)) state.frameColor = Object.keys(colors)[0];
  row.innerHTML = '';
  for (const [c, label] of Object.entries(colors)) {
    const b = document.createElement('button');
    b.className = 'sm-frame-color' + (c === state.frameColor ? ' active' : '');
    b.dataset.color = c;
    b.textContent = label;
    b.addEventListener('click', () => { state.frameColor = c; refresh(); });
    row.appendChild(b);
  }
}

function attachGeocode() {
  /* ⚠ БАГ, ПОЙМАННЫЙ НА ЖИВОМ ЗАКАЗЕ 14.08.2026 (David Simmons, £26.99).
     Раньше координаты применялись ТОЛЬКО по клику на подсказку. Человек набирал
     «Berwick», подсказку не нажимал и уходил дальше — в поле стоял Berwick, а state
     хранил координаты предыдущего места (у него — Санторини, оставшийся от игры с
     интерфейсом). В дизайн-код уходили СТАРЫЕ координаты, и на постере под словом
     BERWICK печаталось «36.3932°N 25.4615°E». Заказ спасло только окно тишины.
     Лечение из трёх частей:
       1. под полем ВСЕГДА видно, какое место реально применено (с координатами);
       2. Enter и уход из поля применяют первую подсказку сами — «набрал и ушёл»
          больше не оставляет расхождения;
       3. если текст так и не удалось привязать к точке, поле возвращается к
          подтверждённому месту, а не притворяется, что выбор состоялся. */
  const input = document.getElementById('sm-place');
  const list  = document.getElementById('sm-place-results');
  const echo  = document.getElementById('sm-place-echo');
  let timer = null, lastResults = [], appliedAt = 0;

  function showEcho(warn) {
    if (!echo) return;
    echo.textContent = (warn ? '⚠ ' : '✦ ') + state.place +
      '  ·  ' + Math.abs(state.lat).toFixed(4) + (state.lat >= 0 ? '°N ' : '°S ') +
      Math.abs(state.lon).toFixed(4) + (state.lon >= 0 ? '°E' : '°W');
    echo.className = warn ? 'sm-place-echo warn' : 'sm-place-echo';
  }

  function apply(res) {
    state.place = [res.name, res.country].filter(Boolean).join(', ');
    state.lat = res.latitude; state.lon = res.longitude;
    state.iana = res.timezone || 'UTC';
    input.value = state.place;
    list.hidden = true;
    appliedAt = Date.now();
    placeConfirmed = true;      // место привязано человеком — гейт перед оплатой пройден
    hidePlaceGate();
    showEcho(false);
    refresh();
  }

  /* ⚠ Автовыбор БЕЗ клика обязан быть консервативным. Проверка фикса 14.08: на запрос
     «Berwick» геокодер первым отдаёт Berwick в Пенсильвании, а покупатель почти наверняка
     имел в виду Berwick-upon-Tweed — доставка у нас бесплатная только по UK, и все заказы
     до сих пор были британские. Поэтому при АВТОприменении предпочитаем UK-результат,
     если он есть в выдаче. Явный клик по подсказке этим правилом не трогается: человек
     выбрал сам, и спорить с ним нельзя. */
  function preferred(results) {
    return results.find(r => r.country_code === 'GB') || results[0];
  }

  /* ⚠ БРИТАНСКИЕ МЕСТА ПЕРВЫМИ (14.08.2026). Геокодер на запрос «Berwick» отдаёт ТОЛЬКО
     американские города — Berwick-upon-Tweed в общей выдаче не появляется вообще, и
     покупатель физически не может его выбрать. При этом тот же запрос с countryCode=GB
     находит его сразу. Поэтому спрашиваем дважды и склеиваем: сначала UK, затем мир.
     Для не-британских запросов UK-выдача пустая (проверено на «Santorini» — 0), так что
     ничего не ломается. Все заказы до сих пор были британские, доставка бесплатна по UK. */
  async function search(q) {
    const url = extra => `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q)}&count=5&language=en&format=json${extra}`;
    const get = async u => { try { const r = await fetch(u); return (await r.json()).results || []; } catch (e) { return []; } };
    const [uk, world] = await Promise.all([get(url('&countryCode=GB')), get(url(''))]);
    const seen = new Set(), out = [];
    for (const r of uk.concat(world)) {
      const k = r.latitude.toFixed(3) + ',' + r.longitude.toFixed(3);
      if (seen.has(k)) continue;
      seen.add(k); out.push(r);
    }
    return out.slice(0, 6);
  }

  input.addEventListener('input', () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (q.length < 2) { list.hidden = true; return; }
    /* пока текст не привязан к точке — честно говорим, что применено ещё старое место */
    if (q !== state.place) showEcho(true);
    timer = setTimeout(async () => {
      lastResults = await search(q);
      list.innerHTML = '';
      lastResults.forEach(res => {
        const li = document.createElement('li');
        li.textContent = [res.name, res.admin1, res.country].filter(Boolean).join(', ');
        li.addEventListener('click', () => apply(res));
        list.appendChild(li);
      });
      list.hidden = lastResults.length === 0;
    }, 250);
  });

  /* Enter — выбрать первое совпадение, не заставляя целиться мышью */
  input.addEventListener('keydown', async e => {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    const q = input.value.trim();
    if (!q || q === state.place) { list.hidden = true; return; }
    const res = lastResults.length ? lastResults : await search(q);
    if (res.length) apply(preferred(res)); else revert();
  });

  /* Ушёл из поля, ничего не выбрав — применяем сами или откатываем.
     ⚠ Нельзя выходить по `list.hidden`: при клике МЫШЬЮ по подсказке blur срабатывает
     РАНЬШЕ click, и список ещё открыт — проверка «список открыт → выйти» глушила
     автоприменение вообще (поймано при проверке фикса 14.08). Поэтому ждём 250 мс и
     смотрим на флаг: успел ли клик применить место за это время. */
  input.addEventListener('blur', () => {
    const left = Date.now();
    setTimeout(async () => {
      if (appliedAt > left) return;           // клик по подсказке уже всё сделал
      const q = input.value.trim();
      if (!q || q === state.place) return;
      const res = lastResults.length ? lastResults : await search(q);
      if (res.length) apply(preferred(res)); else revert();
    }, 250);
  });

  function revert() {
    input.value = state.place;
    list.hidden = true;
    showEcho(false);
  }

  document.addEventListener('click', e => {
    if (!list.contains(e.target) && e.target !== input) list.hidden = true;
  });
  showEcho(false);
}

function attachControls() {
  document.getElementById('sm-date').addEventListener('change', e => { if (e.target.value) { state.dateStr = e.target.value; refresh(); } });
  document.getElementById('sm-time').addEventListener('change', e => { if (e.target.value) { state.timeStr = e.target.value; refresh(); } });
  document.getElementById('sm-dedication').addEventListener('input', e => {
    state.dedication = e.target.value.slice(0, 40);
    refresh();
  });
  document.querySelectorAll('.sm-theme').forEach(btn => btn.addEventListener('click', () => {
    state.theme = btn.dataset.theme;
    document.querySelectorAll('.sm-theme').forEach(b => b.classList.toggle('active', b === btn));
    refresh();
  }));
  document.querySelectorAll('.sm-size').forEach(btn => btn.addEventListener('click', () => {
    state.size = btn.dataset.size;
    document.querySelectorAll('.sm-size').forEach(b => b.classList.toggle('active', b === btn));
    refresh();
  }));
  document.querySelectorAll('.sm-format').forEach(btn => btn.addEventListener('click', () => {
    state.frameType = btn.dataset.frametype;
    document.querySelectorAll('.sm-format').forEach(b => b.classList.toggle('active', b === btn));
    refresh();
  }));
  
  // CRO 01.09.2026: сильнейший наш процесс — превью до печати — теперь виден у кнопки
  (() => {
    const btn = document.getElementById('sm-buy');
    if (btn && !document.querySelector('.sm-preview-note')) {
      const n = document.createElement('div');
      n.className = 'sm-preview-note';
      n.textContent = "\u2713\u00a0 Free preview by email before we print \u2014 we'll fix anything";
      btn.insertAdjacentElement('afterend', n);
    }
  })();
  document.getElementById('sm-buy').addEventListener('click', () => {
    const go = () => {
      const link = PAYMENT_LINKS[formatToken()];
      const code = designCode();
      if (link) {
        window.location.href = `${link}?client_reference_id=${encodeURIComponent(code)}`;
      } else {
        const box = document.getElementById('sm-checkout-note');
        box.hidden = false;
        box.querySelector('code').textContent = code;
      }
    };
    /* 300 мс — даём blur-автоприменению поля места успеть (см. starmap.js) */
    setTimeout(() => { placeConfirmed ? go() : askPlaceConfirm(go); }, 300);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  if (window.MN_PRESET) {
    Object.assign(state, window.MN_PRESET);
    /* пресет места страницей = осознанный выбор, гейт не нужен */
    if ('place' in window.MN_PRESET || 'lat' in window.MN_PRESET) placeConfirmed = true;
  }
  document.getElementById('sm-date').value = state.dateStr;
  document.getElementById('sm-time').value = state.timeStr;
  document.getElementById('sm-place').value = state.place;
  document.getElementById('sm-dedication').value = state.dedication;
  document.querySelectorAll('.sm-theme').forEach(b => b.classList.toggle('active', b.dataset.theme === state.theme));
  document.querySelectorAll('.sm-size').forEach(b => b.classList.toggle('active', b.dataset.size === state.size));
  document.querySelectorAll('.sm-format').forEach(b => b.classList.toggle('active', b.dataset.frametype === state.frameType));
  attachGeocode();
  attachControls();
  refresh();
});
})();
