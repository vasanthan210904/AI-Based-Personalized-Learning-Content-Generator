/* Admin catalog — subject and topic create/edit/delete */
(function () {
  "use strict";

  let config = {};
  try {
    config = JSON.parse(document.getElementById("adminConfig")?.textContent || "{}");
  } catch (error) {
    config = {};
  }

  const Modal = window.bootstrap ? window.bootstrap.Modal : null;

  function reloadWith(message, type) {
    LF.flashNext(message, type || "success");
    window.location.reload();
  }

  /* ------------------------------------------------------------------ */
  /* Subjects                                                           */
  /* ------------------------------------------------------------------ */
  const subjectModalEl = document.getElementById("subjectModal");
  const subjectForm = document.getElementById("subjectForm");
  const subjectApi = config.subjectsApi;

  if (subjectModalEl && subjectForm && subjectApi && Modal) {
    const modal = Modal.getOrCreateInstance(subjectModalEl);
    const title = document.getElementById("subjectModalTitle");
    const idField = document.getElementById("subjectId");
    const nameField = document.getElementById("subjectName");
    const descriptionField = document.getElementById("subjectDescription");
    const submitButton = document.getElementById("subjectSubmitButton");

    const reset = () => {
      subjectForm.reset();
      LF.clearFieldErrors(subjectForm);
      if (idField) idField.value = "";
      if (title) title.textContent = "New subject";
    };

    document.querySelectorAll("[data-open-subject-modal]").forEach((button) => {
      button.addEventListener("click", () => {
        reset();
        modal.show();
        window.setTimeout(() => nameField?.focus(), 250);
      });
    });

    document.querySelectorAll("[data-edit-subject]").forEach((button) => {
      button.addEventListener("click", () => {
        reset();
        if (idField) idField.value = button.getAttribute("data-edit-subject") || "";
        if (nameField) nameField.value = button.getAttribute("data-subject-name") || "";
        if (descriptionField) {
          descriptionField.value = button.getAttribute("data-subject-description") || "";
        }
        if (title) title.textContent = "Edit subject";
        modal.show();
      });
    });

    subjectForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      LF.clearFieldErrors(subjectForm);
      const id = idField?.value || "";
      const payload = {
        subject_name: nameField?.value.trim() || "",
        description: descriptionField?.value.trim() || "",
      };
      if (!payload.subject_name) {
        nameField?.classList.add("is-invalid");
        LF.showToast("Subject name is required.", "warning");
        return;
      }

      LF.setLoading(submitButton, true, "Saving…");
      try {
        const response = await LF.request(id ? `${subjectApi}/${id}` : subjectApi, {
          method: id ? "PUT" : "POST",
          body: payload,
        });
        modal.hide();
        reloadWith(response.message || "Subject saved.");
      } catch (error) {
        LF.setLoading(submitButton, false);
        LF.handleFailure(error, "Could not save the subject.");
      }
    });

    document.querySelectorAll("[data-delete-subject]").forEach((button) => {
      button.addEventListener("click", async () => {
        const id = button.getAttribute("data-delete-subject");
        const name = button.getAttribute("data-subject-name") || "this subject";
        const confirmed = await LF.confirm({
          title: "Delete this subject?",
          message: `“${name}” and its unused topics will be removed. Subjects used by materials, quizzes or plans are protected.`,
          confirmLabel: "Delete subject",
        });
        if (!confirmed) return;
        button.disabled = true;
        try {
          const response = await LF.request(`${subjectApi}/${id}`, { method: "DELETE" });
          reloadWith(response.message || "Subject deleted.");
        } catch (error) {
          button.disabled = false;
          LF.handleFailure(error, "Could not delete the subject.");
        }
      });
    });
  }

  /* ------------------------------------------------------------------ */
  /* Topics                                                             */
  /* ------------------------------------------------------------------ */
  const topicModalEl = document.getElementById("topicModal");
  const topicForm = document.getElementById("topicForm");
  const topicApi = config.topicsApi;

  if (topicModalEl && topicForm && topicApi && Modal) {
    const modal = Modal.getOrCreateInstance(topicModalEl);
    const title = document.getElementById("topicModalTitle");
    const idField = document.getElementById("topicId");
    const subjectField = document.getElementById("topicSubject");
    const nameField = document.getElementById("topicName");
    const descriptionField = document.getElementById("topicDescription");
    const submitButton = document.getElementById("topicSubmitButton");

    const reset = () => {
      topicForm.reset();
      LF.clearFieldErrors(topicForm);
      if (idField) idField.value = "";
      if (title) title.textContent = "New topic";
    };

    document.querySelectorAll("[data-open-topic-modal]").forEach((button) => {
      button.addEventListener("click", () => {
        reset();
        modal.show();
        window.setTimeout(() => nameField?.focus(), 250);
      });
    });

    document.querySelectorAll("[data-edit-topic]").forEach((button) => {
      button.addEventListener("click", () => {
        reset();
        if (idField) idField.value = button.getAttribute("data-edit-topic") || "";
        if (nameField) nameField.value = button.getAttribute("data-topic-name") || "";
        if (descriptionField) {
          descriptionField.value = button.getAttribute("data-topic-description") || "";
        }
        if (subjectField) {
          subjectField.value = button.getAttribute("data-topic-subject") || subjectField.value;
        }
        if (title) title.textContent = "Edit topic";
        modal.show();
      });
    });

    topicForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      LF.clearFieldErrors(topicForm);
      const id = idField?.value || "";
      const payload = {
        subject_id: subjectField?.value || "",
        topic_name: nameField?.value.trim() || "",
        description: descriptionField?.value.trim() || "",
      };
      if (!payload.subject_id || !payload.topic_name) {
        LF.showToast("Choose a subject and enter a topic name.", "warning");
        return;
      }

      LF.setLoading(submitButton, true, "Saving…");
      try {
        const response = await LF.request(id ? `${topicApi}/${id}` : topicApi, {
          method: id ? "PUT" : "POST",
          body: payload,
        });
        modal.hide();
        reloadWith(response.message || "Topic saved.");
      } catch (error) {
        LF.setLoading(submitButton, false);
        LF.handleFailure(error, "Could not save the topic.");
      }
    });

    document.querySelectorAll("[data-delete-topic]").forEach((button) => {
      button.addEventListener("click", async () => {
        const id = button.getAttribute("data-delete-topic");
        const name = button.getAttribute("data-topic-name") || "this topic";
        const confirmed = await LF.confirm({
          title: "Delete this topic?",
          message: `“${name}” will be removed. Topics used by materials or quizzes are protected.`,
          confirmLabel: "Delete topic",
        });
        if (!confirmed) return;
        button.disabled = true;
        try {
          const response = await LF.request(`${topicApi}/${id}`, { method: "DELETE" });
          reloadWith(response.message || "Topic deleted.");
        } catch (error) {
          button.disabled = false;
          LF.handleFailure(error, "Could not delete the topic.");
        }
      });
    });
  }
})();
