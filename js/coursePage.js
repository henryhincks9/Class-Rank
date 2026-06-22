const params = new URLSearchParams(window.location.search);
const courseId = Number(params.get('id'));
const courseNameEl = document.getElementById('courseName');
const departmentEl = document.getElementById('department');
const reviewForm = document.getElementById('reviewForm');
const reviewsContainer = document.getElementById('reviews');
const averageDifficultyEl = document.getElementById('averageDifficulty');
const averageEnjoymentEl = document.getElementById('averageEnjoyment');
const averageWorkloadEl = document.getElementById('averageWorkload');

fetch('data/courses.json')
    .then(response => response.json())
    .then(courses => {
        const course = courses.find(c => c.id === courseId);
        if (!course) {
            showCourseNotFound();
            return;
        }

        courseNameEl.textContent = course.name;
        departmentEl.textContent = course.department;
        loadReviews();
    })
    .catch(error => {
        console.error('Error loading course details:', error);
        showCourseNotFound();
    });

function showCourseNotFound() {
    courseNameEl.textContent = 'Course not found';
    departmentEl.textContent = '';
    if (reviewsContainer) {
        reviewsContainer.innerHTML = '<p>This course could not be found.</p>';
    }
    if (averageDifficultyEl) averageDifficultyEl.textContent = '0';
    if (averageEnjoymentEl) averageEnjoymentEl.textContent = '0';
    if (averageWorkloadEl) averageWorkloadEl.textContent = '0';
    if (reviewForm) reviewForm.style.display = 'none';
}

function loadReviews() {
    const reviews = JSON.parse(localStorage.getItem('reviews')) || [];
    const courseReviews = reviews.filter(review => review.courseId === courseId);
    reviewsContainer.innerHTML = '';

    if (courseReviews.length === 0) {
        reviewsContainer.innerHTML = '<p>No reviews yet. Be the first to leave one.</p>';
    }

    courseReviews.forEach(review => {
        reviewsContainer.innerHTML += `
        <div class="course-card">
            <p>Difficulty: ${review.difficulty}/5</p>
            <p>Enjoyment: ${review.enjoyment}/5</p>
            <p>Workload: ${review.workload}/5</p>
            <p>${review.review}</p>
        </div>
        `;
    });

    updateStatistics(courseReviews);
}

function updateStatistics(courseReviews) {
    if (!courseReviews.length) {
        averageDifficultyEl.textContent = '0';
        averageEnjoymentEl.textContent = '0';
        averageWorkloadEl.textContent = '0';
        return;
    }

    const avgDifficulty = courseReviews.reduce((sum, review) => sum + review.difficulty, 0) / courseReviews.length;
    const avgEnjoyment = courseReviews.reduce((sum, review) => sum + review.enjoyment, 0) / courseReviews.length;
    const avgWorkload = courseReviews.reduce((sum, review) => sum + review.workload, 0) / courseReviews.length;

    averageDifficultyEl.textContent = avgDifficulty.toFixed(1);
    averageEnjoymentEl.textContent = avgEnjoyment.toFixed(1);
    averageWorkloadEl.textContent = avgWorkload.toFixed(1);
}

if (reviewForm) {
    reviewForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const difficulty = Number(document.getElementById('difficulty').value);
        const enjoyment = Number(document.getElementById('enjoyment').value);
        const workload = Number(document.getElementById('workload').value);
        const reviewText = document.getElementById('reviewText').value.trim();

        if (!reviewText) {
            return;
        }

        const reviews = JSON.parse(localStorage.getItem('reviews')) || [];
        reviews.push({
            courseId,
            difficulty,
            enjoyment,
            workload,
            review: reviewText,
        });

        localStorage.setItem('reviews', JSON.stringify(reviews));
        reviewForm.reset();
        loadReviews();
    });
}
