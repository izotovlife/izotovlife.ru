// Путь: frontend/src/components/SmartMedia.jsx
// Назначение: Универсальный компонент изображения/аудио с безопасными фолбэками.
// Что делает:
// - Для картинок строит URL ресайзера (/api/media/thumbnail/?src=...)
// - Никогда не шлёт в ресайзер data:/blob:/about: и аудио-файлы
// - При любой ошибке показывает встроенный SVG-плейсхолдер (не 404)
// - Поддерживает кастомные размеры (thumb={ w,h,q,fmt,fit })
// - Аудио-URL рендерятся через <audio controls>
// Зависимости: использует утилиты из Api.js (buildThumbnailUrl, buildThumbnailOrPlaceholder, isAudioUrl)

import React, { useMemo, useState } from "react";
import s from "./SmartMedia.module.css";
import {
  buildThumbnailUrl,
  buildThumbnailOrPlaceholder,
  isAudioUrl,
  DEFAULT_NEWS_PLACEHOLDER,
} from "../Api";

/**
 * Props:
 *  - src: исходный URL медиа
 *  - alt: alt текст для <img>
 *  - className: классы для <img> или <audio>
 *  - thumb: опции ресайзера { w, h, q, fmt, fit }
 *  - preferOriginal: не использовать ресайзер, показывать оригинал (для логотипов и т.п.)
 *  - loading: "lazy" | "eager"
 *  - sizes: <img sizes>
 *  - onClick: обработчик клика по медиа
 */
export default function SmartMedia({
  src,
  alt = "Изображение",
  className = "",
  thumb = { w: 1200, h: 630, q: 85, fmt: "webp", fit: "cover" },
  preferOriginal = false,
  loading = "lazy",
  sizes,
  onClick,
  style,
  imgProps = {},
  audioProps = {},
}) {
  const [failed, setFailed] = useState(false);

  const kind = useMemo(() => {
    if (!src) return "image";
    return isAudioUrl(src) ? "audio" : "image";
  }, [src]);

  const computedSrc = useMemo(() => {
    if (failed) return DEFAULT_NEWS_PLACEHOLDER;
    if (kind === "audio") return src || "";
    if (preferOriginal) {
      // показываем оригинальную картинку как есть, но при ошибке упадём на плейсхолдер
      return src || DEFAULT_NEWS_PLACEHOLDER;
    }
    // картинка через ресайзер; если ресайзер не подходит — вернётся плейсхолдер
    const viaResizer = buildThumbnailUrl(src, thumb);
    return viaResizer || buildThumbnailOrPlaceholder(src, thumb);
  }, [failed, kind, preferOriginal, src, thumb]);

  if (kind === "audio") {
    // аудио никогда не отправляем в ресайзер
    return (
      <audio
        className={`${s.audio} ${className || ""}`.trim()}
        controls
        src={src || ""}
        {...audioProps}
      />
    );
  }

  // image
  return (
    <img
      className={`${s.img} ${className || ""}`.trim()}
      src={computedSrc}
      alt={alt}
      loading={loading}
      sizes={sizes}
      style={style}
      onClick={onClick}
      onError={() => setFailed(true)}
      {...imgProps}
    />
  );
}
