/* Путь: frontend/src/components/SmartMedia.jsx
   Назначение: Обложка новости. Безопасно рендерит изображение через ресайзер
               (utils.thumb → обычно /api/news/media/thumbnail/, если у тебя иначе — utils сам знает),
               умеет компактный режим, иконку источника и (по желанию) плейсхолдер.

   Совместимость (всё сохранено):
     • Пропсы: src, alt, title, sourceLogo, compactOnNoImage, showTitleInPlaceholder,
               className, width, height, fit, quality, sharpen, style, imgProps.
     • ДОБАВЛЕНЫ флаги управления отображением без изображения:
         - hideIfNoImage (по умолчанию true) — если нет картинки, вообще ничего не рисовать;
         - showPlaceholder (по умолчанию false) — если нужен плейсхолдер, включите вручную.

   Что добавлено (чтобы убрать 400 у ресайзера):
     • Не проксируем НЕ http(s) источники: data:/blob:/about: — отдаём как есть (никаких запросов к ресайзеру).
     • Не проксируем аудио (mp3/ogg/wav/...), для них finalSrc пустой → блок скрывается по умолчанию.
     • Для не-http(s) путей (например, относительный "/media/...") — тоже не трогаем ресайзер и рисуем напрямую.

   Важно: поведением по умолчанию соответствует требованию «без заглушек, только текст».
*/

import React, { useMemo, useState } from "react";
import { thumbUrl, PLACEHOLDER } from "../utils/thumb";

// --- Предикаты для безопасной работы с src ---
const AUDIO_EXT = [".mp3", ".ogg", ".wav", ".m4a", ".aac", ".flac"];
const isAudioUrl = (u) => {
  const s = String(u || "").toLowerCase().split("?")[0];
  return AUDIO_EXT.some((ext) => s.endsWith(ext));
};
const isHttpLike = (u) => /^https?:\/\//i.test(String(u || ""));
const isDataOrBlob = (u) => /^(data:|blob:|about:)/i.test(String(u || ""));

export default function SmartMedia({
  // базовые
  src,
  alt = "",
  title = "",
  sourceLogo = "",
  className = "",
  style = {},
  imgProps = {},

  // рендеринг и качество
  width = 980,
  height = 520,
  fit = "cover",
  quality = 85,
  sharpen = 1,

  // совместимость со старым кодом
  compactOnNoImage = false,
  showTitleInPlaceholder = false,

  // новое управление поведением без изображения
  hideIfNoImage = true,   // ⬅ по умолчанию ничего не показываем, если картинки нет
  showPlaceholder = false // ⬅ плейсхолдер выключен по умолчанию, можно включить вручную
}) {
  const [errored, setErrored] = useState(false);

  // 1) Выбираем, КАК показывать src:
  //    - data:/blob:/about: → напрямую (не трогаем ресайзер)
  //    - аудио → не рендерим картинку (finalSrc = "")
  //    - http(s) → проксируем через ресайзер utils.thumb (который знает правильный эндпоинт)
  //    - прочее (например, "/media/..") → рисуем напрямую
  const finalSrc = useMemo(() => {
    if (!src || errored) return "";
    const s = String(src).trim();
    if (!s) return "";

    if (isAudioUrl(s)) return "";            // аудио не является картинкой
    if (isDataOrBlob(s)) return s;           // data:, blob:, about: — отдаем как есть
    if (!isHttpLike(s)) return s;            // относительные/файловые пути — тоже как есть

    try {
      // http(s) — безопасно через ресайзер
      return thumbUrl(s, {
        w: width,
        h: height,
        fmt: "webp",
        fit,
        q: quality,
        sharpen,
      });
    } catch {
      return "";
    }
  }, [src, errored, width, height, fit, quality, sharpen]);

  // --- Политика отображения без изображения ---
  // 1) Полностью скрываем блок (поведение по умолчанию и «компактный» режим).
  if (compactOnNoImage || hideIfNoImage) {
    if (!src || !finalSrc || errored) return null;
  }

  // 2) Если скрывать не нужно и плейсхолдер разрешён — отрисуем плейсхолдер.
  const shouldShowPlaceholder =
    !compactOnNoImage && !hideIfNoImage && showPlaceholder && (!src || !finalSrc || errored);

  return (
    <div className={`smart-media ${className}`} style={{ position: "relative", ...style }}>
      {shouldShowPlaceholder ? (
        // Плейсхолдер показывается ТОЛЬКО если его явно включили (showPlaceholder)
        <div
          style={{
            width: "100%",
            aspectRatio: `${width}/${height}`,
            background: "#0a0f1a",
            borderRadius: 16,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            overflow: "hidden",
          }}
        >
          {showTitleInPlaceholder && title ? (
            <div
              style={{
                padding: 16,
                textAlign: "center",
                fontSize: 18,
                lineHeight: 1.35,
                color: "#9aa6bf",
              }}
            >
              {title}
            </div>
          ) : (
            <img
              src={PLACEHOLDER}
              alt=""
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          )}
        </div>
      ) : (
        // Обычная картинка
        finalSrc && (
          <img
            src={finalSrc}
            alt={alt || title || ""}
            width={width}
            height={height}
            loading="lazy"
            decoding="async"
            onError={() => setErrored(true)}
            style={{ width: "100%", height: "auto", objectFit: fit, borderRadius: 16 }}
            {...imgProps}
          />
        )
      )}

      {/* Иконка источника (если есть). Если с ней ошибка — скрываем. */}
      {sourceLogo ? (
        <img
          src={sourceLogo}
          alt=""
          className="smart-media__logo"
          onError={(e) => (e.currentTarget.style.display = "none")}
          style={{
            position: "absolute",
            right: 8,
            bottom: 8,
            width: 32,
            height: 32,
            borderRadius: 8,
            background: "#0f1526",
            padding: 4,
            objectFit: "contain",
            opacity: 0.9,
          }}
        />
      ) : null}
    </div>
  );
}
