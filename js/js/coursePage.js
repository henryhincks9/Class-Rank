const params = new URLSearchParams(window.location.search);
const courseId = Number(params.get("id"));

fetch("data/courses.json")
    .then(response => response.json())
    .then(courses => {

        const course = courses.find(c => c.id === courseId);

        if (!course) return;

        document.getElementById("courseName").textContent =
            course.name;

        document.getElementById("department").textContent =
            course.department;

        loadReviews();

    });

function loadReviews() {

    const reviews =
        JSON.parse(localStorage.getItem("reviews")) || [];

    const courseReviews =
        reviews.filter(review =>
            review.courseId === courseId
        );

    const container =
        document.getElementById("reviews");

    container.innerHTML = "";

    courseReviews.forEach(review => {

        container.innerHTML += `

        <div class="course-card">

            <p>
                Difficulty: ${review.difficulty}/5
            </p>

            <p>
                Enjoyment: ${review.enjoyment}/5
            </p>

            <p>
                Workload: ${review.workload}/5
            </p>

            <p>
                ${review.review}
            </p>

        </div>

        `;

    });

    updateStatistics(courseReviews);
}

function updateStatistics(courseReviews) {

    if (courseReviews.length === 0) {

        document.getElementById("averageDifficulty").textContent = 0;
        document.getElementById("averageEnjoyment").textContent = 0;
        document.getElementById("averageWorkload").textContent = 0;

        return;
    }

    const avgDifficulty =
        courseReviews.reduce(
            (sum, review) => sum + review.difficulty,
            0
        ) / courseReviews.length;

    const avgEnjoyment =
        courseReviews.reduce(
            (sum, review) => sum + review.enjoyment,
            0
        ) / courseReviews.length;

    const avgWorkload =
        courseReviews.reduce(
            (sum, review) => sum + review.workload,
            0
        ) / courseReviews.length;

    document.getElementById("averageDifficulty").textContent =
        avgDifficulty.toFixed(1);

    document.getElementById("averageEnjoyment").textContent =
        avgEnjoyment.toFixed(1);

    document.getElementById("averageWorkload").textContent =
        avgWorkload.toFixed(1);
}

const reviewForm =
    document.getElementById("reviewForm");

reviewForm.addEventListener("submit", function (e) {

    e.preventDefault();

    const difficulty =
        Number(document.getElementById("difficulty").value);

    const enjoyment =
        Number(document.getElementById("enjoyment").value);

    const workload =
        Number(document.getElementById("workload").value);

    const reviewText =
        document.getElementById("reviewText").value;

    const reviews =
        JSON.parse(localStorage.getItem("reviews")) || [];

    reviews.push({

        courseId,

        difficulty,

        enjoyment,

        workload,

        review: reviewText

    });

    localStorage.setItem(
        "reviews",
        JSON.stringify(reviews)
    );

    reviewForm.reset();

    loadReviews();

});