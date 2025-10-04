// frontend/src/components/SmartImage.js
// Назначение: Лениво грузит изображение (IntersectionObserver / native lazy-load),
// сначала показывает превью (можно то же изображение, но браузер притормозит до появления во вьюпорте),
// поддерживает srcSet/sizes, держит место (width/height) и даёт плавное убирание blur.

import React, { useEffect, useRef, useState } from "react";

export default function SmartImage({
  src,
  alt = "",
  className = "",
  previewSrc,
  srcSet,
  sizes = "(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw",
  width,
  height,
  style,
  loading = "lazy",
  onError,
  onLoad,
}) {
  const [inView, setInView] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    // если есть native lazy — пусть браузер сам решит
    if ("loading" in HTMLImageElement.prototype && loading === "lazy") {
      setInView(true);
      return;
    }
    if (!ref.current) return;
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            setInView(true);
            obs.disconnect();
          }
        });
      },
      { rootMargin: "200px" }
    );
    obs.observe(ref.current);
    return () => obs.disconnect();
  }, [loading]);

  const effectiveSrc = inView ? src : (previewSrc || src);
  const effectiveSrcSet = inView ? srcSet : undefined;

  return (
    <img
      ref={ref}
      src={effectiveSrc}
      srcSet={effectiveSrcSet}
      sizes={effectiveSrcSet ? sizes : undefined}
      alt={alt}
      className={className}
      width={width}
      height={height}
      loading={loading}
      style={{
        filter: loaded ? "none" : "blur(8px)",
        transition: "filter .25s ease",
        backgroundColor: "#0b1220",
        ...style,
      }}
      onLoad={(e) => {
        setLoaded(true);
        onLoad && onLoad(e);
      }}
      onError={onError}
    />
  );
}
