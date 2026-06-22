let courses = [];
const searchBar = document.getElementById('searchBar');
const searchHint = document.getElementById('searchHint');
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

function normalizeSearchText(value) {
    return String(value || '')
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, ' ')
        .trim();
}

function isSubsequenceMatch(query, candidate) {
    if (!query || !candidate) {
        return false;
    }
    let queryIndex = 0;
    for (const char of candidate) {
        if (char === query[queryIndex]) {
            queryIndex += 1;
            if (queryIndex === query.length) {
                return true;
            }
        }
    }
    return false;
}

function levenshteinDistance(first, second) {
    const rows = first.length + 1;
    const cols = second.length + 1;
    const matrix = Array.from({length: rows}, (_, row) => {
        const values = Array(cols).fill(0);
        values[0] = row;
        return values;
    });

    for (let col = 0; col < cols; col += 1) {
        matrix[0][col] = col;
    }

    for (let row = 1; row < rows; row += 1) {
        for (let col = 1; col < cols; col += 1) {
            const substitutionCost = first[row - 1] === second[col - 1] ? 0 : 1;
            matrix[row][col] = Math.min(
                matrix[row - 1][col] + 1,
                matrix[row][col - 1] + 1,
                matrix[row - 1][col - 1] + substitutionCost
            );
        }
    }

    return matrix[rows - 1][cols - 1];
}

function tokenMatches(queryToken, candidateToken) {
    if (!queryToken || !candidateToken) {
        return false;
    }
    if (candidateToken.includes(queryToken) || queryToken.includes(candidateToken)) {
        return true;
    }
    if (isSubsequenceMatch(queryToken, candidateToken)) {
        return true;
    }
    if (Math.abs(queryToken.length - candidateToken.length) > 2) {
        return false;
    }
    return levenshteinDistance(queryToken, candidateToken) <= 2;
}

function scoreCourseMatch(course, query) {
    const normalizedQuery = normalizeSearchText(query);
    if (!normalizedQuery) {
        return 1;
    }

    const fields = [course.name, course.department, course.id, course.level]
        .map(normalizeSearchText)
        .filter(Boolean);
    const combined = fields.join(' ');

    if (combined.includes(normalizedQuery)) {
        return 100;
    }

    const queryTokens = normalizedQuery.split(' ').filter(Boolean);
    const fieldTokens = combined.split(' ').filter(Boolean);
    let score = 0;

    for (const token of queryTokens) {
        if (fieldTokens.some(candidateToken => candidateToken.startsWith(token))) {
            score += 30;
            continue;
        }
        if (fieldTokens.some(candidateToken => tokenMatches(token, candidateToken))) {
            score += 18;
            continue;
        }
        if (combined.includes(token) || isSubsequenceMatch(token, combined.replace(/\s+/g, ''))) {
            score += 10;
            continue;
        }
        return 0;
    }

    return score;
}

function isExactCourseMatch(course, query) {
    const normalizedQuery = normalizeSearchText(query);
    if (!normalizedQuery) {
        return true;
    }

    const combined = [course.name, course.department, course.id, course.level]
        .map(normalizeSearchText)
        .filter(Boolean)
        .join(' ');

    return combined.includes(normalizedQuery);
}

function updateSearchHint(searchResult) {
    if (!searchHint) {
        return;
    }

    if (!searchResult.query || !searchResult.usedFuzzy) {
        searchHint.textContent = '';
        searchHint.classList.add('hidden');
        return;
    }

    searchHint.textContent = `Showing close matches for "${searchResult.query}".`;
    searchHint.classList.remove('hidden');
}

function applySearch() {
    const searchText = searchBar ? normalizeSearchText(searchBar.value) : '';
    const scoredMatches = searchText
        ? courses
            .map(course => ({course, score: scoreCourseMatch(course, searchText)}))
            .filter(item => item.score > 0)
            .sort((left, right) => right.score - left.score || left.course.name.localeCompare(right.course.name))
        : courses.map(course => ({course, score: 1}));
    const searchResult = {
        courses: scoredMatches.map(item => item.course),
        query: searchText,
        usedFuzzy: !!searchText && scoredMatches.length > 0 && !scoredMatches.some(item => isExactCourseMatch(item.course, searchText)),
    };
    displayCourses(searchResult.courses);
    updateSearchHint(searchResult);
}

if (searchBar) {
    searchBar.addEventListener('input', applySearch);
}
