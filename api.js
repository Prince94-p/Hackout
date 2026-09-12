/* =========================================================
   Carbon Core — Shared API & Client Utility
   Strictly adheres to:
   - Token & active factory storage in localStorage only
   - Auth-guarded API fetch
   - Loading, Empty, and Error state helpers
   - Dynamic Chart.js helpers using Carbon Core brand colors
========================================================= */

const API_BASE = "";

const BRAND_COLORS = {
  orange: "#ff7b45",
  green: "#238761",
  greenSoft: "#e5f4ea",
  blue: "#2b6de8",
  blueSoft: "#eaf1ff",
  ink: "#102019",
  text: "#34453c",
  muted: "#7c8981",
  line: "#dbe2dc"
};

// 1. LocalStorage Management
function getAuthToken() {
  return localStorage.getItem("authToken");
}

function setAuthToken(token) {
  if (token) {
    localStorage.setItem("authToken", token);
  } else {
    localStorage.removeItem("authToken");
  }
}

function getActiveFactoryId() {
  const fid = localStorage.getItem("activeFactoryId");
  return fid ? parseInt(fid, 10) : null;
}

function setActiveFactoryId(id) {
  if (id) {
    localStorage.setItem("activeFactoryId", id);
  } else {
    localStorage.removeItem("activeFactoryId");
  }
}

function clearAuthSession() {
  localStorage.removeItem("authToken");
  localStorage.removeItem("activeFactoryId");
  localStorage.removeItem("selectedHotspotId");
  localStorage.removeItem("selectedRecommendationId");
  localStorage.removeItem("selectedScenarioId");
  window.location.href = "login.html";
}

// Shared sidebar factory name loader — call on DOMContentLoaded in all app pages
async function loadSidebarFactory() {
  const factoryId = getActiveFactoryId();
  if (!factoryId) return;

  // Update any sidebar factory name elements
  const nameEls = document.querySelectorAll(".sidebar-factory-name, #sidebarFactoryName");
  const metaEls = document.querySelectorAll(".sidebar-factory-meta, #sidebarFactoryMeta");

  try {
    const summary = await apiFetch(`/api/factories/${factoryId}/emissions/summary`);
    const name = summary.factory_name || "Your Factory";
    nameEls.forEach(el => { el.textContent = name; });
    // Meta is optional
  } catch (err) {
    // Silently fail — not critical
  }
}

// 2. Authorized Fetch Helper
async function apiFetch(endpoint, options = {}) {
  const token = getAuthToken();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(endpoint, {
      ...options,
      headers
    });

    if (res.status === 401) {
      clearAuthSession();
      throw new Error("Session expired. Please sign in again.");
    }

    if (!res.ok) {
      let errorMsg = `Server error (${res.status})`;
      try {
        const errJson = await res.json();
        if (errJson && errJson.detail) {
          errorMsg = Array.isArray(errJson.detail) 
            ? errJson.detail.map(d => d.msg).join(", ") 
            : errJson.detail;
        }
      } catch (e) {}
      throw new Error(errorMsg);
    }

    return await res.json();
  } catch (err) {
    console.error("API error:", err);
    throw err;
  }
}

// 3. UI State Helpers
function renderLoadingState(elementId, message = "Loading carbon data...") {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.innerHTML = `
    <div style="padding: 2.5rem; text-align: center; color: var(--muted); font-family: 'DM Sans', sans-serif;">
      <div style="display: inline-block; width: 28px; height: 28px; border: 3px solid var(--line); border-top-color: var(--green); border-radius: 50%; animation: ccSpin 0.8s linear infinite; margin-bottom: 0.75rem;"></div>
      <p style="font-size: 0.95rem; font-weight: 500;">${message}</p>
    </div>
    <style>
      @keyframes ccSpin { to { transform: rotate(360deg); } }
    </style>
  `;
}

