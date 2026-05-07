const isGuest = document.body.dataset.guest === 'true';

const DEBATES = [
  {
    id: 1,
    prompt: 'Universal basic income should be implemented globally',
    timer: 'Ends in about 12 hours',
    agree: 723,
    disagree: 556,
    comments: [],
    tags: ['politics', 'economics'],
    voted: null,
  },
  {
    id: 2,
    prompt: 'Artificial Intelligence will create more jobs than it destroys',
    timer: 'Ends in about 18 hours',
    agree: 445,
    disagree: 678,
    comments: [],
    tags: ['technology', 'work'],
    voted: null,
  },
  {
    id: 3,
    prompt: 'Climate change is the most pressing issue of our time',
    timer: 'Ends in 1 day',
    agree: 892,
    disagree: 234,
    comments: [],
    tags: ['politics', 'environment'],
    voted: null,
  },
];

const ALL_TAGS = ['politics', 'economics', 'technology', 'work', 'environment'];

const activeFilters = new Set();
let searchQuery = '';

const filterTags = document.getElementById('filter-tags');
const searchInput = document.getElementById('search-input');
const debatesList = document.getElementById('debates-list');
const emptyState = document.getElementById('empty-state');

function showLoginPopup(message) {
  const popup = document.getElementById('login-popup');
  const messageBox = document.getElementById('login-popup-message');

  if (!popup || !messageBox) return;

  messageBox.textContent = message;
  popup.classList.remove('hidden');
}

function closeLoginPopup() {
  const popup = document.getElementById('login-popup');
  if (popup) popup.classList.add('hidden');
}

function renderFilterTags() {
  filterTags.innerHTML = '';

  ALL_TAGS.forEach(tag => {
    const button = document.createElement('button');
    button.className = 'filter-tag';
    button.textContent = tag;

    button.addEventListener('click', () => {
      if (activeFilters.has(tag)) {
        activeFilters.delete(tag);
        button.classList.remove('active');
      } else {
        activeFilters.add(tag);
        button.classList.add('active');
      }

      renderDebates();
    });

    filterTags.appendChild(button);
  });
}

function getFilteredDebates() {
  return DEBATES.filter(debate => {
    const matchesSearch =
      searchQuery === '' ||
      debate.prompt.toLowerCase().includes(searchQuery);

    const matchesTags =
      activeFilters.size === 0 ||
      debate.tags.some(tag => activeFilters.has(tag));

    return matchesSearch && matchesTags;
  });
}

function renderDebates() {
  const filteredDebates = getFilteredDebates();

  debatesList.innerHTML = '';

  if (filteredDebates.length === 0) {
    emptyState.style.display = 'block';
    return;
  }

  emptyState.style.display = 'none';

  filteredDebates.forEach(debate => {
    debatesList.appendChild(createDebateCard(debate));
  });
}

function createDebateCard(debate) {
  const totalVotes = debate.agree + debate.disagree;
  const agreePercent =
    totalVotes === 0 ? 50 : Math.round((debate.agree / totalVotes) * 100);
  const disagreePercent = 100 - agreePercent;

  const card = document.createElement('article');
  card.className = 'debate-card';
  card.dataset.id = debate.id;

  card.innerHTML = `
    <div class="debate-meta">${debate.timer}</div>

    <h3 class="debate-title">${debate.prompt}</h3>

    <div class="vote-row">
      <button class="vote-box agree-box ${debate.voted === 'agree' ? 'selected' : ''}" data-vote="agree">
        <span class="vote-label">Agree</span>
        <span class="vote-count">${debate.agree.toLocaleString()}</span>
        <span class="vote-percent">${agreePercent}%</span>
      </button>

      <button class="vote-box disagree-box ${debate.voted === 'disagree' ? 'selected' : ''}" data-vote="disagree">
        <span class="vote-label">Disagree</span>
        <span class="vote-count">${debate.disagree.toLocaleString()}</span>
        <span class="vote-percent">${disagreePercent}%</span>
      </button>
    </div>

    <div class="vote-progress">
      <div class="agree-progress" style="width: ${agreePercent}%"></div>
    </div>

    <div class="debate-footer">
      <button class="comments-toggle">
        Comments <span class="comment-count">${debate.comments.length}</span>
      </button>

      <div class="debate-tags">
        ${debate.tags.map(tag => `<span class="debate-tag">${tag}</span>`).join('')}
      </div>
    </div>

    <div class="comments-section hidden">
      <div class="comments-list">
        ${debate.comments.length === 0 ? '<p class="no-comments">No comments yet.</p>' : ''}
        ${debate.comments.map(comment => `
          <div class="comment ${comment.stance}">
            <strong>${comment.stance}</strong>: ${comment.text}
          </div>
        `).join('')}
      </div>

      <form class="comment-form">
        <textarea
          class="comment-input"
          maxlength="250"
          placeholder="Write a comment..."
        ></textarea>
        <button type="submit">Post</button>
      </form>
    </div>
  `;

  return card;
}

function handleVote(card, side) {
  if (isGuest) {
    showLoginPopup('You need to log in to vote on this debate.');
    return;
  }

  const debateId = Number(card.dataset.id);
  const debate = DEBATES.find(item => item.id === debateId);

  if (!debate || debate.voted === side) return;

  if (debate.voted === 'agree') debate.agree--;
  if (debate.voted === 'disagree') debate.disagree--;

  debate[side]++;
  debate.voted = side;

  renderDebates();
}

function handleCommentSubmit(form) {
  if (isGuest) {
    showLoginPopup('You need to log in to comment on this debate.');
    return;
  }

  const card = form.closest('.debate-card');
  const debateId = Number(card.dataset.id);
  const debate = DEBATES.find(item => item.id === debateId);
  const input = form.querySelector('.comment-input');

  if (!debate || input.value.trim() === '') return;

  debate.comments.push({
    text: input.value.trim(),
    stance: debate.voted || 'neutral',
  });

  input.value = '';
  renderDebates();
}

document.addEventListener('click', event => {
  const voteBox = event.target.closest('.vote-box');
  const commentsToggle = event.target.closest('.comments-toggle');
  const closePopup = event.target.closest('#close-popup');
  const popupBackground = event.target.id === 'login-popup';

  if (voteBox) {
    const card = voteBox.closest('.debate-card');
    handleVote(card, voteBox.dataset.vote);
  }

  if (commentsToggle) {
    const card = commentsToggle.closest('.debate-card');
    card.querySelector('.comments-section').classList.toggle('hidden');
  }

  if (closePopup || popupBackground) {
    closeLoginPopup();
  }
});

document.addEventListener('submit', event => {
  const form = event.target.closest('.comment-form');

  if (form) {
    event.preventDefault();
    handleCommentSubmit(form);
  }
});

searchInput.addEventListener('input', event => {
  searchQuery = event.target.value.toLowerCase().trim();
  renderDebates();
});

renderFilterTags();
renderDebates();