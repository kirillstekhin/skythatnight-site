/**
 * Sky, That Night — сохранение дизайна (звёздная карта и Луна) и выдача оплаты. Cloudflare Pages Function.
 * Проект: platform/DESIGN_STORE_SKN_PLAN.md · образец: platform/natal/site/functions/api/design.js (Ortus)
 * Пара на чтение: tools/design_store.py (SKN_PRODUCTS, SKN), fulfil.personalisation (ветка d_).
 *
 * ЗАЧЕМ (11.10.2026, решение владельца). Код SM2/MN2 не несёт ни подписи, ни названия места: их
 * перепечатывали в необязательные поля Payment Link, и при пустом поле печаталось «Sky That Night»
 * (6 из 12 оплат сайта на 10.10), а при пустом месте заказ стоял до ответа покупателя. Здесь сайт
 * сохраняет дизайн целиком — ровно то, что было в превью, — и получает ссылку на оплату. Покупатель
 * вводит данные ОДИН раз.
 *
 * ⛔ТОЛЬКО ЗАПИСЬ. Чтения нет: в записи место и личная подпись. Читает фулфилмент, отдельным ключом.
 * ⛔ССЫЛКА — ТОЛЬКО ПОСЛЕ УСПЕШНОЙ ЗАПИСИ. Ошибка R2 = 503 и никакой ссылки.
 * ⛔ЦЕНУ ВЫБИРАЕТ СЕРВЕР по доверенной сетке — суммы в теле запроса нет вовсе.
 * ⛔В ЛОГИ НЕ ПИСАТЬ ПЕРСОНАЛЬНОЕ: ни места, ни подписи — только id и код ошибки.
 * ⚠️ВАЛИДАЦИЯ ОБЯЗАНА СОВПАДАТЬ С PYTHON: platform/design_store_cases_skn.json гоняют оба
 *   (tools/design_store_parity.py).
 *
 * Идемпотентность, попытки, надгробия, сверка режима — ровно как у Ortus (там подробные причины
 * каждого правила, здесь они не повторяются, чтобы не разъехаться):
 *   ①попытка фиксируется до первого запроса; ②повтор шлёт Stripe те же параметры с тем же ключом;
 *   ③потерянный ответ не теряет сессию; ④попытка привязана к содержимому; ⑤удалённый дизайн не
 *   воскрешается; режим (STRIPE_MODE ↔ ключ ↔ таблица ↔ livemode сессии) сверяется трижды.
 *
 * ОТЛИЧИЕ ОТ ORTUS — АТРИБУЦИЯ. В client_reference_id кроме `d_<id>` едут метка канала `_c1_<канал>`
 * и токен `_a1_<токен>` (как у старого пути, site/assets/attr.js buildRef; разбор —
 * fulfil.split_client_reference). Они не входят в отпечаток содержимого (на печать не влияют) и
 * фиксируются в параметрах попытки при ПЕРВОМ запросе: повтор идёт с тем же ключом идемпотентности,
 * значит и с теми же параметрами. Не влезает в 200 — теряем токен, потом канал, но не заказ.
 *
 * Привязки (Pages): R2 `DESIGNS` (приватный bucket skn-designs) · секреты STRIPE_MODE, STRIPE_KEY.
 * Нет привязки или ключа — 503 not_configured, и сайт уходит по старой Payment Link (assets/starmap.js).
 */

export const SCHEMA_VERSION = 2;
export const MAX_BODY = 4096;
export const LIMITS = { place: 80, dedication: 40 };
const RATE_WINDOW_S = 60;
const RATE_MAX = 10;

export const CODE_RE =
  /^(SM2|MN2|NT2|FC2|CP2)-(\d{8})-(\d{4})-([NS])(\d+)-([EW])(\d+)-Z(-?\d+)-([A-Z]+)-([A-Z0-9]+)-([A-Z]+)$/;
export const PRODUCTS = ["sky", "moon"];
export const PREFIX = { sky: "SM2", moon: "MN2" };
const CHANNEL_RE = /^[a-z0-9-]{1,24}$/;          // = attr.js CHANNEL_RE
const TOKEN_RE = /^t[a-z2-7]{26}$/;              // = attr.js TOKEN_RE
const CLIENT_REF_MAX = 200;                      // предел Stripe
const RETURN_RE = /^\/[a-z0-9][a-z0-9\-_.\/]{0,118}$|^\/$/i;

