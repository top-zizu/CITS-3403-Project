document.addEventListener("DOMContentLoaded", () => {
  const friends = [
    {
      name: "Alex",
      username: "@alexdebates",
      status: "Online",
      meta: "Currently debating AI ethics",
      avatar: "A"
    },
    {
      name: "Sarah",
      username: "@sarahlogic",
      status: "Offline",
      meta: "Last active 2 hours ago",
      avatar: "S"
    },
    {
      name: "Jamie",
      username: "@jamievotes",
      status: "Online",
      meta: "Commented on remote work",
      avatar: "J"
    }
  ];

  const requests = [
    {
      name: "LogicQueen",
      username: "@logicqueen",
      meta: "Sent you a friend request",
      avatar: "L"
    },
    {
      name: "ArgumentKing",
      username: "@argumentking",
      meta: "Sent you a friend request",
      avatar: "A"
    }
  ];

  const list = document.getElementById("friends-list");
  const tabs = document.querySelectorAll(".friends-tab");

  function getCurrentTab() {
    const params = new URLSearchParams(window.location.search);
    return params.get("tab") === "requests" ? "requests" : "friends";
  }

  function render(tab) {
    tabs.forEach(button => {
      button.classList.toggle("active", button.dataset.tab === tab);
    });

    const data = tab === "requests" ? requests : friends;

    if (data.length === 0) {
      list.innerHTML = `<p class="empty-state">Nothing to show here yet.</p>`;
      return;
    }

    list.innerHTML = data.map(user => {
      if (tab === "requests") {
        return `
          <div class="friend-row">
            <div class="friend-avatar">${user.avatar}</div>

            <div class="friend-info">
              <h3>${user.name}</h3>
              <p>${user.username} · ${user.meta}</p>
            </div>

            <div class="friend-actions">
              <button class="accept-btn">Accept</button>
              <button class="decline-btn">Decline</button>
            </div>
          </div>
        `;
      }

      return `
        <div class="friend-row">
          <div class="friend-avatar">${user.avatar}</div>

          <div class="friend-info">
            <h3>${user.name}</h3>
            <p>${user.username} · ${user.meta}</p>
          </div>

          <span class="friend-status ${user.status.toLowerCase()}">${user.status}</span>
        </div>
      `;
    }).join("");
  }

  tabs.forEach(button => {
    button.addEventListener("click", () => {
      const tab = button.dataset.tab;
      history.pushState(null, "", `/friends?tab=${tab}`);
      render(tab);
    });
  });

  render(getCurrentTab());
});