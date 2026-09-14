/* SKN — рекламная атрибуция на стороне браузера (14.09.2026).
   Схема: platform/ATTRIBUTION_SPEC.md · сервер: functions/api/attr.js
   Общий модуль: подключается ДО starmap.js и moon.js, обоим нужен один и тот же путь.

   ⛔РЕКЛАМА — УЧЁТ, А НЕ ГЕЙТ. Ни одна ветка не имеет права помешать оплате: не ответил
   сервер, вышел таймаут, отказано в согласии, не влез токен — покупатель уходит платить по
   ПРЕЖНЕЙ ссылке с чистым design-кодом.

   ⛔ДО СОГЛАСИЯ ИДЕНТИФИКАТОР НЕ СОХРАНЯЕТСЯ НИГДЕ: ни в localStorage, ни в cookies, ни в
   sessionStorage, ни на сервере. Он живёт в переменной страницы.

   ⛔ТОКЕН ПРИДУМЫВАЕТ КЛИЕНТ, А НЕ СЕРВЕР (правка по замечанию юзера). Иначе оборванный
   запрос оставлял сервер с сохранённым идентификатором, а клиента — без токена, которым
   его отзывать: `abort` отменяет ОЖИДАНИЕ ответа, но не саму запись. Теперь попытка
   известна заранее, поэтому отозвать можно и то, ответа по чему мы не получили.

   ⛔СРАВНИВАЕМ ВЕРСИЮ СОГЛАСИЯ, А НЕ ТОЛЬКО ТЕКУЩЕЕ ЗНАЧЕНИЕ. «Отозвал → согласился снова»
   во время полёта запроса даёт то же самое `granted`, но это уже ДРУГОЕ согласие: ответ
   относится к старому. Поэтому перед запросом версия фиксируется и сверяется после.

   ⛔В ОЧЕРЕДЬ ОТЗЫВА КЛАДЁМ ТОЛЬКО ТОКЕН И ТЕХНИКУ ПОВТОРА. Никакого рекламного
   идентификатора: очередь живёт в localStorage и переживает отказ согласия. */
