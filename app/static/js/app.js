/**
 * Comportamiento común de las páginas con sidebar (base.html): colapsar y
 * expandir el panel, recordando la preferencia en localStorage.
 */
(function () {
  "use strict";

  function initSidebar() {
    const layout = document.querySelector(".layout");
    const toggleBtn = document.getElementById("sidebar-toggle");
    if (!layout || !toggleBtn) return;
    const collapsed = localStorage.getItem("sidebar-collapsed") === "1";
    layout.classList.toggle("is-sidebar-collapsed", collapsed);
    toggleBtn.addEventListener("click", () => {
      const isCollapsed = layout.classList.toggle("is-sidebar-collapsed");
      localStorage.setItem("sidebar-collapsed", isCollapsed ? "1" : "0");
    });
  }

  document.addEventListener("DOMContentLoaded", initSidebar);
})();
