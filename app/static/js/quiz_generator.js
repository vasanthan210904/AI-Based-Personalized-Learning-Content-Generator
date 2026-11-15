/* Quiz studio — cascade, custom topic input, quick suggestions and generation */
(function () {
  "use strict";

  const form = document.getElementById("quizForm");
  if (!form) return;

  let subjects = [];
  try {
    subjects = JSON.parse(document.getElementById("subjectsData")?.textContent || "[]");
  } catch (error) {
    subjects = [];
  }

  const subjectSelect = document.getElementById("quizSubject");
  const topicSelect = document.getElementById("quizTopic");
  const topicSelectWrap = document.getElementById("topicSelectWrap");
  const topicCustomWrap = document.getElementById("topicCustomWrap");
  const customTopicInput = document.getElementById("customTopicInput");
  const btnSelectTopicMode = document.getElementById("btnSelectTopicMode");
  const btnCustomTopicMode = document.getElementById("btnCustomTopicMode");
  const button = document.getElementById("quizGenerateButton");
  const timeEstimateBadge = document.getElementById("quizTimeEstimate");
  const quickTopicChips = document.getElementById("quickTopicChips");
  const params = new URLSearchParams(window.location.search);

  let isCustomTopicMode = false;

  function setTopicMode(custom) {
    isCustomTopicMode = custom;
    if (custom) {
      btnCustomTopicMode?.classList.add("active", "btn-primary");
      btnCustomTopicMode?.classList.remove("btn-outline-secondary");
      btnSelectTopicMode?.classList.remove("active", "btn-primary");
      btnSelectTopicMode?.classList.add("btn-outline-primary");

      topicSelectWrap?.classList.add("d-none");
      topicCustomWrap?.classList.remove("d-none");
      customTopicInput?.focus();
    } else {
      btnSelectTopicMode?.classList.add("active", "btn-primary");
      btnSelectTopicMode?.classList.remove("btn-outline-primary");
      btnCustomTopicMode?.classList.remove("active", "btn-primary");
      btnCustomTopicMode?.classList.add("btn-outline-secondary");

      topicCustomWrap?.classList.add("d-none");
      topicSelectWrap?.classList.remove("d-none");
    }
    topicSelect?.classList.remove("is-invalid");
    customTopicInput?.classList.remove("is-invalid");
  }

  btnSelectTopicMode?.addEventListener("click", () => setTopicMode(false));
  btnCustomTopicMode?.addEventListener("click", () => setTopicMode(true));

  // Quick-Pick Topic Chips handler
  quickTopicChips?.addEventListener("click", (e) => {
    const chip = e.target.closest(".badge-chip");
    if (!chip) return;
    const targetSubject = chip.getAttribute("data-subject");
    const targetTopic = chip.getAttribute("data-topic");

    if (targetSubject && subjectSelect) {
      subjectSelect.value = targetSubject;
      subjectSelect.dispatchEvent(new Event("change"));
    }

    setTopicMode(true);
    if (customTopicInput) {
      customTopicInput.value = targetTopic;
      customTopicInput.classList.remove("is-invalid");
    }
    LF.showToast(`Selected "${targetTopic}"! Ready to generate quiz.`, "info");
  });

  // Time estimate on question count change and robust pill click handling
  const timeLabels = {
    "5": "⏱️ ~5 min sprint",
    "10": "⏱️ ~10 min standard test",
    "15": "⏱️ ~15 min comprehensive exam",
    "20": "⏱️ ~20 min mastery challenge"
  };

  const countPills = form.querySelectorAll(".count-pill");
  function syncPillActive() {
    countPills.forEach((pill) => {
      const radio = pill.querySelector('input[type="radio"]');
      if (radio && radio.checked) {
        pill.classList.add("active");
        if (timeEstimateBadge && timeLabels[radio.value]) {
          timeEstimateBadge.textContent = timeLabels[radio.value];
        }
      } else {
        pill.classList.remove("active");
      }
    });
  }

  countPills.forEach((pill) => {
    const radio = pill.querySelector('input[type="radio"]');
    pill.addEventListener("click", () => {
      if (radio && !radio.checked) {
        radio.checked = true;
        radio.dispatchEvent(new Event("change", { bubbles: true }));
      }
      syncPillActive();
    });
  });

  form.querySelectorAll('input[name="num_questions"]').forEach((radio) => {
    radio.addEventListener("change", syncPillActive);
  });

  syncPillActive();

  function fillTopics(selectedId) {
    if (!topicSelect) return;
    const subject = subjects.find((item) => String(item.id) === String(subjectSelect.value));
    topicSelect.innerHTML = '<option value="">Choose a topic</option>';
    if (!subject || !subject.topics.length) {
      topicSelect.disabled = true;
      return;
    }
    subject.topics.forEach((topic) => {
      const option = document.createElement("option");
      option.value = topic.id;
      option.textContent = topic.name;
      if (selectedId && String(topic.id) === String(selectedId)) option.selected = true;
      topicSelect.appendChild(option);
    });
    topicSelect.disabled = false;
  }

  if (subjectSelect) {
    subjectSelect.addEventListener("change", () => {
      fillTopics(params.get("topic"));
      subjectSelect.classList.remove("is-invalid");
      topicSelect?.classList.remove("is-invalid");
    });
    if (subjectSelect.value) fillTopics(params.get("topic"));
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    let valid = true;
    if (subjectSelect && !subjectSelect.value) {
      subjectSelect.classList.add("is-invalid");
      valid = false;
    } else {
      subjectSelect?.classList.remove("is-invalid");
    }

    if (isCustomTopicMode) {
      if (!customTopicInput?.value.trim()) {
        customTopicInput?.classList.add("is-invalid");
        valid = false;
      } else {
        customTopicInput?.classList.remove("is-invalid");
      }
    } else {
      if (!topicSelect?.value) {
        topicSelect?.classList.add("is-invalid");
        valid = false;
      } else {
        topicSelect?.classList.remove("is-invalid");
      }
    }

    if (!form.querySelector('input[name="difficulty"]:checked')) valid = false;
    if (!form.querySelector('input[name="num_questions"]:checked')) valid = false;

    if (!valid) {
      LF.showToast("Please choose a subject, topic, difficulty and question count.", "warning");
      return;
    }

    const data = new FormData(form);
    const payload = {
      subject_id: data.get("subject_id"),
      difficulty: data.get("difficulty"),
      num_questions: data.get("num_questions"),
      ai_engine: data.get("ai_engine") || form.querySelector("#quizAiEngineSelect")?.value,
    };

    if (isCustomTopicMode) {
      payload.custom_topic = customTopicInput.value.trim();
    } else {
      payload.topic_id = data.get("topic_id");
    }

    LF.setLoading(button, true, "Generating quiz…");
    try {
      const response = await LF.request("/api/generate-quiz", {
        method: "POST",
        body: payload,
      });
      LF.showToast(response.message || "Quiz generated successfully.", "success");
      window.location.href = response.data.redirect_url || `/quiz/${response.data.id}/take`;
    } catch (error) {
      LF.setLoading(button, false);
      LF.handleFailure(error, "Could not generate the quiz.");
    }
  });
})();