/* ⛔ДОВЕРЕННАЯ СЕТКА ПО РЕЖИМАМ. Боевые Price — из line_items действующих Payment Links SKN (10.10).
   Тестовые заполняет tools/stripe_test_catalog.py --brand skn. Зеркало design_store.SKN. */
export const SKN = {
  live: {
    "sky/PRINT3040": { pence: 3499, price: "price_1UEUkyK6RIyYA8uFt2PO9JNS" },
    "sky/PRINT4050": { pence: 3999, price: "price_1UEUkzK6RIyYA8uF1h4ifyl2" },
    "sky/PRINT5070": { pence: 4499, price: "price_1UEUl0K6RIyYA8uFXCOr27Dv" },
    "sky/CLASSIC3040": { pence: 6999, price: "price_1UFEVaK6RIyYA8uFVqmIGWwr" },
    "sky/CLASSIC4050": { pence: 7999, price: "price_1UFEVxK6RIyYA8uFDRGqjJVY" },
    "sky/CLASSIC5070": { pence: 8999, price: "price_1UFEVzK6RIyYA8uFOj0OvWQt" },
    "moon/PRINT3040": { pence: 3499, price: "price_1UJehmK6RIyYA8uFzxSQrOk8" },
    "moon/PRINT4050": { pence: 3999, price: "price_1UJehoK6RIyYA8uFO7Cv1kSW" },
    "moon/PRINT5070": { pence: 4499, price: "price_1UJehqK6RIyYA8uF5CNpSL6R" },
    "moon/CLASSIC3040": { pence: 6999, price: "price_1UJehrK6RIyYA8uFX1kylRH3" },
    "moon/CLASSIC4050": { pence: 7999, price: "price_1UJehtK6RIyYA8uFOzZlKWPm" },
    "moon/CLASSIC5070": { pence: 8999, price: "price_1UJehuK6RIyYA8uFvBpLyq6q" },
  },
  test: {
    "sky/PRINT3040": { pence: 3499, price: "price_1UPI2AK6RIyYA8uFVtCIOojK" },
    "sky/PRINT4050": { pence: 3999, price: "price_1UPI2CK6RIyYA8uFPQXCZjdF" },
    "sky/PRINT5070": { pence: 4499, price: "price_1UPI2EK6RIyYA8uFcA2cyJ29" },
    "sky/CLASSIC3040": { pence: 6999, price: "price_1UPI2GK6RIyYA8uFZhd1UILl" },
    "sky/CLASSIC4050": { pence: 7999, price: "price_1UPI2HK6RIyYA8uFcQHRDNkJ" },
    "sky/CLASSIC5070": { pence: 8999, price: "price_1UPI2JK6RIyYA8uFEAAhJleg" },
    "moon/PRINT3040": { pence: 3499, price: "price_1UPI2LK6RIyYA8uFHlP22q47" },
    "moon/PRINT4050": { pence: 3999, price: "price_1UPI2NK6RIyYA8uFLBogZKVH" },
    "moon/PRINT5070": { pence: 4499, price: "price_1UPI2PK6RIyYA8uFlX2O8xoi" },
    "moon/CLASSIC3040": { pence: 6999, price: "price_1UPI2QK6RIyYA8uFOAWikUy3" },
    "moon/CLASSIC4050": { pence: 7999, price: "price_1UPI2SK6RIyYA8uFnwKywLQg" },
    "moon/CLASSIC5070": { pence: 8999, price: "price_1UPI2UK6RIyYA8uFvzYqHdEG" },
  },
};
const GRID_KEYS = Object.keys(SKN.live);
const MODE_KEY_RE = { test: /^(sk|rk)_test_/, live: /^(sk|rk)_live_/ };

/* Страница оплаты повторяет Payment Links SKN (сняты 10.10): тексты, страны, «спасибо» с SKU. */
const SUBMIT_TEXT = {
  sky: "Before anything is printed we email you your finished star map — the exact file that goes to press. If a date, a place or the spelling is wrong, reply within 24 hours and we will fix it.",
  moon: "Before anything is printed we email you your finished moon print — the exact file that goes to press. If a date, a place or the spelling is wrong, reply within 24 hours and we will fix it.",
};
const SHIPPING_TEXT = "Free delivery to the UK and US. Made to order and dispatched in 3–6 working days.";
const DEFAULT_RETURN = { sky: "/", moon: "/moon.html" };

