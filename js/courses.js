let courses = [];
const searchBar = document.getElementById('searchBar');
const themeToggle = document.getElementById('themeToggle');
const THEME_STORAGE_KEY = 'class-rank-theme';

function applyTheme(theme) {
    const chosenTheme = theme === 'dark' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', chosenTheme);
    if (themeToggle) {
        const nextThemeLabel = chosenTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
        const nextThemeAria = chosenTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
        themeToggle.textContent = nextThemeLabel;
        themeToggle.setAttribute('aria-label', nextThemeAria);
    }
}

function initializeTheme() {
    let storedTheme;
    try {
        storedTheme = localStorage.getItem(THEME_STORAGE_KEY);
    } catch {
        storedTheme = null;
    }

    if (storedTheme === 'light' || storedTheme === 'dark') {
        applyTheme(storedTheme);
        return;
    }

    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(prefersDark ? 'dark' : 'light');
}

if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
        const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(nextTheme);
        try {
            localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
        } catch {
            // Ignore storage failures in locked-down browsers.
        }
    });
}

initializeTheme();

fetch('data/courses.json')
    .then(response => response.json())
    .then(data => {
        courses = data;
        const initialQuery = getSearchQuery();
        if (searchBar) {
            searchBar.value = initialQuery;
        }
        applySearch();
    })
    .catch(error => console.error('Error loading courses:', error));

function displayCourses(courseList) {
    const container = document.getElementById('courseContainer');
    container.innerHTML = '';

    if (!courseList.length) {
        container.innerHTML = '<p>No courses match your search.</p>';
        return;
    }

    courseList.forEach(course => {
        container.innerHTML += `
        <div class="course-card">
            <h2>${course.name}</h2>
            <p>${course.department}</p>
            <a href="course.html?id=${course.id}">View Course</a>
        </div>
        `;
    });
}

function getSearchQuery() {
    const params = new URLSearchParams(window.location.search);
    return params.get('search') || '';
}

function applySearch() {
    const searchText = searchBar ? searchBar.value.trim().toLowerCase() : '';
    const filtered = searchText
        ? courses.filter(course =>
            course.name.toLowerCase().includes(searchText) ||
            course.department.toLowerCase().includes(searchText)
        )
        : courses;
    displayCourses(filtered);
}

if (searchBar) {
    searchBar.addEventListener('input', applySearch);
}
