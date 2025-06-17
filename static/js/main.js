// main.js - Dark mode, animations and other interactivity
document.addEventListener("DOMContentLoaded", function () {
  const themeToggleBtn = document.getElementById("theme-toggle-btn");
  const htmlElement = document.documentElement;

  // Update icon based on current theme
  function updateIcon() {
    if (htmlElement.classList.contains("dark-mode")) {
      themeToggleBtn.innerHTML = '<i class="bi bi-sun-fill"></i>';
      themeToggleBtn.setAttribute(
        "aria-label",
        "Light mode aktivdir, keçmək üçün basın"
      );
    } else {
      themeToggleBtn.innerHTML = '<i class="bi bi-moon-stars-fill"></i>';
      themeToggleBtn.setAttribute(
        "aria-label",
        "Dark mode aktivdir, keçmək üçün basın"
      );
    }
  }

  // Toggle dark/light mode
  themeToggleBtn.addEventListener("click", () => {
    htmlElement.classList.toggle("dark-mode");
    const mode = htmlElement.classList.contains("dark-mode") ? "dark" : "light";
    localStorage.setItem("theme", mode);
    updateIcon();
  });

  // Initialize icon
  updateIcon();

  // Scroll animation for about section
  const aboutSection = document.getElementById("about-section");

  function checkScroll() {
    const sectionTop = aboutSection.getBoundingClientRect().top;
    const windowHeight = window.innerHeight;

    if (sectionTop < windowHeight - 100) {
      aboutSection.classList.add("visible");
      window.removeEventListener("scroll", checkScroll);
    }
  }

  if (aboutSection) {
    window.addEventListener("scroll", checkScroll);
    // Check on initial load in case section is already visible
    checkScroll();
  }

  // Add hover effects to nav buttons
  const navButtons = document.querySelectorAll(".nav-btn");
  navButtons.forEach((button) => {
    button.addEventListener("mouseenter", () => {
      button.style.transform = "translateY(-2px)";
    });
    button.addEventListener("mouseleave", () => {
      button.style.transform = "translateY(0)";
    });
  });
});