/** SKU для страницы «спасибо» — как в after_completion старых ссылок: SKN-PRINT-3040, SKN-MOON-CLASSIC-3040. */
export function skuOf(product, fmt) {
  const m = /^(PRINT|CLASSIC)(\d{4})$/.exec(fmt || "");
  if (!m) return "";
  return `SKN-${product === "moon" ? "MOON-" : ""}${m[1]}-${m[2]}`;
}

export const onSale = (row) => !!(row && row.price && row.price !== "TBD");

/** Режим + его таблица, либо код отказа. Любое расхождение — отказ, а не «возьмём что есть». */
export function modeOf(env) {
  const m = env && env.STRIPE_MODE;
  if (!MODE_KEY_RE[m]) return { error: "mode_unset" };
  if (!env.STRIPE_KEY) return { error: "key_unset" };
  if (!MODE_KEY_RE[m].test(env.STRIPE_KEY)) return { error: "mode_key_mismatch" };
  if (!env.DESIGNS) return { error: "storage_unbound" };
  const grid = SKN[m];
  for (const k of GRID_KEYS) {
    if (!grid[k]) return { error: "mode_table_incomplete" };
    if (grid[k].pence !== SKN.live[k].pence) return { error: "mode_table_diverged" };
    if (onSale(SKN.live[k]) && !onSale(grid[k])) return { error: "mode_table_incomplete" };
  }
  return { mode: m, grid };
}

const DASHES = ["—", "-", "?", "–"];

/** Полная проверка записи. → массив проблем; пустой = годно. Зеркало design_store.validate для sky/moon. */
export function validate(rec) {
  const bad = [];
  const product = rec && rec.product;
  if (!PRODUCTS.includes(product)) bad.push(`product=${JSON.stringify(product)}: жду sky или moon`);

  const code = ((rec && rec.design_code) || "").trim();
  const m = CODE_RE.exec(code);
  if (!m) bad.push("design_code не соответствует формату");
  else {
    const want = PREFIX[product];
    if (want && !code.startsWith(want)) bad.push(`design_code начинается не с ${want} — код и продукт разошлись`);
  }

  const fmt = rec && rec.format;
  if (!GRID_KEYS.includes(`${product}/${fmt}`)) bad.push(`format=${JSON.stringify(fmt)} не из сетки SKN`);
  else if (m && m[10] !== fmt) bad.push(`format=${JSON.stringify(fmt)} не совпадает с форматом в design_code (${m[10]})`);

  const pl = (rec && rec.place) || null;
  const place = ((pl && typeof pl.name === "string" && pl.name) || "").trim();
  if (!pl) bad.push("нужно место: название и координаты");
  else if (!place || DASHES.includes(place)) bad.push("нужно настоящее название места, а не прочерк");
  // ⚠️[...] — по кодовым ТОЧКАМ, как len() в Python
  else if ([...place].length > LIMITS.place) bad.push(`место длиннее ${LIMITS.place} символов`);
  if (rec && rec.members !== undefined && rec.members !== null) bad.push("у звёздной карты и Луны нет списка людей");

  if (m && pl) {
    const lat = pl.lat, lon = pl.lon;
    if (lat === undefined || lat === null || lon === undefined || lon === null) bad.push("у места нет координат");
    else {
      const wantLat = Number(m[5]) * (m[4] === "N" ? 1 : -1);
      const wantLon = Number(m[7]) * (m[6] === "E" ? 1 : -1);
      const gotLat = Math.round(lat * 10000), gotLon = Math.round(lon * 10000);
      if (gotLat !== wantLat || gotLon !== wantLon)
        bad.push(`координаты места ${lat},${lon} не совпадают с design-кодом (${wantLat / 10000},${wantLon / 10000})`);
    }
  }

  const ded = ((rec && typeof rec.dedication === "string" && rec.dedication) || "").trim();
  if ([...ded].length > LIMITS.dedication) bad.push(`посвящение длиннее ${LIMITS.dedication} символов`);
  return bad;
}

