// Game & Auth State Variables
let currentScore = 0;
let currentXP = 0;
let currentStreak = 0;
let isLoggedIn = false;
let isLoginMode = true; // Tracks if the modal is on "Login" or "Register"

// ==========================================
// 1. AUTHENTICATION & MODAL LOGIC
// ==========================================

function openModal() {
    document.getElementById("loginModal").style.display = "block";
}

function closeModal() {
    document.getElementById("loginModal").style.display = "none";
    document.getElementById("auth-message").innerText = ""; // Clear errors
}

function toggleAuthMode() {
    isLoginMode = !isLoginMode;
    document.getElementById("modal-title").innerText = isLoginMode ? "Ninja Login" : "Academy Registration";
    document.getElementById("auth-submit").innerText = isLoginMode ? "Enter Academy" : "Create Account";
    document.getElementById("auth-toggle-text").innerText = isLoginMode ? "Need an account?" : "Already a ninja?";
    document.getElementById("auth-message").innerText = ""; // Clear errors
}

async function attemptAuth() {
    const usernameInput = document.getElementById("username").value;
    const passwordInput = document.getElementById("password").value;
    const messageEl = document.getElementById("auth-message");

    if (!usernameInput || !passwordInput) {
        messageEl.style.color = "#ff4d4d";
        messageEl.innerText = "Please fill in both fields.";
        return;
    }

    const endpoint = isLoginMode ? "/api/login" : "/api/register";

    try {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: usernameInput, password: passwordInput })
        });

        const data = await response.json();

        if (response.ok) {
            if (isLoginMode) {
                // Successfully Logged In
                isLoggedIn = true;

                // Save to localStorage for the dashboard page to pick up
                localStorage.setItem('ninja_xp', data.xp);
                localStorage.setItem('ninja_streak', data.streak);
                localStorage.setItem('ninja_score', data.score);
                localStorage.setItem('ninja_username', data.username);

                // Redirect to dashboard
                window.location.href = "/dashboard";
            } else {
                // Successfully Registered
                messageEl.style.color = "#00ffcc";
                messageEl.innerText = "Account created! You can now log in.";
                setTimeout(() => toggleAuthMode(), 1500); // Automatically switch to login screen
            }
        } else {
            // Error (e.g., Wrong password or Username taken)
            messageEl.style.color = "#ff4d4d";
            messageEl.innerText = data.error || "An error occurred.";
        }
    } catch (error) {
        console.error("Auth Error:", error);
        messageEl.innerText = "Server connection failed.";
    }
}

async function logout() {
    await fetch("/api/logout", { method: "POST" });
    isLoggedIn = false;

    // Clear localStorage
    localStorage.removeItem('ninja_xp');
    localStorage.removeItem('ninja_streak');
    localStorage.removeItem('ninja_score');
    localStorage.removeItem('ninja_username');
    localStorage.removeItem('ninja_rank');

    // Redirect to home
    window.location.href = "/";
}

async function saveStatsToServer(options = {}) {
    if (!isLoggedIn && !localStorage.getItem('ninja_username')) return;

    try {
        const payload = {
            score: currentScore,
            xp: currentXP,
            streak: currentStreak,
            ...options
        };

        const response = await fetch("/api/save_stats", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const data = await response.json();
            if (data.rank) {
                localStorage.setItem('ninja_rank', data.rank);
                localStorage.setItem('ninja_xp', currentXP);
                localStorage.setItem('ninja_streak', currentStreak);
            }
        }
    } catch (error) {
        console.error("Failed to save stats:", error);
    }
}

// ==========================================
// 2. QUIZ GENERATION & GAMEPLAY LOGIC
// ==========================================

async function generateQuiz() {
    const topic = document.getElementById("topic").value;
    const num_questions = document.getElementById("num_questions").value || 5;

    if (!topic) {
        alert("Please enter a topic!");
        return;
    }

    const container = document.getElementById("quizContainer");
    container.innerHTML = "<h3>Generating your quiz...</h3>";
    container.classList.remove("fade-in");

    try {
        const response = await fetch("/api/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ topic: topic, num_questions: num_questions })
        });

        const data = await response.json();
        displayQuiz(data.quiz);
    } catch (error) {
        container.innerHTML = "<h3>Error generating quiz.</h3>";
        console.error(error);
    }
}

