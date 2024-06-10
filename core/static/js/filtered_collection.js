document.addEventListener('DOMContentLoaded', () => {
    const collectionWrappers = document.querySelectorAll('.filtered-collection-wrapper');
    collectionWrappers.forEach(wrapper => {
        const filterInput = wrapper.querySelector('.filtered-collection-filter input');
        const items = wrapper.querySelectorAll('.filtered-collection-item');
        const resultCountSpan = wrapper.querySelector('.result-count');

        filterInput.addEventListener('input', () => {
            const filterValue = filterInput.value.toLowerCase();
            let visibleItemCount = 0;

            items.forEach(item => {
                const itemName = item.dataset.value.toLowerCase();
                if (!itemName.includes(filterValue)) {
                    item.style.display = 'none';
                } else {
                    item.style.display = '';
                    visibleItemCount += 1;
                }
            });

            if (resultCountSpan) {
                resultCountSpan.textContent = visibleItemCount;
            }
        });

        if (resultCountSpan) {
            resultCountSpan.textContent = items.length;
        }
    });
});