// Путь: frontend/src/utils/share.js
// Назначение: Утилиты для формирования ссылок "Поделиться" и UTM-меток.
// Содержимое: addUtm(), absoluteUrl(), buildShareLinks(), copyToClipboard()

/**
 * Возвращает абсолютный URL (если передали относительный).
 * Пример: "/news/politika/foo/" -> "http(s)://<host>/news/politika/foo/"
 */
export function absoluteUrl(url) {
  try {
    // Уже абсолютный
    const u = new URL(url);
    return u.toString();
  } catch {
    // Относительный — собираем от текущего origin
    const base = typeof window !== "undefined" ? window.location.origin : "";
    return `${base}${url.startsWith("/") ? url : `/${url}`}`;
  }
}

/**
 * Аккуратно добавляет UTM-метки к URL.
 * Пример: addUtm('https://site/page', {source:'vk', medium:'social', campaign:'share'})
 */
export function addUtm(url, { source, medium = "social", campaign = "share_button" } = {}) {
  const abs = absoluteUrl(url);
  const u = new URL(abs);
  if (source) u.searchParams.set("utm_source", source);
  if (medium) u.searchParams.set("utm_medium", medium);
  if (campaign) u.searchParams.set("utm_campaign", campaign);
  return u.toString();
}

/**
 * Собирает ссылки для соцсетей. Возвращает объект:
 * { vk, telegram, whatsapp, facebook, x, viber, ok }
 */
export function buildShareLinks({ url, title, text, utmSource }) {
  const pageUrl = addUtm(url, { source: utmSource });
  const enc = encodeURIComponent;
  const encText = enc(text || title || "");
  const encTitle = enc(title || "");
  const encUrl = enc(pageUrl);

  return {
    vk: `https://vk.com/share.php?url=${encUrl}&title=${encTitle}`,
    telegram: `https://t.me/share/url?url=${encUrl}&text=${encText || encTitle}`,
    whatsapp: `https://api.whatsapp.com/send?text=${encText ? `${encText}%20` : ""}${encUrl}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encUrl}`,
    x: `https://twitter.com/intent/tweet?url=${encUrl}&text=${encTitle}`,
    viber: `viber://forward?text=${encText ? `${encText}%20` : ""}${encUrl}`,
    ok: `https://connect.ok.ru/offer?url=${encUrl}&title=${encTitle}`,
  };
}

/**
 * Копирует ссылку в буфер обмена (с тайм-аутом на iOS/старые браузеры).
 */
export async function copyToClipboard(text) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {}
  // Фолбэк для старых браузеров
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  let ok = false;
  try {
    ok = document.execCommand("copy");
  } catch {}
  document.body.removeChild(ta);
  return ok;
}
