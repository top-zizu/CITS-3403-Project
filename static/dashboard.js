document.addEventListener("DOMContentLoaded", () => {
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const filterButtons = document.querySelectorAll(".filters button");
  const debateContainer = document.querySelector(".debates");
  let debates = [];
  let currentFilter = "all";
  let searchQuery = "";

  if (!debateContainer) return;

  function escapeHTML(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function formatNumber(value) {
    return Number(value || 0).toLocaleString();
  }

  function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
  }

  async function loadDashboardStats() {
    const response = await fetch("/api/dashboard");
    if (!response.ok) throw new Error("Could not load dashboard stats");

    const data = await response.json();
    const stats = data.stats || {};

    setText("stat-points", formatNumber(stats.points));
    setText("stat-debates", formatNumber(stats.debates));
    setText("stat-comments", formatNumber(stats.comments));
    setText("stat-win-rate", `${formatNumber(stats.win_rate)}%`);
  }

  async function loadDebates() {
    const response = await fetch("/api/debates?sort=newest");
    if (!response.ok) throw new Error("Could not load debates");

    const data = await response.json();
    debates = data.debates || [];
    renderDebates();
  }

  function highlight(text, query) {
    if (!query) return escapeHTML(text);
    const escaped = escapeHTML(text);
    const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return escaped.replace(new RegExp(`(${escapedQuery})`, "gi"), '<mark class="search-highlight">$1</mark>');
  }

  function renderDebates() {
    const query = searchQuery.trim().toLowerCase();

    let filtered = currentFilter === "all"
      ? debates
      : debates.filter(debate => debate.status === currentFilter);

    if (query) {
      filtered = filtered.filter(debate =>
        debate.title.toLowerCase().includes(query) ||
        (debate.tags || []).some(tag => tag.toLowerCase().includes(query))
      );
    }

    if (filtered.length === 0) {
      debateContainer.innerHTML = query
        ? `<p class="empty-state">No debates match "<strong>${escapeHTML(query)}</strong>".</p>`
        : `<p class="empty-state">No debates to show.</p>`;
      return;
    }

    debateContainer.innerHTML = filtered.map(debate => {
      const agreePercent = debate.total_votes === 0 ? 0 : debate.agree_pct;
      const disagreePercent = debate.total_votes === 0 ? 0 : debate.disagree_pct;
      const hasVoted = debate.user_vote !== null;

      return `
        <article class="debate-card" data-id="${debate.id}" data-status="${debate.status}">
          <button class="save-btn ${debate.saved ? "saved" : ""}" data-action="bookmark" title="${debate.saved ? "Unsave debate" : "Save debate"}">
            <svg viewBox="0 0 24 24" fill="${debate.saved ? "currentColor" : "none"}" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
            </svg>
          </button>

          <p class="time">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            ${escapeHTML(debate.timer)}
          </p>

          <h2>${highlight(debate.title, searchQuery.trim())}</h2>

          <div class="votes">
            <button class="agree ${debate.user_vote === "agree" ? "selected-vote" : ""}" data-vote="agree" ${!debate.is_active || hasVoted ? "disabled" : ""}>
              <p>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M7 10v11"/>
                  <path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z"/>
                </svg>
                Agree
              </p>
              <strong>${formatNumber(debate.agree)}</strong>
              <div>${agreePercent}%</div>
            </button>

            <button class="disagree ${debate.user_vote === "disagree" ? "selected-vote" : ""}" data-vote="disagree" ${!debate.is_active || hasVoted ? "disabled" : ""}>
              <p>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17 14V3"/>
                  <path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22h0a3.13 3.13 0 0 1-3-3.88Z"/>
                </svg>
                Disagree
              </p>
              <strong>${formatNumber(debate.disagree)}</strong>
              <div>${disagreePercent}%</div>
            </button>
          </div>

          <div class="progress-bar">
            <div class="agree-bar" style="width: ${agreePercent}%"></div>
            <div class="disagree-bar" style="width: ${disagreePercent}%"></div>
          </div>

          <div class="card-footer">
            <a class="comments-btn" href="${debate.url}">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              <span class="comment-count">${formatNumber(debate.comments)}</span> Comments
            </a>

            <div class="card-tags">
              ${debate.tags.map(tag => `
                <span class="card-tag">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                    stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20.59 13.41 11 3H4v7l9.59 9.59a2 2 0 0 0 2.82 0l4.18-4.18a2 2 0 0 0 0-2.82Z"/>
                    <circle cx="7.5" cy="7.5" r=".5"/>
                  </svg>
                  ${escapeHTML(tag)}
                </span>
              `).join("")}
            </div>
          </div>
        </article>
      `;
    }).join("");
  }

  async function castVote(debateId, side) {
    const debate = debates.find(item => item.id === debateId);
    if (!debate || !debate.is_active || debate.user_vote) return;

    const formData = new FormData();
    formData.append("vote_type", side);

    const response = await fetch(`/debates/${debateId}/vote`, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken },
      body: formData,
    });
    const data = await response.json();

    if (!response.ok || data.error) {
      alert(data.error || "Vote failed. Please try again.");
      return;
    }

    debate[side] += 1;
    debate.total_votes += 1;
    debate.user_vote = side;
    debate.agree_pct = debate.total_votes === 0 ? 0 : Math.round((debate.agree / debate.total_votes) * 1000) / 10;
    debate.disagree_pct = debate.total_votes === 0 ? 0 : Math.round((debate.disagree / debate.total_votes) * 1000) / 10;
    renderDebates();
    loadDashboardStats().catch(() => {});
  }

  async function toggleBookmark(debateId) {
    const debate = debates.find(item => item.id === debateId);
    if (!debate) return;

    const response = await fetch(`/debates/${debateId}/bookmark`, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken },
    });
    const data = await response.json();

    if (!response.ok) {
      alert(data.error || "Save failed. Please try again.");
      return;
    }

    debate.saved = data.bookmarked;
    renderDebates();
  }

  filterButtons.forEach(button => {
    button.addEventListener("click", () => {
      filterButtons.forEach(btn => btn.classList.remove("active"));
      button.classList.add("active");

      currentFilter = button.dataset.filter || "all";
      renderDebates();
    });
  });

  debateContainer.addEventListener("click", event => {
    const bookmarkButton = event.target.closest('[data-action="bookmark"]');
    if (bookmarkButton) {
      const card = bookmarkButton.closest(".debate-card");
      toggleBookmark(Number(card.dataset.id));
      return;
    }

    const voteButton = event.target.closest("[data-vote]");
    if (!voteButton) return;

    const card = voteButton.closest(".debate-card");
    castVote(Number(card.dataset.id), voteButton.dataset.vote);
  });

  const searchInput = document.getElementById("debate-search");

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      searchQuery = searchInput.value;
      renderDebates();
    });
  }

  Promise.all([loadDashboardStats(), loadDebates()]).catch(() => {
    debateContainer.innerHTML = `<p class="empty-state">Unable to load dashboard data. Please try again.</p>`;
  });
});
