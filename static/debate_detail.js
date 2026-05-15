 /* ── Constants injected from Flask ── */
  const DEBATE_ID   = {{ debate.id }};
  const IS_ACTIVE   = {{ 'true' if debate.is_active else 'false' }};
  const IS_REVEALED = {{ 'true' if vote_data.revealed else 'false' }};
  const CSRF_TOKEN  = document.querySelector('meta[name="csrf-token"]').content;

  /* ── Vote state ── */
  let activeCommentFilter = 'blue';
  let voted   = {{ 'true' if user_vote else 'false' }};
  let votedSide = {{ ('"' + user_vote.vote_type + '"') | safe if user_vote else 'null' }};
  let agree   = {{ debate.agree_votes }};
  let disagree = {{ debate.disagree_votes }};

  /* ── Initial comments from DB ── */
  const INITIAL_COMMENTS = [
    {% for c in comments %}
    {
      id: {{ c.id }},
      author: {{ c.author.username | tojson }},
      stance: 'neutral',
      time: {{ c.created_at.strftime('%d %b %Y, %H:%M') | tojson }},
      text: {{ c.content | tojson }},
      likes: {{ c.likes | length }},
      liked: false,
      replies: [
        {% for r in c.replies %}
        {
          id: {{ r.id }},
          author: {{ r.author.username | tojson }},
          stance: 'neutral',
          time: {{ r.created_at.strftime('%d %b %Y, %H:%M') | tojson }},
          text: {{ r.content | tojson }},
          likes: {{ r.likes | length }},
          liked: false,
        },
        {% endfor %}
      ]
    },
    {% endfor %}
  ];

  let comments = JSON.parse(JSON.stringify(INITIAL_COMMENTS));
  let nextId   = Date.now();

  /* ── Stance tabs ── */
  function setStance(s, btn) {
    activeCommentFilter = s;
    document.querySelectorAll('.stance-tab').forEach(t => t.classList.remove('active'));
    btn.classList.add('active');
    renderComments();
  }

  /* ── Vote — calls Flask AJAX ── */
  function castVote(side) {
    if (!IS_ACTIVE) { alert('This debate has closed — voting is no longer allowed.'); return; }

    fetch(`/debates/${DEBATE_ID}/vote`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': CSRF_TOKEN,
      },
      body: `vote_type=${side}`,
    })
    .then(r => r.json())
    .then(data => {
      if (data.error) { alert(data.error); return; }
      if (data.removed) {
        if (side === 'agree') agree--;
        else disagree--;
        voted = false;
        votedSide = null;
        document.getElementById('agree-panel').classList.remove('voted');
        document.getElementById('disagree-panel').classList.remove('voted');
        return;
      }
      if (data.changed) {
        if (votedSide === 'agree') agree--;
        else disagree--;
      }
      voted     = true;
      votedSide = side;
      if (side === 'agree') agree++;
      else disagree++;
      document.getElementById('agree-panel').classList.toggle('voted', side === 'agree');
      document.getElementById('disagree-panel').classList.toggle('voted', side === 'disagree');
    })
    .catch(() => alert('Something went wrong. Please try again.'));
  }

  /* ── Bookmark — calls Flask AJAX ── */
  function toggleBookmark() {
    fetch(`/debates/${DEBATE_ID}/bookmark`, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF_TOKEN },
    })
    .then(r => r.json())
    .then(data => {
      const btn = document.getElementById('bookmark-btn');
      const svg = btn.querySelector('svg');
      if (data.bookmarked) {
        svg.setAttribute('fill', 'currentColor');
        btn.style.color = 'var(--accent)';
        btn.title = 'Bookmarked';
      } else {
        svg.setAttribute('fill', 'none');
        btn.style.color = '';
        btn.title = 'Bookmark';
      }
    })
    .catch(() => alert('Something went wrong.'));
  }

  /* ── Post comment — calls Flask AJAX ── */
  function postComment() {
    const input = document.getElementById('comment-input');
    const text  = input.value.trim();
    if (!text) return;

    fetch(`/debates/${DEBATE_ID}/comments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': CSRF_TOKEN,
      },
      body: `content=${encodeURIComponent(text)}`,
    })
    .then(r => r.json())
    .then(data => {
      if (data.error) { alert(data.error); return; }
      comments.unshift({
        id: data.comment_id,
        author: data.username,
        stance: data.stance,
        time: data.created_at,
        text: data.content,
        likes: 0,
        liked: false,
        replies: [],
      });
      input.value = '';
      renderComments();
    })
    .catch(() => alert('Something went wrong.'));
  }

  /* ── Post reply — calls Flask AJAX ── */
  function postReply(commentId) {
    const input = document.getElementById('reply-input-' + commentId);
    const text  = input.value.trim();
    if (!text) return;

    fetch(`/comments/${commentId}/reply`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': CSRF_TOKEN,
      },
      body: `content=${encodeURIComponent(text)}`,
    })
    .then(r => r.json())
    .then(data => {
      if (data.error) { alert(data.error); return; }
      const parent = comments.find(c => c.id === commentId);
      if (parent) {
        parent.replies.push({
          id: data.comment_id,
          author: data.username,
          stance: data.stance,
          time: data.created_at,
          text: data.content,
          likes: 0,
          liked: false,
        });
      }
      input.value = '';
      renderComments();
    })
    .catch(() => alert('Something went wrong.'));
  }

  /* ── Toggle reply box ── */
  function toggleReply(commentId) {
    const wrap = document.getElementById('reply-wrap-' + commentId);
    wrap.classList.toggle('open');
    if (wrap.classList.contains('open')) {
      document.getElementById('reply-input-' + commentId).focus();
    }
  }

  /* ── Like ── */
  function toggleLike(id, isReply, parentId) {
    let item;
    if (isReply) {
      const parent = comments.find(c => c.id === parentId);
      item = parent?.replies.find(r => r.id === id);
    } else {
      item = comments.find(c => c.id === id);
    }
    if (!item) return;
    item.liked  = !item.liked;
    item.likes += item.liked ? 1 : -1;

    fetch(`/comments/${id}/like`, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF_TOKEN },
    }).catch(() => {});

    renderComments();
  }

  /* ── Render helpers ── */
  function stanceLabel(s) {
    return s === 'blue' ? 'Agree' : s === 'red' ? 'Disagree' : 'Neutral';
  }

  function compareByLikes(a, b) {
    if (b.likes !== a.likes) return b.likes - a.likes;
    return b.id - a.id;
  }

  function compareByActiveFilter(a, b) {
    const aMatches = a.stance === activeCommentFilter;
    const bMatches = b.stance === activeCommentFilter;

    if (aMatches !== bMatches) return aMatches ? -1 : 1;
    return compareByLikes(a, b);
  }

  function buildComment(c, isReply = false, parentId = null) {
    return `
      <div class="comment ${c.stance}" id="comment-${c.id}">
        <div class="comment-header">
          <a href="/user/${c.author}" class="comment-author">${c.author}</a>
          <span class="stance-pill ${c.stance}">${stanceLabel(c.stance)}</span>
          <span class="comment-time">
            ${c.time}
            <button class="like-btn ${c.liked ? 'liked' : ''}"
                    onclick="toggleLike(${c.id}, ${isReply}, ${parentId})">
              <svg viewBox="0 0 24 24"
                   fill="${c.liked ? 'currentColor' : 'none'}"
                   stroke="currentColor" stroke-width="2"
                   stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3H14z"/>
                <path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>
              </svg>
              ${c.likes}
            </button>
          </span>
        </div>
        <div class="comment-body">${c.text}</div>
        ${!isReply ? `<button class="reply-btn" onclick="toggleReply(${c.id})">Reply</button>` : ''}
        ${!isReply ? `
          <div class="reply-input-wrap" id="reply-wrap-${c.id}">
            <input class="reply-input" id="reply-input-${c.id}"
                   type="text" placeholder="Write a reply...">
            <button class="reply-post-btn" onclick="postReply(${c.id})">Reply</button>
          </div>
          <div class="replies">
            ${c.replies.map(r => buildComment(r, true, c.id)).join('')}
          </div>
        ` : ''}
      </div>
    `;
  }

  function renderComments() {
    document.getElementById('comments-list').innerHTML =
      [...comments].sort(compareByActiveFilter).map(c => buildComment(c)).join('');
    document.getElementById('comment-count').textContent = comments.length;
  }

  renderComments();
