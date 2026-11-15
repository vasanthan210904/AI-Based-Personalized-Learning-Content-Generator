/* LearnForge — flashcard deck builder and study experience */
(function () {
  "use strict";

  const $ = (selector, root) => (root || document).querySelector(selector);
  const $$ = (selector, root) => Array.from((root || document).querySelectorAll(selector));

  function parseJson(id, fallback) {
    try {
      return JSON.parse(document.getElementById(id)?.textContent || "");
    } catch (error) {
      return fallback;
    }
  }

  /* ------------------------------------------------------------------ */
  /* Deck builder                                                       */
  /* ------------------------------------------------------------------ */
  function initDeckBuilder() {
    const form = $("#flashcardForm");
    if (!form) return;

    const catalog = parseJson("flashcardsCatalog", []);
    const sourceButtons = $$("[data-flashcard-source]");
    const panels = $$("[data-flashcard-panel]");
    const materialSelect = $("#flashcardMaterial");
    const subjectSelect = $("#flashcardSubject");
    const topicSelect = $("#flashcardTopic");
    const submitButton = $("#flashcardGenerate");
    let source = "material";

    function setSource(next) {
      source = next;
      sourceButtons.forEach((button) => {
        const active = button.getAttribute("data-flashcard-source") === next;
        button.classList.toggle("is-active", active);
        button.setAttribute("aria-selected", active ? "true" : "false");
      });
      panels.forEach((panel) => {
        panel.classList.toggle(
          "d-none",
          panel.getAttribute("data-flashcard-panel") !== next
        );
      });
    }

    sourceButtons.forEach((button) => {
      button.addEventListener("click", () => setSource(button.getAttribute("data-flashcard-source")));
    });

    function fillTopics() {
      if (!topicSelect) return;
      const subject = catalog.find(
        (item) => String(item.id) === String(subjectSelect?.value)
      );
      topicSelect.innerHTML = '<option value="">Choose a topic</option>';
      if (!subject || !subject.topics.length) {
        topicSelect.disabled = true;
        return;
      }
      subject.topics.forEach((topic) => {
        const option = document.createElement("option");
        option.value = topic.id;
        option.textContent = topic.name;
        topicSelect.appendChild(option);
      });
      topicSelect.disabled = false;
    }

    subjectSelect?.addEventListener("change", () => {
      fillTopics();
      subjectSelect.classList.remove("is-invalid");
    });

    // If the page was opened with ?mode=topic, honour it without a reload.
    if (new URLSearchParams(window.location.search).get("mode") === "topic") {
      setSource("topic");
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      LF.clearFieldErrors(form);
      let payload;

      if (source === "material") {
        if (!materialSelect || !materialSelect.value) {
          LF.showToast("Generate a material first, or choose the By topic option.", "warning");
          return;
        }
        payload = { content_id: Number(materialSelect.value) };
      } else {
        let valid = true;
        if (!subjectSelect?.value) {
          subjectSelect?.classList.add("is-invalid");
          valid = false;
        }
        if (!topicSelect?.value) {
          topicSelect?.classList.add("is-invalid");
          valid = false;
        }
        if (!valid) {
          LF.showToast("Choose a subject and a topic to build the deck.", "warning");
          return;
        }
        payload = {
          subject_id: Number(subjectSelect.value),
          topic_id: Number(topicSelect.value),
        };
      }

      LF.setLoading(submitButton, true, "Building deck…");
      try {
        const response = await LF.request("/api/flashcards/generate", {
          method: "POST",
          body: payload,
        });
        LF.showToast(response.message || "Flashcard deck ready.", "success");
        window.location.href =
          response.data.redirect_url || `/flashcards/${response.data.id}`;
      } catch (error) {
        LF.handleFailure(error, "Could not create the flashcard deck.");
      } finally {
        LF.setLoading(submitButton, false);
      }
    });

    initDeckActions(null);
  }

  /* ------------------------------------------------------------------ */
  /* Shared deck actions                                                */
  /* ------------------------------------------------------------------ */
  function initDeckActions(onReset) {
    document.addEventListener("click", async (event) => {
      const resetButton = event.target.closest("[data-reset-deck]");
      if (resetButton) {
        event.preventDefault();
        const deckId = resetButton.getAttribute("data-reset-deck");
        const confirmed = await LF.confirm({
          title: "Reset this deck?",
          message: "Every card will be marked new again and your review counts will be cleared.",
          confirmLabel: "Reset progress",
          tone: "primary",
          icon: "bi-arrow-counterclockwise",
        });
        if (!confirmed) return;
        LF.setLoading(resetButton, true, "Resetting…");
        try {
          const response = await LF.request(`/api/flashcards/${deckId}/reset`, {
            method: "POST",
          });
          LF.showToast(response.message || "Deck reset.", "success");
          if (onReset) {
            onReset(response.data);
          } else {
            window.setTimeout(() => window.location.reload(), 350);
          }
        } catch (error) {
          LF.handleFailure(error, "Could not reset the deck.");
        } finally {
          LF.setLoading(resetButton, false);
        }
        return;
      }

      const deleteButton = event.target.closest("[data-delete-deck]");
      if (!deleteButton) return;
      event.preventDefault();
      const deckId = deleteButton.getAttribute("data-delete-deck");
      const title = deleteButton.getAttribute("data-deck-title") || "this deck";
      const confirmed = await LF.confirm({
        title: "Delete this flashcard deck?",
        message: `“${title}” and all of its review progress will be permanently removed.`,
        confirmLabel: "Delete deck",
        icon: "bi-trash3",
      });
      if (!confirmed) return;
      LF.setLoading(deleteButton, true, "Deleting…");
      try {
        const response = await LF.request(`/api/flashcards/${deckId}`, {
          method: "DELETE",
        });
        LF.showToast(response.message || "Deck deleted.", "success");
        window.location.href = "/flashcards";
      } catch (error) {
        LF.handleFailure(error, "Could not delete the deck.");
        LF.setLoading(deleteButton, false);
      }
    });
  }

  /* ------------------------------------------------------------------ */
  /* Study experience                                                   */
  /* ------------------------------------------------------------------ */
  function initStudy() {
    const scene = $("#flashcardScene");
    const dataNode = $("#flashcardData");
    if (!scene || !dataNode) return;

    const deck = parseJson("flashcardData", null);
    if (!deck || !Array.isArray(deck.cards) || !deck.cards.length) return;

    const card3d = $("#flashcard3d");
    const frontNode = $("#flashcardFront");
    const backNode = $("#flashcardBack");
    const frontLabel = $("#flashcardFrontLabel");
    const backLabel = $("#flashcardBackLabel");
    const positionNode = $("#flashcardPosition");
    const totalNode = $("#flashcardTotal");
    const statusText = $("#flashcardStatusText");
    const progressFill = $("#flashcardProgressFill");
    const knownChip = $("#flashcardKnownChip");
    const flipButton = $("#flipCard");
    const prevButton = $("#prevCard");
    const nextButton = $("#nextCard");
    const reviewActions = $("#reviewActions");
    const completeBox = $("#flashcardComplete");
    const modeButtons = $$("[data-study-mode]");
    const shuffleButton = $("#shuffleDeck");
    const restartButton = $("#restartDeck");

    let mode = "all";
    let cards = deck.cards.slice();
    let visible = [];
    let index = 0;
    let flipped = false;

    function statusMeta(status) {
      return {
        new: { label: "New card", tone: "chip-indigo" },
        review: { label: "Needs review", tone: "chip-amber" },
        known: { label: "Known", tone: "chip-teal" },
      }[status] || { label: "Card", tone: "chip-muted" };
    }

    function knownCount() {
      return cards.filter((card) => card.status === "known").length;
    }

    function counts() {
      return {
        new: cards.filter((card) => card.status === "new").length,
        review: cards.filter((card) => card.status === "review").length,
        known: knownCount(),
        total: cards.length,
      };
    }

    function updateSideStats() {
      const current = counts();
      const mastery = current.total
        ? Math.round((current.known / current.total) * 100)
        : 0;
      if (knownChip) {
        knownChip.textContent = `${current.known}/${current.total} known`;
      }
      const sideMastery = $("#sideMastery");
      if (sideMastery) sideMastery.innerHTML = `${mastery}<small>%</small>`;
      const sideKnown = $("#sideKnown");
      if (sideKnown) sideKnown.textContent = `${current.known} of ${current.total}`;
      const sideNew = $("#sideNew");
      if (sideNew) sideNew.textContent = current.new;
      const sideReview = $("#sideReview");
      if (sideReview) sideReview.textContent = current.review;
      const sideKnownCount = $("#sideKnownCount");
      if (sideKnownCount) sideKnownCount.textContent = current.known;
      const modeAll = $("#modeAll");
      if (modeAll) modeAll.textContent = current.total;
      const ring = $(".deck-stat-ring .progress-ring");
      if (ring) ring.style.setProperty("--value", mastery);
    }

    function rebuildVisible(resetIndex) {
      visible = cards.filter((card) => mode === "all" || card.status === mode);
      if (resetIndex !== false) index = 0;
      if (index >= visible.length) index = Math.max(0, visible.length - 1);
    }

    function setFlipped(next) {
      flipped = next;
      card3d?.classList.toggle("is-flipped", flipped);
      scene.classList.toggle("is-flipped", flipped);
      if (flipButton) {
        flipButton.innerHTML = flipped
          ? '<i class="bi bi-arrow-repeat"></i> Show question'
          : '<i class="bi bi-arrow-repeat"></i> Reveal answer';
      }
      scene.setAttribute(
        "aria-label",
        flipped
          ? "Flashcard answer shown. Press Space or Enter to show the question."
          : "Flashcard question. Press Space or Enter to reveal the answer."
      );
      if (statusText) {
        statusText.textContent = flipped
          ? "How well did you know it? Mark the card below."
          : "Reveal the answer when you are ready.";
      }
    }

    function showComplete() {
      if (!completeBox) return;
      scene.classList.add("d-none");
      if (reviewActions) reviewActions.classList.add("d-none");
      const controls = $(".flashcard-stage-controls");
      if (controls) controls.classList.add("d-none");
      if ($(".flashcard-progress")) $(".flashcard-progress").classList.add("d-none");
      completeBox.classList.remove("d-none");
    }

    function hideComplete() {
      completeBox?.classList.add("d-none");
      scene.classList.remove("d-none");
      reviewActions?.classList.remove("d-none");
      $(".flashcard-stage-controls")?.classList.remove("d-none");
      $(".flashcard-progress")?.classList.remove("d-none");
    }

    function render() {
      updateSideStats();
      if (!visible.length) {
        if (mode !== "all" && counts().known === cards.length) {
          showComplete();
        } else {
          scene.classList.add("d-none");
          if (reviewActions) reviewActions.classList.add("d-none");
          if (statusText) {
            statusText.textContent =
              mode === "all"
                ? "No cards in this deck."
                : "No cards match this study mode. Choose another mode.";
          }
          LF.showToast("No cards match this study mode.", "warning");
        }
        return;
      }

      hideComplete();
      const card = visible[index];
      if (!card) return;

      setFlipped(false);
      if (frontNode) frontNode.textContent = card.front;
      if (backNode) backNode.textContent = card.back;
      const meta = statusMeta(card.status);
      if (frontLabel) frontLabel.textContent = `Question · ${meta.label}`;
      if (backLabel) backLabel.textContent = `Answer · ${meta.label}`;
      if (positionNode) positionNode.textContent = index + 1;
      if (totalNode) totalNode.textContent = visible.length;
      if (statusText) {
        statusText.textContent =
          mode === "all"
            ? "Reveal the answer when you are ready."
            : `Studying ${mode === "review" ? "cards that need review" : mode + " cards"}.`;
      }
      if (progressFill) {
        const pct = Math.round(((index + 1) / visible.length) * 100);
        progressFill.style.width = `${pct}%`;
      }
      prevButton && (prevButton.disabled = visible.length < 2);
      nextButton && (nextButton.disabled = visible.length < 2);
    }

    function move(step) {
      if (visible.length < 2) return;
      index = (index + step + visible.length) % visible.length;
      render();
    }

    async function mark(status) {
      if (!visible.length) return;
      const card = visible[index];
      if (!card) return;

      $$("button[data-review-status]").forEach((button) => {
        button.disabled = true;
      });
      try {
        const response = await LF.request(`/api/flashcards/cards/${card.id}/review`, {
          method: "POST",
          body: { status: status },
        });
        card.status = status;
        updateSideStats();
        LF.showToast(
          status === "known" ? "Nice — marked as known." : "Saved for another review.",
          "success"
        );
        if (response.data?.deck) {
          cards = cards.map((item) => item);
        }

        if (cards.every((item) => item.status === "known")) {
          showComplete();
          return;
        }

        rebuildVisible(false);
        if (!visible.length) {
          render();
          return;
        }
        if (visible.length > 1 && index >= visible.length) index = 0;
        if (mode !== "all") {
          const current = visible[index];
          if (!current || current.status !== status) {
            index = 0;
          }
        }
        if (mode === "all" && visible.length > 1) {
          move(1);
        } else {
          render();
        }
      } catch (error) {
        LF.handleFailure(error, "Could not save your review.");
      } finally {
        $$("button[data-review-status]").forEach((button) => {
          button.disabled = false;
        });
      }
    }

    scene.addEventListener("click", () => setFlipped(!flipped));
    scene.addEventListener("keydown", (event) => {
      if (event.key === " " || event.key === "Enter") {
        event.preventDefault();
        setFlipped(!flipped);
      }
    });
    flipButton?.addEventListener("click", () => setFlipped(!flipped));
    prevButton?.addEventListener("click", () => move(-1));
    nextButton?.addEventListener("click", () => move(1));

    $$("button[data-review-status]").forEach((button) => {
      button.addEventListener("click", () =>
        mark(button.getAttribute("data-review-status"))
      );
    });

    modeButtons.forEach((button) => {
      button.addEventListener("click", () => {
        mode = button.getAttribute("data-study-mode");
        modeButtons.forEach((item) => item.classList.toggle("is-active", item === button));
        rebuildVisible(true);
        render();
      });
    });

    shuffleButton?.addEventListener("click", () => {
      cards = cards.slice().sort(() => Math.random() - 0.5);
      rebuildVisible(true);
      render();
      LF.showToast("Deck shuffled.", "info");
    });

    restartButton?.addEventListener("click", async () => {
      LF.setLoading(restartButton, true, "Resetting…");
      try {
        await LF.request(`/api/flashcards/${deck.id}/reset`, { method: "POST" });
        cards.forEach((card) => {
          card.status = "new";
          card.review_count = 0;
        });
        mode = "all";
        modeButtons.forEach((item) =>
          item.classList.toggle("is-active", item.getAttribute("data-study-mode") === "all")
        );
        index = 0;
        rebuildVisible(true);
        hideComplete();
        render();
        LF.showToast("Deck reset. You can study every card again.", "success");
      } catch (error) {
        LF.handleFailure(error, "Could not reset the deck.");
      } finally {
        LF.setLoading(restartButton, false);
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.target.matches("input, textarea, select") || completeBox?.matches(":not(.d-none)")) return;
      if (event.key === "ArrowLeft") {
        event.preventDefault();
        move(-1);
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        move(1);
      } else if (event.key === "1" && !event.ctrlKey && !event.metaKey) {
        mark("review");
      } else if (event.key === "2" && !event.ctrlKey && !event.metaKey) {
        mark("known");
      }
    });

    initDeckActions((summary) => {
      cards.forEach((card) => {
        card.status = "new";
        card.review_count = 0;
      });
      deck.total_cards = summary.total_cards ?? cards.length;
      deck.known_cards = summary.known_cards ?? 0;
      deck.new_cards = summary.new_cards ?? cards.length;
      deck.review_cards = 0;
      mode = "all";
      modeButtons.forEach((item) =>
        item.classList.toggle("is-active", item.getAttribute("data-study-mode") === "all")
      );
      index = 0;
      rebuildVisible(true);
      hideComplete();
      render();
    });

    rebuildVisible(true);
    render();
  }

  document.addEventListener("DOMContentLoaded", () => {
    initDeckBuilder();
    initStudy();
  });
})();
