document.addEventListener('DOMContentLoaded', () => {
    const navbar = `
      <nav id="main-nav">
        <a href="homepage.html" class="nav-brand">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
            <polyline points="16 7 22 7 22 13"/>
          </svg>
          DebateHub
        </a>
        <ul class="nav-links">
          <li><a href="homepage.html">Home</a></li>
          <li><a href="searchdebates.html">Search</a></li>
          <li><a href="dashboard.html">Dashboard</a></li>
          <li><a href="leaderboard.html">Leaderboard</a></li>
        </ul>
        <button class="btn-new" onclick="window.location.href='create_debate.html'">+ New Debate</button>
        <div class="nav-user">
          <div class="nav-avatar">D</div>
          <span>DebateMaster</span>
        </div>
      </nav>
    `;
  
    document.getElementById('nav-placeholder').innerHTML = navbar;
  
    // Auto-highlight active link
    document.querySelectorAll('.nav-links a').forEach(link => {
      if (link.href === window.location.href) {
        link.classList.add('active');
      }
    });
  });