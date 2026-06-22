const sections = {
    home: document.getElementById("homeSection"),
    login: document.getElementById("loginSection"),
    courses: document.getElementById("coursesSection"),
    course: document.getElementById("courseSection"),
    rankings: document.getElementById("rankingsSection"),
    admin: document.getElementById("adminSection"),
};

const navButtons = document.querySelectorAll("[data-nav]");
const homeSearch = document.getElementById("homeSearch");
const coursesSearch = document.getElementById("coursesSearch");
const courseContainer = document.getElementById("courseContainer");
const rankingsContainer = document.getElementById("rankingsContainer");
const backToCourses = document.getElementById("backToCourses");
const adminSection = document.getElementById("adminSection");
const adminReviewsContainer = document.getElementById("adminReviewsContainer");
const adminUsersContainer = document.getElementById("adminUsersContainer");
const adminNavButton = document.getElementById("adminNavButton");
const courseNameEl = document.getElementById("courseName");
const departmentEl = document.getElementById("department");
const averageDifficultyEl = document.getElementById("averageDifficulty");
const averageEnjoymentEl = document.getElementById("averageEnjoyment");
const averageWorkloadEl = document.getElementById("averageWorkload");
const reviewsEl = document.getElementById("reviews");
const reviewForm = document.getElementById("reviewForm");
const reviewAuthPrompt = document.getElementById("reviewAuthPrompt");
const loginSection = document.getElementById("loginSection");
const userNameEl = document.getElementById("userName");
const loginButton = document.getElementById("loginButton");
const logoutButton = document.getElementById("logoutButton");
const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");
const authMessage = document.getElementById("authMessage");

const api = {
    courses: "/api/courses",
    reviews: "/api/reviews",
    rankings: "/api/rankings",
    login: "/api/login",
    logout: "/api/logout",
    register: "/api/register",
    me: "/api/me",
};

let courses = [];
let currentCourseId = null;
let currentUser = null;

function hideAllSections() {
    Object.values(sections).forEach(section => section.classList.add("hidden"));
}

function showSection(name) {
    hideAllSections();
    sections[name].classList.remove("hidden");
}

function setActiveNav(target) {
    navButtons.forEach(button => {
        button.classList.toggle("active", button.dataset.nav === target);
    });
}

function updateAuthUI() {
    if (currentUser) {
        const identity = currentUser.email ? `${currentUser.username} (${currentUser.email})` : currentUser.username;
        userNameEl.textContent = `Signed in as ${identity}`;
        loginButton.classList.add("hidden");
        logoutButton.classList.remove("hidden");
    } else {
        userNameEl.textContent = "";
        loginButton.classList.remove("hidden");
        logoutButton.classList.add("hidden");
    }
    if (adminNavButton) {
        const isAdmin = !!(currentUser && currentUser.role === "admin");
        adminNavButton.classList.toggle("hidden", !isAdmin);
    }
    updateReviewFormVisibility();
}

function showHome() {
    setActiveNav("home");
    showSection("home");
}

function showLogin() {
    setActiveNav("home");
    showSection("login");
    authMessage.textContent = "";
}

function showCourses() {
    setActiveNav("courses");
    showSection("courses");
    renderCourseList(filterCourses(coursesSearch.value));
}

function showRankings() {
    setActiveNav("rankings");
    showSection("rankings");
    renderRankings();
}

function showAdminPanel() {
    setActiveNav("admin");
    showSection("admin");
    renderAdminReviews();
    renderAdminUsers();
}

function showCourseDetail(courseId) {
    const course = courses.find(c => c.id === Number(courseId));
    if (!course) {
        courseNameEl.textContent = "Course not found";
        departmentEl.textContent = "";
        reviewsEl.innerHTML = "<p>Course ID not found.</p>";
        averageDifficultyEl.textContent = "0";
        averageEnjoymentEl.textContent = "0";
        averageWorkloadEl.textContent = "0";
        setActiveNav("courses");
        showSection("course");
        return;
    }

    currentCourseId = course.id;
    setActiveNav("courses");
    showSection("course");
    courseNameEl.textContent = course.name;
    departmentEl.textContent = course.department;
    updateReviewFormVisibility();
    loadReviews();
}

