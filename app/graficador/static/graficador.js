/*
 * Graficador: gráfico de un ticker de Yahoo Finance con lightweight-charts v5
 * (API ``addSeries`` y panes), sin framework.
 *
 * - Pane 0: la serie principal (velas, línea o área, según el selector).
 * - Pane 1: histograma de volumen.
 * Los datos vienen de /api/candles/<ticker>?range=&interval= (core) y la
 * cabecera de /api/quote/<ticker>. Los colores se leen de los tokens CSS de
 * core/static/css/style.css para que el gráfico siga el tema oscuro.
 */
(function () {
  "use strict";

  const root = document.getElementById("graficador");
  const LC = window.LightweightCharts;
  if (!root || !root.dataset.ticker || !LC) return;

  const ticker = root.dataset.ticker;
  const apiUrl = (template) => template.replace("__T__", encodeURIComponent(ticker));
  const candlesUrl = apiUrl(root.dataset.candlesUrl);
  const quoteUrl = apiUrl(root.dataset.quoteUrl);

  const statusEl = document.getElementById("graficador-status");
  const legendEl = document.getElementById("graficador-legend");
  const quoteEl = document.getElementById("graficador-quote");
  const nameEl = document.getElementById("graficador-name");
  const rangeButtons = Array.from(root.querySelectorAll("[data-range]"));
  const typeButtons = Array.from(root.querySelectorAll("[data-series-type]"));

  // ───────────────────────── Tema ─────────────────────────
  const css = getComputedStyle(document.documentElement);
  const token = (name, fallback) => css.getPropertyValue(name).trim() || fallback;
  const THEME = {
    bg: token("--bg-panel", "#131a24"),
    border: token("--border", "#232c3a"),
    text: token("--text-muted", "#7c8a9e"),
    accent: token("--accent", "#2962ff"),
    up: token("--up", "#26a69a"),
    down: token("--down", "#ef5350"),
  };

  function withAlpha(hex, alpha) {
    const n = parseInt(hex.replace("#", ""), 16);
    return "rgba(" + ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + alpha + ")";
  }

  // ───────────────────────── Formato ─────────────────────────
  const fmtNumber = (value, digits) =>
    value === null || value === undefined
      ? "—"
      : value.toLocaleString("es-ES", { minimumFractionDigits: digits, maximumFractionDigits: digits, useGrouping: "always" });
  const fmtPrice = (value) => fmtNumber(value, Math.abs(value) < 1 ? 4 : 2);

  function fmtVolume(value) {
    if (!value) return "—";
    const units = [[1e9, " B"], [1e6, " M"], [1e3, " K"]];
    for (const [size, suffix] of units) {
      if (value >= size) return fmtNumber(value / size, 2) + suffix;
    }
    return fmtNumber(value, 0);
  }

  let intraday = false;
  function fmtTime(time) {
    const options = { timeZone: "UTC", day: "2-digit", month: "short", year: "numeric" };
    if (intraday) Object.assign(options, { hour: "2-digit", minute: "2-digit" });
    return new Date(time * 1000).toLocaleString("es-ES", options);
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // ───────────────────────── Gráfico ─────────────────────────
  const chart = LC.createChart(document.getElementById("graficador-chart"), {
    autoSize: true,
    layout: {
      background: { type: LC.ColorType.Solid, color: THEME.bg },
      textColor: THEME.text,
      fontFamily: getComputedStyle(document.body).fontFamily,
      panes: { separatorColor: THEME.border, separatorHoverColor: withAlpha(THEME.accent, 0.2), enableResize: true },
    },
    grid: { vertLines: { color: withAlpha(THEME.border, 0.6) }, horzLines: { color: withAlpha(THEME.border, 0.6) } },
    rightPriceScale: { borderColor: THEME.border },
    timeScale: { borderColor: THEME.border, timeVisible: true, secondsVisible: false },
    crosshair: { mode: LC.CrosshairMode.Normal },
    localization: { locale: "es-ES" },
  });

  const SERIES = {
    candles: () =>
      chart.addSeries(
        LC.CandlestickSeries,
        { upColor: THEME.up, downColor: THEME.down, borderVisible: false, wickUpColor: THEME.up, wickDownColor: THEME.down },
        0,
      ),
    line: () => chart.addSeries(LC.LineSeries, { color: THEME.accent, lineWidth: 2 }, 0),
    area: () =>
      chart.addSeries(
        LC.AreaSeries,
        { lineColor: THEME.accent, topColor: withAlpha(THEME.accent, 0.4), bottomColor: withAlpha(THEME.accent, 0.02), lineWidth: 2 },
        0,
      ),
  };

  let seriesType = (typeButtons.find((b) => b.getAttribute("aria-pressed") === "true") || typeButtons[0]).dataset.seriesType;
  let mainSeries = SERIES[seriesType]();
  const volumeSeries = chart.addSeries(
    LC.HistogramSeries,
    { priceFormat: { type: "volume" }, priceLineVisible: false, lastValueVisible: false },
    1,
  );
  // El pane de precios ocupa 3/4 de la altura y el de volumen 1/4.
  chart.panes()[0].setStretchFactor(3);
  chart.panes()[1].setStretchFactor(1);

  let candles = [];
  let byTime = new Map();

  function mainData() {
    if (seriesType === "candles") return candles;
    return candles.map((c) => ({ time: c.time, value: c.close }));
  }

  function volumeData() {
    return candles.map((c) => ({
      time: c.time,
      value: c.volume || 0,
      color: withAlpha(c.close >= c.open ? THEME.up : THEME.down, 0.5),
    }));
  }

  function setSeriesType(type) {
    if (type === seriesType || !SERIES[type]) return;
    // Se crea la nueva antes de quitar la anterior para que el pane 0 nunca quede vacío.
    const previous = mainSeries;
    seriesType = type;
    mainSeries = SERIES[type]();
    mainSeries.setData(mainData());
    chart.removeSeries(previous);
  }

  // ───────────────────────── Leyenda OHLC ─────────────────────────
  function renderLegend(candle) {
    if (!candle) {
      legendEl.innerHTML = "";
      return;
    }
    const tone = candle.close >= candle.open ? "is-up" : "is-down";
    const item = (label, value) => '<span class="' + tone + '">' + label + " <b>" + value + "</b></span>";
    legendEl.innerHTML =
      "<span>" + escapeHtml(ticker) + " · " + fmtTime(candle.time) + "</span>" +
      item("O", fmtPrice(candle.open)) +
      item("H", fmtPrice(candle.high)) +
      item("L", fmtPrice(candle.low)) +
      item("C", fmtPrice(candle.close)) +
      item("Vol", fmtVolume(candle.volume));
  }

  chart.subscribeCrosshairMove((param) => {
    const candle = param && param.time !== undefined ? byTime.get(param.time) : null;
    renderLegend(candle || candles[candles.length - 1]);
  });

  // ───────────────────────── Estados ─────────────────────────
  function showStatus(text, isError) {
    statusEl.hidden = !text;
    statusEl.textContent = text || "";
    statusEl.classList.toggle("graficador__status--error", Boolean(isError));
  }

  function getJSON(url) {
    return fetch(url, { headers: { Accept: "application/json" } }).then((response) =>
      response.json().then((data) => {
        if (!response.ok) throw new Error(data.error || "HTTP " + response.status);
        return data;
      }),
    );
  }

  // Cada carga lleva un número; si llega tarde la respuesta de un rango anterior, se ignora.
  let request = 0;
  function load(button) {
    const id = ++request;
    intraday = !/^(1d|1wk|1mo)$/.test(button.dataset.interval);
    showStatus("Cargando datos de Yahoo Finance…");
    getJSON(candlesUrl + "?range=" + button.dataset.range + "&interval=" + button.dataset.interval)
      .then((data) => {
        if (id !== request) return;
        candles = data;
        byTime = new Map(candles.map((c) => [c.time, c]));
        mainSeries.setData(mainData());
        volumeSeries.setData(volumeData());
        chart.timeScale().fitContent();
        renderLegend(candles[candles.length - 1]);
        showStatus(
          candles.length ? "" : "No hay datos de «" + ticker + "» en Yahoo Finance para este rango. Revisa el ticker.",
          !candles.length,
        );
      })
      .catch(() => id === request && showStatus("No pudimos cargar el gráfico. Inténtalo de nuevo.", true));
  }

  function press(buttons, active) {
    buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === active)));
  }

  rangeButtons.forEach((button) =>
    button.addEventListener("click", () => {
      press(rangeButtons, button);
      load(button);
    }),
  );
  typeButtons.forEach((button) =>
    button.addEventListener("click", () => {
      press(typeButtons, button);
      setSeriesType(button.dataset.seriesType);
    }),
  );

  load(rangeButtons.find((b) => b.getAttribute("aria-pressed") === "true") || rangeButtons[0]);

  // ───────────────────────── Cabecera (precio actual) ─────────────────────────
  getJSON(quoteUrl)
    .then((q) => {
      if (q.name && q.name !== ticker) nameEl.textContent = q.name;
      if (q.price === null || q.price === undefined) return;
      const tone = (q.change || 0) >= 0 ? "is-up" : "is-down";
      const sign = (q.change || 0) >= 0 ? "+" : "";
      const change =
        q.change === null
          ? ""
          : ' <span class="' + tone + '">' + sign + fmtPrice(q.change) + " (" + sign + q.change_percent.toFixed(2) + "%)</span>";
      quoteEl.innerHTML = "<strong>" + fmtPrice(q.price) + "</strong> " + escapeHtml(q.currency || "") + change;
    })
    .catch(() => {});
})();
