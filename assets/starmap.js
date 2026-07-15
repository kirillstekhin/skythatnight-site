/* SHOPCIENTY star-map configurator — browser port of starmap_v3.py.
   Preview only: the authoritative print file is rendered server-side from the same params. */
(function () {
'use strict';

/* ───────────────────────── astro engine ───────────────────────── */

function julianDate(y, mo, d, utHours) {
  return 367 * y - Math.floor(7 * (y + Math.floor((mo + 9) / 12)) / 4)
       + Math.floor(275 * mo / 9) + d + 1721013.5 + utHours / 24.0;
}
function lstDeg(dateStr, timeStr, lon, tzOffset) {
  const [y, mo, d] = dateStr.split('-').map(Number);
  const [hh, mm]   = timeStr.split(':').map(Number);
  const ut = hh + mm / 60 - tzOffset;
  const jd = julianDate(y, mo, d, ut);
  const T  = jd - 2451545.0;
  const gmst = ((280.46061837 + 360.98564736629 * T) % 360 + 360) % 360;
  return { lst: ((gmst + lon) % 360 + 360) % 360, jd };
}
function altAz(raDeg, decDeg, lst, latDeg) {
  const ha   = ((lst - raDeg) % 360 + 360) % 360 * Math.PI / 180;
  const dec  = decDeg * Math.PI / 180;
  const lat  = latDeg * Math.PI / 180;
  const sinA = Math.sin(dec) * Math.sin(lat) + Math.cos(dec) * Math.cos(lat) * Math.cos(ha);
  const alt  = Math.asin(Math.max(-1, Math.min(1, sinA)));
  const cosZ = (Math.sin(dec) - Math.sin(lat) * sinA) / (Math.cos(lat) * Math.cos(alt) + 1e-12);
  let az = Math.acos(Math.max(-1, Math.min(1, cosZ)));
  if (Math.sin(ha) > 0) az = 2 * Math.PI - az;
  return [alt, az];
}
function project(alt, az, cx, cy, R) {
  const r = (Math.PI / 2 - alt) / (Math.PI / 2);
  return [cx + R * r * Math.sin(az), cy - R * r * Math.cos(az)];
}
function moonPhase(jd) {
  const age  = ((jd - 2451550.1) % 29.530588853 + 29.530588853) % 29.530588853;
  const lit  = (1 - Math.cos(2 * Math.PI * age / 29.530588853)) / 2;
  return { age, lit, waxing: age < 14.765 };
}
function moonName(p) {
  if (p.lit < 0.04)  return 'New moon';
  if (p.lit > 0.96)  return 'Full moon';
  if (Math.abs(p.lit - 0.5) < 0.06) return p.waxing ? 'First quarter' : 'Last quarter';
  if (p.lit < 0.5)   return p.waxing ? 'Waxing crescent' : 'Waning crescent';
  return p.waxing ? 'Waxing gibbous' : 'Waning gibbous';
}

/* ───────────────────────── themes (mirror of starmap_v3.THEMES) ───────────────────────── */

const THEMES = {
  midnight: { page:'#0b1733', sky:'#0a1430', ink:'#eaf0ff', sub:'#8fb0e6', faint:'#6f8bc0',
              star:'#ffffff', ring:'#3a5a9a', grid:'#20345f', lines:'#4f6fa8', lineOp:0.34,
              accent:'#8fb0e6', lineW:0.7, label:'Midnight' },
  luxegold: { page:'#0b1733', sky:'#0a1430', ink:'#eaf0ff', sub:'#8fb0e6', faint:'#6f8bc0',
              star:'#ffffff', ring:'#c9a961', grid:'#20345f', lines:'#4f6fa8', lineOp:0.34,
              accent:'#c9a961', lineW:0.7, label:'Luxe · Gold' },
  luxesilver:{ page:'#0b1733', sky:'#0a1430', ink:'#eaf0ff', sub:'#8fb0e6', faint:'#6f8bc0',
              star:'#ffffff', ring:'#c3ccd8', grid:'#20345f', lines:'#4f6fa8', lineOp:0.34,
              accent:'#c3ccd8', lineW:0.7, label:'Luxe · Silver' },
  porcelain:{ page:'#f5f2ea', sky:'#f5f2ea', ink:'#0d1830', sub:'#33496e', faint:'#5f7396',
              star:'#0d1830', ring:'#0f1b33', grid:'#ccd3e0', lines:'#2c4269', lineOp:0.82,
              accent:'#243a63', lineW:1.6, dotScale:1.8, opMin:0.78, opBase:0.68, label:'Porcelain' },
  noir:     { page:'#060608', sky:'#060608', ink:'#e8dcc0', sub:'#c9a961', faint:'#8a7845',
              star:'#f5efe0', ring:'#c9a961', grid:'#1d1a12', lines:'#8a7845', lineOp:0.32,
              accent:'#c9a961', lineW:0.7, label:'Noir' },
};

const NAMED = [
  ['Sirius',101.29,-16.72,-1.46],['Canopus',95.99,-52.70,-0.74],['Arcturus',213.92,19.18,-0.05],
  ['Vega',279.23,38.78,0.03],['Capella',79.17,46.00,0.08],['Rigel',78.63,-8.20,0.13],
  ['Procyon',114.83,5.23,0.34],['Betelgeuse',88.79,7.41,0.42],['Altair',297.69,8.87,0.77],
  ['Aldebaran',68.99,16.51,0.85],['Antares',247.35,-26.43,0.96],['Spica',201.30,-11.16,0.98],
  ['Deneb',310.35,45.28,1.25],['Polaris',37.95,89.26,1.98],
];

/* ───────────────────────── SVG renderer ───────────────────────── */

let CATALOG = null; // {stars:[[ra,dec,mag]...], lines:[[[ra,dec],...],...]}

function esc(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function moonIconSvg(cx, cy, r, phase, fill, ring) {
  const k = Math.cos(2 * Math.PI * phase.age / 29.530588853);
  const lit = 1 - (k + 1) / 2;
  let s = `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${ring}" stroke-width="0.8" opacity="0.7"/>`;
  if (lit < 0.02) return s;
  const big = r - 0.6;
  if (lit > 0.98) return s + `<circle cx="${cx}" cy="${cy}" r="${big}" fill="${fill}" opacity="0.9"/>`;
  const side = phase.waxing ? 1 : -1;
  const rx = Math.abs(k) * big;
  const sweepOut = side === 1 ? 1 : 0;
  const sweepIn  = side === 1 ? (k < 0 ? 1 : 0) : (k < 0 ? 0 : 1);
  s += `<path d="M ${cx} ${cy - big} A ${big} ${big} 0 0 ${sweepOut} ${cx} ${cy + big} A ${rx.toFixed(2)} ${big} 0 0 ${sweepIn} ${cx} ${cy - big} Z" fill="${fill}" opacity="0.9"/>`;
  return s;
}

/* Аспект = print-area Prodigi (иначе печать обрежет постер):
   30x40cm (12x16") → 3:4 · 40x50cm (16x20") → 4:5. Превью ОБЯЗАНО совпадать с печатью. */
const PRINT_SIZES = { '30x40': 4 / 3, '40x50': 5 / 4 };            // H/W
const FORMAT_SIZE = { print: '30x40', framed: '30x40', framedXL: '40x50' };

function renderSvg(o) {
  // o: {dateStr,timeStr,lat,lon,tz,place,dedication,theme,format}
  const t = THEMES[o.theme] || THEMES.midnight;
  const W = 1200;
  const H = Math.round(W * PRINT_SIZES[FORMAT_SIZE[o.format] || '30x40']);
  const MOON_R = 16;
  const TEXT_H = 108 + (2 * MOON_R + 9) + 136;   // круг → луна → посвящение/место/дата/координаты
  const region = H - 58;                          // полезная высота над строкой бренда
  const R = Math.min(0.4167 * W, (region - TEXT_H - 180) / 2);
  const top = (region - (2 * R + TEXT_H)) / 2;    // остаток поровну → композиция сбалансирована
  const cx = W / 2, cy = top + R;
  const { lst, jd } = lstDeg(o.dateStr, o.timeStr, o.lon, o.tz);
  const s = [`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}">`];
  s.push(`<defs><clipPath id="skyclip"><circle cx="${cx}" cy="${cy}" r="${R}"/></clipPath></defs>`);
  s.push(`<rect width="${W}" height="${H}" fill="${t.page}"/>`);
  // passe-partout border
  s.push(`<rect x="34" y="34" width="${W-68}" height="${H-68}" fill="none" stroke="${t.accent}" stroke-width="1.4" opacity="0.9"/>`);
  s.push(`<rect x="44" y="44" width="${W-88}" height="${H-88}" fill="none" stroke="${t.accent}" stroke-width="0.6" opacity="0.7"/>`);
  s.push(`<circle cx="${cx}" cy="${cy}" r="${R}" fill="${t.sky}"/>`);

  // constellation lines
  s.push(`<g clip-path="url(#skyclip)" stroke="${t.lines}" stroke-opacity="${t.lineOp}" stroke-width="${t.lineW}" fill="none" stroke-linecap="round">`);
  for (const line of CATALOG.lines) {
    let path = '', pen = false, below = 0;
    for (const [ra, dec] of line) {
      const [alt, az] = altAz(ra, dec, lst, o.lat);
      if (alt < -0.14) { below++; }
      const [x, y] = project(alt, az, cx, cy, R);
      path += (pen ? 'L' : 'M') + x.toFixed(1) + ',' + y.toFixed(1);
      pen = true;
    }
    if (below < line.length) s.push(`<path d="${path}"/>`);
  }
  s.push('</g>');

  // grid + ring + ticks
  s.push(`<circle cx="${cx}" cy="${cy}" r="${(R/3).toFixed(1)}" fill="none" stroke="${t.grid}" stroke-width="1"/>`);
  s.push(`<circle cx="${cx}" cy="${cy}" r="${(2*R/3).toFixed(1)}" fill="none" stroke="${t.grid}" stroke-width="1"/>`);
  s.push(`<circle cx="${cx}" cy="${cy}" r="${R}" fill="none" stroke="${t.ring}" stroke-width="1.6"/>`);
  s.push(`<circle cx="${cx}" cy="${cy}" r="${R+13}" fill="none" stroke="${t.ring}" stroke-width="0.6" opacity="0.65"/>`);
  for (let deg = 0; deg < 360; deg += 5) {
    const a = deg * Math.PI / 180;
    const L = deg % 45 === 0 ? 14 : deg % 15 === 0 ? 9 : 5;
    const x1 = cx + (R-2) * Math.sin(a), y1 = cy - (R-2) * Math.cos(a);
    const x2 = cx + (R-2-L) * Math.sin(a), y2 = cy - (R-2-L) * Math.cos(a);
    s.push(`<line x1="${x1.toFixed(1)}" y1="${y1.toFixed(1)}" x2="${x2.toFixed(1)}" y2="${y2.toFixed(1)}" stroke="${t.ring}" stroke-width="${deg%45===0?1.2:0.6}" opacity="${deg%45===0?0.9:0.45}"/>`);
  }

  // stars
  s.push(`<g clip-path="url(#skyclip)">`);
  for (const [ra, dec, mag] of CATALOG.stars) {
    const [alt, az] = altAz(ra, dec, lst, o.lat);
    if (alt <= 0.01) continue;
    const [x, y] = project(alt, az, cx, cy, R);
    const base = Math.max(7.2 - mag, 0.35);
    const rad = Math.max(0.5, 0.30 * Math.pow(base, 1.25)) * (t.dotScale || 1);
    const op  = Math.max(t.opMin || 0.25, Math.min(1, (t.opBase || 0.30) + (7.0 - mag) * 0.11));
    if (mag < 1.6) s.push(`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(rad*2.2).toFixed(1)}" fill="${t.star}" opacity="0.16"/>`);
    s.push(`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${rad.toFixed(2)}" fill="${t.star}" fill-opacity="${op.toFixed(2)}"/>`);
  }
  s.push('</g>');

  // labels
  for (const [name, ra, dec, mag] of NAMED) {
    if (mag > 1.05) continue;
    const [alt, az] = altAz(ra, dec, lst, o.lat);
    if (alt < 0.07) continue;
    const [x, y] = project(alt, az, cx, cy, R);
    s.push(`<text x="${(x+7).toFixed(1)}" y="${(y+3).toFixed(1)}" fill="${t.sub}" fill-opacity="0.85" font-family="'EB Garamond',Georgia,serif" font-size="12">${name}</text>`);
  }

  // compass
  for (const [ang, lab] of [[0,'N'],[90,'E'],[180,'S'],[270,'W']]) {
    const a = ang * Math.PI / 180;
    s.push(`<text x="${(cx+(R+28)*Math.sin(a)).toFixed(1)}" y="${(cy-(R+28)*Math.cos(a)+8).toFixed(1)}" fill="${t.accent}" font-family="'EB Garamond',Georgia,serif" font-size="24" text-anchor="middle">${lab}</text>`);
  }

  // typography block
  const months = ['','January','February','March','April','May','June','July','August','September','October','November','December'];
  const [Y, MO, D] = o.dateStr.split('-').map(Number);
  const phase = moonPhase(jd);
  let ty = cy + R + 108;
  s.push(`<g>${moonIconSvg(cx, ty - 17, 16, phase, o.theme === 'porcelain' ? t.ink : t.star, t.accent)}</g>`);
  ty += 41;
  const ded = (o.dedication || 'Sky That Night').toUpperCase();
  s.push(`<text x="${cx}" y="${ty}" fill="${t.ink}" font-family="'EB Garamond',Georgia,serif" font-size="34" letter-spacing="4" text-anchor="middle">${esc(ded)}</text>`);
  const oy = ty + 26;
  s.push(`<line x1="${cx-130}" y1="${oy}" x2="${cx-14}" y2="${oy}" stroke="${t.accent}" stroke-width="0.8" opacity="0.7"/>`);
  s.push(`<line x1="${cx+14}" y1="${oy}" x2="${cx+130}" y2="${oy}" stroke="${t.accent}" stroke-width="0.8" opacity="0.7"/>`);
  s.push(`<path d="M ${cx} ${oy-5} L ${cx+4} ${oy} L ${cx} ${oy+5} L ${cx-4} ${oy} Z" fill="${t.accent}"/>`);
  s.push(`<text x="${cx}" y="${oy+34}" fill="${t.sub}" font-family="'EB Garamond',Georgia,serif" font-size="21" letter-spacing="6" text-anchor="middle">${esc((o.place||'').toUpperCase())}</text>`);
  s.push(`<text x="${cx}" y="${oy+68}" fill="${o.theme==='porcelain'?t.ink:'#c9d6f2'}" font-family="'EB Garamond',Georgia,serif" font-size="19" letter-spacing="1" text-anchor="middle">${months[MO]} ${D}, ${Y}  ·  ${o.timeStr}</text>`);
  const latS = Math.abs(o.lat).toFixed(4) + '°' + (o.lat >= 0 ? 'N' : 'S');
  const lonS = Math.abs(o.lon).toFixed(4) + '°' + (o.lon >= 0 ? 'E' : 'W');
  s.push(`<text x="${cx}" y="${oy+100}" fill="${t.faint}" font-family="'EB Garamond',Georgia,serif" font-size="16" letter-spacing="2" text-anchor="middle">${latS}   ${lonS}</text>`);
  s.push(`<text x="${cx}" y="${H-58}" fill="${t.faint}" font-family="'EB Garamond',Georgia,serif" font-size="14" letter-spacing="3" text-anchor="middle">S K Y ,  T H A T  N I G H T</text>`);
  s.push('</svg>');
  return { svg: s.join(''), phase };
}

/* ───────────────────────── configurator UI ───────────────────────── */

const FORMATS = {
  print:    { label: 'Print only · 30×40 cm',       price: 39, note: 'Museum-grade giclée, shipped rolled' },
  framed:   { label: 'Framed · 30×40 cm',           price: 49, note: 'Handmade wood frame, ready to hang' },
  framedXL: { label: 'Framed large · 40×50 cm',     price: 64, note: 'Our statement size' },
};

/* Stripe Payment Links — вставить URL после создания в Stripe Dashboard (см. STRIPE_SETUP.md).
   Каждой ссылке добавляется ?client_reference_id=<design code> автоматически. */
const PAYMENT_LINKS = {
  // LIVE links (13.07, account activated)
  print:    'https://buy.stripe.com/dRm4gA3wGbitdzd2di7g400',
  framed:   'https://buy.stripe.com/eVq5kE3wG0DP1Qv4lq7g401',
  framedXL: 'https://buy.stripe.com/8x26oI3wGcmxeDh05a7g402',
};

const state = {
  dateStr: '2021-06-19', timeStr: '21:45',
  place: 'London, United Kingdom', lat: 51.5074, lon: -0.1278, tz: 1, iana: 'Europe/London',
  dedication: 'Sky That Night',
  theme: 'midnight', format: 'framed', frameColor: 'white',
};

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

/* SM2: включает часовой пояс (Z<минуты, со знаком>). Без него сервер отрендерил бы
   небо другого часа, чем видел клиент — печать не совпала бы с превью. */
function designCode() {
  const d = state.dateStr.replace(/-/g, '');
  const t = state.timeStr.replace(':', '');
  const la = (state.lat >= 0 ? 'N' : 'S') + Math.abs(Math.round(state.lat * 10000));
  const lo = (state.lon >= 0 ? 'E' : 'W') + Math.abs(Math.round(state.lon * 10000));
  const z = 'Z' + Math.round(state.tz * 60);   // смещение в минутах, напр. Z60 / Z-300
  return `SM2-${d}-${t}-${la}-${lo}-${z}-${state.theme.toUpperCase()}-${state.format.toUpperCase()}-${state.frameColor.toUpperCase()}`;
}

function refresh() {
  state.tz = tzOffsetHours(state.iana, state.dateStr, state.timeStr);
  const { svg, phase } = renderSvg(state);
  document.getElementById('sm-preview').innerHTML = svg;
  const chip = document.getElementById('sm-moon');
  chip.textContent = `☾ ${moonName(phase)} — the real moon of your night`;
  const f = FORMATS[state.format];
  document.getElementById('sm-price').textContent = `£${f.price}`;
  document.getElementById('sm-price-note').textContent = f.note + ' · free UK delivery included';
  document.getElementById('sm-code').textContent = designCode();
  const frameRow = document.getElementById('sm-frame-colors');
  frameRow.style.display = state.format === 'print' ? 'none' : '';
}

function attachGeocode() {
  const input = document.getElementById('sm-place');
  const list  = document.getElementById('sm-place-results');
  let timer = null;
  input.addEventListener('input', () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (q.length < 2) { list.hidden = true; return; }
    timer = setTimeout(async () => {
      try {
        const r = await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q)}&count=5&language=en&format=json`);
        const j = await r.json();
        list.innerHTML = '';
        (j.results || []).forEach(res => {
          const label = [res.name, res.admin1, res.country].filter(Boolean).join(', ');
          const li = document.createElement('li');
          li.textContent = label;
          li.addEventListener('click', () => {
            state.place = [res.name, res.country].filter(Boolean).join(', ');
            state.lat = res.latitude; state.lon = res.longitude;
            state.iana = res.timezone || 'UTC';
            input.value = state.place;
            list.hidden = true;
            refresh();
          });
          list.appendChild(li);
        });
        list.hidden = (j.results || []).length === 0;
      } catch (e) { list.hidden = true; }
    }, 250);
  });
  document.addEventListener('click', e => { if (!list.contains(e.target) && e.target !== input) list.hidden = true; });
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
  document.querySelectorAll('.sm-format').forEach(btn => btn.addEventListener('click', () => {
    state.format = btn.dataset.format;
    document.querySelectorAll('.sm-format').forEach(b => b.classList.toggle('active', b === btn));
    refresh();
  }));
  document.querySelectorAll('.sm-frame-color').forEach(btn => btn.addEventListener('click', () => {
    state.frameColor = btn.dataset.color;
    document.querySelectorAll('.sm-frame-color').forEach(b => b.classList.toggle('active', b === btn));
    refresh();
  }));
  document.getElementById('sm-buy').addEventListener('click', () => {
    const link = PAYMENT_LINKS[state.format];
    const code = designCode();
    if (link) {
      window.location.href = `${link}?client_reference_id=${encodeURIComponent(code)}`;
    } else {
      const box = document.getElementById('sm-checkout-note');
      box.hidden = false;
      box.querySelector('code').textContent = code;
    }
  });
}

/* ───────────────────────── boot ───────────────────────── */

document.addEventListener('DOMContentLoaded', async () => {
  if (window.SM_PRESET) Object.assign(state, window.SM_PRESET);
  try {
    const r = await fetch('assets/starmap-data.json');
    CATALOG = await r.json();
  } catch (e) {
    document.getElementById('sm-preview').innerHTML =
      '<p style="padding:2rem;text-align:center;">Preview unavailable — please refresh.</p>';
    return;
  }
  document.getElementById('sm-date').value = state.dateStr;
  document.getElementById('sm-time').value = state.timeStr;
  document.getElementById('sm-place').value = state.place;
  document.getElementById('sm-dedication').value = state.dedication;
  document.querySelectorAll('.sm-theme').forEach(b => b.classList.toggle('active', b.dataset.theme === state.theme));
  document.querySelectorAll('.sm-format').forEach(b => b.classList.toggle('active', b.dataset.format === state.format));
  document.querySelectorAll('.sm-frame-color').forEach(b => b.classList.toggle('active', b.dataset.color === state.frameColor));
  attachGeocode();
  attachControls();
  refresh();
});
})();
