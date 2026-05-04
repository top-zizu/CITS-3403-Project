document.addEventListener('DOMContentLoaded', () => {
    fetch('navbar.html')
      .then(r => r.text())
      .then(html => {
        document.getElementById('nav-placeholder').innerHTML = html;
  
        // Auto-highlight the active nav link
        document.querySelectorAll('.nav-links a').forEach(link => {
          if (link.href === window.location.href) {
            link.classList.add('active');
          }
        });
      });
  });