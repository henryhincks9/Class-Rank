const reviews = JSON.parse(localStorage.getItem("reviews")) || [];
const grouped = {};
reviews.forEach(review => {
    if(!grouped[review.courseId]) {
        grouped[review.courseId] =[];
    }
    grouped[review.courseId].push(review);
});
console.log(grouped);