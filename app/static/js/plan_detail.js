/* Study plan detail — persist day completion toggles */
(function () {
  "use strict";

  const timeline = document.getElementById("dayTimeline");
  if (!timeline) return;

  const planId = timeline.getAttribute("data-plan-id");
  const dayCounter = document.getElementById("planDayCounter");
  const progressRing = document.querySelector(".plan-overview-progress .progress-ring");
  const progressStrong = document.querySelector(".plan-progress-copy strong");
  const progressText = document.getElementById("planProgressText");

  function updateSummary(data) {
    if (dayCounter) {
      dayCounter.textContent = `${data.completed_days}/${data.total_days} days`;
    }
    if (progressRing) {
      progressRing.style.setProperty("--value", data.percentage);
      const label = progressRing.querySelector("span");
      if (label) label.innerHTML = `${data.percentage}<small>%</small>`;
    }
    if (progressStrong) {
      progressStrong.textContent = `${data.completed_days} of ${data.total_days} days complete`;
    }
    if (progressText) {
      if (data.plan_complete) {
        progressText.textContent = "Plan finished — well done!";
      } else {
        const remaining = data.total_days - data.completed_days;
        progressText.textContent = `${remaining} day${remaining === 1 ? "" : "s"} remaining`;
      }
    }
  }

  timeline.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-toggle-day]");
    if (!button || button.disabled) return;

    const dayIndex = Number(button.getAttribute("data-toggle-day"));
    const card = timeline.querySelector(`[data-day-card="${dayIndex}"]`);
    if (!card || !Number.isInteger(dayIndex)) return;

    button.disabled = true;
    try {
      const response = await LF.request(`/api/study-plans/${planId}/toggle`, {
        method: "POST",
        body: { day_index: dayIndex },
      });
      const data = response.data || {};
      const complete = Boolean(data.completed);

      card.classList.toggle("is-complete", complete);
      button.classList.toggle("checked", complete);
      button.setAttribute("aria-pressed", complete ? "true" : "false");
      const status = card.querySelector(".day-status");
      if (status) status.textContent = complete ? "Completed" : "Not completed";

      updateSummary(data);
      LF.showToast(
        complete ? "Day marked complete. Keep going!" : "Day marked as not completed.",
        complete ? "success" : "info"
      );
    } catch (error) {
      LF.handleFailure(error, "Could not update the study day.");
    } finally {
      button.disabled = false;
    }
  });
})();
