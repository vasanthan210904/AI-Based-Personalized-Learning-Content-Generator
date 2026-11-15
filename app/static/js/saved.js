/* Saved library — client-side search, sorting, notes and flashcard creation */
(function () {
  "use strict";

  const grid = document.getElementById("savedGrid");
  if (!grid) return;

  const cards = Array.from(grid.querySelectorAll("[data-saved-card]"));
  const search = document.getElementById("savedSearch");
  const sort = document.getElementById("savedSort");
  const noResults = document.getElementById("savedNoResults");
  const countText = document.getElementById("savedCountText");
  const clearButton = document.getElementById("clearSavedSearch");

  function applyFilters() {
    const query = (search?.value || "").trim().toLowerCase();
    let shown = 0;
    cards.forEach((card) => {
      const match = !query || (card.getAttribute("data-search") || "").includes(query);
      card.classList.toggle("d-none", !match);
      if (match) shown += 1;
    });
    if (noResults) noResults.classList.toggle("d-none", shown > 0);
    if (countText) {
      countText.textContent = query
        ? `${shown} of ${cards.length} saved materials match.`
        : `${cards.length} saved material${cards.length === 1 ? "" : "s"}.`;
    }
  }

  function applySort() {
    if (!sort) return;
    const value = sort.value;
    const sorted = cards.slice().sort((a, b) => {
      if (value === "title") {
        return (a.dataset.title || "").localeCompare(b.dataset.title || "");
      }
      if (value === "subject") {
        return (a.dataset.subject || "").localeCompare(b.dataset.subject || "");
      }
      const aTime = Number(a.dataset.savedAt || 0);
      const bTime = Number(b.dataset.savedAt || 0);
      return value === "oldest" ? aTime - bTime : bTime - aTime;
    });
    sorted.forEach((card) => grid.appendChild(card));
  }

  search?.addEventListener("input", applyFilters);
  sort?.addEventListener("change", applySort);
  clearButton?.addEventListener("click", () => {
    if (search) search.value = "";
    applyFilters();
    search?.focus();
  });

  grid.addEventListener("click", async (event) => {
    const noteButton = event.target.closest("[data-save-note]");
    if (noteButton) {
      const contentId = noteButton.getAttribute("data-save-note");
      const editor = document.querySelector(`[data-saved-note="${contentId}"]`);
      const status = document.querySelector(`[data-note-status="${contentId}"]`);
      if (!editor) return;

      LF.setLoading(noteButton, true, "Saving…");
      try {
        await LF.request(`/api/bookmarks/${contentId}`, {
          method: "PUT",
          body: { note: editor.value },
        });
        if (status) {
          status.textContent = editor.value.trim() ? "Note saved" : "No note yet";
        }
        const card = noteButton.closest("[data-saved-card]");
        if (card) {
          const baseSearch = [
            card.dataset.title || "",
            card.dataset.subject || "",
          ]
            .join(" ")
            .trim();
          card.dataset.search = `${baseSearch} ${editor.value}`.toLowerCase();
        }
        LF.showToast("Your private note was saved.", "success");
      } catch (error) {
        LF.handleFailure(error, "Could not save the note.");
      } finally {
        LF.setLoading(noteButton, false);
      }
      return;
    }

    const flashButton = event.target.closest("[data-create-flashcards]");
    if (!flashButton) return;
    const contentId = flashButton.getAttribute("data-create-flashcards");
    LF.setLoading(flashButton, true, "Building…");
    try {
      const response = await LF.request("/api/flashcards/generate", {
        method: "POST",
        body: { content_id: Number(contentId) },
      });
      LF.showToast(response.message || "Flashcard deck ready.", "success");
      window.location.href =
        response.data.redirect_url || `/flashcards/${response.data.id}`;
    } catch (error) {
      LF.handleFailure(error, "Could not create flashcards.");
    } finally {
      LF.setLoading(flashButton, false);
    }
  });

  applyFilters();
  applySort();
})();
