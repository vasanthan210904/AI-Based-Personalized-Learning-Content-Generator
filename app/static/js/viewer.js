/* Material viewer — active table of contents and reading progress */
(function () {
  "use strict";

  const links = Array.from(document.querySelectorAll("[data-toc-link]"));
  const sections = links
    .map((link) => document.getElementById(link.getAttribute("data-toc-link")))
    .filter(Boolean);

  if (sections.length && "IntersectionObserver" in window) {
    const linkById = new Map(
      links.map((link) => [link.getAttribute("data-toc-link"), link])
    );

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          links.forEach((link) => link.classList.remove("is-active"));
          const link = linkById.get(entry.target.id);
          if (link) {
            link.classList.add("is-active");
          }
        });
      },
      { rootMargin: "-90px 0px -65% 0px", threshold: 0 }
    );

    sections.forEach((section) => observer.observe(section));
    if (links[0]) links[0].classList.add("is-active");
  }

  /* Reading progress bar injected below the top bar. */
  const article = document.getElementById("readingCard");
  const main = document.querySelector(".app-main");
  if (article && main) {
    const bar = document.createElement("div");
    bar.className = "reader-progress";
    bar.setAttribute("aria-hidden", "true");
    bar.innerHTML = "<span></span>";
    const topbar = main.querySelector(".app-topbar");
    if (topbar) {
      topbar.insertAdjacentElement("afterend", bar);
    } else {
      main.prepend(bar);
    }
    const fill = bar.querySelector("span");

    const update = () => {
      const rect = article.getBoundingClientRect();
      const start = window.scrollY + rect.top;
      const total = article.offsetHeight - window.innerHeight * 0.35;
      const progress = Math.min(
        100,
        Math.max(0, ((window.scrollY - start + 140) / Math.max(total, 1)) * 100)
      );
      fill.style.width = `${progress}%`;
    };

    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  }

  /* ------------------------------------------------------------------ */
  /* Private notes                                                      */
  /* ------------------------------------------------------------------ */
  const noteButton = document.getElementById("saveBookmarkNote");
  if (noteButton) {
    noteButton.addEventListener("click", async () => {
      const contentId = noteButton.getAttribute("data-save-note");
      const note = document.getElementById("bookmarkNote")?.value || "";
      noteButton.disabled = true;
      try {
        await LF.request(`/api/bookmarks/${contentId}`, {
          method: "POST",
          body: { note: note },
        });
        const bookmarkButton = document.querySelector(
          `[data-bookmark-toggle="${contentId}"]`
        );
        if (bookmarkButton) {
          bookmarkButton.dataset.bookmarkSaved = "true";
          bookmarkButton.classList.add("is-saved");
          bookmarkButton.setAttribute("aria-pressed", "true");
          const icon = bookmarkButton.querySelector("i");
          if (icon) icon.className = "bi bi-bookmark-fill";
          const label = bookmarkButton.querySelector("[data-bookmark-label]");
          if (label) label.textContent = "Saved";
        }
        LF.showToast("Your private note was saved.", "success");
      } catch (error) {
        LF.handleFailure(error, "Could not save your note.");
      } finally {
        noteButton.disabled = false;
      }
    });
  }

  /* ------------------------------------------------------------------ */
  /* Share links                                                        */
  /* ------------------------------------------------------------------ */
  const sharePanel = document.getElementById("sharePanel");
  if (sharePanel) {
    const contentId = sharePanel.getAttribute("data-share-content");
    const activeBox = document.getElementById("shareActiveBox");
    const inactiveText = document.getElementById("shareInactiveText");
    const shareUrl = document.getElementById("shareUrl");
    const createButton = document.getElementById("createShare");
    const revokeButton = document.getElementById("revokeShare");
    const copyButton = document.getElementById("copyShareUrl");
    const openLink = document.getElementById("openShareUrl");
    const viewsNode = document.getElementById("shareViews");

    const showActive = (payload) => {
      activeBox?.classList.remove("d-none");
      createButton?.classList.add("d-none");
      if (inactiveText) inactiveText.classList.add("d-none");
      if (shareUrl) {
        shareUrl.value = new URL(payload.url, window.location.origin).href;
        shareUrl.dataset.absolute = shareUrl.value;
      }
      if (openLink) openLink.href = payload.url;
      if (viewsNode) viewsNode.textContent = payload.views ?? 0;
      sharePanel.dataset.shareActive = "true";
      sharePanel.dataset.shareUrl = payload.url;
    };

    const showInactive = () => {
      activeBox?.classList.add("d-none");
      createButton?.classList.remove("d-none");
      inactiveText?.classList.remove("d-none");
      if (shareUrl) shareUrl.value = "";
      sharePanel.dataset.shareActive = "false";
      sharePanel.dataset.shareUrl = "";
    };

    if (sharePanel.getAttribute("data-share-active") === "true") {
      activeBox?.classList.remove("d-none");
      createButton?.classList.add("d-none");
      inactiveText?.classList.add("d-none");
    }

    createButton?.addEventListener("click", async () => {
      LF.setLoading(createButton, true, "Creating…");
      try {
        const payload = await LF.request(
          `/api/learning-content/${contentId}/share`,
          { method: "POST" }
        );
        showActive({ ...payload.data.share, url: payload.data.share.url });
        LF.showToast("Read-only share link created.", "success");
      } catch (error) {
        LF.handleFailure(error, "Could not create the share link.");
      } finally {
        LF.setLoading(createButton, false);
      }
    });

    revokeButton?.addEventListener("click", async () => {
      const confirmed = await LF.confirm({
        title: "Revoke the share link?",
        message: "Anyone with the current link will lose access immediately.",
        confirmLabel: "Revoke link",
        tone: "danger",
        icon: "bi-link-45deg",
      });
      if (!confirmed) return;
      LF.setLoading(revokeButton, true, "Revoking…");
      try {
        await LF.request(`/api/learning-content/${contentId}/share`, {
          method: "DELETE",
        });
        showInactive();
        LF.showToast("Share link revoked.", "success");
      } catch (error) {
        LF.handleFailure(error, "Could not revoke the link.");
      } finally {
        LF.setLoading(revokeButton, false);
      }
    });

    copyButton?.addEventListener("click", async () => {
      const url = shareUrl?.dataset.absolute || shareUrl?.value;
      if (!url) return;
      try {
        await navigator.clipboard.writeText(url);
        LF.showToast("Share link copied.", "success");
      } catch (error) {
        shareUrl?.select();
        document.execCommand("copy");
        LF.showToast("Share link copied.", "success");
      }
    });
  }

  /* ------------------------------------------------------------------ */
  /* Create flashcards from this material                               */
  /* ------------------------------------------------------------------ */
  document.querySelectorAll("[data-create-flashcards]").forEach((button) => {
    button.addEventListener("click", async () => {
      const contentId = button.getAttribute("data-create-flashcards");
      LF.setLoading(button, true, "Building deck…");
      try {
        const payload = await LF.request("/api/flashcards/generate", {
          method: "POST",
          body: { content_id: Number(contentId) },
        });
        if (button.getAttribute("data-create-flashcards-redirect") === "true") {
          window.location.href = payload.data.redirect_url;
        } else {
          LF.showToast(payload.message || "Flashcard deck ready.", "success");
        }
      } catch (error) {
        LF.handleFailure(error, "Could not create flashcards.");
      } finally {
        LF.setLoading(button, false);
      }
    });
  });
})();
