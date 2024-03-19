function adjustSidePanel(header, footer, sidePanel) {
    const windowHeight = window.innerHeight || document.documentElement.clientHeight;
    const visibleFooterHeight = Math.max(0, windowHeight - footer.getBoundingClientRect().top);
    const visibleHeaderHeight = Math.max(0, header.getBoundingClientRect().bottom);
    const maxHeightOffset = visibleHeaderHeight + visibleFooterHeight + 80;
    const topOffset = visibleHeaderHeight + 40
    sidePanel.style.top = topOffset + 'px';
    sidePanel.style.maxHeight = 'calc(100% - ' + maxHeightOffset + 'px)';
}

document.addEventListener("DOMContentLoaded", function() {
    const header = document.getElementById('main-header');
    const footer = document.getElementById('main-footer');
    const sidePanel = document.getElementById('side-panel');
    const mainPanel = document.getElementById('main-panel')
    adjustSidePanel(header, footer, sidePanel);
    window.addEventListener("scroll", function() {
        adjustSidePanel();
    });

    const sidePanelToggle = document.getElementById('side-panel-toggle');
    sidePanelToggle.addEventListener("click", function () {
        mainPanel.classList.toggle('truncated-main');
        mainPanel.classList.toggle('full-main');
        sidePanel.classList.toggle('hidden');
    });

    const nav_headers = document.querySelectorAll('.side-panel h4');

    nav_headers.forEach(function(header, index) {
        if (index !== 0) {
            toggleContent(header.nextElementSibling);
        }
        header.addEventListener('click', function() {
            toggleContent(header.nextElementSibling);
        });
    });
});

function toggleContent(contentElement) {
    contentElement.style.display = (contentElement.style.display === "none") ? "block" : "none";
}