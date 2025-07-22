/**
 * Fully Accessible Dark Mode Implementation
 * Supports system preference detection, user preference persistence,
 * keyboard navigation, and screen reader announcements
 */

class DarkModeManager {
  constructor() {
    this.storageKey = 'theme-preference';
    this.themes = {
      LIGHT: 'light',
      DARK: 'dark',
      AUTO: 'auto'
    };
    
    this.currentTheme = this.getStoredTheme();
    this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    this.init();
  }

  init() {
    this.createToggleButton();
    this.applyTheme(this.currentTheme);
    this.setupEventListeners();
    this.announceThemeChange(this.getEffectiveTheme(), false);
  }

  /**
   * Get stored theme preference or default to auto
   */
  getStoredTheme() {
    try {
      const stored = localStorage.getItem(this.storageKey);
      return Object.values(this.themes).includes(stored) ? stored : this.themes.AUTO;
    } catch (error) {
      console.warn('Unable to access localStorage for theme preference:', error);
      return this.themes.AUTO;
    }
  }

  /**
   * Store theme preference
   */
  setStoredTheme(theme) {
    try {
      localStorage.setItem(this.storageKey, theme);
    } catch (error) {
      console.warn('Unable to store theme preference:', error);
    }
  }

  /**
   * Get the effective theme (resolving auto to light/dark)
   */
  getEffectiveTheme() {
    if (this.currentTheme === this.themes.AUTO) {
      return this.mediaQuery.matches ? this.themes.DARK : this.themes.LIGHT;
    }
    return this.currentTheme;
  }

  /**
   * Apply theme to document
   */
  applyTheme(theme) {
    const effectiveTheme = theme === this.themes.AUTO 
      ? (this.mediaQuery.matches ? this.themes.DARK : this.themes.LIGHT)
      : theme;

    // Remove existing theme classes
    document.documentElement.classList.remove('dark-mode', 'light-mode');
    
    // Add appropriate theme class
    if (effectiveTheme === this.themes.DARK) {
      document.documentElement.classList.add('dark-mode');
    } else {
      document.documentElement.classList.add('light-mode');
    }

    // Update meta theme-color for mobile browsers
    this.updateMetaThemeColor(effectiveTheme);
    
    // Update toggle button state
    this.updateToggleButton(effectiveTheme);
    
    // Store preference
    this.setStoredTheme(theme);
    this.currentTheme = theme;
  }

