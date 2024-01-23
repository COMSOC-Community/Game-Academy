function adjustSidePanel() {
    const header = document.querySelector('header');
    const footer = document.querySelector('footer');
    const sidePanel = document.querySelector('.side-panel');
    const windowHeight = window.innerHeight || document.documentElement.clientHeight;
    const visibleFooterHeight = Math.max(0, windowHeight - footer.getBoundingClientRect().top);
    const visibleHeaderHeight = Math.max(0, header.getBoundingClientRect().bottom);
    const maxHeightOffset = visibleHeaderHeight + visibleFooterHeight + 80;
    const topOffset = visibleHeaderHeight + 40
    sidePanel.style.top = topOffset + 'px';
    sidePanel.style.maxHeight = 'calc(100% - ' + maxHeightOffset + 'px)';
}

document.addEventListener("DOMContentLoaded", function() {
    adjustSidePanel();
});

window.addEventListener("scroll", function() {
    adjustSidePanel();
});