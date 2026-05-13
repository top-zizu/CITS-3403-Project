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

  // Returns a short action label and a matching SVG icon for each activity type
  function getActionMeta(type) {
    switch (type) {
      case "vote":
        return {
          label: "voted on",
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M7 10v11"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z"/>
          </svg>`
        };
      case "comment":
        return {
          label: "commented on",
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>`
        };
      case "create":
        return {
          label: "created",
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
          </svg>`
        };
      case "bookmark":
        return {
          label: "saved",
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
          </svg>`
        };
      default:
        return {
          label: "interacted with",
          icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
          </svg>`
        };
    }
  }

  async function loadFriendActivity() {
    const container = document.getElementById("friend-activity");

    try {
      const res = await fetch("/api/activity/friends");
      if (!res.ok) throw new Error("Failed to fetch");

      const data = await res.json();
      const activities = (data.activities || data || []).slice(0, 6);

      if (activities.length === 0) {
        container.innerHTML = `<p class="activity" style="color: var(--muted); font-size: 0.9rem;">No recent activity from friends.</p>`;
        return;
      }

      // Each activity object is expected to have:
      //   username   – friend's display name
      //   type       – "vote" | "comment" | "create" | "bookmark"
      //   debate_title – title of the debate
      //   debate_url   – URL to the debate detail page
      container.innerHTML = activities.map(item => {
        const { label, icon } = getActionMeta(item.type);
        const initial = (item.username || "?")[0].toUpperCase();

        return `
          <a href="${escapeHTML(item.debate_url)}" class="activity-pill">
            <div class="pill-avatar">${escapeHTML(initial)}</div>
            ${icon}
            <span class="pill-text">
              <strong>${escapeHTML(item.username)}</strong>
              ${label}
              <em>"${escapeHTML(item.debate_title)}"</em>
            </span>
          </a>
        `;
      }).join("");

    } catch (err) {
      console.error("Error loading friend activity:", err);
      container.innerHTML = `<p class="activity" style="color: var(--muted); font-size: 0.9rem;">Could not load friend activity.</p>`;
    }
  }

  async function loadForYouDebates() {
    const container = document.getElementById("for-you-debates");

    try {
      const res = await fetch("/api/debates?sort=newest");
      if (!res.ok) throw new Error("Failed to fetch");

      const data = await res.json();
      const debates = (data.debates || []).slice(0, 5);

      if (debates.length === 0) {
        container.innerHTML = `<p class="activity" style="color: var(--muted); font-size: 0.9rem;">No debates to show right now.</p>`;
        return;
      }

      container.innerHTML = debates.map(debate => {
        const topic = (debate.tags && debate.tags.length > 0) ? debate.tags[0] : "General";
        const totalVotes = debate.total_votes || 0;
        const comments = debate.comments || 0;
        const status = debate.is_active ? "Active" : "Ended";

        return `
          <a href="${escapeHTML(debate.url)}" class="debate-preview">
            <span class="topic">${escapeHTML(topic)}</span>
            <h3>${escapeHTML(debate.title)}</h3>
            <p>${formatNumber(totalVotes)} vote${totalVotes !== 1 ? "s" : ""} · ${formatNumber(comments)} comment${comments !== 1 ? "s" : ""} · ${status}</p>
          </a>
        `;
      }).join("");

    } catch (err) {
      console.error("Error loading debates:", err);
      container.innerHTML = `<p class="activity" style="color: var(--muted); font-size: 0.9rem;">Could not load debates.</p>`;
    }
  }

  async function loadHomeStats() {
    try {
      const res = await fetch("/api/dashboard");
      if (!res.ok) return;

      const data = await res.json();
      const stats = data.stats || {};

      const pointsEl   = document.getElementById("home-stat-points");
      const debatesEl  = document.getElementById("home-stat-debates");
      const commentsEl = document.getElementById("home-stat-comments");

      if (pointsEl   && stats.points   !== undefined) pointsEl.textContent   = formatNumber(stats.points);
      if (debatesEl  && stats.debates  !== undefined) debatesEl.textContent  = formatNumber(stats.debates);
      if (commentsEl && stats.comments !== undefined) commentsEl.textContent = formatNumber(stats.comments);
    } catch (err) {
      console.warn("Could not load home stats:", err);
    }
  }

  loadForYouDebates();
  loadHomeStats();
  loadFriendActivity();