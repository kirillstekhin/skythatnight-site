/**
 * SKN — сохранение рекламной атрибуции и выдача короткого токена. Pages Function.
 * Схема: platform/ATTRIBUTION_SPEC.md · чтение: tools/attribution_store.py
 *
 * ЗАЧЕМ. Чтобы посчитать, окупается ли реклама, нужно связать оплату с кликом. Сам
 * идентификатор клика (`gclid`/`wbraid`/`gbraid`) в Stripe не отправляется: сервер кладёт
 * его к себе и возвращает КОРОТКИЙ непрозрачный токен, который дописывается к
 * `client_reference_id` как `_a1_<токен>`.
 *
 * ⛔ЧЕТЫРЕ УСЛОВИЯ ЮЗЕРА (14.09.2026), каждое закрывает свой провал:
 * ①СБОЙ АТРИБУЦИИ НЕ МЕШАЕТ ОПЛАТЕ. Клиент ходит сюда с коротким таймаутом и при любой
 *   осечке уходит по ПРЕЖНЕЙ ссылке с чистым design-кодом. Реклама — учёт, а не гейт:
 *   потерять измерение можно, потерять заказ нельзя.
 * ②ТОКЕН ВЫДАЁТСЯ ТОЛЬКО ПОСЛЕ УСПЕШНОЙ ЗАПИСИ. Иначе в `client_reference_id` поедет
 *   ссылка на то, чего нет, и мы будем думать, что измеряем, хотя измерять нечего.
 *   Чтения из браузера тут нет вовсе — только запись.
 * ③ОТЗЫВ СОГЛАСИЯ РАБОТАЕТ И ПОСЛЕ СОХРАНЕНИЯ. Очистить браузер мало: запись уже лежит у
 *   нас. Поэтому есть отзыв по токену, он помечает запись, и экспорт обязан проверять
 *   отметку ПЕРЕД отправкой.
 * ④У АТРИБУЦИИ СВОЙ СРОК. Сроки дизайнов (7/90 дней) сюда не переносятся: он определяется
 *   окном импорта и корректировок. Пока окно не подтверждено — `expires_at` не
 *   проставляется, и уборка атрибуции не запускается (см. attribution_store).
 *
 * ⛔СОГЛАСИЕ. Запись делается ТОЛЬКО при `ad_user_data: granted`. При отказе идентификатор
 *   не сохраняется НИГДЕ — ни здесь, ни в браузере: клиент в этом случае сюда не ходит,
 *   а если всё же пришёл — получаем отказ и ничего не пишем.
 * ⛔В ЛОГИ НЕ ПИСАТЬ САМ ИДЕНТИФИКАТОР. Только тип, токен и код ошибки.
 */

export const SCHEMA_VERSION = 1;
export const MAX_BODY = 1024;
const RATE_WINDOW_S = 60;
const RATE_MAX = 20;

/** Допустимые типы. ⚠️Обрабатываются они импортом ПО-РАЗНОМУ — какие реально поддержаны
    выбранным путём загрузки, проверяется отдельно; здесь мы лишь не принимаем чужое. */
export const ID_TYPES = ["gclid", "wbraid", "gbraid"];
const ID_RE = /^[A-Za-z0-9_.-]{10,200}$/;
const TOKEN_RE = /^[a-z0-9]{12}$/;

const json = (obj, status = 200) =>
  new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json" } });

/** t + 11 символов base32 = 12 знаков, подходит под `[A-Za-z0-9]{6,32}` в суффиксе. */
function newToken() {
  const raw = crypto.getRandomValues(new Uint8Array(8));
  const A = "abcdefghijklmnopqrstuvwxyz234567";
  let bits = 0, acc = 0, out = "";
  for (const b of raw) {
    acc = ((acc << 8) | b) & 0xfff; bits += 8;
    while (bits >= 5) { out += A[(acc >>> (bits - 5)) & 31]; bits -= 5; }
  }
  return "t" + out.slice(0, 11);
}

/* ⚠️Ограничитель — первая линия, а не гарантия: Cache API живёт в пределах одного
   дата-центра. Жёсткий предел ставится правилом Rate Limiting при развёртывании. */
