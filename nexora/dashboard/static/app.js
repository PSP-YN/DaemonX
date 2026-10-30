/**
 * NEXORA Local Dashboard Client-Side Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  // Navigation Tabs
  const navItems = document.querySelectorAll(".nav-item");
  const tabViews = document.querySelectorAll(".tab-view");

  navItems.forEach((btn) => {
    btn.addEventListener("click", () => {
      navItems.forEach((b) => b.classList.remove("active"));
      tabViews.forEach((v) => v.classList.remove("active"));

      btn.classList.add("active");
      const tabId = `view-${btn.dataset.tab}`;
      const targetView = document.getElementById(tabId);
      if (targetView) targetView.classList.add("active");

      if (btn.dataset.tab === "device") refreshScreen();
      if (btn.dataset.tab === "skills") loadSkills();
      if (btn.dataset.tab === "tasks") loadTasks();
      if (btn.dataset.tab === "cleanup") loadCleanupPreview();
    });
  });

  // Global Refresh
  document.getElementById("btn-refresh").addEventListener("click", () => {
    loadStatus();
    refreshScreen();
  });

  // Export buttons
  document.getElementById("btn-export-json").addEventListener("click", () => {
    window.open("/api/export?format=json", "_blank");
  });
  document.getElementById("btn-export-md").addEventListener("click", () => {
    window.open("/api/export?format=markdown", "_blank");
  });

  // Screen Click & Tapping
  const overlay = document.getElementById("screen-click-overlay");
  const screenImg = document.getElementById("live-screen-img");
  const coordDisplay = document.getElementById("click-coords");

  overlay.addEventListener("click", async (e) => {
    const rect = overlay.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Scale to native device resolution (1080x2460)
    const nativeX = Math.round((clickX / rect.width) * 1080);
    const nativeY = Math.round((clickY / rect.height) * 2460);

    coordDisplay.innerText = `(${nativeX}, ${nativeY})`;

    try {
      await fetch("/api/action/tap", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ x: nativeX, y: nativeY })
      });
      setTimeout(refreshScreen, 300);
    } catch (err) {
      console.error("Tap failed:", err);
    }
  });

  // Navigation Keys
  document.getElementById("btn-back").addEventListener("click", async () => {
    await fetch("/api/action/key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key: "back" })
    });
    setTimeout(refreshScreen, 300);
  });

  document.getElementById("btn-home").addEventListener("click", async () => {
    await fetch("/api/action/key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key: "home" })
    });
    setTimeout(refreshScreen, 300);
  });

  document.getElementById("btn-scroll-up").addEventListener("click", async () => {
    await fetch("/api/action/swipe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ x1: 540, y1: 600, x2: 540, y2: 1800, duration_ms: 300 })
    });
    setTimeout(refreshScreen, 300);
  });

  document.getElementById("btn-scroll-down").addEventListener("click", async () => {
    await fetch("/api/action/swipe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ x1: 540, y1: 1800, x2: 540, y2: 600, duration_ms: 300 })
    });
    setTimeout(refreshScreen, 300);
  });

  document.getElementById("btn-capture-now").addEventListener("click", refreshScreen);

  // Search input
  const searchInput = document.getElementById("global-search");
  searchInput.addEventListener("keydown", async (e) => {
    if (e.key === "Enter") {
      const q = searchInput.value.trim();
      if (!q) return;

      // Switch to knowledge tab
      document.querySelector('[data-tab="knowledge"]').click();
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
      const results = await res.json();
      renderKnowledgeResults(results);
    }
  });

  // Cleanup Refresh
  document.getElementById("btn-refresh-cleanup").addEventListener("click", loadCleanupPreview);

  // Initial Load
  loadStatus();
  refreshScreen();
  setInterval(loadStatus, 10000);
});

async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();

    document.getElementById("stat-total-media").innerText = data.database.total_media;
    document.getElementById("stat-processed-media").innerText = data.database.processed_media;
    document.getElementById("stat-resources").innerText = data.database.resources;
    document.getElementById("stat-jobs").innerText = data.database.total_jobs;

    if (data.device) {
      document.getElementById("info-model").innerText = data.device.model;
      document.getElementById("sidebar-device-model").innerText = data.device.model;
      document.getElementById("info-android").innerText = `Android ${data.device.android_version} (SDK ${data.device.sdk_version})`;
      document.getElementById("info-screen").innerText = `${data.device.width} x ${data.device.height} @ ${data.device.density} dpi`;
      document.getElementById("device-conn-type").innerText = `${data.device.connection_type.toUpperCase()} Connected`;
    }
  } catch (err) {
    console.error("Status load error:", err);
  }
}

function refreshScreen() {
  const img = document.getElementById("live-screen-img");
  img.src = `/api/screen?t=${Date.now()}`;
}

async function loadSkills() {
  const res = await fetch("/api/skills");
  const skills = await res.json();
  const container = document.getElementById("skills-list");
  container.innerHTML = "";

  skills.forEach((s) => {
    const card = document.createElement("div");
    card.className = "skill-card";
    card.innerHTML = `
      <h4>${s.name}</h4>
      <p>${s.description}</p>
    `;
    container.appendChild(card);
  });
}

async function loadTasks() {
  const res = await fetch("/api/jobs");
  const jobs = await res.json();
  const tbody = document.getElementById("tasks-table-body");
  tbody.innerHTML = "";

  if (jobs.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty-cell">No active jobs yet.</td></tr>';
    return;
  }

  jobs.forEach((j) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><code>${j.id}</code></td>
      <td><strong>${j.task_name}</strong></td>
      <td><span class="badge ${j.status === 'completed' ? 'online' : ''}">${j.status.toUpperCase()}</span></td>
      <td>${j.current_step} / ${j.total_steps}</td>
      <td>${new Date(j.updated_at * 1000).toLocaleTimeString()}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderKnowledgeResults(results) {
  const container = document.getElementById("knowledge-results");
  container.innerHTML = "";

  if (!results || results.length === 0) {
    container.innerHTML = '<div class="empty-state">No matching records found.</div>';
    return;
  }

  results.forEach((r) => {
    const card = document.createElement("div");
    card.className = "panel";
    card.style.marginBottom = "16px";
    card.innerHTML = `
      <div class="panel-header">
        <h4>${r.caption || r.media_id} (${r.source_type})</h4>
        <span class="tag">@${r.creator || 'unknown'}</span>
      </div>
      <div class="panel-body">
        <p style="margin-bottom: 8px; font-size: 13px;">${r.summary || ''}</p>
        <pre style="background: #000; padding: 10px; border-radius: 6px; font-size: 11px; max-height: 120px; overflow-y: auto;">${r.full_text || ''}</pre>
      </div>
    `;
    container.appendChild(card);
  });
}

async function loadCleanupPreview() {
  const res = await fetch("/api/cleanup/preview");
  const data = await res.json();

  document.getElementById("cleanup-candidate-count").innerText = `${data.total_candidates} candidates eligible (${Math.round(data.total_size_bytes / 1024)} KB)`;
  const list = document.getElementById("cleanup-candidates-list");
  list.innerHTML = "";

  if (data.candidates.length === 0) {
    list.innerHTML = '<p class="subtext">No files currently eligible for quarantine.</p>';
    return;
  }

  data.candidates.forEach((c) => {
    const item = document.createElement("div");
    item.className = "panel";
    item.style.marginBottom = "10px";
    item.innerHTML = `
      <div class="panel-body" style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <strong>${c.media_id}</strong>
          <div class="subtext">${c.original_path}</div>
        </div>
        <button class="btn btn-secondary" onclick="quarantineItem('${c.media_id}')">Quarantine</button>
      </div>
    `;
    list.appendChild(item);
  });
}

async function quarantineItem(mediaId) {
  await fetch("/api/cleanup/quarantine", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ media_id: mediaId, approved: true })
  });
  loadCleanupPreview();
}
