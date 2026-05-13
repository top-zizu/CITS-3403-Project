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
          // Use the first tag as the topic label, fall back to "General"
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