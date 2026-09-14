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
 * ⛔СОГЛАСИЕ — ОБА ФЛАГА (исправлено 14.09 по замечанию юзера; до этого запись требовала
 *   только `ad_user_data`, и это была подмена согласованной схемы). Для консервативного
 *   варианта, который мы выбрали:
 *     `ad_storage`   — разрешение ХРАНИТЬ идентификатор;
 *     `ad_user_data` — разрешение ПЕРЕДАВАТЬ данные Google для рекламы.
 *   Запись требует **обоих** `granted`; экспорт дополнительно проверяет отсутствие отзыва.
 *   При отказе идентификатор не сохраняется НИГДЕ — ни здесь, ни в браузере.
 * ⛔СБОР РЕАЛЬНЫХ ДАННЫХ ЗАПЕРТ, ПОКА НЕ ВЫБРАН СРОК ХРАНЕНИЯ. Запрет уборки предотвращает
 *   случайное удаление, но сам по себе оставляет данные бессрочно — это не выполненное
 *   условие, а отложенное. Поэтому режим `live` требует объявленного `ATTR_RETENTION_DAYS`,
 *   а без него разрешён только режим `test` с ВЫМЫШЛЕННЫМИ данными, и такие записи экспорт
 *   не отправляет никогда.
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
  // ⛔ОТДЕЛЬНЫЙ ПРИВАТНЫЙ BUCKET (замечание юзера 14.09). Префикс разделяет ИМЕНА, но не
  //   доступ: binding на bucket дизайнов дал бы этой Function доступ и к персонализации
  //   заказов. У рекламной атрибуции нет ни одной причины её видеть.
  if (!env.ATTR) return json({ error: "not_configured", detail: "attr_bucket_unbound" }, 503);
  const mode = env.ATTR_MODE;
  if (mode !== "test" && mode !== "live")
    return json({ error: "not_configured", detail: "attr_mode_unset" }, 503);
  const retention = Number(env.ATTR_RETENTION_DAYS || 0);
  if (mode === "live" && !(retention > 0))
    return json({ error: "not_configured", detail: "retention_undefined" }, 503);

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
    // ⛔ПОВТОРНЫЙ ОТЗЫВ — УСПЕХ, А НЕ ОШИБКА. Клиент, у которого отзыв не прошёл из-за
    //   недоступного сервера, обязан повторить его позже; вторая попытка должна
    //   завершаться так же спокойно, как первая.
    if (rec.state === "revoked") {
      console.log("attr revoke repeated", token);
      return json({ revoked: true, already: true });
    }
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
  // ⛔НУЖНЫ ОБА. `ad_storage` разрешает хранить, `ad_user_data` — передавать Google.
  //   Хранить то, что нельзя передать, бессмысленно; передавать без права хранить —
  //   нельзя. Поэтому запись только при обоих `granted`.
  if (consent.ad_storage !== "granted" || consent.ad_user_data !== "granted")
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
    // ④СРОК: в режиме `live` он обязателен и проставляется; в `test` может отсутствовать.
    expires_at: retention > 0
      ? new Date(Date.now() + retention * 86400000).toISOString().replace(/\.\d+Z$/, "Z")
      : null,
    // ⛔РЕЖИМ ДАННЫХ. `test` = вымышленные, экспорт их не отправляет НИКОГДА.
    mode,
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
