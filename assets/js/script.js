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

  // =========== HIGHLIGHT ACTIVE SECTION NAV ============
  // Grab all sections that have an id (e.g., hero, work, about, etc.)
  const sections = document.querySelectorAll('section[id]');
  // Grab all nav links inside .nav-links
  const navLinks = document.querySelectorAll('.nav-links li a');

  // Intersection Observer options: adjust the top margin to account for sticky header height.
  const observerOptions = {
    root: null,
    rootMargin: '-50px 0px 0px 0px', // Adjust '-100px' if your header height differs
    threshold: 0.1,
  };

  // Callback: runs when a section enters/exits the viewport
  const observerCallback = (entries) => {
    entries.forEach((entry) => {
      console.log('Section', entry.target.id, 'isIntersecting:', entry.isIntersecting);
      if (entry.isIntersecting) {
        const sectionId = entry.target.getAttribute('id');
        // Remove .active from all nav links
        navLinks.forEach((link) => {
          link.classList.remove('active');
          // If link href matches the section id, add .active
          if (link.getAttribute('href') === '#' + sectionId) {
            link.classList.add('active');
          }
        });
      }
    });
  };

  // Create the observer and watch each section
  const observer = new IntersectionObserver(observerCallback, observerOptions);
  sections.forEach((section) => observer.observe(section));
});

// =========== AOS INIT ============
AOS.init({
  once: true
});
