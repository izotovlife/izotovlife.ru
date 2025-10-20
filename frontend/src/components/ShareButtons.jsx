// Путь: frontend/src/components/ShareButtons.jsx
// Назначение: Панель «Поделиться» (VK, OK, Telegram, WhatsApp, Viber) + минимальная атрибуция источника.
// В этой версии:
//  • Оставлена только строка "Источник: <ссылка>" — без разъясняющего абзаца. (УДАЛЕНО пояснение)
//  • Иконки-логотипы, адаптация к светлой/тёмной теме (через CSS переменные), ховер-подсветка и анимация.
//  • UTM-метки: utm_source=vk|ok|tg|wa|viber|copy; utm_medium=social; utm_campaign=share_button.

import React, { useMemo, useState } from "react";
import styles from "./ShareButtons.module.css";
import { addUtm, absoluteUrl, buildShareLinks, copyToClipboard } from "../utils/share";

export default function ShareButtons({
  title,
  summary,
  url,          // относительный или абсолютный URL вашей детальной страницы; по умолчанию — текущий
  sourceName,   // название издания-источника (для атрибуции)
  sourceUrl,    // оригинальная ссылка на материал
  className = "",
  campaign = "share_button",
}) {
  const pageUrl = useMemo(() => absoluteUrl(url || window.location.href), [url]);
  const [copied, setCopied] = useState(false);

  const textForShare = useMemo(() => {
    const clean = (summary || "").replace(/\s+/g, " ").trim();
    const short = clean.length > 180 ? `${clean.slice(0, 177)}…` : clean;
    return short || title || "Читайте на IzotovLife";
  }, [summary, title]);

  // Базовые ссылки (подменим utm_source под каждую кнопку)
  const links = useMemo(
    () =>
      buildShareLinks({
        url: pageUrl,
        title,
        text: textForShare,
        utmSource: "direct",
      }),
    [pageUrl, title, textForShare]
  );

  async function handleCopy() {
    const ok = await copyToClipboard(addUtm(pageUrl, { source: "copy", campaign }));
    setCopied(!!ok);
    setTimeout(() => setCopied(false), 1600);
  }

  return (
    <div className={`${styles.shareWrap} ${className}`} data-qa="share-block">
      <div className={styles.bar} role="group" aria-label="Поделиться">
        {/* VK */}
        <a
          className={styles.btnIcon}
          href={addUtm(pageUrl, { source: "vk", campaign })}
          onClick={(e) => {
            e.preventDefault();
            window.open(links.vk.replace("utm_source=direct", "utm_source=vk"), "_blank", "noopener,noreferrer,width=720,height=600");
          }}
          rel="noopener noreferrer"
          target="_blank"
          aria-label="Поделиться ВКонтакте"
          title="ВКонтакте"
        >
          <IconVK />
        </a>

        {/* Telegram */}
        <a
          className={styles.btnIcon}
          href={addUtm(pageUrl, { source: "tg", campaign })}
          onClick={(e) => {
            e.preventDefault();
            window.open(links.telegram.replace("utm_source=direct", "utm_source=tg"), "_blank", "noopener,noreferrer,width=720,height=600");
          }}
          rel="noopener noreferrer"
          target="_blank"
          aria-label="Поделиться в Telegram"
          title="Telegram"
        >
          <IconTG />
        </a>

        {/* WhatsApp */}
        <a
          className={styles.btnIcon}
          href={addUtm(pageUrl, { source: "wa", campaign })}
          rel="noopener noreferrer"
          target="_blank"
          aria-label="Поделиться в WhatsApp"
          title="WhatsApp"
        >
          <IconWA />
        </a>

        {/* Viber */}
        <a
          className={styles.btnIcon}
          href={addUtm(pageUrl, { source: "viber", campaign })}
          rel="noopener noreferrer"
          aria-label="Поделиться в Viber"
          title="Viber"
        >
          <IconViber />
        </a>

        {/* OK (Одноклассники) */}
        <a
          className={styles.btnIcon}
          href={addUtm(pageUrl, { source: "ok", campaign })}
          onClick={(e) => {
            e.preventDefault();
            window.open(links.ok.replace("utm_source=direct", "utm_source=ok"), "_blank", "noopener,noreferrer,width=720,height=600");
          }}
          rel="noopener noreferrer"
          target="_blank"
          aria-label="Поделиться в Одноклассниках"
          title="Одноклассники"
        >
          <IconOK />
        </a>

        {/* Копировать ссылку */}
        <button
          className={styles.btnIcon}
          onClick={handleCopy}
          aria-label="Скопировать ссылку"
          title={copied ? "Скопировано!" : "Скопировать ссылку"}
          type="button"
        >
          <IconLink />
        </button>
      </div>

      {(sourceName || sourceUrl) && (
        <div className={styles.attribution} data-qa="attribution">
          {/* УДАЛЕНО: заголовок и абзац с разъяснением цитирования — по вашему требованию */}
          <p className={styles.attrSource}>
            Источник:{" "}
            {sourceUrl ? (
              <a href={sourceUrl} rel="noopener noreferrer" target="_blank">
                {sourceName || new URL(sourceUrl).host}
              </a>
            ) : (
              <span>{sourceName}</span>
            )}
          </p>
        </div>
      )}
    </div>
  );
}

