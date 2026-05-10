document.addEventListener("DOMContentLoaded", () => {
  let notifications = [
    {
      type: "debates",
      title: "Alex replied to your comment",
      message: "On the debate: Should AI tools be allowed in university assessments?",
      fullMessage: "Alex replied to your comment on the debate about AI tools in university assessments. Click through later to continue the discussion and respond.",
      time: "5 minutes ago",
      unread: true,
      icon: "message"
    },
    {
      type: "social",
      title: "LogicQueen sent you a friend request",
      message: "You can accept or decline this request from the Friends page.",
      fullMessage: "LogicQueen sent you a friend request. Open the Friends page to accept or decline the request.",
      time: "18 minutes ago",
      unread: true,
      icon: "user"
    }
  ];

  const list = document.getElementById("notifications-list");
  const tabs = document.querySelectorAll(".notification-tab");
  let currentFilter = "all";
  let expandedIndex = null;

  function render(filter = currentFilter) {
    currentFilter = filter;

    tabs.forEach(tab => {
      tab.classList.toggle("active", tab.dataset.filter === filter);
    });

    let filtered = notifications
      .map((item, index) => ({ ...item, index }))
      .filter(item => {
        if (filter === "unread") return item.unread;
        if (filter === "debates") return item.type === "debates";
        if (filter === "social") return item.type === "social";
        return true;
      });

    if (filtered.length === 0) {
      list.innerHTML = `<p class="empty-state">No notifications to show.</p>`;
      return;
    }

    list.innerHTML = filtered.map(item => `
      <div class="notification-row ${item.unread ? "unread" : ""} ${expandedIndex === item.index ? "expanded" : ""}"
           data-index="${item.index}">
        <div class="notification-icon">${getIcon(item.icon)}</div>

        <div class="notification-content">
          <div class="notification-title-row">
            <h3>${item.title}</h3>
            ${item.unread ? '<span class="unread-dot"></span>' : ""}
          </div>

          <p>${item.message}</p>
          <span class="notification-time">${item.time}</span>

          ${expandedIndex === item.index ? `
            <div class="notification-expanded">
              <p>${item.fullMessage}</p>
            </div>
          ` : ""}
        </div>
      </div>
    `).join("");

    document.querySelectorAll(".notification-row").forEach(row => {
      row.addEventListener("click", () => {
        const index = Number(row.dataset.index);

        expandedIndex = expandedIndex === index ? null : index;
        notifications[index].unread = false;

        render(currentFilter);
      });
    });
  }

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      expandedIndex = null;
      render(tab.dataset.filter);
    });
  });

  function getIcon(icon) {
    const icons = {
      message: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`,
      user: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="17" y1="11" x2="23" y2="11"/></svg>`
    };

    return icons[icon] || icons.message;
  }

  render("all");
});