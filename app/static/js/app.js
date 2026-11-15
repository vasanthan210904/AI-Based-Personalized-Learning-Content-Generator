/* LearnForge AI — shared front-end helpers */
(function () {
  "use strict";

  const LF = (window.LF = window.LF || {});

  LF.csrfToken =
    document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") || "";

  LF.escapeHtml = function (value) {
    const div = document.createElement("div");
    div.textContent = value == null ? "" : String(value);
    return div.innerHTML;
  };

  LF.showToast = function (message, type) {
    const kind = ["success", "danger", "warning", "info"].includes(type)
      ? type
      : "info";
    const container = document.getElementById("toastContainer");
    if (!container || typeof bootstrap === "undefined") {
      window.alert(message);
      return;
    }
    const icons = {
      success: "bi-check-circle-fill",
      danger: "bi-x-circle-fill",
      warning: "bi-exclamation-triangle-fill",
      info: "bi-info-circle-fill",
    };
    const wrapper = document.createElement("div");
    wrapper.className = `toast lf-toast toast-${kind}`;
    wrapper.setAttribute("role", "status");
    wrapper.setAttribute("aria-live", "polite");
    wrapper.setAttribute("aria-atomic", "true");
    wrapper.innerHTML = `
      <div class="toast-body">
        <i class="bi ${icons[kind]} toast-icon" aria-hidden="true"></i>
        <div class="flex-grow-1">${LF.escapeHtml(message)}</div>
        <button type="button" class="btn-close btn-close-sm ms-1" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>`;
    container.appendChild(wrapper);
    const toast = new bootstrap.Toast(wrapper, { delay: 5200 });
    wrapper.addEventListener("hidden.bs.toast", () => wrapper.remove());
    toast.show();
  };

  /* Queue a toast across a full page reload. */
  LF.flashNext = function (message, type) {
    try {
      sessionStorage.setItem(
        "lfFlash",
        JSON.stringify({ message: message, type: type || "success" })
      );
    } catch (error) {
      /* storage may be unavailable; ignore */
    }
  };

  LF.drainQueuedFlash = function () {
    try {
      const raw = sessionStorage.getItem("lfFlash");
      if (!raw) return;
      sessionStorage.removeItem("lfFlash");
      const payload = JSON.parse(raw);
      if (payload && payload.message) {
        LF.showToast(payload.message, payload.type);
      }
    } catch (error) {
      /* ignore malformed queue entries */
    }
  };

  LF.applyFieldErrors = function (fields) {
    if (!fields || typeof fields !== "object") return;
    Object.keys(fields).forEach((name) => {
      const message = fields[name];
      const input = document.querySelector(`[name="${name}"]`);
      if (!input) return;
      input.classList.add("is-invalid");
      const wrap = input.closest(".mb-3, .mb-1, .mb-2, .modal-body") || input.parentElement;
      if (wrap && !wrap.querySelector(`[data-lf-error="${name}"]`)) {
        const note = document.createElement("div");
        note.className = "field-error";
        note.dataset.lfError = name;
        note.innerHTML = `<span>${LF.escapeHtml(message)}</span>`;
        wrap.appendChild(note);
      }
    });
  };

  LF.clearFieldErrors = function (root) {
    const scope = root || document;
    scope.querySelectorAll(".is-invalid").forEach((el) => el.classList.remove("is-invalid"));
    scope.querySelectorAll("[data-lf-error]").forEach((el) => el.remove());
  };

  /**
   * Fetch wrapper for the JSON API. Resolves with the full response payload
   * ({success, data, message}) and rejects with an Error carrying status,
   * code and fields so callers can present useful feedback.
   */
  LF.request = async function (url, options) {
    const opts = Object.assign({ method: "GET" }, options || {});
    const headers = new Headers(opts.headers || {});
    let body = opts.body;

    if (body != null && typeof body !== "string" && !(body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
      body = JSON.stringify(body);
    }
    if (!["GET", "HEAD", "OPTIONS"].includes(opts.method.toUpperCase())) {
      headers.set("X-CSRFToken", LF.csrfToken);
    }
    headers.set("Accept", "application/json");

    let response;
    try {
      response = await fetch(url, {
        method: opts.method,
        headers: headers,
        body: body,
        credentials: "same-origin",
        cache: "no-store",
      });
    } catch (error) {
      const netError = new Error(
        "Could not reach the server. Check your connection and try again."
      );
      netError.code = "network_error";
      throw netError;
    }

    let payload = null;
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      try {
        payload = await response.json();
      } catch (error) {
        payload = null;
      }
    }

    if (!response.ok || !payload || payload.success === false) {
      const info = (payload && payload.error) || {};
      const failure = new Error(
        info.message ||
          (response.status === 401
            ? "Your session has expired. Please sign in again."
            : "Something went wrong. Please try again.")
      );
      failure.status = response.status;
      failure.code = info.code || "request_failed";
      failure.fields = info.fields || null;
      if (response.status === 401) {
        failure.authExpired = true;
      }
      throw failure;
    }

    return payload;
  };

  LF.setLoading = function (button, loading, label) {
    if (!button) return;
    if (loading) {
      if (!button.dataset.originalHtml) {
        button.dataset.originalHtml = button.innerHTML;
      }
      button.disabled = true;
      button.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>${LF.escapeHtml(label || "Working…")}`;
    } else {
      button.disabled = false;
      if (button.dataset.originalHtml) {
        button.innerHTML = button.dataset.originalHtml;
        delete button.dataset.originalHtml;
      }
    }
  };

  /* Promise-based confirmation using the shared modal when available. */
  LF.confirm = function (options) {
    const settings = Object.assign(
      {
        title: "Are you sure?",
        message: "This action cannot be undone.",
        confirmLabel: "Confirm",
        cancelLabel: "Cancel",
        tone: "danger",
        icon: "bi-trash3",
      },
      options || {}
    );

    const modalEl = document.getElementById("lfConfirmModal");
    if (!modalEl || typeof bootstrap === "undefined") {
      return Promise.resolve(window.confirm(settings.message));
    }

    return new Promise((resolve) => {
      const icon = document.getElementById("lfConfirmIcon");
      const title = document.getElementById("lfConfirmTitle");
      const message = document.getElementById("lfConfirmMessage");
      const confirmButton = document.getElementById("lfConfirmButton");
      const cancelButton = modalEl.querySelector('[data-bs-dismiss="modal"].btn-light');

      if (icon) icon.innerHTML = `<i class="bi ${settings.icon}"></i>`;
      if (title) title.textContent = settings.title;
      if (message) message.textContent = settings.message;
      if (confirmButton) {
        confirmButton.textContent = settings.confirmLabel;
        confirmButton.className =
          settings.tone === "danger" ? "btn btn-danger" : "btn btn-primary";
      }
      if (cancelButton) cancelButton.textContent = settings.cancelLabel;

      const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
      let settled = false;

      const finish = (value) => {
        if (settled) return;
        settled = true;
        confirmButton?.removeEventListener("click", onConfirm);
        modalEl.removeEventListener("hidden.bs.modal", onHidden);
        resolve(value);
      };
      const onConfirm = () => {
        finish(true);
        modal.hide();
      };
      const onHidden = () => finish(false);

      confirmButton?.addEventListener("click", onConfirm);
      modalEl.addEventListener("hidden.bs.modal", onHidden);
      modal.show();
    });
  };

  LF.handleFailure = function (error, fallback) {
    const message = error && error.message ? error.message : fallback || "Something went wrong.";
    LF.showToast(message, "danger");
    if (error && error.fields) LF.applyFieldErrors(error.fields);
    if (error && error.authExpired) {
      window.setTimeout(() => {
        const next = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = `/login?next=${next}`;
      }, 900);
    }
  };

  /* ------------------------------------------------------------------ */
  /* Theme                                                              */
  /* ------------------------------------------------------------------ */
  function updateThemeButtons(theme) {
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      const dark = theme === "dark";
      button.innerHTML = `<i class="bi ${dark ? "bi-sun" : "bi-moon-stars"}"></i>`;
      button.setAttribute(
        "aria-label",
        dark ? "Switch to light theme" : "Switch to dark theme"
      );
      button.setAttribute("title", dark ? "Light theme" : "Dark theme");
    });
  }

  function setTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem("lfTheme", theme);
    } catch (error) {
      /* storage may be unavailable; theme still applies for this page */
    }
    updateThemeButtons(theme);
  }

  function initTheme() {
    const current =
      document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
    updateThemeButtons(current);
    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        setTheme(
          document.documentElement.getAttribute("data-theme") === "dark"
            ? "light"
            : "dark"
        );
      });
    });
  }

  /* ------------------------------------------------------------------ */
  /* Bookmark toggles                                                   */
  /* ------------------------------------------------------------------ */
  function setBookmarkState(button, saved) {
    button.dataset.bookmarkSaved = saved ? "true" : "false";
    button.setAttribute("aria-pressed", saved ? "true" : "false");
    button.classList.toggle("is-saved", saved);
    const label = saved ? "Remove from saved" : "Save material";
    button.setAttribute("title", label);
    button.setAttribute("aria-label", label);
    const icon = button.querySelector("i");
    if (icon) icon.className = `bi ${saved ? "bi-bookmark-fill" : "bi-bookmark"}`;
    const text = button.querySelector("[data-bookmark-label]");
    if (text) text.textContent = saved ? "Saved" : "Save";
  }

  function initBookmarkToggles() {
    document.addEventListener("click", async (event) => {
      const trigger = event.target.closest("[data-bookmark-toggle]");
      if (!trigger) return;
      event.preventDefault();
      const id = trigger.getAttribute("data-bookmark-toggle");
      if (!id || trigger.disabled) return;
      const saved = trigger.getAttribute("data-bookmark-saved") === "true";
      trigger.disabled = true;
      try {
        await LF.request(`/api/bookmarks/${id}`, {
          method: saved ? "DELETE" : "POST",
          body: saved ? undefined : {},
        });
        setBookmarkState(trigger, !saved);
        LF.showToast(
          saved ? "Removed from your saved library." : "Saved to your library.",
          "success"
        );
        if (trigger.hasAttribute("data-bookmark-reload")) {
          window.setTimeout(() => window.location.reload(), 500);
        }
      } catch (error) {
        LF.handleFailure(error, "Could not update your saved library.");
      } finally {
        trigger.disabled = false;
      }
    });
  }

  /* ------------------------------------------------------------------ */
  /* Sidebar                                                            */
  /* ------------------------------------------------------------------ */
  function setSidebar(open) {
    const sidebar = document.getElementById("appSidebar");
    const backdrop = document.querySelector(".sidebar-backdrop");
    if (!sidebar) return;
    sidebar.classList.toggle("is-open", open);
    if (backdrop) backdrop.classList.toggle("is-visible", open);
    document.body.classList.toggle("sidebar-locked", open);
    const toggle = document.querySelector("[data-sidebar-toggle]");
    if (toggle) toggle.setAttribute("aria-expanded", open ? "true" : "false");
  }

  function initSidebar() {
    document.querySelectorAll("[data-sidebar-toggle]").forEach((button) => {
      button.addEventListener("click", () => {
        const sidebar = document.getElementById("appSidebar");
        setSidebar(!(sidebar && sidebar.classList.contains("is-open")));
      });
    });
    document.querySelectorAll("[data-sidebar-close]").forEach((button) => {
      button.addEventListener("click", () => setSidebar(false));
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") setSidebar(false);
    });
    window.addEventListener("resize", () => {
      if (window.innerWidth >= 992) setSidebar(false);
    });
  }

  /* ------------------------------------------------------------------ */
  /* Password visibility                                                */
  /* ------------------------------------------------------------------ */
  function initPasswordToggles() {
    document.querySelectorAll("[data-toggle-password]").forEach((button) => {
      button.addEventListener("click", () => {
        const wrap = button.closest(".password-wrap");
        const input = wrap ? wrap.querySelector("input") : null;
        if (!input) return;
        const show = input.type === "password";
        input.type = show ? "text" : "password";
        button.innerHTML = `<i class="bi ${show ? "bi-eye-slash" : "bi-eye"}"></i>`;
        button.setAttribute("aria-label", show ? "Hide password" : "Show password");
      });
    });
  }

  /* ------------------------------------------------------------------ */
  /* Flash messages                                                     */
  /* ------------------------------------------------------------------ */
  function initFlashMessages() {
    document.querySelectorAll("#flash-store [data-flash-message]").forEach((node) => {
      const type = node.getAttribute("data-flash-type") || "info";
      LF.showToast(node.getAttribute("data-flash-message"), type);
    });
    LF.drainQueuedFlash();
  }

  /* ------------------------------------------------------------------ */
  /* Global delete-content flow                                         */
  /* ------------------------------------------------------------------ */
  function initContentDeletes() {
    document.addEventListener("click", async (event) => {
      const trigger = event.target.closest("[data-delete-content]");
      if (!trigger) return;
      event.preventDefault();
      const id = trigger.getAttribute("data-delete-content");
      const title = trigger.getAttribute("data-delete-title") || "this material";
      if (!id) return;

      const confirmed = await LF.confirm({
        title: "Delete this material?",
        message: `“${title}” will be permanently removed from your history. This cannot be undone.`,
        confirmLabel: "Delete material",
        icon: "bi-trash3",
      });
      if (!confirmed) return;

      if (trigger.tagName === "BUTTON") trigger.disabled = true;
      try {
        await LF.request(`/api/learning-content/${id}`, { method: "DELETE" });
        LF.flashNext("Learning material deleted.", "success");
        if (window.location.pathname.startsWith("/learning/content/")) {
          window.location.href = "/learning/history";
        } else {
          window.location.reload();
        }
      } catch (error) {
        if (trigger.tagName === "BUTTON") trigger.disabled = false;
        LF.handleFailure(error, "Could not delete the material.");
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initSidebar();
    initPasswordToggles();
    initFlashMessages();
    initContentDeletes();
    initBookmarkToggles();
  });
})();
