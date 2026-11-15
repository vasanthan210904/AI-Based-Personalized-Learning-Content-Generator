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

  /* ------------------------------------------------------------------ */
  /* Audio Voice Reader (Speech Synthesis)                              */
  /* ------------------------------------------------------------------ */
  const btnPlaySpeech = document.getElementById("btnPlaySpeech");
  const btnPauseSpeech = document.getElementById("btnPauseSpeech");
  const btnStopSpeech = document.getElementById("btnStopSpeech");
  const speechRateSelect = document.getElementById("speechRateSelect");
  const readerStatus = document.getElementById("readerStatus");
  const btnToggleAudioBar = document.getElementById("btnToggleAudioBar");
  const audioReaderBar = document.getElementById("audioReaderBar");

  btnToggleAudioBar?.addEventListener("click", () => {
    if (audioReaderBar) {
      audioReaderBar.scrollIntoView({ behavior: "smooth", block: "center" });
      audioReaderBar.classList.add("border-primary");
      setTimeout(() => audioReaderBar.classList.remove("border-primary"), 1500);
    }
  });

  if ("speechSynthesis" in window && btnPlaySpeech) {
    let currentUtterance = null;
    let isSpeaking = false;
    let isPaused = false;

    function getReadableText() {
      const title = document.querySelector(".viewer-title-block h1")?.textContent || "";
      const intro = document.getElementById("introduction")?.innerText || "";
      const summary = document.getElementById("summary")?.innerText || "";
      const concepts = document.getElementById("concepts")?.innerText || "";
      return `${title}. \n\nIntroduction: ${intro}. \n\nCore Concepts: ${concepts}. \n\nSummary: ${summary}`;
    }

    btnPlaySpeech.addEventListener("click", () => {
      if (isPaused) {
        window.speechSynthesis.resume();
        isPaused = false;
        isSpeaking = true;
        btnPlaySpeech.innerHTML = '<i class="bi bi-play-fill"></i> Resume';
        btnPauseSpeech.disabled = false;
        btnStopSpeech.disabled = false;
        if (readerStatus) readerStatus.textContent = "Playing notes aloud…";
        return;
      }

      window.speechSynthesis.cancel();
      const text = getReadableText();
      if (!text.trim()) {
        LF.showToast("No text available to read aloud.", "warning");
        return;
      }

      currentUtterance = new SpeechSynthesisUtterance(text);
      currentUtterance.rate = parseFloat(speechRateSelect?.value || "1.0");
      currentUtterance.lang = "en-US";

      currentUtterance.onstart = () => {
        isSpeaking = true;
        isPaused = false;
        btnPlaySpeech.disabled = true;
        btnPauseSpeech.disabled = false;
        btnStopSpeech.disabled = false;
        if (readerStatus) readerStatus.textContent = "Reading notes aloud…";
      };

      currentUtterance.onend = () => {
        isSpeaking = false;
        isPaused = false;
        btnPlaySpeech.disabled = false;
        btnPauseSpeech.disabled = true;
        btnStopSpeech.disabled = true;
        btnPlaySpeech.innerHTML = '<i class="bi bi-play-fill"></i> Play';
        if (readerStatus) readerStatus.textContent = "Finished reading notes.";
      };

      currentUtterance.onerror = () => {
        isSpeaking = false;
        isPaused = false;
        btnPlaySpeech.disabled = false;
        btnPauseSpeech.disabled = true;
        btnStopSpeech.disabled = true;
        btnPlaySpeech.innerHTML = '<i class="bi bi-play-fill"></i> Play';
        if (readerStatus) readerStatus.textContent = "Audio playback stopped.";
      };

      window.speechSynthesis.speak(currentUtterance);
    });

    btnPauseSpeech?.addEventListener("click", () => {
      if (isSpeaking && !isPaused) {
        window.speechSynthesis.pause();
        isPaused = true;
        btnPauseSpeech.disabled = true;
        btnPlaySpeech.disabled = false;
        btnPlaySpeech.innerHTML = '<i class="bi bi-play-fill"></i> Resume';
        if (readerStatus) readerStatus.textContent = "Audio paused.";
      }
    });

    btnStopSpeech?.addEventListener("click", () => {
      window.speechSynthesis.cancel();
      isSpeaking = false;
      isPaused = false;
      btnPlaySpeech.disabled = false;
      btnPauseSpeech.disabled = true;
      btnStopSpeech.disabled = true;
      btnPlaySpeech.innerHTML = '<i class="bi bi-play-fill"></i> Play';
      if (readerStatus) readerStatus.textContent = "Audio stopped.";
    });

    speechRateSelect?.addEventListener("change", () => {
      if (isSpeaking) {
        LF.showToast("Speed updated for next playback.", "info");
      }
    });
  }

  /* ------------------------------------------------------------------ */
  /* Ask AI Tutor Chat Assistant                                       */
  /* ------------------------------------------------------------------ */
  const tutorForm = document.getElementById("tutorQuestionForm");
  const tutorInput = document.getElementById("tutorQuestionInput");
  const tutorStream = document.getElementById("tutorChatStream");
  const tutorSubmitBtn = document.getElementById("btnSubmitTutorQuestion");

  let viewerData = {};
  try {
    viewerData = JSON.parse(document.getElementById("viewerData")?.textContent || "{}");
  } catch (e) {
    viewerData = {};
  }
  const contentId = viewerData.contentId;

  async function submitTutorQuestion(questionText) {
    if (!questionText.trim() || !contentId) return;

    // Append User Bubble
    const userBubble = document.createElement("div");
    userBubble.className = "user-msg p-3 bg-primary text-white rounded-3 mb-3 ms-4 shadow-sm";
    userBubble.innerHTML = `<div class="small fw-semibold mb-1 opacity-75">You</div><div>${LF.escapeHtml(questionText)}</div>`;
    tutorStream?.appendChild(userBubble);
    tutorStream.scrollTop = tutorStream.scrollHeight;

    // Loading indicator
    const loadingBubble = document.createElement("div");
    loadingBubble.className = "tutor-msg p-3 bg-white rounded-3 border mb-3 shadow-sm";
    loadingBubble.innerHTML = `<div class="d-flex align-items-center gap-2 text-primary small"><span class="spinner-border spinner-border-sm" role="status"></span> AI Tutor is thinking…</div>`;
    tutorStream?.appendChild(loadingBubble);
    tutorStream.scrollTop = tutorStream.scrollHeight;

    if (tutorInput) tutorInput.value = "";
    if (tutorSubmitBtn) tutorSubmitBtn.disabled = true;

    try {
      const res = await LF.request(`/api/learning-content/${contentId}/ask-tutor`, {
        method: "POST",
        body: { question: questionText }
      });

      loadingBubble.remove();
      const replyData = res.data;

      const aiBubble = document.createElement("div");
      aiBubble.className = "tutor-msg p-3 bg-white rounded-3 border mb-3 shadow-sm";
      let followupsHtml = "";
      if (replyData.suggested_followups && replyData.suggested_followups.length) {
        followupsHtml = `<div class="mt-3 pt-2 border-top"><div class="small fw-semibold text-muted mb-1">Suggested Follow-ups:</div><div class="d-flex flex-wrap gap-1">${replyData.suggested_followups.map(f => `<button type="button" class="btn btn-xs btn-outline-primary rounded-pill py-1 px-2 small tutor-chip">${LF.escapeHtml(f)}</button>`).join("")}</div></div>`;
      }

      aiBubble.innerHTML = `
        <div class="fw-semibold text-primary mb-1 d-flex align-items-center gap-1">
          <i class="bi bi-stars"></i> LearnForge AI Tutor
        </div>
        <div class="small text-dark lh-base">${LF.escapeHtml(replyData.answer).replace(/\n/g, "<br>")}</div>
        ${followupsHtml}
      `;
      tutorStream?.appendChild(aiBubble);
      tutorStream.scrollTop = tutorStream.scrollHeight;
    } catch (err) {
      loadingBubble.remove();
      LF.handleFailure(err, "Could not get an answer from the tutor.");
    } finally {
      if (tutorSubmitBtn) tutorSubmitBtn.disabled = false;
    }
  }

  tutorForm?.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = tutorInput?.value.trim();
    if (q) submitTutorQuestion(q);
  });

  tutorStream?.addEventListener("click", (e) => {
    const chip = e.target.closest(".tutor-chip");
    if (chip) {
      const q = chip.textContent.trim();
      if (q) submitTutorQuestion(q);
    }
  });

  /* ------------------------------------------------------------------ */
  /* Code Snippet Copy Buttons                                          */
  /* ------------------------------------------------------------------ */
  document.querySelectorAll(".example-card pre, pre.example-text").forEach((pre) => {
    const wrapper = pre.parentElement;
    if (!wrapper) return;
    wrapper.style.position = "relative";
    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.className = "btn btn-xs btn-light border position-absolute top-0 end-0 m-2";
    copyBtn.innerHTML = '<i class="bi bi-clipboard"></i> Copy';
    copyBtn.title = "Copy snippet";
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(pre.textContent);
        copyBtn.innerHTML = '<i class="bi bi-check2 text-success"></i> Copied!';
        setTimeout(() => {
          copyBtn.innerHTML = '<i class="bi bi-clipboard"></i> Copy';
        }, 2000);
      } catch (e) {
        LF.showToast("Could not copy to clipboard.", "warning");
      }
    });
    wrapper.appendChild(copyBtn);
  });

  /* ------------------------------------------------------------------ */
  /* Quick Revision Cheat Sheet Loader                                   */
  /* ------------------------------------------------------------------ */
  let cheatSheetData = null;
  const cheatSheetModal = document.getElementById("cheatSheetModal");
  const cheatSheetLoading = document.getElementById("cheatSheetLoading");
  const cheatSheetContent = document.getElementById("cheatSheetContent");
  const cheatSheetGrid = document.getElementById("cheatSheetGrid");
  const btnCopyCheatSheet = document.getElementById("btnCopyCheatSheet");

  if (cheatSheetModal && contentId) {
    cheatSheetModal.addEventListener("show.bs.modal", async () => {
      if (cheatSheetData) return; // already loaded
      try {
        const res = await LF.request(`/api/learning-content/${contentId}/cheat-sheet`);
        cheatSheetData = res.data;
        renderCheatSheet(cheatSheetData);
      } catch (err) {
        if (cheatSheetLoading) {
          cheatSheetLoading.innerHTML = `
            <div class="alert alert-danger mb-0">
              <i class="bi bi-exclamation-circle me-1"></i> Failed to generate cheat sheet. Please try again.
            </div>`;
        }
      }
    });
  }

  function renderCheatSheet(data) {
    if (!cheatSheetGrid) return;
    if (cheatSheetLoading) cheatSheetLoading.classList.add("d-none");
    if (cheatSheetContent) cheatSheetContent.classList.remove("d-none");

    let defsHtml = "";
    if (data.definitions && data.definitions.length) {
      defsHtml = data.definitions
        .map(
          (d) => `
          <div class="mb-2 pb-1 border-bottom border-light">
            <strong class="text-primary d-block font-monospace small">${LF.escapeHtml(d.term)}</strong>
            <span class="small text-secondary">${LF.escapeHtml(d.meaning)}</span>
          </div>`
        )
        .join("");
    } else {
      defsHtml = '<span class="small text-muted">No specific definitions extracted.</span>';
    }

    let takeawaysHtml = "";
    if (data.takeaways && data.takeaways.length) {
      takeawaysHtml = data.takeaways
        .map((t) => `<li class="small mb-1">${LF.escapeHtml(t)}</li>`)
        .join("");
    }

    let conceptsHtml = "";
    if (data.formulas_and_concepts && data.formulas_and_concepts.length) {
      conceptsHtml = data.formulas_and_concepts
        .map(
          (f) => `
          <div class="mb-2">
            <span class="badge bg-indigo-subtle text-indigo fw-bold small me-1">${LF.escapeHtml(f.name)}</span>
            <p class="small text-muted mb-0 mt-1">${LF.escapeHtml(f.summary)}</p>
          </div>`
        )
        .join("");
    }

    let pitfallsHtml = "";
    if (data.common_pitfalls && data.common_pitfalls.length) {
      pitfallsHtml = data.common_pitfalls
        .map((p) => `<li class="small mb-1 text-danger-emphasis">${LF.escapeHtml(p)}</li>`)
        .join("");
    }

    let mnemonicsHtml = "";
    if (data.mnemonics && data.mnemonics.length) {
      mnemonicsHtml = data.mnemonics
        .map((m) => `<li class="small mb-1 text-success-emphasis">${LF.escapeHtml(m)}</li>`)
        .join("");
    }

    cheatSheetGrid.innerHTML = `
      <div class="col-md-6">
        <div class="card h-100 border-0 shadow-sm p-3 bg-light">
          <h6 class="fw-bold text-dark d-flex align-items-center gap-1 mb-2">
            <i class="bi bi-bookmark-star-fill text-warning"></i> Key Takeaways &amp; Core Ideas
          </h6>
          <ul class="ps-3 mb-0">${takeawaysHtml}</ul>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card h-100 border-0 shadow-sm p-3 bg-light">
          <h6 class="fw-bold text-dark d-flex align-items-center gap-1 mb-2">
            <i class="bi bi-book-half text-primary"></i> Essential Definitions
          </h6>
          <div>${defsHtml}</div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card h-100 border-0 shadow-sm p-3 bg-light">
          <h6 class="fw-bold text-dark d-flex align-items-center gap-1 mb-2">
            <i class="bi bi-cpu text-info"></i> Formulas &amp; Sub-Concepts
          </h6>
          <div>${conceptsHtml || '<span class="small text-muted">Core principles are structured conceptually.</span>'}</div>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card h-100 border-0 shadow-sm p-3 bg-light">
          <h6 class="fw-bold text-dark d-flex align-items-center gap-1 mb-2">
            <i class="bi bi-exclamation-triangle-fill text-danger"></i> Exam Pitfalls &amp; Memory Tips
          </h6>
          <div class="mb-2">
            <strong class="small text-dark d-block mb-1">Common Traps:</strong>
            <ul class="ps-3 mb-2">${pitfallsHtml}</ul>
          </div>
          <div>
            <strong class="small text-dark d-block mb-1">Memory Hacks:</strong>
            <ul class="ps-3 mb-0">${mnemonicsHtml}</ul>
          </div>
        </div>
      </div>
    `;
  }

  btnCopyCheatSheet?.addEventListener("click", () => {
    if (!cheatSheetData) return;
    const lines = [
      `=== ${cheatSheetData.topic} (${cheatSheetData.level}) REVISION CHEAT SHEET ===`,
      "",
      "--- KEY TAKEAWAYS ---",
      ...(cheatSheetData.takeaways || []).map((t) => `• ${t}`),
      "",
      "--- ESSENTIAL DEFINITIONS ---",
      ...(cheatSheetData.definitions || []).map((d) => `• ${d.term}: ${d.meaning}`),
      "",
      "--- CORE CONCEPTS & FORMULAS ---",
      ...(cheatSheetData.formulas_and_concepts || []).map((f) => `• ${f.name}: ${f.summary}`),
      "",
      "--- EXAM PITFALLS TO AVOID ---",
      ...(cheatSheetData.common_pitfalls || []).map((p) => `⚠ ${p}`),
      "",
      "--- MEMORY MNEMONICS ---",
      ...(cheatSheetData.mnemonics || []).map((m) => `💡 ${m}`),
    ];
    navigator.clipboard
      .writeText(lines.join("\n"))
      .then(() => LF.showToast("Cheat sheet copied to clipboard!", "success"))
      .catch(() => LF.showToast("Failed to copy.", "warning"));
  });
})();
