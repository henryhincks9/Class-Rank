fetch('data/courses.json')
    .then(response => response.json())
    .then(courses => {
        const reviews = JSON.parse(localStorage.getItem('reviews')) || [];
        const rankingList = courses.map(course => {
            const courseReviews = reviews.filter(review => review.courseId === course.id);
            const averageRating = courseReviews.length
                ? courseReviews.reduce((sum, review) => sum + (review.difficulty + review.enjoyment + review.workload) / 3, 0) / courseReviews.length
                : 0;
            return {
                course,
                averageRating,
                reviewCount: courseReviews.length,
            };
        });

        rankingList.sort((a, b) => b.averageRating - a.averageRating || a.course.name.localeCompare(b.course.name));

        const rankingsContainer = document.getElementById('rankings');
        if (!rankingsContainer) {
            return;
        }

        if (!rankingList.length) {
            rankingsContainer.innerHTML = '<p>No courses available.</p>';
            return;
        }

        rankingsContainer.innerHTML = '';
        rankingList.slice(0, 10).forEach((item, index) => {
            rankingsContainer.innerHTML += `
            <div class="course-card">
                <h2>${index + 1}. ${item.course.name}</h2>
                <p>${item.course.department}</p>
                <p>Average Rating: ${item.averageRating.toFixed(1)} (${item.reviewCount} reviews)</p>
                <a href="course.html?id=${item.course.id}">View course details</a>
            </div>
            `;
        });
    })
    .catch(error => console.error('Error loading rankings:', error));
