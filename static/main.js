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
          <li><a href="/">Home</a></li>
          <li><a href="/search">Search</a></li>
          <li><a href="/dashboard">Dashboard</a></li>
          <li><a href="/leaderboard">Leaderboard</a></li>
        </ul>
        <button class="btn-new" onclick="window.location.href='/debates/create'">+ New Debate</button>
        <div class="nav-user" id="nav-user">
          <div class="nav-avatar">D</div>
          <span>DebateMaster</span>

          <div class="user-menu hidden" id="user-menu">
            <div class="user-menu-header">
              <strong>DebateMaster</strong>
              <small>Gold debater</small>
            </div>

            <a href="/profile">👤 Profile</a>
            <a href="/dashboard">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 7h18"></path>
                <path d="M3 12h18"></path>
                <path d="M3 17h18"></path>
              </svg>

              My Debates
            </a>
            <a href="#">⭐ Saved Debates</a>
            <a href="#">🔔 Notifications</a>
            <a href="/settings">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="3"></circle>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82"></path>
              </svg>

              Settings
            </a>
            <button type="button">🌙 Dark Mode</button>
            <a href="/logout">↩ Log Out</a>
          </div>
        </div>
      </nav>
    `;
  
    document.getElementById('nav-placeholder').innerHTML = navbar;
    const navUser = document.getElementById('nav-user');
    const userMenu = document.getElementById('user-menu');

    navUser.addEventListener('click', event => {
      event.stopPropagation();
      userMenu.classList.toggle('hidden');
    });

    document.addEventListener('click', () => {
      userMenu.classList.add('hidden');
    });
  
    // Auto-highlight active link
    document.querySelectorAll('.nav-links a').forEach(link => {
      if (link.href === window.location.href) {
        link.classList.add('active');
      }
    });
  });