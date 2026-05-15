const USERS = [
    { id: 'argumentking',    name: 'ArgumentKing',    meta: '203 votes · 145 comments', points: 1523, debates: 67, badge: 'Contrarian',  conformity: 28,  color: '#f59e0b' },
    { id: 'consensusbuilder',name: 'ConsensusBuilder',meta: '187 votes · 98 comments',  points: 1345, debates: 51, badge: 'Conformist',  conformity: 89,  color: '#6366f1' },
    { id: 'debatemaster',    name: 'DebateMaster',    meta: '156 votes · 87 comments',  points: 1247, debates: 42, badge: 'Conformist',  conformity: 67,  color: '#2563eb', you: true },
    { id: 'voiceofreason',   name: 'VoiceOfReason',   meta: '167 votes · 79 comments',  points: 1156, debates: 44, badge: 'Conformist',  conformity: 73,  color: '#10b981' },
    { id: 'logicqueen',      name: 'LogicQueen',      meta: '142 votes · 65 comments',  points: 1089, debates: 38, badge: 'Moderate',    conformity: 52,  color: '#ec4899' },
    { id: 'contrarymary',    name: 'ContraryMary',    meta: '128 votes · 72 comments',  points: 987,  debates: 35, badge: 'Contrarian',  conformity: 15,  color: '#ef4444' },
    { id: 'mindchanger',     name: 'MindChanger',     meta: '115 votes · 54 comments',  points: 876,  debates: 29, badge: 'Moderate',    conformity: 45,  color: '#8b5cf6' },
    { id: 'perspectiveseeker',name:'PerspectiveSeeker',meta: '98 votes · 43 comments',  points: 765,  debates: 26, badge: 'Moderate',    conformity: 51,  color: '#14b8a6' },
  ];

  let currentSort = 'points';

  const RANK_ICONS = { 1: '🥇', 2: '🥈', 3: '🥉' };

  function badgeClass(badge) {
    if (badge === 'Conformist')  return 'badge-conformist';
    if (badge === 'Contrarian')  return 'badge-contrarian';
    return 'badge-moderate';
  }

  function badgeIcon(badge) {
    if (badge === 'Conformist')  return '↗';
    if (badge === 'Contrarian')  return '↙';
    return '—';
  }

  function getSorted(sort) {
    const copy = [...USERS];
    if (sort === 'points') {
      return copy.sort((a, b) => b.points - a.points);
    } else {
      // Most distinctive = lowest conformity (most contrarian)
      return copy.sort((a, b) => a.conformity - b.conformity);
    }
  }

  function renderLeaderboard(sort) {
    const sorted = getSorted(sort);
    const body = document.getElementById('leaderboard-body');
    body.innerHTML = '';

    sorted.forEach((user, i) => {
      const rank = i + 1;
      const row = document.createElement('a');
      row.href = `user-profile.html?user=${user.id}`;
      row.className = 'leaderboard-row' + (user.you ? ' you' : '');
      row.style.animationDelay = `${i * 40}ms`;

      row.innerHTML = `
        <div class="rank-cell">
          <span class="rank-icon">${RANK_ICONS[rank] || ''}</span>
          <span class="rank-num">#${rank}</span>
        </div>
        <div class="user-cell">
          <div class="avatar" style="background:${user.color}">${user.name[0]}</div>
          <div class="user-info">
            <div class="username">
              ${user.name}
              ${user.you ? '<span class="you-badge">You</span>' : ''}
            </div>
            <div class="user-meta">${user.meta}</div>
          </div>
        </div>
        <div class="points-cell">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
          ${user.points.toLocaleString()}
        </div>
        <div class="debates-cell">${user.debates}</div>
        <div>
          <span class="badge-pill ${badgeClass(user.badge)}">
            ${badgeIcon(user.badge)} ${user.badge}
          </span>
        </div>
        <div class="conformity-cell">
          <span class="conformity-pct">${user.conformity}%</span>
          <div class="conf-bar-track">
            <div class="conf-bar-fill" style="width:${user.conformity}%"></div>
          </div>
        </div>
      `;

      body.appendChild(row);
    });
  }

  function setSort(sort, btn) {
    currentSort = sort;
    document.querySelectorAll('.sort-tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    renderLeaderboard(sort);
  }

  renderLeaderboard('points');