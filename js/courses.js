let courses = [];
const searchBar = document.getElementById('searchBar');

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
