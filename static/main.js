document.addEventListener('DOMContentLoaded', () => {
  const navbar = `
    <nav id="main-nav">
      <a href="/" class="nav-brand">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
          <polyline points="16 7 22 7 22 13"/>
        </svg>
        DebateHub
      </a>

      <ul class="nav-links">
        <li><a href="/home">Home</a></li>
        <li><a href="/search">Search</a></li>
        <li><a href="/dashboard">Dashboard</a></li>
        <li><a href="/leaderboard">Leaderboard</a></li>
      </ul>

      <button class="btn-new" onclick="window.location.href='/debates/create'">
        + New Debate
      </button>

      <div class="nav-user" id="nav-user">
        <div class="nav-avatar">D</div>
        <span>DebateMaster</span>

        <div class="user-menu hidden" id="user-menu">
          <div class="user-menu-header">
            <strong>DebateMaster</strong>
            <small>Gold debater</small>
          </div>

          <a href="/user-profile">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 21a8 8 0 0 0-16 0"/>
              <circle cx="12" cy="7" r="4"/>
            </svg>
            Profile
          </a>

          <a href="/dashboard">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="7" height="7" rx="1"/>
              <rect x="14" y="3" width="7" height="7" rx="1"/>
              <rect x="3" y="14" width="7" height="7" rx="1"/>
              <rect x="14" y="14" width="7" height="7" rx="1"/>
            </svg>
            My Debates
          </a>

          <a href="#">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
            </svg>
            Saved Debates
          </a>

          <a href="#">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            Notifications
          </a>

          <a href="/settings">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06A2 2 0 1 1 7.04 4.3l.06.06A1.65 1.65 0 0 0 8.92 4a1.65 1.65 0 0 0 1-1.51V2a2 2 0 1 1 4 0v.09A1.65 1.65 0 0 0 15 3.6a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.14.31.22.65.22 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
            Settings
          </a>

          <button type="button">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
            Dark Mode
          </button>

          <a href="/logout">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
              stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
            Log Out
          </a>
        </div>
      </div>
    </nav>
  `;

  document.getElementById('nav-placeholder').innerHTML = navbar;

  const navUser = document.getElementById('nav-user');
  const userMenu = document.getElementById('user-menu');
  const darkModeButton = userMenu.querySelector('button');

function applyTheme(isDark) {
  document.body.classList.toggle('dark-mode', isDark);

  darkModeButton.innerHTML = `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
      stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      ${
        isDark
          ? '<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>'
          : '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>'
      }
    </svg>
    ${isDark ? 'Light Mode' : 'Dark Mode'}
  `;
}

applyTheme(localStorage.getItem('theme') === 'dark');

darkModeButton.addEventListener('click', event => {
  event.preventDefault();
  event.stopPropagation();

  const isDark = !document.body.classList.contains('dark-mode');
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
  applyTheme(isDark);
});

  navUser.addEventListener('click', event => {
    event.stopPropagation();
    userMenu.classList.toggle('hidden');
  });

  userMenu.addEventListener('click', event => {
    event.stopPropagation();
  });

  document.addEventListener('click', () => {
    userMenu.classList.add('hidden');
  });

  document.querySelectorAll('.nav-links a').forEach(link => {
    if (link.pathname === window.location.pathname) {
      link.classList.add('active');
    }
  });
});