(function () {
  'use strict';

  /* ⛔ПО УМОЛЧАНИЮ — ОТНОСИТЕЛЬНЫЙ АДРЕС, то есть тот же хост, где находится покупатель
     (`www.skythatnight.com`). Переопределяется ТОЛЬКО в тестовом окружении, где витрина и
     Worker живут на разных адресах; в бою переопределения нет и CORS не нужен. */
  var ENDPOINT = (typeof window !== 'undefined' && window.SKN_ATTR_ENDPOINT) || '/api/attr';
  var TIMEOUT_MS = 1200;              /* верхняя граница задержки перед оплатой */
  var REVOKE_TIMEOUT_MS = 4000;
  var SESSION_ID_KEY = 'skn_attr_id';        /* идентификатор — ТОЛЬКО после согласия */
  var SESSION_TOKEN_KEY = 'skn_attr_token';
  var PENDING_KEY = 'skn_attr_pending_revoke';
  var LINKED_KEY = 'skn_attr_linked';        /* токены, уже привязанные к оплате */
  var CONSENT_VER_KEY = 'skn_consent_ver';
  var CONSENT_KEY = 'skn_consent';
  var ID_PARAMS = [['gclid', 'gclid'], ['wbraid', 'wbraid'], ['gbraid', 'gbraid']];
  var ID_RE = /^[A-Za-z0-9_.-]{10,200}$/;
  /* ⛔27 СИМВОЛОВ: `t` + 26 base32 = 128 бит (замечание юзера 14.09). Было 12 — я взял
     8 байт и обрезал их до 11 символов, то есть выбрасывал 9 бит из 64 и писал в описании
     несуществующие «8 байт → 11 символов». Токен даёт право ОТОЗВАТЬ запись, поэтому
     случайность тут не место экономить. */
  var TOKEN_RE = /^t[a-z2-7]{26}$/;
  var CLIENT_REF_MAX = 200;           /* предел Stripe — тот же, что в fulfil.py */

  var mem = { id_type: null, id_value: null };

  function get(store, k) { try { return store.getItem(k); } catch (e) { return null; } }
  function set(store, k, v) {
    try { v === null ? store.removeItem(k) : store.setItem(k, v); } catch (e) {}
  }
  function parse(raw, dflt) { try { return JSON.parse(raw); } catch (e) { return dflt; } }

  /* ── согласие ─────────────────────────────────────────────────────────── */
  function consent() {
    var g = get(localStorage, CONSENT_KEY) === 'granted';
    return {
      granted: g,
      ad_storage: g ? 'granted' : 'denied',
      ad_user_data: g ? 'granted' : 'denied',
      /* Версия растёт при каждой СМЕНЕ решения. Одинаковое `granted` до и после отзыва
         различается именно ею. */
      ver: Number(get(localStorage, CONSENT_VER_KEY) || 0),
    };
  }

  function bumpConsentVer() {
    set(localStorage, CONSENT_VER_KEY, String(Number(get(localStorage, CONSENT_VER_KEY) || 0) + 1));
  }

  /* ── идентификатор ────────────────────────────────────────────────────── */
  function capture(search) {
    var q = new URLSearchParams(search === undefined ? location.search : search);
    for (var i = 0; i < ID_PARAMS.length; i++) {
      var v = q.get(ID_PARAMS[i][0]);
      if (v && ID_RE.test(v)) { mem.id_type = ID_PARAMS[i][1]; mem.id_value = v; break; }
    }
    if (consent().granted) persist();
  }

  function persist() {
    if (!mem.id_value) return;
    set(sessionStorage, SESSION_ID_KEY, JSON.stringify(mem));
  }

  function identifier() {
    if (mem.id_value) return { id_type: mem.id_type, id_value: mem.id_value };
    var d = parse(get(sessionStorage, SESSION_ID_KEY), null);
    return d && d.id_value && ID_RE.test(d.id_value) ? d : null;
  }

  function forget() {
    mem.id_type = mem.id_value = null;
    set(sessionStorage, SESSION_ID_KEY, null);
  }

  /* ── сеть ─────────────────────────────────────────────────────────────── */
  function post(body, timeoutMs) {
    var ctrl = new AbortController();
    var timer = setTimeout(function () { ctrl.abort(); }, timeoutMs);
    return fetch(ENDPOINT, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body), signal: ctrl.signal, keepalive: true,
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (d) {
        return { ok: r.ok, status: r.status, data: d };
      });
    }).catch(function () {
      return { ok: false, status: 0, data: {} };
    }).then(function (res) { clearTimeout(timer); return res; });
  }

  /* ── очередь отзыва ───────────────────────────────────────────────────── */
  function queue() { var l = parse(get(localStorage, PENDING_KEY), []); return Array.isArray(l) ? l : []; }

  function queueAdd(token) {
    if (!TOKEN_RE.test(token || '')) return;
    var l = queue();
    for (var i = 0; i < l.length; i++) if (l[i].token === token) return;
    /* ⛔ТОЛЬКО ТОКЕН И ТЕХНИКА ПОВТОРА. Рекламного идентификатора здесь нет и быть не может:
       человек отозвал согласие, значит хранить его нам больше не на чем. */
    l.push({ token: token, tries: 0, queued_at: Date.now() });
    set(localStorage, PENDING_KEY, JSON.stringify(l.slice(-20)));
  }

  function queueDrop(token) {
    var left = queue().filter(function (e) { return e.token !== token; });
    set(localStorage, PENDING_KEY, left.length ? JSON.stringify(left) : null);
  }

  function queueBump(token) {
    var l = queue();
    for (var i = 0; i < l.length; i++) if (l[i].token === token) l[i].tries = (l[i].tries || 0) + 1;
    set(localStorage, PENDING_KEY, JSON.stringify(l));
  }

  function revoke(token) {
    if (!TOKEN_RE.test(token || '')) return Promise.resolve(false);
    queueAdd(token);                         /* сначала в очередь, потом попытка */
    return post({ revoke: token }, REVOKE_TIMEOUT_MS).then(function (res) {
      if (res.ok || res.status === 404) {
        queueDrop(token);                    /* ⛔подтверждён — запись очереди удаляется */
        unlink(token);                       /* и привязка снимается: записи больше нет */
        if (get(sessionStorage, SESSION_TOKEN_KEY) === token) set(sessionStorage, SESSION_TOKEN_KEY, null);
        return true;
      }
      queueBump(token);
      return false;
    });
  }

  /* ⛔ПРИВЯЗАННЫЕ К ОПЛАТЕ ТОКЕНЫ АВТОМАТИЧЕСКОЙ ОЧИСТКОЙ НЕ ТРОГАЕМ (замечание юзера
     14.09). Предварительная запись в очередь нужна на случай потерянного ответа — но если
     токен всё-таки доехал до оплаты, автоповтор при следующем заходе стёр бы атрибуцию
     НАСТОЯЩЕЙ покупки. Хранится только сам токен: ни идентификатора, ни заказа.
     ⚠️При НАСТОЯЩЕМ отзыве согласия `revoke()` вызывается явно и работает всё равно —
     привязка не делает запись неудаляемой, она лишь запрещает удалять её МОЛЧА. */
  function linked() { var l = parse(get(localStorage, LINKED_KEY), []); return Array.isArray(l) ? l : []; }

  function markLinked(token) {
    if (!TOKEN_RE.test(token || '')) return;
    var l = linked();
    if (l.indexOf(token) === -1) l.push(token);
    set(localStorage, LINKED_KEY, JSON.stringify(l.slice(-20)));
    queueDrop(token);
  }

  function unlink(token) {
    var l = linked().filter(function (t) { return t !== token; });
    set(localStorage, LINKED_KEY, l.length ? JSON.stringify(l) : null);
  }

  function flushPending() {
    var link = linked();
    var l = queue().filter(function (e) { return link.indexOf(e.token) === -1; }).slice(0, 5);
    return l.reduce(function (p, e) { return p.then(function () { return revoke(e.token); }); },
                    Promise.resolve());
  }

  /* ── токен ────────────────────────────────────────────────────────────── */
  function newToken() {
    var a = new Uint8Array(16);                 /* 128 бит, и все они доезжают до токена */
    crypto.getRandomValues(a);
    var A = 'abcdefghijklmnopqrstuvwxyz234567', bits = 0, acc = 0, out = '';
    for (var i = 0; i < a.length; i++) {
      acc = ((acc << 8) | a[i]) & 0xfff; bits += 8;
      while (bits >= 5) { out += A[(acc >>> (bits - 5)) & 31]; bits -= 5; }
    }
    if (bits > 0) out += A[(acc << (5 - bits)) & 31];   /* хвост, а не отбрасывание */
    return 't' + out;                                   /* 1 + 26 = 27 символов */
  }

  function token() {
    var c = consent();
    if (!c.granted) return Promise.resolve(null);      /* отказ: на сервер не ходим вовсе */
    var id = identifier();
    if (!id) return Promise.resolve(null);
    var have = get(sessionStorage, SESSION_TOKEN_KEY);
    if (have) return Promise.resolve(have);

    /* ⛔ПОПЫТКА ИЗВЕСТНА ЗАРАНЕЕ. Токен придумываем здесь и кладём в очередь отзыва ДО
       запроса: если ответ потеряется, а сервер запись сделает, нам всё равно будет чем
       её отозвать. Успешный ответ уберёт запись из очереди. */
    var t = newToken();
    queueAdd(t);
    var verAtStart = c.ver;
    return post({ attempt: t, id_type: id.id_type, id_value: id.id_value,
                  consent: { ad_storage: c.ad_storage, ad_user_data: c.ad_user_data } }, TIMEOUT_MS)
      .then(function (res) {
        var got = res.ok && res.data && res.data.token;
        var now = consent();
        /* ⛔СВЕРЯЕМ И ЗНАЧЕНИЕ, И ВЕРСИЮ. «Отозвал и согласился снова» даёт то же самое
           `granted`, но это другое согласие — ответ относится к прежнему. */
        if (!now.granted || now.ver !== verAtStart) {
          revoke(t);
          return null;
        }
        if (!got) return null;                 /* очередь оставляем: вдруг запись всё же есть */
        queueDrop(t);
        set(sessionStorage, SESSION_TOKEN_KEY, got);
        return got;
      });
  }

  function buildRef(code, tok) {
    if (!tok) return code;
    var candidate = code + '_a1_' + tok;
    return candidate.length > CLIENT_REF_MAX ? code : candidate;   /* не влез — теряем ТОКЕН */
  }

  /* ── наблюдение за согласием ──────────────────────────────────────────── */
  function watch() {
    var last = consent().granted;
    var tick = function () {
      var now = consent().granted;
      if (now === last) return;
      last = now;
      bumpConsentVer();
      if (now) { persist(); return; }
      forget();
      var tok = get(sessionStorage, SESSION_TOKEN_KEY);
      if (tok) revoke(tok);
    };
    window.addEventListener('storage', tick);
    var iv = setInterval(tick, 500);
    setTimeout(function () { clearInterval(iv); }, 120000);
    return tick;                                  /* возвращаем для проверок */
  }

  /* ⛔ПЕРЕХОД К ОПЛАТЕ — ЗДЕСЬ, А НЕ В КАЖДОЙ ВИТРИНЕ. Обе (звёздная и лунная) зовут одну
     функцию, поэтому «один переход и только один» проверяется один раз и работает в обеих.
     Флаг ставится ДО ожидания токена: поздний ответ не имеет права увести второй раз. */
  var navigated = false;
  function navigateToPayment(link, code) {
    if (navigated) return Promise.resolve(false);
    navigated = true;
    return token().catch(function () { return null; }).then(function (tok) {
      var ref = buildRef(code, tok);
      /* Привязываем ТОЛЬКО если токен реально уехал в ссылку: не влез по длине — значит
         он никуда не привязан, и автоочистка вправе его убрать. */
      if (tok && ref !== code) markLinked(tok);
      location.href = link + '?client_reference_id=' + encodeURIComponent(ref);
      return true;
    });
  }

  function boot() {
    try { capture(); watch(); flushPending(); } catch (e) {}
  }

  window.SknAttr = {
    boot: boot, capture: capture, token: token, buildRef: buildRef, revoke: revoke,
    navigateToPayment: navigateToPayment,
    consent: consent, bumpConsentVer: bumpConsentVer, queue: queue, flushPending: flushPending,
    forget: forget, identifier: identifier, watch: watch, linked: linked, markLinked: markLinked,
    _mem: mem, ENDPOINT: ENDPOINT, TIMEOUT_MS: TIMEOUT_MS, CLIENT_REF_MAX: CLIENT_REF_MAX,
  };
})();
