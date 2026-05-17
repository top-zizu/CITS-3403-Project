const isGuest = document.body.dataset.guest === 'true';
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';

let debates = [];
let categories = [];
const initialParams = new URLSearchParams(window.location.search);
const initialTag = initialParams.get('tag') || initialParams.get('category') || '';
const initialStatus = initialParams.get('status') === 'ended' ? 'closed' : initialParams.get('status');
const activeFilters = new Set(initialTag ? [initialTag] : []);
let searchQuery = initialParams.get('q') || '';
let currentStatus = ['active', 'closed'].includes(initialStatus) ? initialStatus : '';
let searchTimer = null;

const filterTags = document.getElementById('filter-tags');
const statusButtons = document.querySelectorAll('#status-filters [data-status]');
const searchInput = document.getElementById('search-input');
const debatesList = document.getElementById('debates-list');
const emptyState = document.getElementById('empty-state');

if (searchInput) {
  searchInput.value = searchQuery;
}

function escapeHTML(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function showLoginPopup(message) {
  const popup = document.getElementById('login-popup');
  const messageBox = document.getElementById('login-popup-message');

  if (!popup || !messageBox) {
    window.location.href = '/login';
    return;
  }

  messageBox.textContent = message;
  popup.classList.remove('hidden');
}

function closeLoginPopup() {
  const popup = document.getElementById('login-popup');
  if (popup) popup.classList.add('hidden');
}

function renderStatusFilters() {
  statusButtons.forEach(button => {
    button.classList.toggle('active', (button.dataset.status || '') === currentStatus);
  });
}

function renderFilterTags() {
  if (!filterTags) return;

  filterTags.innerHTML = '';

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

      updateFilterUrl();
      renderFilterTags();
      renderDebates();

    });

    filterTags.appendChild(button);
  });
}

function updateFilterUrl() {
  const params = new URLSearchParams(window.location.search);
  const selectedTags = [...activeFilters];

  params.delete('category');

  if (selectedTags.length === 1) {
    params.set('tag', selectedTags[0]);
  } else {
    params.delete('tag');
  }

  if (searchQuery) {
    params.set('q', searchQuery);
  } else {
    params.delete('q');
  }

  if (currentStatus) {
    params.set('status', currentStatus);
  } else {
    params.delete('status');
  }

  const queryString = params.toString();
  window.history.replaceState(null, '', queryString ? `/search?${queryString}` : '/search');
}

function getFilteredDebates() {

  if (activeFilters.size === 0) {
    return debates;
  }

  return debates.filter(debate =>
    debate.tags.some(tag => activeFilters.has(tag))
  );
}

function renderDebates() {

  if (!debatesList || !emptyState) return;

  const filteredDebates = getFilteredDebates();

  debatesList.innerHTML = '';

  if (filteredDebates.length === 0) {
    emptyState.style.display = 'block';
    return;
  }

  emptyState.style.display = 'none';

  filteredDebates.forEach((debate, index) => {
    debatesList.appendChild(createDebateCard(debate, index));
  });
}

function createDebateCard(debate, index) {

  const agreePercent =
    debate.total_votes === 0 ? 0 : debate.agree_pct;

  const disagreePercent =
    debate.total_votes === 0 ? 0 : debate.disagree_pct;

  const showCounts = !debate.is_active;

  const card = document.createElement('article');

  card.className = 'debate-card';
  card.dataset.id = debate.id;
  card.style.animationDelay = `${index * 60}ms`;

  card.innerHTML = `
    <button
      class="save-btn ${debate.saved ? 'saved' : ''}"
      data-action="bookmark"
      title="${debate.saved ? 'Unsave debate' : 'Save debate'}"
    >
      <svg
        viewBox="0 0 24 24"
        fill="${debate.saved ? 'currentColor' : 'none'}"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
      </svg>
    </button>

    <div class="card-timer">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <circle cx="12" cy="12" r="10"/>
        <polyline points="12 6 12 12 16 14"/>
      </svg>

      ${escapeHTML(debate.timer)}
    </div>

    <div class="card-prompt">
      ${escapeHTML(debate.title)}
    </div>

    <div class="vote-row">

      <button
        class="vote-btn agree ${debate.user_vote === 'agree' ? 'voted' : ''}"
        data-vote="agree"
        ${!debate.is_active ? 'disabled' : ''}
      >
        <div class="vote-label">Agree</div>

        ${showCounts
          ? `
            <div class="vote-count">
              ${debate.agree.toLocaleString()}
            </div>

            <div class="vote-pct">
              ${agreePercent}%
            </div>
          `
          : ''
        }
      </button>

      <button
        class="vote-btn disagree ${debate.user_vote === 'disagree' ? 'voted' : ''}"
        data-vote="disagree"
        ${!debate.is_active ? 'disabled' : ''}
      >
        <div class="vote-label">Disagree</div>

        ${showCounts
          ? `
            <div class="vote-count">
              ${debate.disagree.toLocaleString()}
            </div>

            <div class="vote-pct">
              ${disagreePercent}%
            </div>
          `
          : ''
        }
      </button>

    </div>

    <div class="progress-track">
      <div
        class="progress-fill"
        style="width: ${showCounts ? agreePercent : 50}%"
      ></div>
    </div>

    <div class="card-footer">

      <a
        href="#"
        class="comment-link"
        data-action="comments"
      >
        <svg
          width="14"
          height="14"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>

        <span>${debate.comments}</span>
        <span>Comments</span>
      </a>

      <div class="card-tags">

        ${debate.tags.map(tag => `
          <span class="card-tag">

            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M20.59 13.41 11 3H4v7l9.59 9.59a2 2 0 0 0 2.82 0l4.18-4.18a2 2 0 0 0 0-2.82z"></path>
              <line x1="7" y1="7" x2="7.01" y2="7"></line>
            </svg>

            ${escapeHTML(tag)}

          </span>
        `).join('')}

      </div>

    </div>
  `;

  card.addEventListener('click', event => {

    if (
      event.target.closest('button') ||
      event.target.closest('a')
    ) {
      return;
    }

    if (isGuest) {
      showLoginPopup('You need to log in to view this debate.');
      return;
    }

    window.location.href = debate.url;

  });

  return card;
}

