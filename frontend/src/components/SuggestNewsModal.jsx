// Путь: frontend/src/components/SuggestNewsModal.jsx
// Назначение: Модальное окно "Предложить новость" с мгновенной отправкой на новый бэкенд.
// Поддержка: заголовок, текст новости, изображение, видео, капча (reCAPTCHA v3), скроллируемая форма.
// Обновлено:
//   ✅ Капча грузится ТОЛЬКО при открытой модалке: useRecaptcha(SITE_KEY, { enabled: open, locale: "ru" })
//   ✅ Кнопка отправки заблокирована, пока капча не готова (если SITE_KEY задан)
//   ❗️Ничего полезного не удалял. Лишь добавил опции к хуку и условие disabled на кнопке.

import React, { useState, useEffect, useRef, useCallback } from "react";
import api, { suggestNews as suggestNewsApi } from "../Api"; // default axios-инстанс + ваш экспорт suggestNews
import useRecaptcha from "../hooks/useRecaptcha";
import styles from "./SuggestNewsModal.module.css";

const SITE_KEY = process.env.REACT_APP_RECAPTCHA_SITE_KEY || "";

export default function SuggestNewsModal({ open, onClose }) {
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    title: "",
    message: "",
    website: "", // honeypot
    recaptcha: "",
    image_file: null,
    video_file: null,
  });
  const [errors, setErrors] = useState({});
  const [sending, setSending] = useState(false);
  const [success, setSuccess] = useState(false);
  const [closing, setClosing] = useState(false);
  const firstInputRef = useRef(null);

  // reCAPTCHA v3 — лениво: грузим скрипт только когда модалка открыта
  // (требуется версия хука с поддержкой {enabled, locale}).
  const { ready, execute } = useRecaptcha(SITE_KEY, { enabled: open && !!SITE_KEY, locale: "ru" });

  const handleClose = useCallback(() => {
    setClosing(true);
    setTimeout(() => {
      setSuccess(false);
      onClose?.();
    }, 250);
  }, [onClose]);

  // ESC закрытие
  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") handleClose();
    }
    if (open) {
      window.addEventListener("keydown", onKey);
      return () => window.removeEventListener("keydown", onKey);
    }
  }, [open, handleClose]);

  // Автофокус
  useEffect(() => {
    if (open && firstInputRef.current) {
      setTimeout(() => firstInputRef.current.focus(), 100);
    }
  }, [open]);

  // Сброс при открытии
  useEffect(() => {
    if (open) {
      setErrors({});
      setSuccess(false);
      setClosing(false);
    }
  }, [open]);

  if (!open) return null;

  const setField = (key) => (e) =>
    setForm((prev) => ({ ...prev, [key]: e.target.value }));

  const onFileChange = (key) => (e) => {
    const file = e.target.files?.[0] || null;
    setForm((prev) => ({ ...prev, [key]: file }));
  };

  const buildFormData = async () => {
    const fd = new FormData();

    // Текстовые поля
    fd.append("first_name", form.first_name.trim());
    fd.append("last_name", form.last_name.trim());
    fd.append("email", form.email.trim());
    if (form.phone?.trim()) fd.append("phone", form.phone.trim());
    fd.append("title", form.title.trim());
    fd.append("message", form.message.trim());

    // Honeypot (если заполнен — просто отправим; на бэке отсеется)
    if (form.website) fd.append("website", form.website);

    // Файлы: кладём под несколькими ключами для совместимости с разными бэкендами
    if (form.image_file) {
      fd.append("image_file", form.image_file);
      fd.append("image", form.image_file);
      fd.append("photo", form.image_file);
    }
    if (form.video_file) {
      fd.append("video_file", form.video_file);
      fd.append("video", form.video_file);
    }

    // reCAPTCHA токен (если есть ключ)
    let token = null;
    if (SITE_KEY) {
      if (!ready) throw new Error("Капча инициализируется, попробуйте через секунду.");
      token = await execute("suggest_news");
    }
    if (token) {
      // Кладём в самые распространённые поля
      fd.append("captcha", token);
      fd.append("recaptcha", token);
      fd.append("g-recaptcha-response", token);
    }

    return fd;
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setErrors({});
    setSuccess(false);

    const errs = {};
    if (!form.first_name.trim()) errs.first_name = "Укажите имя";
    if (!form.last_name.trim()) errs.last_name = "Укажите фамилию";
    if (!form.email.trim()) errs.email = "Укажите e-mail";
    if (!form.title.trim()) errs.title = "Укажите заголовок новости";
    if (!form.message.trim() || form.message.trim().length < 15)
      errs.message = "Опишите новость подробнее (минимум 15 символов)";
    if (Object.keys(errs).length) {
      setErrors(errs);
      return;
    }
    if (form.website) {
      // honeypot сработал — тихо закрываем без отправки
      setSuccess(true);
      setTimeout(() => handleClose(), 800);
      return;
    }

    setSending(true);

    try {
      const fd = await buildFormData();

      // 1) Пытаемся использовать ваш экспорт suggestNews (если он умеет FormData)
      try {
        await suggestNewsApi(fd);
      } catch (inner) {
        // 2) Fallback: шлём напрямую через общий axios-инстанс на новый бэкенд
        await api.post("/news/suggest/", fd);
      }

      setSuccess(true);
      setForm({
        first_name: "",
        last_name: "",
        email: "",
        phone: "",
        title: "",
        message: "",
        website: "",
        recaptcha: "",
        image_file: null,
        video_file: null,
      });

      // Мягкое автозакрытие
      setTimeout(() => handleClose(), 2500);
    } catch (err) {
      console.error("Ошибка при отправке новости:", err);
      // Разбираем DRF-ошибки, если есть
      const data = err?.response?.data;
      if (err?.response?.status === 400 && data && typeof data === "object") {
        const fe = {};
        if (typeof data.detail === "string") fe._common = data.detail;
        ["first_name","last_name","email","phone","title","message","captcha","recaptcha","g-recaptcha-response"].forEach((k) => {
          if (Array.isArray(data[k])) fe[k] = data[k].join(" ");
          else if (typeof data[k] === "string") fe[k] = data[k];
        });
        setErrors(Object.keys(fe).length ? fe : { _common: "Проверьте поля формы." });
      } else if (err?.message) {
        setErrors({ _common: err.message });
      } else {
        setErrors({ _common: "Ошибка сети или сервера. Попробуйте позже." });
      }
      setSuccess(false);
    } finally {
      setSending(false);
    }
  };

  return (
    <div
      className={`${styles.backdrop} ${closing ? styles.fadeOut : styles.fadeIn}`}
      onClick={handleClose}
    >
      <div
        className={`${styles.modal} ${closing ? styles.fadeOut : styles.fadeIn}`}
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <div className={styles.header}>
          <div className={styles.title}>Предложить новость</div>
          <button className={styles.close} onClick={handleClose} aria-label="Закрыть">×</button>
        </div>

        {success ? (
          <div className={styles.success}>Спасибо! Ваша новость отправлена в редакцию.</div>
        ) : (
          <form onSubmit={onSubmit} className={styles.form}>
            {errors._common && <div className={styles.error}>{errors._common}</div>}

            <div className={styles.row}>
              <label className={styles.label}>Имя*</label>
              <input
                ref={firstInputRef}
                className={styles.input}
                value={form.first_name}
                onChange={setField("first_name")}
                placeholder="Иван"
              />
              {errors.first_name && <div className={styles.fieldError}>{errors.first_name}</div>}
            </div>

            <div className={styles.row}>
              <label className={styles.label}>Фамилия*</label>
              <input
                className={styles.input}
                value={form.last_name}
                onChange={setField("last_name")}
                placeholder="Иванов"
              />
              {errors.last_name && <div className={styles.fieldError}>{errors.last_name}</div>}
            </div>

            <div className={styles.row}>
              <label className={styles.label}>E-mail*</label>
              <input
                className={styles.input}
                type="email"
                value={form.email}
                onChange={setField("email")}
                placeholder="you@example.com"
              />
              {errors.email && <div className={styles.fieldError}>{errors.email}</div>}
            </div>

            <div className={styles.row}>
              <label className={styles.label}>Телефон</label>
              <input
                className={styles.input}
                value={form.phone}
                onChange={setField("phone")}
                placeholder="+7 900 000-00-00"
              />
              {errors.phone && <div className={styles.fieldError}>{errors.phone}</div>}
            </div>

            <div className={styles.row}>
              <label className={styles.label}>Заголовок новости*</label>
              <input
                className={styles.input}
                value={form.title}
                onChange={setField("title")}
                placeholder="Краткий заголовок новости"
              />
              {errors.title && <div className={styles.fieldError}>{errors.title}</div>}
            </div>

            <div className={styles.row}>
              <label className={styles.label}>Новость*</label>
              <textarea
                className={styles.textarea}
                value={form.message}
                onChange={setField("message")}
                placeholder="Кто? Что? Где? Когда? Подробности, ссылки, факты…"
                rows={6}
              />
              {errors.message && <div className={styles.fieldError}>{errors.message}</div>}
            </div>

            <div className={styles.row}>
              <label className={styles.label}>Фото / Видео</label>
              <input type="file" accept="image/*" onChange={onFileChange("image_file")} />
              <input type="file" accept="video/*" onChange={onFileChange("video_file")} />
              <small>Поддерживаются форматы: jpg, png, gif, mp4</small>
            </div>

            <div className={styles.honeypot} aria-hidden="true">
              <label>Ваш сайт</label>
              <input
                value={form.website}
                onChange={setField("website")}
                tabIndex={-1}
                autoComplete="off"
              />
            </div>

            <div className={styles.actions}>
              <button
                className={styles.submit}
                type="submit"
                disabled={sending || (SITE_KEY && !ready)}
              >
                {sending ? "Отправляем…" : "Отправить новость"}
              </button>
              <button className={styles.secondary} type="button" onClick={handleClose}>
                Отмена
              </button>
            </div>

            {/* Неброская подсказка статуса капчи (для DEV) */}
            {SITE_KEY && (
              <div className={styles.meta} style={{ opacity: 0.7, fontSize: 12, marginTop: 8 }}>
                Защита: reCAPTCHA v3 {ready ? "готова" : "инициализация…"}
              </div>
            )}
          </form>
        )}
      </div>
    </div>
  );
}
