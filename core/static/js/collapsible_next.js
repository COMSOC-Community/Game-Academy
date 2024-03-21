
document.addEventListener("DOMContentLoaded", function() {
    const nextCollapsibles = document.querySelectorAll(".next-collapsible");

    nextCollapsibles.forEach(function (e) {
        e.addEventListener("click", function () {
            this.nextElementSibling.classList.toggle("hidden");
        });
    });
});