async function loadDebates() {

  const params = new URLSearchParams();

  if (searchQuery) {
    params.set('q', searchQuery);
  }

  if (currentStatus) {
    params.set('status', currentStatus);
  }

  const response = await fetch(`/api/debates?${params.toString()}`);

  if (!response.ok) {
    throw new Error('Could not load debates');
  }

  const data = await response.json();

  debates = data.debates || [];
  categories = data.categories || [];

  renderFilterTags();
  renderDebates();
}

async function vote(debateId, side) {

  const debate = debates.find(item => item.id === debateId);

  if (!debate || !debate.is_active) return;

  if (isGuest) {
    showLoginPopup('You need to log in to vote on this debate.');
    return;
  }

  const formData = new FormData();

  formData.append('vote_type', side);

  const response = await fetch(`/debates/${debateId}/vote`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken
    },
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

  debate.agree_pct =
    debate.total_votes === 0
      ? 0
      : Math.round((debate.agree / debate.total_votes) * 1000) / 10;

  debate.disagree_pct =
    debate.total_votes === 0
      ? 0
      : Math.round((debate.disagree / debate.total_votes) * 1000) / 10;

  renderDebates();
}

async function toggleBookmark(debateId) {

  if (isGuest) {
    showLoginPopup('You need to log in to save debates.');
    return;
  }

  const debate = debates.find(item => item.id === debateId);

  if (!debate) return;

  const response = await fetch(`/debates/${debateId}/bookmark`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken
    },
  });

  const data = await response.json();

  if (!response.ok) {
    alert(data.error || 'Save failed. Please try again.');
    return;
  }

  debate.saved = data.bookmarked;

  renderDebates();
}

document.addEventListener('click', event => {

  const voteBtn =
    event.target.closest('.vote-btn');

  const bookmarkBtn =
    event.target.closest('[data-action="bookmark"]');

  const commentsLink =
    event.target.closest('[data-action="comments"]');

  const closePopup =
    event.target.closest('#close-popup');

  const popupBackground =
    event.target.id === 'login-popup';

  if (voteBtn) {

    const card = voteBtn.closest('.debate-card');

    vote(
      Number(card.dataset.id),
      voteBtn.dataset.vote
    );
  }

  if (bookmarkBtn) {

    const card = bookmarkBtn.closest('.debate-card');

    toggleBookmark(
      Number(card.dataset.id)
    );
  }

  if (commentsLink) {

    event.preventDefault();

    if (isGuest) {
      showLoginPopup('You need to log in to comment on this debate.');
      return;
    }

    const card =
      commentsLink.closest('.debate-card');

    const debate =
      debates.find(item =>
        item.id === Number(card.dataset.id)
      );

    if (debate) {
      window.location.href = debate.url;
    }
  }

  if (closePopup || popupBackground) {
    closeLoginPopup();
  }
});

statusButtons.forEach(button => {
  button.addEventListener('click', () => {
    currentStatus = button.dataset.status || '';
    renderStatusFilters();
    updateFilterUrl();

    loadDebates().catch(() => {
      debatesList.innerHTML = '';
      emptyState.textContent = 'Unable to load debates. Please try again.';
      emptyState.style.display = 'block';
    });
  });
});

searchInput?.addEventListener('input', event => {

  searchQuery = event.target.value.trim();
  updateFilterUrl();

  clearTimeout(searchTimer);

  searchTimer = setTimeout(() => {

    loadDebates().catch(() => {

      debatesList.innerHTML = '';

      emptyState.textContent =
        'Unable to load debates. Please try again.';

      emptyState.style.display = 'block';
    });

  }, 250);
});

renderStatusFilters();

loadDebates().catch(() => {

  if (!debatesList || !emptyState) return;

  debatesList.innerHTML = '';

  emptyState.textContent =
    'Unable to load debates. Please try again.';

  emptyState.style.display = 'block';
});
