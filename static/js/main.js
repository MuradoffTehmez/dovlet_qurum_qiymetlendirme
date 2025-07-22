// main.js - Modern JavaScript with enhanced functionality
(function() {
  'use strict';

  // Utility functions
  const utils = {
    debounce(func, wait) {
      let timeout;
      return function executedFunction(...args) {
        const later = () => {
          clearTimeout(timeout);
          func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    },

    throttle(func, limit) {
      let inThrottle;
      return function executedFunction(...args) {
        if (!inThrottle) {
          func.apply(this, args);
          inThrottle = true;
          setTimeout(() => inThrottle = false, limit);
        }
      };
    },

    showLoadingSpinner() {
      const spinner = document.getElementById('loading-spinner');
      if (spinner) {
        spinner.style.display = 'flex';
      }
    },

    hideLoadingSpinner() {
      const spinner = document.getElementById('loading-spinner');
      if (spinner) {
        spinner.style.display = 'none';
      }
    },

    showToast(message, type = 'info') {
      const toastContainer = document.querySelector('.toast-container');
      if (!toastContainer) return;

      const toastId = 'toast-' + Date.now();
      const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0 animate__animated animate__fadeInRight" 
             role="alert" aria-live="assertive" aria-atomic="true" data-bs-autohide="true" data-bs-delay="5000">
          <div class="d-flex">
            <div class="toast-body">
              <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
              ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
          </div>
        </div>
      `;

      toastContainer.insertAdjacentHTML('beforeend', toastHTML);
      const toastElement = document.getElementById(toastId);
      const toast = new bootstrap.Toast(toastElement);
      toast.show();

      // Remove toast element after it's hidden
      toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
      });
    }
  };

  // Theme management
  const themeManager = {
    init() {
      // Theme management is now handled by dark-mode.js
      // This is kept for backward compatibility
      console.log('Theme management initialized by DarkModeManager');
    }
  };

  // Navigation enhancements
  const navigationManager = {
    init() {
      this.setupMobileNavigation();
      this.setupAccessibility();
      this.setupScrollBehavior();
    },

    setupMobileNavigation() {
      const navbarToggler = document.querySelector('.navbar-toggler');
      const navbarCollapse = document.querySelector('.navbar-collapse');

      if (navbarToggler && navbarCollapse) {
        navbarToggler.addEventListener('click', () => {
          const isExpanded = navbarToggler.getAttribute('aria-expanded') === 'true';
          navbarToggler.setAttribute('aria-expanded', !isExpanded);
        });

        // Close mobile menu when clicking on a link
        const navLinks = navbarCollapse.querySelectorAll('a');
        navLinks.forEach(link => {
          link.addEventListener('click', () => {
            if (window.innerWidth < 992) {
              const bsCollapse = new bootstrap.Collapse(navbarCollapse, {
                toggle: true
              });
            }
          });
        });
      }
    },

    setupAccessibility() {
      // Add keyboard navigation support
      const dropdownToggles = document.querySelectorAll('[data-bs-toggle="dropdown"]');
      dropdownToggles.forEach(toggle => {
        toggle.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggle.click();
          }
        });
      });
    },

    setupScrollBehavior() {
      let lastScrollY = window.scrollY;
      const navbar = document.querySelector('.navbar');

      const handleScroll = utils.throttle(() => {
        const currentScrollY = window.scrollY;
        
        if (navbar) {
          if (currentScrollY > lastScrollY && currentScrollY > 100) {
            navbar.style.transform = 'translateY(-100%)';
          } else {
            navbar.style.transform = 'translateY(0)';
          }
        }

        lastScrollY = currentScrollY;
      }, 100);

      window.addEventListener('scroll', handleScroll);
    }
  };

  // Toast notifications
  const toastManager = {
    init() {
      this.initializeToasts();
    },

    initializeToasts() {
      const toasts = document.querySelectorAll('.toast');
      toasts.forEach(toastEl => {
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
      });
    }
  };

  // Form enhancements
  const formManager = {
    init() {
      this.setupFormValidation();
      this.setupAsyncForms();
    },

    setupFormValidation() {
      const forms = document.querySelectorAll('form[data-validate]');
      forms.forEach(form => {
        form.addEventListener('submit', (e) => {
          if (!form.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
            utils.showToast('Zəhmət olmasa, bütün tələb olunan sahələri doldurun', 'warning');
          }
          form.classList.add('was-validated');
        });
      });
    },

    setupAsyncForms() {
      const asyncForms = document.querySelectorAll('form[data-async]');
      asyncForms.forEach(form => {
        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          utils.showLoadingSpinner();

          try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
              method: form.method,
              body: formData,
              headers: {
                'X-Requested-With': 'XMLHttpRequest'
              }
            });

            if (response.ok) {
              utils.showToast('Əməliyyat uğurla tamamlandı', 'success');
              if (form.dataset.redirect) {
                setTimeout(() => {
                  window.location.href = form.dataset.redirect;
                }, 1000);
              }
            } else {
              throw new Error('Server error');
            }
          } catch (error) {
            utils.showToast('Xəta baş verdi. Zəhmət olmasa yenidən cəhd edin', 'error');
          } finally {
            utils.hideLoadingSpinner();
          }
        });
      });
    }
  };

  // Accessibility enhancements
  const accessibilityManager = {
    init() {
      this.setupSkipLinks();
      this.setupFocusManagement();
      this.setupKeyboardNavigation();
    },

    setupSkipLinks() {
      const skipLinks = document.querySelectorAll('a[href^="#"]');
      skipLinks.forEach(link => {
        link.addEventListener('click', (e) => {
          const target = document.querySelector(link.getAttribute('href'));
          if (target) {
            e.preventDefault();
            target.focus();
            target.scrollIntoView({ behavior: 'smooth' });
          }
        });
      });
    },

    setupFocusManagement() {
      // Trap focus in modals
      const modals = document.querySelectorAll('.modal');
      modals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', () => {
          const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          );
          if (focusableElements.length) {
            focusableElements[0].focus();
          }
        });
      });
    },

    setupKeyboardNavigation() {
      // Add keyboard support for custom interactive elements
      const interactiveElements = document.querySelectorAll('[data-keyboard]');
      interactiveElements.forEach(element => {
        element.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            element.click();
          }
        });
      });
    }
  };

  // Performance monitoring
  const performanceManager = {
    init() {
      if ('performance' in window) {
        this.monitorPageLoad();
        this.monitorNetworkRequests();
      }
    },

    monitorPageLoad() {
      window.addEventListener('load', () => {
        const perfData = performance.getEntriesByType('navigation')[0];
        if (perfData) {
          console.log('Səhifə yüklənmə vaxtı:', perfData.loadEventEnd - perfData.loadEventStart, 'ms');
        }
      });
    },

    monitorNetworkRequests() {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach(entry => {
          if (entry.duration > 1000) {
            console.warn('Yavaş sorğu:', entry.name, entry.duration + 'ms');
          }
        });
      });

      observer.observe({ entryTypes: ['resource'] });
    }
  };

  // Initialize everything when DOM is ready
  document.addEventListener('DOMContentLoaded', () => {
    themeManager.init();
    navigationManager.init();
    toastManager.init();
    formManager.init();
    accessibilityManager.init();
    performanceManager.init();

    // Hide loading spinner after everything is loaded
    utils.hideLoadingSpinner();
  });

  // Export utils for global use
  window.AppUtils = utils;
})();