function renderEmptyState(elementId, title = "No carbon calculation available yet.", description = "Enter factory activity data to calculate your baseline.", actionUrl = "factory-data.html", actionText = "Enter Factory Data →") {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.innerHTML = `
    <div style="padding: 3rem 1.5rem; text-align: center; background: #ffffff; border: 1px dashed var(--line); border-radius: 16px; margin: 1rem 0;">
      <div style="display: inline-flex; align-items: center; justify-content: center; width: 52px; height: 52px; border-radius: 14px; background: var(--orangeSoft); color: var(--orange); font-size: 1.5rem; font-weight: 700; margin-bottom: 1rem;">!</div>
      <h3 style="font-size: 1.25rem; font-weight: 700; color: var(--ink); margin-bottom: 0.5rem;">${title}</h3>
      <p style="font-size: 0.95rem; color: var(--text); max-width: 480px; margin: 0 auto 1.5rem; line-height: 1.5;">${description}</p>
      ${actionUrl ? `<a href="${actionUrl}" class="primary-btn" style="display: inline-block; padding: 0.75rem 1.5rem; background: var(--green); color: #fff; border-radius: 10px; font-weight: 600; text-decoration: none;">${actionText}</a>` : ""}
    </div>
  `;
}

function renderErrorState(elementId, errorMessage = "Failed to load data.", retryFnName = null) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.innerHTML = `
    <div style="padding: 2.5rem 1.5rem; text-align: center; background: #fff5f5; border: 1px solid #ffd0d0; border-radius: 14px; margin: 1rem 0;">
      <h4 style="color: #c92a2a; font-weight: 700; margin-bottom: 0.5rem;">Unable to load data</h4>
      <p style="color: #666; font-size: 0.9rem; margin-bottom: 1rem;">${errorMessage}</p>
      ${retryFnName ? `<button onclick="${retryFnName}()" style="padding: 0.5rem 1rem; border-radius: 8px; background: #fff; border: 1px solid #c92a2a; color: #c92a2a; font-weight: 600; cursor: pointer;">Retry</button>` : ""}
    </div>
  `;
}

// 4. Chart.js Dynamic Rendering Helpers
let activeCharts = {};

function renderBarChart(canvasId, labels, data, colors, yLabel = "tCO₂e") {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof Chart === "undefined") return;

  if (activeCharts[canvasId]) {
    activeCharts[canvasId].destroy();
  }

  const ctx = canvas.getContext("2d");
  activeCharts[canvasId] = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: yLabel,
        data: data,
        backgroundColor: colors || BRAND_COLORS.orange,
        borderRadius: 8,
        borderSkipped: false,
        maxBarThickness: 44
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#102019",
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: (item) => ` ${item.raw.toLocaleString("en-IN")} ${yLabel}`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { family: "DM Sans", size: 12, weight: 600 }, color: "#34453c" }
        },
        y: {
          grid: { color: "#eef2ee" },
          ticks: { font: { family: "DM Sans", size: 11 }, color: "#7c8981" }
        }
      }
    }
  });
}

function renderDoughnutChart(canvasId, labels, data, colors) {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof Chart === "undefined") return;

  if (activeCharts[canvasId]) {
    activeCharts[canvasId].destroy();
  }

  const ctx = canvas.getContext("2d");
  activeCharts[canvasId] = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: colors || [BRAND_COLORS.orange, BRAND_COLORS.green, BRAND_COLORS.blue],
        borderWidth: 2,
        borderColor: "#ffffff"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "70%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            boxWidth: 12,
            font: { family: "DM Sans", size: 12, weight: 600 },
            color: "#34453c"
          }
        },
        tooltip: {
          backgroundColor: "#102019",
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: (item) => ` ${item.label}: ${item.raw}%`
          }
        }
      }
    }
  });
}

function renderLineChart(canvasId, labels, data, lineLabel = "Footprint (tCO₂e)") {
  const canvas = document.getElementById(canvasId);
  if (!canvas || typeof Chart === "undefined") return;

  if (activeCharts[canvasId]) {
    activeCharts[canvasId].destroy();
  }

  const ctx = canvas.getContext("2d");
  activeCharts[canvasId] = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: lineLabel,
        data: data,
        borderColor: BRAND_COLORS.green,
        backgroundColor: "rgba(35, 135, 97, 0.08)",
        fill: true,
        tension: 0.35,
        pointBackgroundColor: BRAND_COLORS.green,
        pointBorderColor: "#fff",
        pointBorderWidth: 2,
        pointRadius: 6,
        pointHoverRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#102019",
          padding: 10,
          cornerRadius: 8,
          callbacks: {
            label: (item) => ` ${item.raw.toLocaleString("en-IN")} tCO₂e`
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { family: "DM Sans", size: 12, weight: 600 }, color: "#34453c" }
        },
        y: {
          grid: { color: "#eef2ee" },
          ticks: { font: { family: "DM Sans", size: 11 }, color: "#7c8981" }
        }
      }
    }
  });
}
