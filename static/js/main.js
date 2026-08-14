(function () {
  "use strict";

  /* ---- Mobile sidebar toggle ---- */
  var sidebar = document.getElementById("sidebar");
  var overlay = document.getElementById("overlay");
  var toggleBtn = document.getElementById("sidebar-toggle");

  function closeSidebar() {
    if (!sidebar) return;
    sidebar.classList.add("-translate-x-full");
    if (overlay) overlay.classList.add("hidden");
  }

  if (toggleBtn) {
    toggleBtn.addEventListener("click", function () {
      sidebar.classList.toggle("-translate-x-full");
      if (overlay) overlay.classList.toggle("hidden");
    });
  }
  if (overlay) {
    overlay.addEventListener("click", closeSidebar);
  }

  /* ---- Flash messages: dismiss button + auto-dismiss ---- */
  document.querySelectorAll(".flash-message").forEach(function (el) {
    var dismissBtn = el.querySelector(".dismiss-btn");
    var remove = function () {
      el.classList.add("flash-out");
      setTimeout(function () {
        el.remove();
      }, 320);
    };
    if (dismissBtn) dismissBtn.addEventListener("click", remove);
    var ttl = parseInt(el.getAttribute("data-dismiss") || "0", 10);
    if (ttl > 0) setTimeout(remove, ttl);
  });

  /* ---- Confirmation for destructive forms ---- */
  document.querySelectorAll(".confirm-form").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      var message = form.getAttribute("data-confirm") || "Are you sure?";
      if (!window.confirm(message)) {
        e.preventDefault();
      }
    });
  });
})();