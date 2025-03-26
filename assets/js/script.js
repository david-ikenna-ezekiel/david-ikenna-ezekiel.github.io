// Run everything once DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Scroll to top on page load (optional, helps on mobile sometimes)
  window.scrollTo(0, 0);

  // =========== TYPED.JS EFFECT ============
  // Only initialize if #typed element is present
  if (document.getElementById('typed')) {
    new Typed('#typed', {
      strings: [
        "am a Data Engineer.",
        "love building scalable data infrastructures.",
        "am passionate about data stories."
      ],
      typeSpeed: 50,
      backSpeed: 30,
      loop: true
    });
  }

  // =========== THEME TOGGLE ============
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)");
    let currentTheme = localStorage.getItem('theme');

    // If no saved theme, use system preference
    if (!currentTheme) {
      currentTheme = prefersDarkScheme.matches ? 'dark' : 'light';
    }
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);

    // Toggle on click
    themeToggle.addEventListener('click', () => {
      let theme = document.documentElement.getAttribute('data-theme');
      theme = (theme === 'light') ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('theme', theme);
      updateThemeIcon(theme);
    });

    function updateThemeIcon(theme) {
      const icon = themeToggle.querySelector('img');
      if (theme === 'dark') {
        icon.src = 'assets/icons/moon.svg';
        icon.alt = 'Switch to Light Mode';
      } else {
        icon.src = 'assets/icons/sun.svg';
        icon.alt = 'Switch to Dark Mode';
      }
    }
  }

  // =========== HAMBURGER MENU TOGGLE ============
  const hamburger = document.querySelector('.hamburger');
  const headerNav = document.querySelector('.header-nav');
  if (hamburger && headerNav) {
    hamburger.addEventListener('click', () => {
      headerNav.classList.toggle('active');
      hamburger.classList.toggle('active'); // for "X" animation, if any
    });
  }
});

// =========== AOS INIT ============
AOS.init({
  once: true
});
