const FG = (() => {
  const API_BASE = '/api';

  function qs(key) {
    const params = new URLSearchParams(window.location.search);
    return params.get(key);
  }

  function qsi(key, defVal = 1) {
    const v = parseInt(qs(key), 10);
    return Number.isFinite(v) && v > 0 ? v : defVal;
  }

  function setNavActive(id) {
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.toggle('active', link.dataset.target === id);
    });
  }

  async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`请求失败 ${res.status}`);
    return res.json();
  }

  function text(val) {
    return val === null || val === undefined ? '' : String(val);
  }

  function hint(el, msg) {
    if (el) el.textContent = msg || '';
  }

  function linkTo(path, params) {
    const url = new URL(path, window.location.origin);
    if (params) Object.entries(params).forEach(([k, v]) => v !== undefined && v !== null && url.searchParams.set(k, v));
    return url.toString();
  }

  return { API_BASE, qs, qsi, setNavActive, fetchJSON, text, hint, linkTo };
})();
