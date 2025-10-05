// Путь: backend/pages/static/pages/admin_staticpage.js
// Назначение: Живой предпросмотр контента CKEditor 5 в админке StaticPage.
// Логика:
//   - Находит редактируемую область CKEditor5 (.ck-editor__editable).
//   - Копирует её HTML в блок #staticpage-live-preview при каждом изменении.
// Особенности:
//   - Без зависимостей, терпеливо ждёт инициализацию редактора.
//   - Не падает, если редактор ещё не готов — делает повторные попытки.

 * Назначение: Контрастный, читаемый Live preview для тёмной и светлой темы.
 */
(function () {
  function updatePreview() {
    var editable = document.querySelector(".ck-editor__editable");
    var preview = document.getElementById("staticpage-live-preview");
    if (!editable || !preview) return;
    preview.innerHTML = editable.innerHTML;
  }

  function bindCopy() {
    var btn = document.getElementById("lp-copy-link");
    if (!btn) return;
    btn.addEventListener("click", function () {
      var url = btn.getAttribute("data-url");
      if (!url) return;
      navigator.clipboard.writeText(url).then(function () {
        btn.textContent = "Ссылка скопирована!";
        setTimeout(function () { btn.textContent = "Скопировать ссылку"; }, 1500);
      }).catch(function () {
        // Fallback
        var ta = document.createElement("textarea");
        ta.value = url;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
        btn.textContent = "Ссылка скопирована!";
        setTimeout(function () { btn.textContent = "Скопировать ссылку"; }, 1500);
      });
    });
  }

  function init() {
    updatePreview();
    bindCopy();

    var editable = document.querySelector(".ck-editor__editable");
    if (!editable) {
      setTimeout(init, 250);
      return;
    }
    editable.addEventListener("input", updatePreview);

    var observer = new MutationObserver(updatePreview);
    observer.observe(editable, { childList: true, subtree: true, characterData: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
