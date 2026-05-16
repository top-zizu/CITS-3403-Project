let currentSort = 'points';
let currentUsers = [];

const RANK_ICONS = { 1: '&#129351;', 2: '&#129352;', 3: '&#129353;' };

function escapeHTML(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function badgeClass(badge) {
  if (badge === 'Conformist') return 'badge-conformist';
  if (badge === 'Contrarian') return 'badge-contrarian';
  return 'badge-moderate';
}

function badgeIcon(badge) {
  if (badge === 'Conformist') return '&#8599;';
  if (badge === 'Contrarian') return '&#8601;';
  return '&mdash;';
}

function showLeaderboardMessage(message) {
  const body = document.getElementById('leaderboard-body');
  if (!body) return;

  body.innerHTML = `
    <div class="leaderboard-row">
      <div class="rank-cell"></div>
      <div class="user-cell">${escapeHTML(message)}</div>
      <div></div>
      <div></div>
      <div></div>
      <div></div>
    </div>
  `;
}

function renderLeaderboard(users) {
  const body = document.getElementById('leaderboard-body');
  if (!body) return;

  if (!users.length) {
    showLeaderboardMessage('No users to rank yet.');
    return;
  }

  body.innerHTML = '';

  users.forEach((user, i) => {
    const rank = i + 1;
    const row = document.createElement('a');
    row.href = user.profile_url || `/profile/${encodeURIComponent(user.username)}`;
    row.className = `leaderboard-row${user.you ? ' you' : ''}`;
    row.style.animationDelay = `${i * 40}ms`;

    row.innerHTML = `
      <div class="rank-cell">
        <span class="rank-icon">${RANK_ICONS[rank] || ''}</span>
        <span class="rank-num">#${rank}</span>
      </div>
      <div class="user-cell">
        <div class="avatar" style="background:${escapeHTML(user.color)}">${escapeHTML((user.name || user.username || '?').slice(0, 1).toUpperCase())}</div>
        <div class="user-info">
          <div class="username">
            ${escapeHTML(user.name || user.username)}
            ${user.you ? '<span class="you-badge">You</span>' : ''}
          </div>
          <div class="user-meta">${escapeHTML(user.meta)}</div>
        </div>
      </div>
      <div class="points-cell">
        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
        ${Number(user.points || 0).toLocaleString()}
      </div>
      <div class="debates-cell">${Number(user.debates || 0).toLocaleString()}</div>
      <div>
        <span class="badge-pill ${badgeClass(user.badge)}">
          ${badgeIcon(user.badge)} ${escapeHTML(user.badge)}
        </span>
      </div>
      <div class="conformity-cell">
        <span class="conformity-pct">${Number(user.conformity || 0).toLocaleString()}%</span>
        <div class="conf-bar-track">
          <div class="conf-bar-fill" style="width:${Math.max(0, Math.min(100, Number(user.conformity || 0)))}%"></div>
        </div>
      </div>
    `;

    body.appendChild(row);
  });
}

async function loadLeaderboard(sort = currentSort) {
  currentSort = sort;
  showLeaderboardMessage('Loading leaderboard...');

  const params = new URLSearchParams({ sort });
  const response = await fetch(`/api/leaderboard?${params.toString()}`);

  if (!response.ok) {
    throw new Error('Could not load leaderboard');
  }

  const data = await response.json();
  currentUsers = data.users || [];
  renderLeaderboard(currentUsers);
}

function setSort(sort, btn) {
  currentSort = sort;
  document.querySelectorAll('.sort-tab').forEach(tab => {
    tab.classList.toggle('active', tab === btn);
  });

  loadLeaderboard(sort).catch(() => {
    showLeaderboardMessage('Unable to load leaderboard data. Please try again.');
  });
}

window.setSort = setSort;

document.addEventListener('DOMContentLoaded', () => {
  loadLeaderboard('points').catch(() => {
    showLeaderboardMessage('Unable to load leaderboard data. Please try again.');
  });
});
