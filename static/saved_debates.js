document.addEventListener('DOMContentLoaded', () => {
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const debatesList = document.getElementById('debates-list');
  const emptyState = document.getElementById('empty-state');
  const searchInput = document.getElementById('search-input');
  const filterTags = document.getElementById('filter-tags');

  let debates = Array.isArray(window.SAVED_DEBATES) ? [...window.SAVED_DEBATES] : [];
  let searchQuery = '';
  const activeFilters = new Set();

  if (!debatesList || !emptyState) return;

  function escapeHTML(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function formatNumber(value) {
    return Number(value || 0).toLocaleString();
  }

  function getCategories() {
    return [...new Set(debates.flatMap(debate => debate.tags || []))]
      .filter(Boolean)
      .sort((a, b) => a.localeCompare(b));
  }

  function renderFilterTags() {
    if (!filterTags) return;

    const categories = getCategories();
    filterTags.innerHTML = '';
    filterTags.style.display = categories.length === 0 ? 'none' : 'flex';

    categories.forEach(tag => {
      const button = document.createElement('button');
      button.className = `filter-tag ${activeFilters.has(tag) ? 'active' : ''}`;
      button.dataset.tag = tag;
      button.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
          <line x1="7" y1="7" x2="7.01" y2="7"/>
        </svg>
        ${escapeHTML(tag)}
      `;

      button.addEventListener('click', () => {
        if (activeFilters.has(tag)) {
          activeFilters.delete(tag);
        } else {
          activeFilters.add(tag);
        }

        renderFilterTags();
        renderDebates();
      });

      filterTags.appendChild(button);
    });
  }

  function getFilteredDebates() {
    const query = searchQuery.trim().toLowerCase();

    return debates.filter(debate => {
      const title = (debate.title || '').toLowerCase();
      const description = (debate.description || '').toLowerCase();
      const tags = debate.tags || [];
      const matchesSearch =
        !query ||
        title.includes(query) ||
        description.includes(query) ||
        tags.some(tag => tag.toLowerCase().includes(query));
      const matchesTags =
        activeFilters.size === 0 ||
        tags.some(tag => activeFilters.has(tag));

      return matchesSearch && matchesTags;
    });
  }

  function createDebateCard(debate, index) {
    const agreePercent = debate.total_votes === 0 ? 0 : debate.agree_pct;
    const disagreePercent = debate.total_votes === 0 ? 0 : debate.disagree_pct;
    const showCounts = !debate.is_active;
    const card = document.createElement('article');

    card.className = 'debate-card';
    card.dataset.id = debate.id;
    card.style.animationDelay = `${index * 60}ms`;

    card.innerHTML = `
      <button class="save-btn saved" data-action="bookmark" title="Unsave debate">
        <svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="1.8"
          stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
        </svg>
      </button>

      <div class="card-timer">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
          stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <polyline points="12 6 12 12 16 14"/>
        </svg>
        ${escapeHTML(debate.timer)}
      </div>

      <div class="card-prompt">${escapeHTML(debate.title)}</div>

      <div class="vote-row">
        <button class="vote-btn agree ${debate.user_vote === 'agree' ? 'voted' : ''}" data-vote="agree" ${!debate.is_active ? 'disabled' : ''}>
          <div class="vote-label">Agree</div>
          ${showCounts ? `<div class="vote-count">${formatNumber(debate.agree)}</div><div class="vote-pct">${agreePercent}%</div>` : ''}
        </button>

        <button class="vote-btn disagree ${debate.user_vote === 'disagree' ? 'voted' : ''}" data-vote="disagree" ${!debate.is_active ? 'disabled' : ''}>
          <div class="vote-label">Disagree</div>
          ${showCounts ? `<div class="vote-count">${formatNumber(debate.disagree)}</div><div class="vote-pct">${disagreePercent}%</div>` : ''}
        </button>
      </div>

      <div class="progress-track">
        <div class="progress-fill" style="width:${showCounts ? agreePercent : 50}%"></div>
      </div>

      <div class="card-footer">
        <a href="${escapeHTML(debate.url)}" class="comment-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          ${formatNumber(debate.comments)} Comments
        </a>

        <div class="card-tags">
          ${(debate.tags || []).map(tag => `
            <span class="card-tag">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20.59 13.41 11 3H4v7l9.59 9.59a2 2 0 0 0 2.82 0l4.18-4.18a2 2 0 0 0 0-2.82Z"/>
                <circle cx="7.5" cy="7.5" r=".5"/>
              </svg>
              ${escapeHTML(tag)}
            </span>
          `).join('')}
        </div>
      </div>
    `;

    return card;
  }

  function renderDebates() {
    const filtered = getFilteredDebates();

    debatesList.innerHTML = '';

    if (filtered.length === 0) {
      emptyState.textContent = debates.length === 0
        ? 'No saved debates yet.'
        : 'No saved debates match your search or filters.';
      emptyState.style.display = 'block';
      return;
    }

    emptyState.style.display = 'none';
    filtered.forEach((debate, index) => {
      debatesList.appendChild(createDebateCard(debate, index));
    });
  }

  async function castVote(debateId, side) {
    const debate = debates.find(item => item.id === debateId);
    if (!debate || !debate.is_active) return;

    const formData = new FormData();
    formData.append('vote_type', side);

    const response = await fetch(`/debates/${debateId}/vote`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
      body: formData,
    });
    const data = await response.json();

    if (!response.ok || data.error) {
      alert(data.error || 'Vote failed. Please try again.');
      return;
    }

    if (data.removed) {
      debate[debate.user_vote] -= 1;
      debate.total_votes -= 1;
      debate.user_vote = null;
    } else if (data.changed) {
      const oldSide = debate.user_vote;
      debate[oldSide] -= 1;
      debate[side] += 1;
      debate.user_vote = side;
    } else {
      debate[side] += 1;
      debate.total_votes += 1;
      debate.user_vote = side;
    }

    debate.agree_pct = debate.total_votes === 0
      ? 0
      : Math.round((debate.agree / debate.total_votes) * 1000) / 10;
    debate.disagree_pct = debate.total_votes === 0
      ? 0
      : Math.round((debate.disagree / debate.total_votes) * 1000) / 10;

    renderDebates();
  }

  async function toggleBookmark(debateId) {
    const response = await fetch(`/debates/${debateId}/bookmark`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
    });
    const data = await response.json();

    if (!response.ok) {
      alert(data.error || 'Save failed. Please try again.');
      return;
    }

    if (!data.bookmarked) {
      debates = debates.filter(debate => debate.id !== debateId);
      activeFilters.forEach(tag => {
        if (!getCategories().includes(tag)) activeFilters.delete(tag);
      });
      renderFilterTags();
      renderDebates();
    }
  }

  debatesList.addEventListener('click', event => {
    const bookmarkButton = event.target.closest('[data-action="bookmark"]');
    if (bookmarkButton) {
      event.preventDefault();
      event.stopPropagation();
      const card = bookmarkButton.closest('.debate-card');
      toggleBookmark(Number(card.dataset.id));
      return;
    }

    const voteButton = event.target.closest('[data-vote]');
    if (voteButton) {
      event.preventDefault();
      event.stopPropagation();
      const card = voteButton.closest('.debate-card');
      castVote(Number(card.dataset.id), voteButton.dataset.vote);
      return;
    }

    const card = event.target.closest('.debate-card');
    if (card && !event.target.closest('a')) {
      const debate = debates.find(item => item.id === Number(card.dataset.id));
      if (debate?.url) window.location.href = debate.url;
    }
  });

  searchInput?.addEventListener('input', event => {
    searchQuery = event.target.value;
    renderDebates();
  });

  renderFilterTags();
  renderDebates();
});
