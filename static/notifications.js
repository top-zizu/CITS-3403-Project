document.addEventListener("DOMContentLoaded", () => {
  let notifications = [];
  const list = document.getElementById("notifications-list");
  const tabs = document.querySelectorAll(".notification-tab");
  let currentFilter = "all";
  let expandedIndex = null;

  function timeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    if (diff < 60) return "Just now";
    if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
    return `${Math.floor(diff / 86400)} days ago`;
  }

  function getIcon(type) {
    const icons = {
      social: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="17" y1="11" x2="23" y2="11"/></svg>`,
      comment: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
      reply: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
      debate_closed: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
    };
    return icons[type] || icons.comment;
  }

  function render(filter = currentFilter) {
    currentFilter = filter;

    tabs.forEach(tab => {
      tab.classList.toggle("active", tab.dataset.filter === filter);
    });

    let filtered = notifications
      .map((item, index) => ({ ...item, index }))
      .filter(item => {
        if (filter === "unread") return !item.is_read;
        if (filter === "debates") return item.type === "debate_closed";
        if (filter === "social") return item.type === "social";
        return true;
      });

    if (filtered.length === 0) {
      list.innerHTML = `<p class="empty-state">No notifications to show.</p>`;
      return;
    }

    list.innerHTML = filtered.map(item => `
      <div class="notification-row ${!item.is_read ? "unread" : ""} ${expandedIndex === item.index ? "expanded" : ""}"
           data-index="${item.index}"
           ${item.link_url ? `data-url="${item.link_url}"` : ""}>
        <div class="notification-icon">${getIcon(item.type)}</div>
        <div class="notification-content">
          <div class="notification-title-row">
            <h3>${item.message}</h3>
            ${!item.is_read ? '<span class="unread-dot"></span>' : ""}
          </div>
          <span class="notification-time">${timeAgo(item.created_at)}</span>
        </div>
      </div>
    `).join("");

    document.querySelectorAll(".notification-row").forEach(row => {
      row.addEventListener("click", () => {
        const index = Number(row.dataset.index);
        const url = row.dataset.url;
        expandedIndex = expandedIndex === index ? null : index;
        notifications[index].is_read = true;
        render(currentFilter);
        if (url) window.location.href = url;
      });
    });
  }

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      expandedIndex = null;
      render(tab.dataset.filter);
    });
  });

  async function loadNotifications() {
    const response = await fetch("/api/notifications");
    if (!response.ok) throw new Error("Could not load notifications");
    const data = await response.json();
    notifications = data.notifications || [];
    render("all");
  }

  loadNotifications().catch(() => {
    list.innerHTML = `<p class="empty-state">Could not load notifications. Please try again.</p>`;
  });
});