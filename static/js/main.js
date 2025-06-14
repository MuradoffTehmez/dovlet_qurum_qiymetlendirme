// main.js - Dark mode və digər interaktivliklər üçün

document.addEventListener("DOMContentLoaded", function () {
    const themeToggleBtn = document.getElementById("theme-toggle-btn");
    const htmlElement = document.documentElement;

    // İkonu yeniləyir (günəş və ya ay)
    function updateIcon() {
        if (htmlElement.classList.contains("dark-mode")) {
            themeToggleBtn.innerHTML = '<i class="bi bi-sun-fill"></i>';
            themeToggleBtn.setAttribute("aria-label", "Light mode aktivdir, keçmək üçün basın");
        } else {
            themeToggleBtn.innerHTML = '<i class="bi bi-moon-stars-fill"></i>';
            themeToggleBtn.setAttribute("aria-label", "Dark mode aktivdir, keçmək üçün basın");
        }
    }

    // Dark/light mode düyməsinin funksionallığı
    themeToggleBtn.addEventListener("click", () => {
        htmlElement.classList.toggle("dark-mode");
        const mode = htmlElement.classList.contains("dark-mode") ? "dark" : "light";
        localStorage.setItem("theme", mode);
        updateIcon();
    });

    updateIcon();
});
