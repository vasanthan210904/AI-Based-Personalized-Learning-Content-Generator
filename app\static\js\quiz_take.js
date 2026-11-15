/* Quiz taking — live progress, navigator and server-side submission */
(function () {
  "use strict";

  const form = document.getElementById("quizTakeForm");
  if (!form) return;

  const quizId = form.getAttribute("data-quiz-id") || form.querySelector('[name="quiz_id"]')?.value;
  const questionCards = Array.from(form.querySelectorAll("[data-question-index]"));
  const total = questionCards.length;
  const navItems = Array.from(document.querySelectorAll("[data-qnav]"));
  const progressFill = document.getElementById("quizProgressFill");
  const progressLabel = document.getElementById("quizProgressLabel");
  const answeredCount = document.getElementById("answeredCount");
  const submitButton = document.getElementById("submitQuizButton");
  const overlay = document.getElementById("quizSubmittingOverlay");
  const warning = document.getElementById("unansweredWarning");
  const warningText = document.getElementById("unansweredWarningText");
  const timerNode = document.getElementById("quizTimer");

  let submitted = false;
  let submitting = false;

  const startTime = Date.now();
  function tick() {
    if (!timerNode) return;
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const minutes = String(Math.floor(elapsed / 60)).padStart(2, "0");
    const seconds = String(elapsed % 60).padStart(2, "0");
    timerNode.textContent = `${minutes}:${seconds}`;
  }
  tick();
  const timer = window.setInterval(tick, 1000);

  function selectedFor(index) {
    return form.querySelector(`input[name="answer_${index}"]:checked`);
  }

  function refresh() {
    let answered = 0;
    questionCards.forEach((card) => {
      const index = card.getAttribute("data-question-index");
      const chosen = selectedFor(index);
      const isAnswered = Boolean(chosen);
      if (isAnswered) answered += 1;
      card.classList.toggle("is-answered", isAnswered);
      card.classList.remove("is-missing");

      const status = card.querySelector("[data-status-for]");
      if (status) {
        status.textContent = isAnswered ? "Answered" : "Unanswered";
        status.classList.toggle("answered", isAnswered);
      }
      const nav = navItems.find((item) => item.getAttribute("data-qnav") === index);
      if (nav) nav.classList.toggle("is-answered", isAnswered);
    });

    const percent = total ? Math.round((answered / total) * 100) : 0;
    if (progressFill) progressFill.style.width = `${percent}%`;
    if (progressLabel) progressLabel.textContent = `${answered} of ${total} answered`;
    if (answeredCount) answeredCount.textContent = String(answered);
    if (warning && answered > 0) warning.hidden = true;

    return answered;
  }

  form.addEventListener("change", (event) => {
    if (event.target.matches('input[type="radio"]')) refresh();
  });

  form.addEventListener("click", (event) => {
    const clear = event.target.closest("[data-clear-question]");
    if (!clear) return;
    const index = clear.getAttribute("data-clear-question");
    form.querySelectorAll(`input[name="answer_${index}"]`).forEach((input) => {
      input.checked = false;
    });
    refresh();
  });

  navItems.forEach((item) => {
    item.addEventListener("click", () => {
      const index = item.getAttribute("data-qnav");
      const card = form.querySelector(`[data-question-index="${index}"]`);
      if (card) {
        card.scrollIntoView({ behavior: "smooth", block: "start" });
        card.classList.add("is-answered");
        window.setTimeout(() => card.classList.remove("is-answered"), 900);
      }
    });
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (submitting) return;

    const answered = refresh();
    const unanswered = total - answered;

    if (unanswered > 0) {
      if (warning) warning.hidden = false;
      if (warningText) {
        warningText.textContent = `${unanswered} question${unanswered === 1 ? "" : "s"} left unanswered. They will be marked incorrect but counted separately.`;
      }
      const confirmed = await LF.confirm({
        title: "Submit with unanswered questions?",
        message: `${unanswered} question${unanswered === 1 ? " is" : "s are"} unanswered. You can still submit and review the answers afterwards.`,
        confirmLabel: "Submit anyway",
        tone: "primary",
        icon: "bi-send-check",
      });
      if (!confirmed) return;
    }

    const answers = {};
    questionCards.forEach((card) => {
      const index = card.getAttribute("data-question-index");
      const chosen = selectedFor(index);
      answers[index] = chosen ? Number(chosen.value) : null;
    });

    submitting = true;
    if (overlay) overlay.hidden = false;
    LF.setLoading(submitButton, true, "Evaluating…");

    try {
      const response = await LF.request("/api/submit-quiz", {
        method: "POST",
        body: { quiz_id: Number(quizId), answers: answers },
      });
      submitted = true;
      window.clearInterval(timer);
      window.location.href = response.data.results_url;
    } catch (error) {
      submitting = false;
      if (overlay) overlay.hidden = true;
      LF.setLoading(submitButton, false);
      LF.handleFailure(error, "Could not submit the quiz.");
    }
  });

  window.addEventListener("beforeunload", (event) => {
    if (submitted || submitting) return;
    const answered = questionCards.some((card) =>
      selectedFor(card.getAttribute("data-question-index"))
    );
    if (!answered) return;
    event.preventDefault();
    event.returnValue = "";
  });

  refresh();
})();
