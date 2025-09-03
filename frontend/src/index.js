// frontend/src/index.js
import React from "react";
import ReactDOM from "react-dom/client";

import "materialize-css/dist/css/materialize.min.css";
import "./u.css";     // наш shim-утилиты вместо Tailwind
import "./index.css"; // твои общие стили (БЕЗ @tailwind)

import App from "./App";
import reportWebVitals from "./reportWebVitals";
import "materialize-css/dist/js/materialize.min.js";

// Materialize иногда падает на hash "#!" — чистим на всякий случай
if (window.location.hash === "#!") {
  const { pathname, search } = window.location;
  window.history.replaceState(null, "", pathname + search);
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

reportWebVitals();
