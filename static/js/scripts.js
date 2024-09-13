// static/js/scripts.js

document.addEventListener("DOMContentLoaded", function() {
    // Dark Mode Toggle with Persistence
    const toggleButton = document.getElementById("toggleTheme");
    const body = document.body;

    // Load the preferred theme from localStorage
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme) {
        body.classList.add(savedTheme);
    }

    toggleButton.addEventListener("click", function() {
        body.classList.toggle("dark-mode");
        if (body.classList.contains("dark-mode")) {
            localStorage.setItem("theme", "dark-mode");
        } else {
            localStorage.setItem("theme", "light-mode");
        }
    });

    // Search Filter Functionality
    const searchInput = document.getElementById("search-input");
    if (searchInput) {
        searchInput.addEventListener("keyup", function() {
            const filter = this.value.toLowerCase();
            const recipes = document.getElementsByClassName("recipe-card");

            Array.from(recipes).forEach(function(recipe) {
                const title = recipe.querySelector(".recipe-title").innerText.toLowerCase();
                if (title.includes(filter)) {
                    recipe.style.display = "";
                } else {
                    recipe.style.display = "none";
                }
            });
        });
    }
});
