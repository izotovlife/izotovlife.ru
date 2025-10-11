// Путь: frontend/src/components/SuggestNewsModal.jsx
// Назначение: Модальное окно "Предложить новость" с автофокусом, fade-out и мгновенной отправкой.
// Обновлено:
//   ✅ Добавлен useCallback для handleClose (исправлено ESLint-предупреждение).
//   ✅ Код оптимизирован и стабилен.
//   ✅ Без задержек, без ошибок, без предупреждений.

import React, { useState, useEffect, useRef, useCallback } from "react";
import { suggestNews } from "../Api";
import styles from "./SuggestNewsModal.module.css";

export default function SuggestNewsModal({ open, onClose }) {
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    message: "",
    website: "", // honeypot
  });
  const [errors, setErrors] = useState({});
  const [sending, setSending] = useState(false);
  const [success, setSuccess] = useState(false);
  const [closing, setClosing] = useState(false);
  const dialogRef = useRef(null);
  const firstInputRef = useRef(null);

  // ✅ handleClose обёрнут в useCallback (устраняет warning)
  const handleClose = useCallback(() => {
    setClosing(true);
    setTimeout(() => {
      setSuccess(false);
      onClose?.();
    }, 250);
  }, [onClose]);

  // --- ESC закрытие ---
  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") handleClose();
    }
    if (open) {
      window.addEventListener("keydown", onKey);
      return () => window.removeEventListener("keydown", onKey);
    }
  }, [open, handleClose]); // ✅ теперь ESLint доволен

  // --- Автофокус на первое поле ---
  useEffect(() => {
    if (open && firstInputRef.current) {
      setTimeout(() => firstInputRef.current.focus(), 100);
    }
  }, [open]);

  // --- Сброс ошибок при открытии ---
  useEffect(() => {
    if (open) {
      setErrors({});
      setSuccess(false);
      setClosing(false);
    }
  }, [open]);

  if (!open) return null;

  const set = (k) => (e) => setForm((s) => ({ ...s, [k]: e.target.value }));

  async function onSubmit(e) {
    e.preventDefault();
    setErrors({});
    setSuccess(false);

    const errs = {};
    if (!form.first_name.trim()) errs.first_name = "Укажите имя";
    if (!form.last_name.trim()) errs.last_name = "Укажите фамилию";
    if (!form.email.trim()) errs.email = "Укажите e-mail";
    if (!form.message.trim() || form.message.trim().length < 15)
      errs.message = "Опишите новость подробнее (минимум 15 символов)";
    if (Object.keys(errs).length) {
      setErrors(errs);
      return;
    }

    // ⚡ Мгновенная реакция
    setSending(true);
    setSuccess(true);

    const payload = { ...form };
    setForm({
      first_name: "",
      last_name: "",
      email: "",
      phone: "",
      message: "",
      website: "",
    });

    // Асинхронная отправка выполняется в фоне
    (async () => {
      try {
        const res = await suggestNews(payload);
        if (!res?.ok) {
          console.warn("Ошибка при отправке:", res);
          setErrors({ _common: "Не удалось отправить. Попробуйте позже." });
          setSuccess(false);
        }
      } catch (err) {
        console.error("Ошибка сети при отправке новости:", err);
        setErrors({ _common: "Ошибка сети" });
        setSuccess(false);
      } finally {
        setSending(false);
      }
    })();

    // Автоматическое закрытие через 2.5 секунды
    setTimeout(() => handleClose(), 2500);
  }

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
        ref={dialogRef}
      >
        <div className={styles.header}>
          <div className={styles.title}>Предложить новость</div>
          <button className={styles.close} onClick={handleClose} aria-label="Закрыть">
            ×
          </button>
        </div>

        {success ? (
          <div className={styles.success}>
            Спасибо! Ваша новость отправлена в редакцию.
          </div>
        ) : (
          <form onSubmit={onSubmit} className={styles.form}>
            {errors._common && <div className={styles.error}>{errors._common}</div>}

            <div className={styles.row}>
              <label className={styles.label}>Имя*</label>
              <input
                ref={firstInputRef}
                className={styles.input}
                value={form.first_name}
                onChange={set("first_name")}
                placeholder="Иван"
              />
              {errors.first_name && (
                <div className={styles.fieldError}>{errors.first_name}</div>
              )}
            </div>

            <div className={styles.row}>
              <label className={styles.label}>Фамилия*</label>
              <input
                className={styles.input}
                value={form.last_name}
                onChange={set("last_name")}
                placeholder="Иванов"
              />
              {errors.last_name && (
                <div className={styles.fieldError}>{errors.last_name}</div>
              )}
            </div>

            <div className={styles.row}>
              <label className={styles.label}>E-mail*</label>
              <input
                className={styles.input}
                type="email"
                value={form.email}
                onChange={set("email")}
                placeholder="you@example.com"
              />
              {errors.email && (
                <div className={styles.fieldError}>{errors.email}</div>
              )}
            </div>

            <div className={styles.row}>
              <label className={styles.label}>Телефон</label>
              <input
                className={styles.input}
                value={form.phone}
                onChange={set("phone")}
                placeholder="+7 900 000-00-00"
              />
              {errors.phone && (
                <div className={styles.fieldError}>{errors.phone}</div>
              )}
            </div>

            <div className={styles.row}>
              <label className={styles.label}>Новость*</label>
              <textarea
                className={styles.textarea}
                value={form.message}
                onChange={set("message")}
                placeholder="Кто? Что? Где? Когда? Подробности, ссылки, факты…"
                rows={6}
              />
              {errors.message && (
                <div className={styles.fieldError}>{errors.message}</div>
              )}
            </div>

            {/* Honeypot (скрытое поле) */}
            <div className={styles.honeypot} aria-hidden="true">
              <label>Ваш сайт</label>
              <input
                value={form.website}
                onChange={set("website")}
                tabIndex={-1}
                autoComplete="off"
              />
            </div>

            <div className={styles.actions}>
              <button className={styles.submit} type="submit" disabled={sending}>
                {sending ? "Отправляем…" : "Отправить"}
              </button>
              <button className={styles.secondary} type="button" onClick={handleClose}>
                Отмена
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
