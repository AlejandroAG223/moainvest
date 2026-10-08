/**
 * Vista "CAPM": pide la tabla de retornos esperados de un sector a la API
 * (sector, año y proxy del mercado elegidos en el formulario) y la muestra
 * en una tabla.
 */
(function () {
  "use strict";

  const form = document.getElementById("capm-form");
  if (!form) return; // esta página no está montada

  const sectorSelect = document.getElementById("sector-select");
  const yearSelect = document.getElementById("year-select");
  const marketSelect = document.getElementById("market-select");
  const btn = document.getElementById("capm-btn");
  const statusEl = document.getElementById("capm-status");
  const resultEl = document.getElementById("capm-result");
  const tableBody = document.getElementById("capm-table-body");
  const summaryEl = document.getElementById("capm-summary");

  function setStatus(message, isError) {
    statusEl.hidden = !message;
    statusEl.textContent = message || "";
    statusEl.classList.toggle("is-error", Boolean(isError));
  }

  function fmtPercent(value) {
    return `${(value * 100).toFixed(1)}%`;
  }

  function fmtBeta(value) {
    return Number(value).toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function fmtDate(isoDate) {
    const [year, month, day] = isoDate.split("-");
    return `${day}/${month}/${year}`;
  }

  function renderTable(rows) {
    const fragment = document.createDocumentFragment();
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.ticker}</td>
        <td>${fmtBeta(row.beta)}</td>
        <td>${fmtPercent(row.expected_return)}</td>
        <td>${fmtPercent(row.risk_free_rate)}</td>
        <td>${fmtDate(row.since)}</td>
      `;
      fragment.appendChild(tr);
    });
    tableBody.replaceChildren(fragment);
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();

    const sector = sectorSelect.value;
    const year = yearSelect.value;
    const market = marketSelect.value;

    btn.disabled = true;
    resultEl.hidden = true;
    setStatus("Descargando precios y tasa libre de riesgo…");

    const url = `/api/capm-table?sector=${encodeURIComponent(sector)}&year=${encodeURIComponent(year)}&market=${encodeURIComponent(market)}`;

    fetch(url)
      .then(async (res) => {
        if (!res.ok) {
          const payload = await res.json().catch(() => ({}));
          throw new Error(payload.error || "Error al calcular el CAPM");
        }
        return res.json();
      })
      .then((data) => {
        if (!data.rows || data.rows.length === 0) {
          setStatus("No se encontraron datos para el sector y año seleccionados.", true);
          return;
        }
        renderTable(data.rows);
        summaryEl.textContent = `${sector} · ${year} · ${data.rows.length} activos`;
        resultEl.hidden = false;
        setStatus("");
      })
      .catch((err) => {
        setStatus(err.message || "Ocurrió un error al calcular el CAPM.", true);
      })
      .finally(() => {
        btn.disabled = false;
      });
  });
})();