function filterCourses(query) {
    const cleaned = (query || "").trim().toLowerCase();
    if (!cleaned) {
        return courses;
    }

    return courses.filter(course => {
        return course.name.toLowerCase().includes(cleaned) ||
            course.department.toLowerCase().includes(cleaned) ||
            String(course.id).includes(cleaned) ||
            (course.level && course.level.toLowerCase().includes(cleaned));
    });
}

function renderCourseList(courseList) {
    if (!courseList.length) {
        courseContainer.innerHTML = "<p>No courses match your search.</p>";
        return;
    }

    courseContainer.innerHTML = courseList.map(course => {
        return `
            <div class="course-card">
                <h3>${course.name}</h3>
                <p><strong>Department:</strong> ${course.department}</p>
                <p><strong>Level:</strong> ${course.level || "N/A"}</p>
                <p><strong>Credits:</strong> ${course.credits}</p>
                <button class="secondary-button" data-course-id="${course.id}">View Details</button>
            </div>
        `;
    }).join("");
}

function renderRankings() {
    fetch(api.rankings)
        .then(response => response.json())
        .then(data => {
            if (!data.length) {
                rankingsContainer.innerHTML = "<p>No ranking data available.</p>";
                return;
            }

            rankingsContainer.innerHTML = data.map((item, index) => {
                return `
                    <div class="course-card">
                        <h3>${index + 1}. ${item.course.name}</h3>
                        <p><strong>Department:</strong> ${item.course.department}</p>
                        <p><strong>Average Rating:</strong> ${item.averageRating.toFixed(1)}</p>
                        <p><strong>Review Count:</strong> ${item.reviewCount}</p>
                        <button class="secondary-button" data-course-id="${item.course.id}">View Details</button>
                    </div>
                `;
            }).join("");
        })
        .catch(() => {
            rankingsContainer.innerHTML = "<p>Unable to load rankings.</p>";
        });
}

function renderAdminReviews() {
    fetch(api.reviews)
        .then(response => response.json())
        .then(data => {
            if (!data.length) {
                adminReviewsContainer.innerHTML = "<p>No reviews available.</p>";
                return;
            }

            adminReviewsContainer.innerHTML = data.map(review => {
                return `
                    <div class="review-card">
                        <p><strong>${review.username}</strong> on <strong>${review.course_id}</strong> wrote:</p>
                        <p>${review.review}</p>
                        <p><small>${review.created_at}</small></p>
                        <button class="secondary-button" data-delete-review-id="${review.id}">Delete review</button>
                    </div>
                `;
            }).join("");
        })
        .catch(() => {
            adminReviewsContainer.innerHTML = "<p>Unable to load reviews.</p>";
        });
}

function renderAdminUsers() {
    fetch('/api/admin/users')
        .then(r => r.json())
        .then(users => {
            if (!users.length) {
                adminUsersContainer.innerHTML = '<p>No users.</p>';
                return;
            }
            adminUsersContainer.innerHTML = users.map(u => `
                <div class="user-card">
                    <p><strong>${u.username}</strong></p>
                    <p><small>${u.email || 'No email'}</small></p>
                    <p>Role: <span id="user-role-${u.id}">${u.role}</span></p>
                    <div>
                        <button class="secondary-button" data-user-id="${u.id}" data-set-role="user">Set user</button>
                        <button class="secondary-button" data-user-id="${u.id}" data-set-role="teacher">Set teacher</button>
                        <button class="secondary-button" data-user-id="${u.id}" data-set-role="admin">Set admin</button>
                    </div>
                </div>
            `).join('');
        })
        .catch(() => {
            adminUsersContainer.innerHTML = '<p>Unable to load users.</p>';
        });
}

