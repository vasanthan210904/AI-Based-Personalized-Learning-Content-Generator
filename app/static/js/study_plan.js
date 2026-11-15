/* Study planner — topic picker, schedule estimate and generation */
(function () {
  "use strict";

  const form = document.getElementById("studyPlanForm");
  if (!form) return;

  let subjects = [];
  try {
    subjects = JSON.parse(document.getElementById("subjectsData")?.textContent || "[]");
  } catch (error) {
    subjects = [];
  }

  const subjectSelect = document.getElementById("planSubject");
  const picker = document.getElementById("topicPicker");
  const pickerEmpty = document.getElementById("topicPickerEmpty");
  const selectAllButton = document.getElementById("selectAllTopics");
  const addCustomTopicInput = document.getElementById("addCustomTopicInput");
  const btnAddCustomTopic = document.getElementById("btnAddCustomTopic");
  const hoursInput = document.getElementById("hoursPerDay");
  const targetInput = document.getElementById("targetDate");
  const estimateNode = document.getElementById("estimateDays");
  const button = document.getElementById("planGenerateButton");
  const overlay = document.getElementById("planGeneratingOverlay");

  let selectedOrder = [];
  let customTopicsList = [];

  function addCustomTopic() {
    if (!subjectSelect?.value) {
      LF.showToast("Please choose a subject first.", "warning");
      subjectSelect?.focus();
      return;
    }
    const name = addCustomTopicInput?.value.trim();
    if (!name) return;

    const label = document.createElement("label");
    label.className = "topic-pick border-primary";
    label.innerHTML = `
      <input type="checkbox" name="custom_topics" value="${LF.escapeHtml(name)}" checked>
      <span><i class="bi bi-stars text-primary me-1"></i>${LF.escapeHtml(name)}</span>`;
    picker.appendChild(label);

    if (!customTopicsList.includes(name)) customTopicsList.push(name);
    addCustomTopicInput.value = "";
    LF.showToast(`Added custom topic "${name}" to schedule!`, "success");
  }

  btnAddCustomTopic?.addEventListener("click", addCustomTopic);
  addCustomTopicInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addCustomTopic();
    }
  });

  function topicsForSubject() {
    const subject = subjects.find((item) => String(item.id) === String(subjectSelect?.value));
    return subject ? subject.topics : [];
  }

  function renderPicker() {
    if (!picker) return;
    picker.innerHTML = "";
    selectedOrder = [];
    const topics = topicsForSubject();
    if (!topics.length) {
      const note = document.createElement("p");
      note.className = "muted-note";
      note.textContent = subjectSelect?.value
        ? "This subject has no topics yet."
        : "Choose a subject to see its topics.";
      picker.appendChild(note);
      return;
    }

    topics.forEach((topic) => {
      const label = document.createElement("label");
      label.className = "topic-pick";
      label.innerHTML = `
        <input type="checkbox" name="topic_ids" value="${topic.id}">
        <span>${LF.escapeHtml(topic.name)}</span>`;
      picker.appendChild(label);
    });
  }

  function updateEstimate() {
    if (!estimateNode || !targetInput || !targetInput.value) return;
    const target = new Date(`${targetInput.value}T00:00:00`);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const days = Math.round((target - today) / 86400000) + 1;
    estimateNode.textContent = Number.isFinite(days) && days > 0 ? String(days) : "—";
  }

  function syncOrder(id, checked) {
    if (checked) {
      if (!selectedOrder.includes(id)) selectedOrder.push(id);
    } else {
      selectedOrder = selectedOrder.filter((value) => value !== id);
    }
  }

  if (subjectSelect) {
    subjectSelect.addEventListener("change", () => {
      renderPicker();
      subjectSelect.classList.remove("is-invalid");
    });
    if (subjectSelect.value) renderPicker();
  }

  picker?.addEventListener("change", (event) => {
    const input = event.target.closest('input[name="topic_ids"]');
    if (!input) return;
    syncOrder(input.value, input.checked);
    const checkedCount = picker.querySelectorAll('input[name="topic_ids"]:checked').length;
    if (checkedCount > 15) {
      input.checked = false;
      syncOrder(input.value, false);
      LF.showToast("A study plan can include at most 15 topics.", "warning");
    }
  });

  selectAllButton?.addEventListener("click", () => {
    const inputs = Array.from(picker?.querySelectorAll('input[name="topic_ids"]') || []);
    if (!inputs.length) {
      LF.showToast("Choose a subject with topics first.", "warning");
      return;
    }
    const allChecked = inputs.every((input) => input.checked);
    inputs.forEach((input) => {
      input.checked = !allChecked;
      syncOrder(input.value, input.checked);
    });
    if (!allChecked && inputs.length > 15) {
      inputs.slice(15).forEach((input) => {
        input.checked = false;
        syncOrder(input.value, false);
      });
      LF.showToast("Only the first 15 topics were selected.", "warning");
    }
    selectAllButton.textContent = allChecked ? "Select all" : "Clear all";
  });

  targetInput?.addEventListener("change", updateEstimate);
  updateEstimate();

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const inputs = Array.from(picker?.querySelectorAll('input[name="topic_ids"]') || []);
    const checkedIds = selectedOrder.filter((id) =>
      inputs.some((input) => input.value === id && input.checked)
    );
    const customChecked = Array.from(picker?.querySelectorAll('input[name="custom_topics"]:checked') || [])
      .map((i) => i.value.trim())
      .filter(Boolean);

    let valid = true;
    if (!subjectSelect?.value) {
      subjectSelect?.classList.add("is-invalid");
      valid = false;
    }
    if (!checkedIds.length && !customChecked.length) {
      LF.showToast("Select or add at least one topic for the study plan.", "warning");
      valid = false;
    }
    if (!valid) return;

    const hours = Number(hoursInput?.value);
    if (!Number.isFinite(hours) || hours < 0.5 || hours > 12) {
      hoursInput?.classList.add("is-invalid");
      LF.showToast("Study hours per day must be between 0.5 and 12.", "warning");
      return;
    }
    hoursInput?.classList.remove("is-invalid");

    if (!targetInput?.value) {
      targetInput?.classList.add("is-invalid");
      LF.showToast("Choose a target completion date.", "warning");
      return;
    }

    const payload = {
      subject_id: subjectSelect.value,
      topic_ids: checkedIds,
      custom_topics: customChecked,
      hours_per_day: hours,
      target_date: targetInput.value,
      learning_level: form.querySelector('[name="learning_level"]')?.value,
    };

    if (overlay) overlay.hidden = false;
    LF.setLoading(button, true, "Building plan…");

    try {
      const response = await LF.request("/api/generate-study-plan", {
        method: "POST",
        body: payload,
      });
      LF.showToast(response.message || "Study plan generated.", "success");
      window.location.href = response.data.redirect_url || `/study-plans/${response.data.id}`;
    } catch (error) {
      if (overlay) overlay.hidden = true;
      LF.setLoading(button, false);
      LF.handleFailure(error, "Could not generate the study plan.");
    }
  });
})();
