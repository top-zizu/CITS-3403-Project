document.addEventListener("DOMContentLoaded", () => {
  const notifications = [
    {
      type: "debates",
      title: "Alex replied to your comment",
      message: "On the debate: Should AI tools be allowed in university assessments?",
      time: "5 minutes ago",
      unread: true,
      icon: "message"
    },
    {
      type: "social",
      title: "LogicQueen sent you a friend request",
      message: "You can accept or decline this request from the Friends page.",
      time: "18 minutes ago",
      unread: true,
      icon: "user"
    },
    {
      type: "debates",
      title: "Your debate is trending",
      message: "Remote work is better than office work has received 95 votes.",
      time: "1 hour ago",
      unread: false,
      icon: "trending"
    },
    {
      type: "social",
      title: "Sarah accepted your friend request",
      message: "You and Sarah are now friends on DebateHub.",
      time: "3 hours ago",
      unread: false,
      icon: "check"
    },
    {
      type: "debates",
      title: "Debate ended",
      message: "Cats are better pets than dogs has ended. View the final results.",
      time: "Yesterday",
      unread: false,
      icon: "clock"
    }
  ];

  const list = document.getElementById("notifications-list");
  const tabs = document.querySelectorAll(".notification-tab");

  function getIcon(icon) {
    const icons = {
      message: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
      `,
      user: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
          <circle cx="8.5" cy="7" r="4"/>
          <line x1="20" y1="8" x2="20" y2="14"/>
          <line x1="17" y1="11" x2="23" y2="11"/>
        </svg>
      `,
      trending: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
          <polyline points="16 7 22 7 22 13"/>
        </svg>
      `,
      check: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 6L9 17l-5-5"/>
        </svg>
      `,
      clock: `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
      `
    };

    return icons[icon] || icons.message;
  }

  function render(filter) {
    tabs.forEach(tab => {
      tab.classList.toggle("active", tab.dataset.filter === filter);
    });

    let filtered = notifications;

    if (filter === "unread") {
      filtered = notifications.filter(item => item.unread);
    } else if (filter === "debates") {
      filtered = notifications.filter(item => item.type === "debates");
    } else if (filter === "social") {
      filtered = notifications.filter(item => item.type === "social");
    }

    if (filtered.length === 0) {
      list.innerHTML = `<p class="empty-state">No notifications to show.</p>`;
      return;
    }

    list.innerHTML = filtered.map(item => `
      <div class="notification-row ${item.unread ? "unread" : ""}">
        <div class="notification-icon">
          ${getIcon(item.icon)}
        </div>

        <div class="notification-content">
          <div class="notification-title-row">
            <h3>${item.title}</h3>
            ${item.unread ? '<span class="unread-dot"></span>' : ''}
          </div>

          <p>${item.message}</p>
          <span class="notification-time">${item.time}</span>
        </div>
      </div>
    `).join("");
  }

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      render(tab.dataset.filter);
    });
  });

  render("all");
});