function loadReviews() {
    fetch(`${api.reviews}?courseId=${currentCourseId}`)
        .then(response => response.json())
        .then(courseReviews => {
            if (!courseReviews.length) {
                reviewsEl.innerHTML = "<p>No reviews yet. Be the first to leave one.</p>";
                averageDifficultyEl.textContent = "0";
                averageEnjoymentEl.textContent = "0";
                averageWorkloadEl.textContent = "0";
                return;
            }

            reviewsEl.innerHTML = courseReviews.map(review => {
                return `
                    <div class="review-card">
                        <p><strong>${review.username}</strong> wrote:</p>
                        <p><strong>Difficulty:</strong> ${review.difficulty}/5</p>
                        <p><strong>Enjoyment:</strong> ${review.enjoyment}/5</p>
                        <p><strong>Workload:</strong> ${review.workload}/5</p>
                        <p>${review.review}</p>
                        ${currentUser && currentUser.role === "admin" ? `<button class="secondary-button" data-delete-review-id="${review.id}">Delete review</button>` : ""}
                        ${currentUser && currentUser.role !== "admin" ? `<button class="secondary-button" data-flag-review-id="${review.id}">Flag review</button>` : ""}
                    </div>
                `;
            }).join("");

            const avgDifficulty = courseReviews.reduce((sum, review) => sum + review.difficulty, 0) / courseReviews.length;
            const avgEnjoyment = courseReviews.reduce((sum, review) => sum + review.enjoyment, 0) / courseReviews.length;
            const avgWorkload = courseReviews.reduce((sum, review) => sum + review.workload, 0) / courseReviews.length;

            averageDifficultyEl.textContent = avgDifficulty.toFixed(1);
            averageEnjoymentEl.textContent = avgEnjoyment.toFixed(1);
            averageWorkloadEl.textContent = avgWorkload.toFixed(1);
        })
        .catch(() => {
            reviewsEl.innerHTML = "<p>Unable to load reviews.</p>";
        });
}

function updateReviewFormVisibility() {
    if (!currentUser) {
        reviewForm.classList.add("hidden");
        reviewAuthPrompt.classList.remove("hidden");
    } else {
        reviewForm.classList.remove("hidden");
        reviewAuthPrompt.classList.add("hidden");
    }
}

function navigateTo(route, param = null) {
    if (param !== null) {
        window.location.hash = `${route}=${param}`;
    } else {
        window.location.hash = route;
    }
}

function handleRoute() {
    const hash = window.location.hash.slice(1) || "home";
    const [route, param] = hash.split("=");

    if (route === "courses") {
        showCourses();
    } else if (route === "rankings") {
        showRankings();
    } else if (route === "admin") {
        showAdminPanel();
    } else if (route === "course" && param) {
        showCourseDetail(param);
    } else if (route === "login") {
        showLogin();
    } else {
        showHome();
    }
}

