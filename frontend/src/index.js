import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import 'materialize-css/dist/css/materialize.min.css';
import 'materialize-css/dist/js/materialize.min.js';

// Materialize tries to query the current hash on load. When the hash is "#!"
// (a common placeholder), this results in an invalid CSS selector and crashes
// the app. Clear such hashbangs before rendering to keep initialization safe.
if (window.location.hash === '#!') {
  const { pathname, search } = window.location;
  window.history.replaceState(null, '', pathname + search);
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
