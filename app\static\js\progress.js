/* Progress analytics — charts rendered from server-provided real data */
(function () {
  "use strict";

  let data = {};
  try {
    data = JSON.parse(document.getElementById("progressData")?.textContent || "{}");
  } catch (error) {
    data = {};
  }

  const activity = Array.isArray(data.activity) ? data.activity : [];
  const trend = Array.isArray(data.score_trend) ? data.score_trend : [];
  const accuracy = data.accuracy || { correct: 0, wrong: 0, unanswered: 0 };

  /* ---------------------------------------------------------------- */
  /* Activity bar chart                                               */
  /* ---------------------------------------------------------------- */
  const chart = document.getElementById("activityChart");
  const axis = document.getElementById("activityAxis");
  const totalNode = document.getElementById("activityTotal");

  if (chart) {
    const max = Math.max(1, ...activity.map((item) => Number(item.count) || 0));
    chart.innerHTML = "";
    activity.forEach((item) => {
      const count = Number(item.count) || 0;
      const wrap = document.createElement("div");
      wrap.className = "activity-bar-wrap";
      wrap.title = `${item.label}: ${count} activit${count === 1 ? "y" : "ies"}`;

      const value = document.createElement("span");
      value.className = "activity-value";
      value.textContent = String(count);

      const bar = document.createElement("div");
      bar.className = `activity-bar${count === 0 ? " is-empty" : ""}`;
      const height = count === 0 ? 3 : Math.max(6, Math.round((count / max) * 100));
      bar.style.height = `${height}%`;

      wrap.appendChild(value);
      wrap.appendChild(bar);
      chart.appendChild(wrap);
    });

    const total = activity.reduce((sum, item) => sum + (Number(item.count) || 0), 0);
    if (totalNode) {
      totalNode.textContent = `${total} activit${total === 1 ? "y" : "ies"}`;
    }
  }

  if (axis) {
    axis.innerHTML = "";
    activity.forEach((item) => {
      const label = document.createElement("span");
      label.textContent = item.label || "";
      axis.appendChild(label);
    });
  }

  /* ---------------------------------------------------------------- */
  /* Quiz score trend (SVG line chart)                                */
  /* ---------------------------------------------------------------- */
  const trendChart = document.getElementById("trendChart");
  const trendLabels = document.getElementById("trendLabels");
  const SVG_NS = "http://www.w3.org/2000/svg";
  const WIDTH = 600;
  const HEIGHT = 170;
  const LEFT = 32;
  const RIGHT = 588;
  const TOP = 14;
  const BOTTOM = 142;

  function el(name, attrs) {
    const node = document.createElementNS(SVG_NS, name);
    Object.entries(attrs || {}).forEach(([key, value]) => node.setAttribute(key, value));
    return node;
  }

  if (trendChart && trend.length) {
    const svg = el("svg", {
      viewBox: `0 0 ${WIDTH} ${HEIGHT}`,
      preserveAspectRatio: "none",
      role: "img",
      "aria-label": "Quiz score trend",
    });

    const defs = el("defs");
    const gradient = el("linearGradient", {
      id: "lfTrendFill",
      x1: "0",
      y1: "0",
      x2: "0",
      y2: "1",
    });
    gradient.appendChild(el("stop", { offset: "0%", "stop-color": "#6366f1", "stop-opacity": "0.28" }));
    gradient.appendChild(el("stop", { offset: "100%", "stop-color": "#6366f1", "stop-opacity": "0" }));
    defs.appendChild(gradient);
    svg.appendChild(defs);

    [0, 50, 100].forEach((value) => {
      const y = TOP + (1 - value / 100) * (BOTTOM - TOP);
      svg.appendChild(
        el("line", {
          x1: LEFT,
          y1: y,
          x2: RIGHT,
          y2: y,
          stroke: "#eef2f7",
          "stroke-width": "1",
          "stroke-dasharray": value === 0 ? "0" : "4 5",
        })
      );
      const text = el("text", {
        x: LEFT - 8,
        y: y + 3,
        "text-anchor": "end",
        "font-size": "9",
        "font-family": "Inter, sans-serif",
        fill: "#94a3b8",
      });
      text.textContent = `${value}%`;
      svg.appendChild(text);
    });

    const step = trend.length > 1 ? (RIGHT - LEFT) / (trend.length - 1) : 0;
    const points = trend.map((item, index) => {
      const x = trend.length === 1 ? (LEFT + RIGHT) / 2 : LEFT + step * index;
      const value = Math.max(0, Math.min(100, Number(item.percentage) || 0));
      const y = TOP + (1 - value / 100) * (BOTTOM - TOP);
      return { x, y, item };
    });

    if (points.length > 1) {
      const linePath = points.map((point, index) => `${index === 0 ? "M" : "L"}${point.x},${point.y}`).join(" ");
      const areaPath = `${linePath} L${points[points.length - 1].x},${BOTTOM} L${points[0].x},${BOTTOM} Z`;
      svg.appendChild(el("path", { d: areaPath, fill: "url(#lfTrendFill)" }));
      svg.appendChild(
        el("path", {
          d: linePath,
          fill: "none",
          stroke: "#4f46e5",
          "stroke-width": "2.5",
          "stroke-linecap": "round",
          "stroke-linejoin": "round",
          "vector-effect": "non-scaling-stroke",
        })
      );
    }

    points.forEach((point) => {
      const circle = el("circle", {
        cx: point.x,
        cy: point.y,
        r: "4.5",
        fill: "#ffffff",
        stroke: "#4f46e5",
        "stroke-width": "2.5",
        "vector-effect": "non-scaling-stroke",
      });
      const title = el("title");
      title.textContent = `${point.item.label}: ${point.item.percentage}%${point.item.topic ? ` · ${point.item.topic}` : ""}`;
      circle.appendChild(title);
      svg.appendChild(circle);
    });

    trendChart.appendChild(svg);
  }

  if (trendLabels) {
    trendLabels.innerHTML = "";
    trend.forEach((item) => {
      const label = document.createElement("span");
      label.textContent = item.label || "";
      trendLabels.appendChild(label);
    });
  }

  /* ---------------------------------------------------------------- */
  /* Accuracy donut                                                   */
  /* ---------------------------------------------------------------- */
  const donut = document.getElementById("accuracyDonut");
  const accuracyPercent = document.getElementById("accuracyPercent");
  if (donut) {
    const correct = Number(accuracy.correct) || 0;
    const wrong = Number(accuracy.wrong) || 0;
    const skipped = Number(accuracy.unanswered) || 0;
    const total = correct + wrong + skipped;

    if (total === 0) {
      donut.style.background = "conic-gradient(#e2e8f0 0 100%)";
      if (accuracyPercent) accuracyPercent.textContent = "—";
    } else {
      const correctEnd = (correct / total) * 100;
      const wrongEnd = ((correct + wrong) / total) * 100;
      donut.style.background = `conic-gradient(
        #6366f1 0% ${correctEnd}%,
        #f43f5e ${correctEnd}% ${wrongEnd}%,
        #cbd5e1 ${wrongEnd}% 100%
      )`;
      if (accuracyPercent) {
        accuracyPercent.textContent = `${Math.round((correct / total) * 100)}%`;
      }
    }
    donut.title = `${correct} correct · ${wrong} incorrect · ${skipped} unanswered`;
  }
})();
