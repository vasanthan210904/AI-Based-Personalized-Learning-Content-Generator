/* Learning preferences — dirty-state guard and instant visual feedback */
(function () {
  "use strict";

  const form = document.getElementById("preferencesForm");
  if (!form) return;

  let dirty = false;
  let submitting = false;

  const markDirty = () => {
    dirty = true;
  };

  form.addEventListener("input", markDirty);
  form.addEventListener("change", markDirty);
  form.addEventListener("submit", () => {
    submitting = true;
    dirty = false;
  });

  window.addEventListener("beforeunload", (event) => {
    if (!dirty || submitting) return;
    event.preventDefault();
    event.returnValue = "";
  });

  /* Keep the selected-subject summary in sync while editing. */
  const preview = document.querySelector(".current-prefs");
  const boxes = Array.from(
    form.querySelectorAll('input[name="interested_subjects"]')
  );
  if (preview && boxes.length) {
    const chips = Array.from(preview.querySelectorAll(".chip"));
    boxes.forEach((box) => {
      box.addEventListener("change", () => {
        const label = box.closest(".check-card")?.querySelector("strong");
        if (!label) return;
        const name = label.textContent.trim();
        const existing = chips.find((chip) => chip.textContent.trim() === name);
        if (box.checked && !existing) {
          const chip = document.createElement("span");
          chip.className = "chip chip-indigo";
          chip.textContent = name;
          preview.appendChild(chip);
          chips.push(chip);
        } else if (!box.checked && existing) {
          existing.remove();
          chips.splice(chips.indexOf(existing), 1);
        }
      });
    });
  }
})();
