document.addEventListener("DOMContentLoaded", () => {
  const list = document.getElementById("friends-list");
  const tabs = document.querySelectorAll(".friends-tab");
  const searchInput = document.getElementById("friends-search-input");
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";

  let currentTab = getCurrentTab();
  let searchQuery = "";
  let searchTimer = null;

  function escapeHTML(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function getCurrentTab() {
    const params = new URLSearchParams(window.location.search);
    const tab = params.get("tab");
    if (tab === "requests") return "followers";
    return ["following", "followers", "discover"].includes(tab) ? tab : "following";
  }

  function tabEmptyMessage(tab) {
    if (tab === "followers") return "No followers yet.";
    if (tab === "discover") return "No users found.";
    return "You are not following anyone yet.";
  }

  function userMeta(user, tab) {
    const details = [
      `${user.follower_count} follower${user.follower_count === 1 ? "" : "s"}`,
      `${user.debate_count} debate${user.debate_count === 1 ? "" : "s"}`,
    ];

    if (tab === "followers" && user.is_following) details.unshift("You follow each other");
    else if (tab === "followers") details.unshift("Follows you");
    else if (tab === "following" && user.follows_you) details.unshift("Follows you back");

    return details.join(" · ");
  }

  function renderTabs(counts = {}) {
    tabs.forEach(button => {
      const tab = button.dataset.tab;
      const label = tab[0].toUpperCase() + tab.slice(1);
      const count = counts[tab];
      button.textContent = Number.isInteger(count) ? `${label} (${count})` : label;
      button.classList.toggle("active", tab === currentTab);
    });
  }

  function renderUsers(users) {
    if (!users.length) {
      list.innerHTML = `<p class="empty-state">${tabEmptyMessage(currentTab)}</p>`;
      return;
    }

    list.innerHTML = users.map(user => `
      <div class="friend-row ${user.is_mutual ? "mutual" : ""}" data-user-id="${user.id}">
        <a class="friend-avatar" href="${user.profile_url}">
          ${user.avatar_url
            ? `<img src="${escapeHTML(user.avatar_url)}" alt="${escapeHTML(user.username)} profile picture">`
            : escapeHTML(user.avatar)}
        </a>

        <div class="friend-info">
          <h3>
            <a href="${user.profile_url}">${escapeHTML(user.username)}</a>
            ${user.is_mutual ? '<span class="mutual-tag">Friends</span>' : ""}
          </h3>
          <p>${escapeHTML(userMeta(user, currentTab))}</p>
          ${user.bio ? `<p class="friend-bio">${escapeHTML(user.bio)}</p>` : ""}
        </div>

        <div class="friend-actions">
          <a class="profile-btn" href="${user.profile_url}">Profile</a>
          ${user.is_following
            ? `<button class="decline-btn" data-action="unfollow">Unfollow</button>`
            : `<button class="accept-btn" data-action="follow">${currentTab === "followers" ? "Follow back" : "Follow"}</button>`}
        </div>
      </div>
    `).join("");
  }

  async function loadUsers() {
    const params = new URLSearchParams({ tab: currentTab });
    if (searchQuery) params.set("q", searchQuery);

    const response = await fetch(`/api/friends?${params.toString()}`);
    if (!response.ok) throw new Error("Could not load friends");

    const data = await response.json();
    renderTabs(data.counts || {});
    renderUsers(data.users || []);
  }

  async function setFollowing(userId, shouldFollow) {
    const response = await fetch(`/api/users/${userId}/follow`, {
      method: shouldFollow ? "POST" : "DELETE",
      headers: { "X-CSRFToken": csrfToken },
    });
    const data = await response.json();

    if (!response.ok || data.error) {
      alert(data.error || "Could not update follow status.");
      return;
    }

    await loadUsers();
  }

  tabs.forEach(button => {
    button.addEventListener("click", () => {
      currentTab = button.dataset.tab;
      history.pushState(null, "", `/friends?tab=${currentTab}`);
      loadUsers().catch(() => {
        list.innerHTML = `<p class="empty-state">Unable to load users. Please try again.</p>`;
      });
    });
  });

  searchInput?.addEventListener("input", event => {
    searchQuery = event.target.value.trim();
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      loadUsers().catch(() => {
        list.innerHTML = `<p class="empty-state">Unable to load users. Please try again.</p>`;
      });
    }, 250);
  });

  list.addEventListener("click", event => {
    const actionButton = event.target.closest("[data-action]");
    if (!actionButton) return;

    const row = actionButton.closest(".friend-row");
    const userId = Number(row.dataset.userId);
    setFollowing(userId, actionButton.dataset.action === "follow");
  });

  renderTabs();
  loadUsers().catch(() => {
    list.innerHTML = `<p class="empty-state">Unable to load users. Please try again.</p>`;
  });
});