/* ------------------------------ SVG иконки (логотипы). Цвет — currentColor ------------------------------ */

function IconVK() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="currentColor">
      <path d="M3 7h3l2.2 4 2-4h3l-3 5 3 5h-3l-2-4-2 4H3l3-5-3-5zM14.5 7h2v3.5l2-3.5h2l-2.4 3.8L21 17h-2l-1.8-3-0.7 1.1V17h-2V7z" />
    </svg>
  );
}
function IconTG() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="currentColor">
      <path d="M9.8 15.6 9.6 19c.4 0 .6-.2.8-.4l2-1.9 4.1 3c.7.4 1.2.2 1.4-.7l2.6-12.2c.2-.9-.3-1.3-1-1L3.7 10c-.9.3-.9.9-.2 1.1l4.7 1.4 10.9-6.6-9.3 9.7z" />
    </svg>
  );
}
function IconWA() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="currentColor">
      <path d="M20 12.1A8 8 0 0 1 8.7 20l-3.2.9.9-3.1A8 8 0 1 1 20 12.1zm-7.8-5.1a6.2 6.2 0 0 0-5.4 9l-.6 2.2 2.3-.6a6.2 6.2 0 1 0 3.7-10.6zm3.4 8.6c-.3.2-.8.2-1.4.1-1.2-.3-2.6-1-3.7-2.1s-1.9-2.5-2.1-3.7c-.1-.6-.1-1 .1-1.4.1-.2.3-.4.6-.5.2-.1.4-.2.6 0l.9 1c.1.1.2.3.2.5s-.2.5-.3.7-.2.3-.1.5c.1.4.5 1 .9 1.4s1 .8 1.4.9c.2.1.4 0 .5-.1.2-.1.5-.3.7-.3s.4.1.5.2l1 1c.1.2.1.4 0 .6-.1.2-.3.4-.5.6z" />
    </svg>
  );
}
function IconViber() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="currentColor">
      <path d="M6 3h12a3 3 0 0 1 3 3v8.5a3 3 0 0 1-3 3H12l-4 3v-3H6a3 3 0 0 1-3-3V6a3 3 0 0 1 3-3zm9.5 5.3a.8.8 0 0 0-.6 1.5 3.7 3.7 0 0 1 2 2 .8.8 0 0 0 1.5-.6A5.3 5.3 0 0 0 15.5 8.3zm-3-1.6a.8.8 0 1 0-.2 1.6 6.9 6.9 0 0 1 6.4 6.4.8.8 0 1 0 1.6-.2 8.5 8.5 0 0 0-7.8-7.8z" />
    </svg>
  );
}
function IconOK() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="currentColor">
      <path d="M12 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8zm0 10c-2.7 0-5.2-.8-6.8-2.2a1.2 1.2 0 0 0-1.6 1.8c1.4 1.2 3.2 2 5.3 2.4l-3 3.1a1.2 1.2 0 1 0 1.8 1.7L12 17l4.3 4a1.2 1.2 0 0 0 1.7-1.8l-3-3.1c2.1-.4 3.9-1.2 5.3-2.4a1.2 1.2 0 0 0-1.6-1.8C17.2 12.2 14.7 13 12 13z" />
    </svg>
  );
}
function IconLink() {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="currentColor">
      <path d="M3.9 12a4.1 4.1 0 0 1 4.1-4.1h3v2h-3a2.1 2.1 0 0 0 0 4.2h3v2h-3A4.1 4.1 0 0 1 3.9 12zm6-1h4v2h-4v-2zm6.1-3.1a4.1 4.1 0 1 1 0 8.2h-3v-2h3a2.1 2.1 0 1 0 0-4.2h-3v-2h3z" />
    </svg>
  );
}
