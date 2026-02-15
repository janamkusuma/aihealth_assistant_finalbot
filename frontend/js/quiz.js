import { API_BASE } from "./api.js";

const token = localStorage.getItem("token");
if (!token) location.href = "login.html";

const headersJSON = {
  "Content-Type": "application/json",
  Authorization: "Bearer " + token
};
const headersAuth = { Authorization: "Bearer " + token };

document.getElementById("logoutBtn").onclick = () => {
  localStorage.removeItem("token");
  location.href = "login.html";
};

// ✅ You can add more questions here (10 shown)
const QUESTIONS = [
  { q: "Strongest bone?", options: ["Jaw", "Femur", "Skull", "Rib"], ans: 1 },
  { q: "Normal body temperature (approx)?", options: ["35°C", "37°C", "39°C", "41°C"], ans: 1 },
  { q: "ORS is mainly used for?", options: ["Pain relief", "Rehydration", "Sleep", "Allergy"], ans: 1 },
  { q: "Which organ pumps blood?", options: ["Lungs", "Kidney", "Heart", "Liver"], ans: 2 },
  { q: "Vitamin from sunlight?", options: ["Vit A", "Vit B12", "Vit C", "Vit D"], ans: 3 },
  { q: "Dengue spreads by?", options: ["Housefly", "Mosquito", "Water", "Food"], ans: 1 },
  { q: "High BP is called?", options: ["Hypotension", "Hypertension", "Diabetes", "Asthma"], ans: 1 },
  { q: "Which is a respiratory disease?", options: ["Pneumonia", "Gastritis", "Diabetes", "Ulcer"], ans: 0 },
  { q: "Main symptom of dehydration?", options: ["Wet skin", "Dark urine", "High hair growth", "Blue nails"], ans: 1 },
  { q: "Handwashing helps prevent?", options: ["Infections", "Broken bones", "All cancers", "None"], ans: 0 }
];

const beginBtn = document.getElementById("beginBtn");
const restartBtn = document.getElementById("restartBtn");
const nextBtn = document.getElementById("nextBtn");

const quizStart = document.getElementById("quizStart");
const quizBox = document.getElementById("quizBox");
const resultBox = document.getElementById("resultBox");

const qnoEl = document.getElementById("qno");
const timerEl = document.getElementById("timer");
const questionEl = document.getElementById("question");
const optionsEl = document.getElementById("options");
const statusEl = document.getElementById("status");
const scoreText = document.getElementById("scoreText");

let idx = 0;
let score = 0;
let timeLeft = 15;
let t = null;
let locked = false;

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// If you want random order each time:
const QUIZ = shuffle(QUESTIONS);

function startTimer() {
  clearInterval(t);
  timeLeft = 15;
  timerEl.textContent = timeLeft;

  t = setInterval(() => {
    timeLeft--;
    timerEl.textContent = timeLeft;
    if (timeLeft <= 0) {
      clearInterval(t);
      lockOptions(null); // timed out
      nextBtn.disabled = false;
      statusEl.innerHTML = `<span class="bad">⏱️ Time up!</span>`;
    }
  }, 1000);
}

function renderQuestion() {
  locked = false;
  nextBtn.disabled = true;
  statusEl.textContent = "";

  const total = QUIZ.length;
  const item = QUIZ[idx];

  qnoEl.textContent = `Q${idx + 1}/${total}`;
  questionEl.textContent = item.q;

  optionsEl.innerHTML = "";
  const letters = ["A", "B", "C", "D"];

  item.options.forEach((opt, i) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "quiz-opt";
    btn.innerHTML = `
      <span class="quiz-letter">${letters[i]}</span>
      <span class="quiz-text">${opt}</span>
      <span class="quiz-mark"></span>
    `;
    btn.onclick = () => {
      if (locked) return;
      lockOptions(i);
      nextBtn.disabled = false;
    };
    optionsEl.appendChild(btn);
  });

  startTimer();
}

function lockOptions(selectedIndex) {
  locked = true;
  clearInterval(t);

  const item = QUIZ[idx];
  const correct = item.ans;

  const btns = [...optionsEl.querySelectorAll(".quiz-opt")];

  btns.forEach((b, i) => {
    b.disabled = true;
    const mark = b.querySelector(".quiz-mark");

    if (i === correct) {
      b.classList.add("correct");
      mark.textContent = "✓ Correct";
    }

    if (selectedIndex !== null && i === selectedIndex && selectedIndex !== correct) {
      b.classList.add("wrong");
      mark.textContent = "✗ Wrong";
    }
  });

  if (selectedIndex === correct) {
    score++;
    statusEl.innerHTML = `<span class="good">✅ Correct!</span>`;
  } else if (selectedIndex === null) {
    statusEl.innerHTML = `<span class="bad">⏱️ No answer selected</span>`;
  } else {
    statusEl.innerHTML = `<span class="bad">❌ Wrong</span>`;
  }
}

async function saveScore() {
  // ✅ adjust this endpoint if your backend uses different path
  // common in your project: /api/quiz/save
  try {
    await fetch(`${API_BASE}/api/quiz/save`, {
      method: "POST",
      headers: headersJSON,
      body: JSON.stringify({ score, total: QUIZ.length })
    });
  } catch (e) {
    // ignore if backend missing
  }
}

function showResult() {
  quizBox.style.display = "none";
  resultBox.style.display = "block";
  scoreText.textContent = `Your Score: ${score} / ${QUIZ.length}`;
  saveScore();
}

function begin() {
  idx = 0;
  score = 0;

  quizStart.style.display = "none";
  resultBox.style.display = "none";
  quizBox.style.display = "block";

  renderQuestion();
}

nextBtn.onclick = () => {
  idx++;
  if (idx >= QUIZ.length) {
    showResult();
  } else {
    renderQuestion();
  }
};

beginBtn.onclick = begin;
restartBtn.onclick = () => location.reload();
