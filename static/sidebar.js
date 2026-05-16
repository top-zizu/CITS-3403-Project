document.addEventListener("DOMContentLoaded", () => {
  const placeholder = document.getElementById("sidebar-placeholder");
  if (!placeholder) return;

  const sidebar = `
    <aside class="dh-sidebar" id="dh-sidebar">

      <button class="sidebar-toggle" id="sidebar-toggle" type="button" aria-label="Toggle sidebar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="3" y1="12" x2="21" y2="12"/>
          <line x1="3" y1="6" x2="21" y2="6"/>
          <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>

      <div class="sidebar-section">
        <a href="/home" class="sidebar-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 10.5L12 3l9 7.5"/>
            <path d="M5 9.5V21h14V9.5"/>
          </svg>
          <span>Home</span>
        </a>

        <a href="/search" class="sidebar-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="7"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <span>Search</span>
        </a>

        <a href="/dashboard" class="sidebar-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
          </svg>
          <span>Dashboard</span>
        </a>

        <a href="/leaderboard" class="sidebar-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 21h8"/>
            <path d="M12 17v4"/>
            <path d="M7 4h10"/>
            <path d="M17 4v4a5 5 0 0 1-10 0V4"/>
          </svg>
          <span>Leaderboard</span>
        </a>
      </div>

      <div class="sidebar-divider"></div>

      <div class="sidebar-label">Social</div>

      <div class="sidebar-section">

        <a href="/friends?tab=following" class="sidebar-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
          <span>Friends</span>
        </a>

        <a href="/notifications" class="sidebar-link">
          <div class="sidebar-icon-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            <div id="sidebar-notification-dot" class="sidebar-unread-dot" style="display: none;"></div>
          </div>
          <span>Notifications</span>
        </a>
      </div>

      <div class="sidebar-divider"></div>

      <div class="sidebar-label">Debates</div>

      <div class="sidebar-section">

        <a href="/debates/create" class="sidebar-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 5v14"/>
            <path d="M5 12h14"/>
          </svg>
          <span>Create Debate</span>
        </a>

        <a href="/saved-debates" class="sidebar-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
          </svg>
          <span>Saved Debates</span>
        </a>

        <a href="/my-debates" class="sidebar-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <span>My Debates</span>
        </a>

      </div>

      <div class="sidebar-divider"></div>

      <div class="sidebar-label">Trending</div>

      <div class="sidebar-section" id="sidebar-trending-links">
        <a href="/search" class="sidebar-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M20.59 13.41 11 3H4v7l9.59 9.59a2 2 0 0 0 2.82 0l4.18-4.18a2 2 0 0 0 0-2.82Z"/>
            <circle cx="7.5" cy="7.5" r=".5"/>
          </svg>
          <span>Loading trends</span>
        </a>
      </div>

    </aside>
  `;

  placeholder.innerHTML = sidebar;

  function escapeHTML(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatTagLabel(tag) {
    return String(tag || "Tag")
      .replace(/[-_]+/g, " ")
      .replace(/\b\w/g, letter => letter.toUpperCase());
  }

  function iconSvg(iconType) {
    const icons = {
      landmark: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 21h18"/><path d="M4 10h16"/><path d="M6 10v7"/>
          <path d="M10 10v7"/><path d="M14 10v7"/><path d="M18 10v7"/>
          <path d="M12 3 3 8h18Z"/>
        </svg>`,
      monitor: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="4" width="18" height="12" rx="2"/>
          <path d="M8 20h8"/><path d="M12 16v4"/>
        </svg>`,
      leaf: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M11 20A7 7 0 0 1 4 13C4 8 8 4 20 4c0 12-4 16-9 16Z"/>
          <path d="M4 13c4 0 8-2 12-6"/>
        </svg>`,
      pizza: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M15 11h.01"/><path d="M11 15h.01"/><path d="M16 16h.01"/>
          <path d="M2 16 22 3 9 23Z"/><path d="M5.71 13.59c3.31 1.47 6.55 3.87 8.7 6.7"/>
        </svg>`,
      briefcase: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
          <path d="M2 13h20"/>
        </svg>`,
      paw: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="4" r="2"/><circle cx="18" cy="8" r="2"/>
          <circle cx="20" cy="16" r="2"/><path d="M9 10a5 5 0 0 1 7 7l-1 1a4 4 0 0 1-6 0l-1-1a5 5 0 0 1 1-7Z"/>
          <circle cx="4" cy="12" r="2"/>
        </svg>`,
      trophy: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M8 21h8"/><path d="M12 17v4"/><path d="M7 4h10"/>
          <path d="M17 4v4a5 5 0 0 1-10 0V4"/><path d="M5 5H3a2 2 0 0 0 2 4"/>
          <path d="M19 5h2a2 2 0 0 1-2 4"/>
        </svg>`,
      film: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="3" width="20" height="18" rx="2"/><path d="M7 3v18"/>
          <path d="M17 3v18"/><path d="M2 8h5"/><path d="M17 8h5"/>
          <path d="M2 16h5"/><path d="M17 16h5"/>
        </svg>`,
      book: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5Z"/>
        </svg>`,
      tag: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20.59 13.41 11 3H4v7l9.59 9.59a2 2 0 0 0 2.82 0l4.18-4.18a2 2 0 0 0 0-2.82Z"/>
          <circle cx="7.5" cy="7.5" r=".5"/>
        </svg>`,
    };

    return icons[iconType] || icons.tag;
  }

  function risingArrowSvg() {
    return `<svg class="trending-arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
        <polyline points="16 7 22 7 22 13"/>
      </svg>`;
  }

  function isActiveTrendingTag(tag) {
    const params = new URLSearchParams(window.location.search);
    return window.location.pathname === "/search" && params.get("tag") === tag;
  }

  async function loadTrendingTags() {
    const trendingWrap = document.getElementById("sidebar-trending-links");
    if (!trendingWrap) return;

    try {
      const response = await fetch("/api/trending-tags");
      if (!response.ok) throw new Error("Could not load trending tags");

      const data = await response.json();
      const tags = data.tags || [];

      if (tags.length === 0) {
        trendingWrap.innerHTML = `
          <a href="/search" class="sidebar-link">
            ${iconSvg("tag")}
            <span>Explore debates</span>
          </a>
        `;
        return;
      }

      trendingWrap.innerHTML = tags.map(tag => `
        <a href="${escapeHTML(tag.url || `/search?tag=${encodeURIComponent(tag.tag)}`)}"
          class="sidebar-link ${isActiveTrendingTag(tag.tag) ? "active" : ""}"
          title="${escapeHTML(`${tag.count} open debate${tag.count === 1 ? "" : "s"}`)}">
          ${iconSvg(tag.icon)}
          ${risingArrowSvg()}
          <span>${escapeHTML(formatTagLabel(tag.tag))}</span>
        </a>
      `).join("");
    } catch (err) {
      trendingWrap.innerHTML = `
        <a href="/search" class="sidebar-link">
          ${iconSvg("tag")}
          <span>Explore debates</span>
        </a>
      `;
    }
  }

  const sidebarEl = document.getElementById("dh-sidebar");
  const toggleBtn = document.getElementById("sidebar-toggle");

  if (localStorage.getItem("sidebarCollapsed") === "true") {
    sidebarEl.classList.add("collapsed");
    document.body.classList.add("sidebar-collapsed");
  } else {
    document.body.classList.add("sidebar-open");
  }

  toggleBtn.addEventListener("click", () => {
    sidebarEl.classList.toggle("collapsed");

    const collapsed = sidebarEl.classList.contains("collapsed");

    localStorage.setItem("sidebarCollapsed", collapsed);

    document.body.classList.toggle("sidebar-collapsed", collapsed);
    document.body.classList.toggle("sidebar-open", !collapsed);
  });

  document.querySelectorAll(".sidebar-link").forEach(link => {
    const href = link.getAttribute("href");

    if (href !== "#" && link.pathname === window.location.pathname) {
      link.classList.add("active");
  }
});

  async function checkUnreadNotifications() {
    try {
      const response = await fetch('/api/notifications/unread-count'); 
      const data = await response.json();
      
      const dot = document.getElementById("sidebar-notification-dot");
      if (dot && data.unread_count > 0) {
        dot.style.display = "block";
      } else if (dot) {
        dot.style.display = "none";
      }
    } catch (err) {
      console.error("Failed to fetch unread notifications", err);
    }
  }

  // Initial check
  checkUnreadNotifications();
  loadTrendingTags();

  // Optional: Check every 60 seconds
  setInterval(checkUnreadNotifications, 60000);
});
