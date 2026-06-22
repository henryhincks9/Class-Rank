const searchBar = document.getElementById('searchBar');

if (searchBar) {
    searchBar.addEventListener('keypress', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            const query = searchBar.value.trim();
            const target = query ? `courses.html?search=${encodeURIComponent(query)}` : 'courses.html';
            window.location.href = target;
        }
    });
}
