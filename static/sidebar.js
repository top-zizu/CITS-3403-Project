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

      <div class="sidebar-section">

        <a href="#" class="sidebar-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a10 10 0 1 0 10 10"/>
            <path d="M2 12h20"/>
          </svg>
          <span>AI</span>
        </a>

        <a href="#" class="sidebar-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <path d="M2 12h20"/>
            <path d="M12 2a15 15 0 0 1 0 20"/>
            <path d="M12 2a15 15 0 0 0 0 20"/>
          </svg>
          <span>Politics</span>
        </a>

        <a href="#" class="sidebar-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="6" width="20" height="12" rx="2"/>
            <path d="M6 12h.01"/>
            <path d="M18 12h.01"/>
          </svg>
          <span>Gaming</span>
        </a>

        <a href="#" class="sidebar-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a7 7 0 0 0-7 7c0 3 2 5 2 7h10c0-2 2-4 2-7a7 7 0 0 0-7-7z"/>
            <path d="M9 21h6"/>
          </svg>
          <span>Philosophy</span>
        </a>

      </div>

    </aside>
  `;

  placeholder.innerHTML = sidebar;

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

  // Optional: Check every 60 seconds
  setInterval(checkUnreadNotifications, 60000);
});