async function rateLimited(ip) {
  try {
    const k = new Request(`https://rl.invalid/attr/${encodeURIComponent(ip)}`);
    const cache = caches.default;
    const hit = await cache.match(k);
    const n = hit ? Number(await hit.text()) || 0 : 0;
    if (n >= RATE_MAX) return true;
    await cache.put(k, new Response(String(n + 1), {
      headers: { "Cache-Control": `max-age=${RATE_WINDOW_S}` },
    }));
    return false;
  } catch { return false; }
}

export async function onRequestPost({ request, env }) {
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  if (await rateLimited(ip)) return json({ error: "too_many_requests" }, 429);
  if (Number(request.headers.get("Content-Length") || 0) > MAX_BODY)
    return json({ error: "too_large" }, 413);
  if (!env.ATTR) return json({ error: "not_configured" }, 503);

  let body;
  try {
    const text = await request.text();
    if (new TextEncoder().encode(text).length > MAX_BODY) return json({ error: "too_large" }, 413);
    body = JSON.parse(text);
  } catch { return json({ error: "bad_json" }, 400); }

  // ── ОТЗЫВ. ③Работает и после сохранения: помечаем запись, экспорт обязан проверить.
  if (body && body.revoke) {
    const token = String(body.revoke);
    if (!TOKEN_RE.test(token)) return json({ error: "bad_token" }, 400);
    const key = `attr/${token}.json`;
    let rec;
    try {
      const o = await env.ATTR.get(key);
      rec = o ? await o.json() : null;
    } catch { return json({ error: "storage_unavailable" }, 503); }
    if (!rec) return json({ error: "not_found" }, 404);
    try {
      // ⛔ИДЕНТИФИКАТОР СТИРАЕМ, А НЕ ПРОСТО ПОМЕЧАЕМ. Отзыв согласия означает, что хранить
      //   его больше не на чем — метка остаётся, чтобы экспорт видел отзыв и не гадал.
      await env.ATTR.put(key, JSON.stringify({
        schema_version: SCHEMA_VERSION, token, state: "revoked",
        revoked_at: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
        id_type: rec.id_type || null,
      }), { httpMetadata: { contentType: "application/json" } });
    } catch { return json({ error: "storage_unavailable" }, 503); }
    console.log("attr revoked", token);
    return json({ revoked: true });
  }

  // ── СОХРАНЕНИЕ ──
  const idType = body && body.id_type;
  const idValue = body && body.id_value;
  const consent = (body && body.consent) || {};
  if (!ID_TYPES.includes(idType) || typeof idValue !== "string" || !ID_RE.test(idValue))
    return json({ error: "bad_identifier" }, 400);
  // ⛔РЕШЕНИЕ ПРИНИМАЕТ `ad_user_data`, а не `ad_storage`: первое разрешает передавать
  //   данные Google для рекламы, второе — лишь хранить в браузере. Без него не пишем.
  if (consent.ad_user_data !== "granted")
    return json({ error: "consent_required" }, 403);

  const token = newToken();
  const rec = {
    schema_version: SCHEMA_VERSION,
    token,
    id_type: idType,
    id_value: idValue,
    consent: {
      ad_user_data: consent.ad_user_data,
      ad_storage: consent.ad_storage || null,
      ad_personalization: consent.ad_personalization || null,
    },
    created: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
    // ④СРОК НЕ ПРОСТАВЛЯЕМ, пока не подтверждено окно импорта и корректировок. Пустое
    //   поле честнее выдуманного: уборка атрибуции по нему откажется работать.
    expires_at: null,
    state: "active",
  };
  try {
    const put = await env.ATTR.put(`attr/${token}.json`, JSON.stringify(rec), {
      httpMetadata: { contentType: "application/json" },
      onlyIf: { etagDoesNotMatch: "*" },
    });
    // ⛔R2 при невыполненном onlyIf возвращает null, а не бросает (урок 13.09).
    if (!put) {
      console.log("attr token collision", token);
      return json({ error: "storage_unavailable" }, 503);
    }
  } catch (e) {
    console.log("attr write failed", token, e && e.name);
    return json({ error: "storage_unavailable" }, 503);
  }
  console.log("attr stored", token, idType);      // ⛔без самого идентификатора
  return json({ token });                          // ②только после успешной записи
}

/* ⛔ЧТЕНИЯ НЕТ. Браузеру оно не нужно: токен он получает в ответе на запись. GET у Pages
   имеет откат на статику и молча вернул бы 200 со страницей — поэтому отбиваем явно
   (ровно этот случай поймали на Ortus 13.09). */
export const onRequestGet = () => json({ error: "method_not_allowed" }, 405);