/** client_reference_id: `d_<id>` + канал + токен. Не влезает — теряем токен, затем канал, но не id. */
export function clientRef(id, channel, token) {
  let base = id;
  if (channel && CHANNEL_RE.test(channel) && (id + "_c1_" + channel).length <= CLIENT_REF_MAX) base = id + "_c1_" + channel;
  if (!token || !TOKEN_RE.test(token)) return base;
  const cand = base + "_a1_" + token;
  return cand.length > CLIENT_REF_MAX ? base : cand;
}

export async function designIdFor(attempt, fp) {
  const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`${attempt}|${fp}`));
  return "d_" + b32(new Uint8Array(h)).slice(0, 26);
}

function b32(raw) {
  const A = "abcdefghijklmnopqrstuvwxyz234567";
  let bits = 0, acc = 0, out = "";
  for (const b of raw) {
    acc = ((acc << 8) | b) & 0xfff; bits += 8;
    while (bits >= 5) { out += A[(acc >>> (bits - 5)) & 31]; bits -= 5; }
  }
  if (bits > 0) out += A[(acc << (5 - bits)) & 31];
  return out;
}

async function rateLimited(ip) {
  try {
    const k = new Request(`https://rl.invalid/skn-design/${encodeURIComponent(ip)}`);
    const cache = caches.default;
    const hit = await cache.match(k);
    const n = hit ? Number(await hit.text()) || 0 : 0;
    if (n >= RATE_MAX) return true;
    await cache.put(k, new Response(String(n + 1), { headers: { "Cache-Control": `max-age=${RATE_WINDOW_S}` } }));
    return false;
  } catch { return false; }
}

const ATTEMPT_RE = /^a_([0-9a-z]{8})([0-9a-z]{16,32})$/;
const ATTEMPT_TTL_S = 7 * 24 * 3600;
const CLOCK_SKEW_S = 3600;
function attemptAge(attempt) {
  const m = ATTEMPT_RE.exec(attempt || "");
  if (!m) return null;
  const ts = parseInt(m[1], 36);
  if (!Number.isFinite(ts) || ts <= 0) return null;
  return Math.floor(Date.now() / 1000) - ts;
}
const SESSION_TTL_S = 23 * 3600;
const AUTO_RETRY_WINDOW_MS = 24 * 3600 * 1000;

function stripeBody(params) {
  const u = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) u.append(k, String(v));
  return u;
}

async function stripe(env, path, params, idemKey) {
  const r = await fetch(`https://api.stripe.com/v1/${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${env.STRIPE_KEY}`,
      "Content-Type": "application/x-www-form-urlencoded",
      ...(idemKey ? { "Idempotency-Key": idemKey } : {}),
    },
    body: stripeBody(params),
  });
  const data = await r.json().catch(() => ({}));
  return { ok: r.ok, status: r.status, data };
}

async function readJson(bucket, key) {
  const o = await bucket.get(key);
  return o ? await o.json() : null;
}

/** Нормализованное содержимое — ровно то, что уйдёт в печать. */
function contentOf(body) {
  return {
    product: body.product,
    design_code: body.design_code.trim(),
    format: body.format,
    dedication: ((body.dedication || "").trim()) || null,
    place: { name: (body.place.name || "").trim(), lat: body.place.lat, lon: body.place.lon },
  };
}

async function fingerprint(c) {
  const canon = JSON.stringify([c.product, c.design_code, c.format, c.dedication, [c.place.name, c.place.lat, c.place.lon]]);
  const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(canon));
  return [...new Uint8Array(h)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });

export async function onRequestPost({ request, env }) {
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  if (await rateLimited(ip)) return json({ error: "too_many_requests" }, 429);

  const len = Number(request.headers.get("Content-Length") || 0);
  if (len > MAX_BODY) return json({ error: "too_large", limit: MAX_BODY }, 413);

  let body;
  try {
    const text = await request.text();
    if (new TextEncoder().encode(text).length > MAX_BODY) return json({ error: "too_large", limit: MAX_BODY }, 413);
    body = JSON.parse(text);
  } catch { return json({ error: "bad_json" }, 400); }
  if (!body || typeof body !== "object" || Array.isArray(body)) return json({ error: "bad_json" }, 400);

  const attempt = body.attempt || "";
  const age = attemptAge(attempt);
  if (age === null || age < -CLOCK_SKEW_S) return json({ error: "bad_attempt" }, 400);
  if (age > ATTEMPT_TTL_S) {
    console.log("attempt expired", attempt);
    return json({ error: "attempt_expired" }, 410);
  }

  // ⛔РЕЖИМ — ДО ВСЕГО. Нет конфигурации — 503 not_configured, и сайт уходит по старой ссылке.
  const cfg = modeOf(env);
  if (cfg.error) {
    console.log("config refused:", cfg.error);
    return json({ error: "not_configured", detail: cfg.error }, 503);
  }

  const problems = validate(body);
  if (problems.length) return json({ error: "invalid", problems }, 400);

  const item = cfg.grid[`${body.product}/${body.format}`];
  if (!onSale(item)) return json({ error: "not_on_sale" }, 503);
  const content = contentOf(body);
  const fp = await fingerprint(content);
  const aKey = `attempts/${attempt}.json`;

  let att;
  try {
    att = await readJson(env.DESIGNS, aKey);
  } catch (e) {
    console.log("attempt read failed", attempt, e && e.name);
    return json({ error: "storage_unavailable" }, 503);
  }
  if (att && att.state === "deleted") return json({ error: "design_expired" }, 410);
  if (att && (att.fp !== fp || att.mode !== cfg.mode)) {
    const why = att.fp !== fp ? "attempt_content_changed" : "attempt_mode_changed";
    console.log("attempt rebound refused", attempt, why);
    return json({ error: why }, 409);
  }
  if (att && att.session_url) {
    const exp = Number((att.params || {}).expires_at || 0);
    if (exp && Date.now() / 1000 >= exp) return json({ error: "checkout_expired" }, 410);
    return json({ id: att.design_id, payment_link: att.session_url, repeat: true });
  }
  if (att) return await linkExisting(env, aKey, att, cfg, attempt, fp);

  return await createAttempt(env, aKey, attempt, cfg, item, content, fp, request, body);
}

async function linkExisting(env, aKey, att, cfg, attempt, fp) {
  if (fp !== undefined && att.fp !== fp) return json({ error: "attempt_content_changed" }, 409);
  if (Date.now() - att.started_ms > AUTO_RETRY_WINDOW_MS) {
    console.log("attempt past auto-retry window", attempt);
    return json({ error: "needs_reconciliation" }, 409);
  }
  const res = await stripe(env, "checkout/sessions", att.params, att.idem_key);
  if (!res.ok || !res.data.url) {
    console.log("stripe retry failed", attempt, res.status);
    return json({ error: "checkout_unavailable" }, 503);
  }
  if (res.data.livemode !== (cfg.mode === "live")) {
    console.log("session mode mismatch on retry", attempt);
    return json({ error: "not_configured", detail: "mode_session_mismatch" }, 503);
  }
  const linked = { ...att, session_id: res.data.id, session_url: res.data.url };
  try {
    await env.DESIGNS.put(aKey, JSON.stringify(linked), { httpMetadata: { contentType: "application/json" } });
  } catch (e) {
    console.log("attempt link write failed", attempt, e && e.name);
    return json({ error: "storage_unavailable" }, 503);
  }
  if (res.data.status === "expired") return json({ error: "checkout_expired" }, 410);
  if (res.data.status && res.data.status !== "open") return json({ error: "already_paid" }, 409);
  return json({ id: att.design_id, payment_link: res.data.url, recovered: true });
}