async function uploadFile() {
    const fileInput = document.getElementById("fileInput");

    if (!fileInput.files.length) {
        alert("Please select a file to upload first!");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const container = document.getElementById("quizContainer");
    container.innerHTML = "<h3>Reading file and generating quiz...</h3>";
    container.classList.remove("fade-in");

    try {
        const response = await fetch("/api/upload", {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        displayQuiz(data.quiz);
    } catch (error) {
        container.innerHTML = "<h3>Error uploading file.</h3>";
        console.error(error);
    }
}

let questionsAttempted = 0;
let totalQuestionsInQuiz = 0;
let currentTopic = "";
let currentQuizScore = 0;

function displayQuiz(quizArray) {
    const container = document.getElementById("quizContainer");
    container.innerHTML = "";

    if (!quizArray || quizArray.length === 0) {
        container.innerHTML = "<p>No questions could be generated. Please try again.</p>";
        return;
    }

    questionsAttempted = 0;
    currentQuizScore = 0;
    totalQuestionsInQuiz = quizArray.length;
    currentTopic = document.getElementById("topic").value || "File Upload";

    quizArray.forEach((item, index) => {
        const questionDiv = document.createElement("div");
        questionDiv.className = "card";

        questionDiv.innerHTML = `<h3>Q${index + 1}. ${item.question}</h3>`;

        const safeAnswer = item.answer.replace(/'/g, "\\'");

        item.options.forEach(option => {
            const optionDiv = document.createElement("div");
            optionDiv.className = "quiz-option";

            optionDiv.innerHTML = `
                <label style="cursor: pointer; display: block;">
                    <input type="radio" name="q${index}" value="${option}" onclick="checkAnswer(this, '${safeAnswer}')">
                    ${option}
                </label>
            `;
            questionDiv.appendChild(optionDiv);
        });

        container.appendChild(questionDiv);
    });

    setTimeout(() => container.classList.add("fade-in"), 10);
}

function checkAnswer(radioInput, correctAnswer) {
    const selectedValue = radioInput.value;
    const allOptions = document.getElementsByName(radioInput.name);

    allOptions.forEach(opt => opt.disabled = true);
    const optionDiv = radioInput.closest('.quiz-option');

    questionsAttempted++;

    if (selectedValue === correctAnswer) {
        optionDiv.classList.add("correct-pulse");
        updateStats(true);
    } else {
        optionDiv.classList.add("wrong-shake");

        allOptions.forEach(opt => {
            if (opt.value === correctAnswer) {
                const correctDiv = opt.closest('.quiz-option');
                correctDiv.style.color = "#00ffcc";
                correctDiv.style.fontWeight = "bold";
            }
        });
        updateStats(false);
    }

    // If all questions are done, send a completion save
    if (questionsAttempted === totalQuestionsInQuiz) {
        saveStatsToServer({
            quiz_completed: true,
            topic: currentTopic,
            score: currentQuizScore,
            total_questions: totalQuestionsInQuiz
        });
    }
}

function updateStats(isCorrect) {
    if (isCorrect) {
        currentStreak += 1;
        currentScore += 10;
        currentQuizScore += 1;
        let multiplier = currentStreak > 5 ? 5 : currentStreak;
        currentXP += (25 * multiplier);
    } else {
        currentStreak = 0;
    }

    updateStatsUI();

    // Save minimal progress
    saveStatsToServer();
}

function updateStatsUI() {
    let rank = "Academy Student";
    if (currentXP >= 100) rank = "Genin";
    if (currentXP >= 300) rank = "Chunin";
    if (currentXP >= 600) rank = "Jonin";
    if (currentXP >= 1000) rank = "Hokage";

    const scoreEl = document.getElementById("score");
    if (scoreEl) scoreEl.innerText = currentScore;

    let xpElement = document.getElementById("xp");
    if (xpElement) xpElement.innerText = `${currentXP} (Rank: ${rank})`;

    let streakText = currentStreak >= 3 ? `${currentStreak} 🔥` : currentStreak;
    let streakElement = document.getElementById("streak");
    if (streakElement) streakElement.innerText = streakText;
}

// Auto-load state on session start
document.addEventListener('DOMContentLoaded', () => {
    const savedUser = localStorage.getItem('ninja_username');
    if (savedUser) {
        isLoggedIn = true;
        currentXP = parseInt(localStorage.getItem('ninja_xp') || '0');
        currentStreak = parseInt(localStorage.getItem('ninja_streak') || '0');
        currentScore = parseInt(localStorage.getItem('ninja_score') || '0');

        const userDisp = document.getElementById("user-display");
        if (userDisp) {
            userDisp.innerText = `Welcome, ${savedUser}!`;
            userDisp.style.display = "inline";
        }

        const loginBtn = document.getElementById("login-btn");
        if (loginBtn) loginBtn.style.display = "none";

        const logoutBtn = document.getElementById("logout-btn");
        if (logoutBtn) logoutBtn.style.display = "inline";

        const dashboardBtn = document.getElementById("dashboard-btn");
        if (dashboardBtn) dashboardBtn.style.display = "inline";

        updateStatsUI();
    }
});