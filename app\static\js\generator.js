/* Content studio — subject/topic cascade, custom topic input, quick suggestions and generation request */
(function () {
  "use strict";

  const form = document.getElementById("generatorForm");
  if (!form) return;

  const subjectsNode = document.getElementById("subjectsData");
  let subjects = [];
  try {
    subjects = JSON.parse(subjectsNode?.textContent || "[]");
  } catch (error) {
    subjects = [];
  }

  const subjectSelect = document.getElementById("subjectSelect");
  const topicSelect = document.getElementById("topicSelect");
  const topicSelectWrap = document.getElementById("topicSelectWrap");
  const topicCustomWrap = document.getElementById("topicCustomWrap");
  const customTopicInput = document.getElementById("customTopicInput");
  const btnSelectTopicMode = document.getElementById("btnSelectTopicMode");
  const btnCustomTopicMode = document.getElementById("btnCustomTopicMode");
  const quickTopicChips = document.getElementById("quickTopicChips");
  const generateButton = document.getElementById("generateButton");
  const overlay = document.getElementById("generatingOverlay");
  const generatingText = document.getElementById("generatingText");

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
    setClientError("topic_id", "");
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
    setClientError("topic_id", "");
    LF.showToast(`Selected "${targetTopic}"! Ready to generate learning content.`, "info");
  });

  function setClientError(name, message) {
    const node = form.querySelector(`[data-client-error="${name}"]`);
    if (!node) return;
    node.textContent = message || "";
    node.classList.toggle("d-none", !message);
  }

  function clearClientErrors() {
    form.querySelectorAll("[data-client-error]").forEach((node) => {
      node.textContent = "";
      node.classList.add("d-none");
    });
  }

  function fillTopics(selectedId, autoSelectFirst) {
    if (!topicSelect) return;
    const subject = subjects.find(
      (item) => String(item.id) === String(subjectSelect?.value)
    );
    topicSelect.innerHTML = '<option value="">Choose a topic</option>';
    if (!subject || !subject.topics.length) {
      topicSelect.disabled = true;
      topicSelect.value = "";
      return;
    }

    subject.topics.forEach((topic) => {
      const option = document.createElement("option");
      option.value = topic.id;
      option.textContent = topic.name;
      if (selectedId && String(topic.id) === String(selectedId)) {
        option.selected = true;
      }
      topicSelect.appendChild(option);
    });
    topicSelect.disabled = false;

    if (selectedId) {
      topicSelect.value = String(selectedId);
    } else if (autoSelectFirst) {
      topicSelect.value = String(subject.topics[0].id);
    }
    setClientError("topic_id", "");
    topicSelect.classList.remove("is-invalid");
  }

  if (subjectSelect) {
    subjectSelect.addEventListener("change", () => {
      fillTopics(null, true);
      subjectSelect.classList.remove("is-invalid");
      setClientError("subject_id", "");
    });
    if (subjectSelect.value) {
      fillTopics(params.get("topic"), true);
    }
  }

  form.querySelectorAll('input[name="content_type"]').forEach((radio) => {
    radio.addEventListener("change", () => {
      setClientError("content_type", "");
    });
  });

  topicSelect?.addEventListener("change", () => {
    topicSelect.classList.remove("is-invalid");
    setClientError("topic_id", "");
  });

  customTopicInput?.addEventListener("input", () => {
    customTopicInput.classList.remove("is-invalid");
    setClientError("topic_id", "");
  });

  function validate() {
    clearClientErrors();
    const missing = [];

    if (subjectSelect && !subjectSelect.value) {
      subjectSelect.classList.add("is-invalid");
      setClientError("subject_id", "Choose a subject.");
      missing.push({ label: "subject", input: subjectSelect });
    }

    if (isCustomTopicMode) {
      if (!customTopicInput?.value.trim()) {
        customTopicInput?.classList.add("is-invalid");
        setClientError("topic_id", "Type a custom topic name.");
        missing.push({ label: "custom topic", input: customTopicInput });
      }
    } else {
      if (subjectSelect?.value && topicSelect && !topicSelect.value) {
        topicSelect.classList.add("is-invalid");
        setClientError("topic_id", "Choose a topic.");
        missing.push({ label: "topic", input: topicSelect });
      }
    }

    const type = form.querySelector('input[name="content_type"]:checked');
    if (!type) {
      setClientError("content_type", "Choose a content type.");
      missing.push({
        label: "content type",
        input: form.querySelector('input[name="content_type"]'),
      });
    }

    if (missing.length) {
      const labels = missing.map((item) => item.label);
      const message =
        labels.length === 1
          ? `Please choose a ${labels[0]} to continue.`
          : `Please choose a ${labels.slice(0, -1).join(", a ")} and a ${labels[labels.length - 1]} to continue.`;
      LF.showToast(message, "warning");
      missing[0].input?.focus();
      return false;
    }
    return true;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    LF.clearFieldErrors(form);
    if (!validate()) return;

    const data = new FormData(form);
    const payload = {
      subject_id: data.get("subject_id"),
      content_type: data.get("content_type"),
      learning_level: data.get("learning_level"),
      explanation_style: data.get("explanation_style"),
      language: data.get("language"),
      ai_engine: data.get("ai_engine") || form.querySelector("#aiEngineSelect")?.value,
      create_flashcards: Boolean(form.querySelector("#createFlashcardsToggle")?.checked),
    };

    if (isCustomTopicMode) {
      payload.custom_topic = customTopicInput.value.trim();
    } else {
      payload.topic_id = data.get("topic_id");
    }

    if (overlay) overlay.hidden = false;
    if (generatingText) {
      generatingText.textContent = "Structuring the 15-section personalized explanation, examples and revision notes…";
    }
    LF.setLoading(generateButton, true, "Generating…");

    try {
      const response = await LF.request("/api/generate-content", {
        method: "POST",
        body: payload,
      });
      const record = response.data || {};
      LF.showToast(response.message || "Learning material generated.", "success");
      window.location.href = record.view_url || `/learning/content/${record.id}`;
    } catch (error) {
      if (overlay) overlay.hidden = true;
      LF.setLoading(generateButton, false);
      LF.handleFailure(error, "Could not generate the material.");
    }
  });
})();