async function createAttempt(env, aKey, attempt, cfg, item, content, fp, request, body) {
  const id = await designIdFor(attempt, fp);
  const rec = {
    schema_version: SCHEMA_VERSION,
    id,
    created: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
    mode: cfg.mode,
    product: content.product,
    design_code: content.design_code,
    format: content.format,
    expected_pence: item.pence,
    dedication: content.dedication,
    place: content.place,
    attempt,
  };
  const payload = new TextEncoder().encode(JSON.stringify(rec));
  if (payload.length > MAX_BODY) return json({ error: "too_large", limit: MAX_BODY }, 413);

  const dKey = `designs/${id}.json`;
  let put;
  try {
    put = await env.DESIGNS.put(dKey, payload, {
      httpMetadata: { contentType: "application/json" },
      onlyIf: { etagDoesNotMatch: "*" },
    });
  } catch (e) {
    console.log("design store write failed", id, e && e.name);
    return json({ error: "storage_unavailable" }, 503);
  }
  if (!put) {
    let existing;
    try {
      existing = await readJson(env.DESIGNS, dKey);
    } catch (e) {
      console.log("existing design read failed", id, e && e.name);
      return json({ error: "storage_unavailable" }, 503);
    }
    if (!existing || existing.attempt !== attempt) {
      console.log("design id collision", id);
      return json({ error: "design_conflict" }, 409);
    }
  }

  const origin = new URL(request.url).origin;
  const ret = typeof body.return_path === "string" && RETURN_RE.test(body.return_path)
    ? body.return_path : DEFAULT_RETURN[content.product];
  const v = (item.pence / 100).toFixed(2);
  const params = {
    mode: "payment",
    "line_items[0][price]": item.price,
    "line_items[0][quantity]": 1,
    client_reference_id: clientRef(id, body.channel, body.token),
    expires_at: Math.floor(Date.now() / 1000) + SESSION_TTL_S,
    success_url: `${origin}/thank-you.html?sku=${skuOf(content.product, content.format)}&v=${v}&session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${origin}${ret}`,
    "shipping_address_collection[allowed_countries][0]": "GB",
    "shipping_address_collection[allowed_countries][1]": "US",
    billing_address_collection: "required",
    "custom_text[shipping_address][message]": SHIPPING_TEXT,
    "custom_text[submit][message]": SUBMIT_TEXT[content.product],
    // design-код в metadata — для воронки (funnel_logic: демо-небо и «SKN с дизайном»); ПДн тут нет
    "metadata[brand]": content.product === "moon" ? "skn-moon" : "skn",
    "metadata[product]": content.product,
    "metadata[fmt]": content.format,
    "metadata[design_code]": content.design_code,
  };
  const idem_key = `att_${attempt}`;
  const marker = { attempt, mode: cfg.mode, fp, design_id: id, idem_key, params, started_ms: Date.now() };

  let mput;
  try {
    mput = await env.DESIGNS.put(aKey, JSON.stringify(marker), {
      httpMetadata: { contentType: "application/json" },
      onlyIf: { etagDoesNotMatch: "*" },
    });
  } catch (e) {
    console.log("attempt marker write failed", attempt, e && e.name);
    return json({ error: "storage_unavailable" }, 503);
  }
  if (!mput) {
    let winner;
    try {
      winner = await readJson(env.DESIGNS, aKey);
    } catch (e) {
      console.log("winner marker read failed", attempt, e && e.name);
      return json({ error: "storage_unavailable" }, 503);
    }
    if (!winner) return json({ error: "storage_unavailable" }, 503);
    if (winner.fp !== fp) return json({ error: "attempt_content_changed" }, 409);
    if (winner.session_url) return json({ id: winner.design_id, payment_link: winner.session_url, repeat: true });
    return await linkExisting(env, aKey, winner, cfg, attempt, fp);
  }

  const res = await stripe(env, "checkout/sessions", params, idem_key);
  if (res.status === 409) return json({ error: "checkout_busy" }, 503);
  if (!res.ok || !res.data.url) {
    console.log("stripe create failed", id, res.status);
    return json({ error: "checkout_unavailable" }, 503);
  }
  if (res.data.livemode !== (cfg.mode === "live")) {
    console.log("session mode mismatch", id);
    return json({ error: "not_configured", detail: "mode_session_mismatch" }, 503);
  }
  try {
    await env.DESIGNS.put(aKey, JSON.stringify({ ...marker, session_id: res.data.id, session_url: res.data.url }),
      { httpMetadata: { contentType: "application/json" } });
  } catch (e) {
    console.log("session link write failed", id, e && e.name);
    return json({ error: "storage_unavailable" }, 503);
  }
  return json({ id, payment_link: res.data.url });
}

/* ⛔ЧТЕНИЯ НЕТ: у GET Pages откатывается на статику и отдал бы 200 — отвечаем 405 явно (урок Ortus 13.09). */
export const onRequestGet = () => json({ error: "method_not_allowed" }, 405);