function attachEventHandlers() {
    navButtons.forEach(button => {
        button.addEventListener("click", () => {
            navigateTo(button.dataset.nav);
        });
    });

    homeSearch.addEventListener("keypress", event => {
        if (event.key === "Enter") {
            event.preventDefault();
            coursesSearch.value = homeSearch.value;
            navigateTo("courses");
        }
    });

    coursesSearch.addEventListener("input", () => {
        renderCourseList(filterCourses(coursesSearch.value));
    });

    document.body.addEventListener("click", event => {
        const courseButton = event.target.closest("[data-course-id]");
        if (courseButton) {
            const courseId = courseButton.dataset.courseId;
            navigateTo("course", courseId);
            return;
        }

        const deleteButton = event.target.closest("[data-delete-review-id]");
        if (deleteButton) {
            const reviewId = deleteButton.dataset.deleteReviewId;
            fetch(`${api.reviews}/${reviewId}`, {
                method: "DELETE",
            })
                .then(response => {
                    if (!response.ok) {
                        throw new Error("Delete failed");
                    }
                    loadReviews();
                    if (adminSection && !adminSection.classList.contains("hidden")) {
                        renderAdminReviews();
                    }
                })
                .catch(() => {
                    alert("Unable to delete review.");
                });
        }
        const flagButton = event.target.closest("[data-flag-review-id]");
        if (flagButton) {
            const reviewId = flagButton.dataset.flagReviewId;
            fetch(`${api.reviews}/${reviewId}/flag`, { method: "POST" })
                .then(response => response.json())
                .then(() => {
                    loadReviews();
                    if (adminSection && !adminSection.classList.contains("hidden")) {
                        renderAdminReviews();
                    }
                })
                .catch(() => alert("Unable to flag review."));
        }

        const roleButton = event.target.closest("[data-user-id]");
        if (roleButton && roleButton.dataset.setRole) {
            const uid = roleButton.dataset.userId;
            const newRole = roleButton.dataset.setRole;
            fetch(`/api/admin/users/${uid}/role`, {
                method: "POST",
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role: newRole }),
            })
                .then(response => {
                    if (!response.ok) throw new Error('role change failed');
                    document.getElementById(`user-role-${uid}`).textContent = newRole;
                })
                .catch(() => alert('Unable to change role.'));
        }
    });

    if (loginButton) {
        loginButton.addEventListener("click", () => navigateTo("login"));
    }

    if (logoutButton) {
        logoutButton.addEventListener("click", () => {
            fetch(api.logout)
                .then(() => {
                    currentUser = null;
                    updateAuthUI();
                    showHome();
                });
        });
    }

    if (adminNavButton) {
        adminNavButton.addEventListener("click", () => navigateTo("admin"));
    }

    if (loginForm) {
        loginForm.addEventListener("submit", event => {
            event.preventDefault();
            const username = document.getElementById("loginUsername").value.trim();
            const password = document.getElementById("loginPassword").value;

            fetch(api.login, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({username, password}),
            })
                .then(response => response.json().then(data => ({ok: response.ok, data})))
                .then(({ok, data}) => {
                    if (!ok) {
                        authMessage.textContent = data.message || "Login failed.";
                        return;
                    }
                    currentUser = data.user;
                    authMessage.textContent = "";
                    updateAuthUI();
                    navigateTo("courses");
                })
                .catch(() => {
                    authMessage.textContent = "Unable to login right now.";
                });
        });
    }

    if (registerForm) {
        registerForm.addEventListener("submit", event => {
            event.preventDefault();
            const username = document.getElementById("registerUsername").value.trim();
            const email = document.getElementById("registerEmail").value.trim().toLowerCase();
            const password = document.getElementById("registerPassword").value;
            const requiredDomain = "@go.dsdmail.net";

            if (!email.endsWith(requiredDomain)) {
                authMessage.textContent = `Please use your Davis School District email (${requiredDomain}).`;
                return;
            }

            fetch(api.register, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({username, email, password}),
            })
                .then(response => response.json().then(data => ({ok: response.ok, data})))
                .then(({ok, data}) => {
                    if (!ok) {
                        authMessage.textContent = data.message || "Registration failed.";
                        return;
                    }
                    currentUser = data.user;
                    authMessage.textContent = "Account created!";
                    updateAuthUI();
                    navigateTo("courses");
                })
                .catch(() => {
                    authMessage.textContent = "Unable to register right now.";
                });
        });
    }

    if (reviewForm) {
        reviewForm.addEventListener("submit", event => {
            event.preventDefault();
            if (!currentUser) {
                authMessage.textContent = "Please login before posting a review.";
                return;
            }

            const difficulty = Number(document.getElementById("difficulty").value);
            const enjoyment = Number(document.getElementById("enjoyment").value);
            const workload = Number(document.getElementById("workload").value);
            const reviewText = document.getElementById("reviewText").value.trim();

            if (!reviewText || !currentCourseId) {
                return;
            }

            fetch(api.reviews, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({
                    courseId: currentCourseId,
                    difficulty,
                    enjoyment,
                    workload,
                    review: reviewText,
                }),
            })
                .then(response => response.json().then(data => ({ok: response.ok, data})))
                .then(({ok, data}) => {
                    if (!ok) {
                        authMessage.textContent = data.message || "Unable to save review.";
                        return;
                    }
                    document.getElementById("reviewText").value = "";
                    authMessage.textContent = "";
                    loadReviews();
                })
                .catch(() => {
                    authMessage.textContent = "Unable to save review.";
                });
        });
    }

    window.addEventListener("hashchange", handleRoute);
}

function init() {
    fetch(api.me)
        .then(response => response.json())
        .then(data => {
            currentUser = data.user || null;
            updateAuthUI();
        })
        .catch(() => {
            currentUser = null;
            updateAuthUI();
        })
        .finally(() => {
            fetch(api.courses)
                .then(response => response.json())
                .then(data => {
                    courses = data;
                    attachEventHandlers();
                    handleRoute();
                })
                .catch(() => {
                    courseContainer.innerHTML = "<p>Unable to load courses.</p>";
                });
        });
}

init();