  /**
   * Update meta theme-color for mobile browsers
   */
  updateMetaThemeColor(theme) {
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', 
        theme === this.themes.DARK ? '#0d1117' : '#ffffff'
      );
    }
  }

  /**
   * Create accessible toggle button
   */
  createToggleButton() {
    // Find existing toggle or create new one
    let toggleContainer = document.getElementById('theme-toggle-container');
    
    if (!toggleContainer) {
      toggleContainer = document.createElement('div');
      toggleContainer.id = 'theme-toggle-container';
      
      // Insert into navbar or create fallback position
      const navbar = document.querySelector('.navbar-nav');
      if (navbar) {
        const listItem = document.createElement('li');
        listItem.className = 'nav-item';
        listItem.appendChild(toggleContainer);
        navbar.appendChild(listItem);
      } else {
        document.body.appendChild(toggleContainer);
      }
    }

    toggleContainer.innerHTML = `
      <button 
        type="button" 
        class="theme-toggle" 
        id="theme-toggle-btn"
        aria-label="Toggle dark mode"
        aria-pressed="${this.getEffectiveTheme() === this.themes.DARK}"
        title="Toggle between light and dark themes"
      >
        <span class="theme-toggle-icon sun" aria-hidden="true">☀️</span>
        <div class="theme-toggle-slider">
          <span class="sr-only">Theme toggle</span>
        </div>
        <span class="theme-toggle-icon moon" aria-hidden="true">🌙</span>
      </button>
      <span class="sr-only" id="theme-status" aria-live="polite" aria-atomic="true"></span>
    `;

    this.toggleButton = document.getElementById('theme-toggle-btn');
    this.statusElement = document.getElementById('theme-status');
  }

  /**
   * Update toggle button visual state
   */
  updateToggleButton(effectiveTheme) {
    if (!this.toggleButton) return;

    const isDark = effectiveTheme === this.themes.DARK;
    
    this.toggleButton.setAttribute('aria-pressed', isDark.toString());
    this.toggleButton.setAttribute('aria-label', 
      isDark ? 'Switch to light mode' : 'Switch to dark mode'
    );
    this.toggleButton.title = isDark 
      ? 'Switch to light mode' 
      : 'Switch to dark mode';
  }

  /**
   * Toggle between themes
   */
  toggleTheme() {
    // Show loading state
    this.toggleButton?.classList.add('loading');
    
    // Determine next theme
    const effectiveTheme = this.getEffectiveTheme();
    const nextTheme = effectiveTheme === this.themes.DARK 
      ? this.themes.LIGHT 
      : this.themes.DARK;

    // Apply theme with slight delay for smooth transition
    setTimeout(() => {
      this.applyTheme(nextTheme);
      this.announceThemeChange(nextTheme, true);
      this.toggleButton?.classList.remove('loading');
    }, 50);
  }

  /**
   * Announce theme change to screen readers
   */
  announceThemeChange(theme, isUserAction = false) {
    if (!this.statusElement) return;

    const messages = {
      [this.themes.LIGHT]: 'Light mode activated',
      [this.themes.DARK]: 'Dark mode activated'
    };

    const message = messages[theme] || 'Theme changed';
    
    if (isUserAction) {
      // Clear and set message for screen readers
      this.statusElement.textContent = '';
      setTimeout(() => {
        this.statusElement.textContent = message;
      }, 100);
    }
  }

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Toggle button click
    if (this.toggleButton) {
      this.toggleButton.addEventListener('click', () => {
        this.toggleTheme();
      });

      // Keyboard support
      this.toggleButton.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          this.toggleTheme();
        }
      });
    }

    // System preference change
    this.mediaQuery.addEventListener('change', (event) => {
      if (this.currentTheme === this.themes.AUTO) {
        const newTheme = event.matches ? this.themes.DARK : this.themes.LIGHT;
        this.applyTheme(this.themes.AUTO);
        this.announceThemeChange(newTheme, false);
      }
    });

    // Storage change (for sync across tabs)
    window.addEventListener('storage', (event) => {
      if (event.key === this.storageKey && event.newValue) {
        this.currentTheme = event.newValue;
        this.applyTheme(this.currentTheme);
        this.announceThemeChange(this.getEffectiveTheme(), false);
      }
    });

    // Page visibility change (refresh theme on tab focus)
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        const storedTheme = this.getStoredTheme();
        if (storedTheme !== this.currentTheme) {
          this.currentTheme = storedTheme;
          this.applyTheme(this.currentTheme);
        }
      }
    });
  }

  /**
   * Public API methods
   */
  setTheme(theme) {
    if (Object.values(this.themes).includes(theme)) {
      this.applyTheme(theme);
      this.announceThemeChange(this.getEffectiveTheme(), true);
    }
  }

  getCurrentTheme() {
    return this.currentTheme;
  }

  getEffectiveThemePublic() {
    return this.getEffectiveTheme();
  }

  /**
   * Check if user prefers reduced motion
   */
  prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /**
   * Get contrast preference
   */
  getContrastPreference() {
    if (window.matchMedia('(prefers-contrast: high)').matches) {
      return 'high';
    }
    if (window.matchMedia('(prefers-contrast: low)').matches) {
      return 'low';
    }
    return 'normal';
  }
}

// Initialize dark mode manager when DOM is ready
let darkModeManager;

function initializeDarkMode() {
  // Apply theme immediately to prevent flash
  const storedTheme = localStorage.getItem('theme-preference') || 'auto';
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  
  let effectiveTheme;
  if (storedTheme === 'auto') {
    effectiveTheme = mediaQuery.matches ? 'dark' : 'light';
  } else {
    effectiveTheme = storedTheme;
  }
  
  if (effectiveTheme === 'dark') {
    document.documentElement.classList.add('dark-mode');
  } else {
    document.documentElement.classList.add('light-mode');
  }
  
  // Initialize full manager when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      darkModeManager = new DarkModeManager();
    });
  } else {
    darkModeManager = new DarkModeManager();
  }
}

// Initialize immediately
initializeDarkMode();

// Export for global access
window.DarkModeManager = DarkModeManager;
window.darkModeManager = darkModeManager;

// Utility functions for external use
window.toggleDarkMode = () => darkModeManager?.toggleTheme();
window.setTheme = (theme) => darkModeManager?.setTheme(theme);
window.getCurrentTheme = () => darkModeManager?.getCurrentTheme();