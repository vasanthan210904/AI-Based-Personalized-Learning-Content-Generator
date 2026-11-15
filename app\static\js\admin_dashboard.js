/* Admin overview — platform activity chart */
(function () {
  "use strict";

  let series = [];
  try {
    series = JSON.parse(document.getElementById("adminChartData")?.textContent || "[]");
  } catch (error) {
    series = [];
  }

  const chart = document.getElementById("adminActivityChart");
  const axis = document.getElementById("adminActivityAxis");
  if (!chart || !Array.isArray(series)) return;

  const max = Math.max(
    1,
    ...series.map((item) => Math.max(Number(item.activity) || 0, Number(item.registrations) || 0))
  );

  chart.innerHTML = "";
  series.forEach((item) => {
    const activity = Number(item.activity) || 0;
    const registrations = Number(item.registrations) || 0;
    const wrap = document.createElement("div");
    wrap.className = "admin-bar-wrap";
    wrap.title = `${item.label} — ${activity} learning activit${activity === 1 ? "y" : "ies"}, ${registrations} registration${registrations === 1 ? "" : "s"}`;

    const activityBar = document.createElement("div");
    activityBar.className = `admin-bar activity${activity === 0 ? " is-empty" : ""}`;
    activityBar.style.height = `${activity === 0 ? 3 : Math.max(6, Math.round((activity / max) * 100))}%`;

    const registrationBar = document.createElement("div");
    registrationBar.className = `admin-bar registrations${registrations === 0 ? " is-empty" : ""}`;
    registrationBar.style.height = `${registrations === 0 ? 3 : Math.max(6, Math.round((registrations / max) * 100))}%`;

    wrap.appendChild(activityBar);
    wrap.appendChild(registrationBar);
    chart.appendChild(wrap);
  });

  if (axis) {
    axis.innerHTML = "";
    series.forEach((item) => {
      const label = document.createElement("span");
      label.textContent = item.label || "";
      axis.appendChild(label);
    });
  }
})();
