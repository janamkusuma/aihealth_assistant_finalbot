function getToken() {
  return localStorage.getItem("token");
}

function base64UrlDecode(str) {
  str = str.replace(/-/g, "+").replace(/_/g, "/");
  const pad = str.length % 4;
  if (pad) str += "=".repeat(4 - pad);
  return decodeURIComponent(
    atob(str)
      .split("")
      .map(c => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
      .join("")
  );
}

function getUserFromToken(token) {
  try {
    const payload = token.split(".")[1];
    const json = JSON.parse(base64UrlDecode(payload));
    return {
      full_name: json.full_name || "User",
      email: json.email || "",
    };
  } catch (e) {
    return null;
  }
}

function showAuthUI(user) {
  const profileWrap = document.getElementById("profileWrap");
  const authActions = document.getElementById("authActions");

  if (!user) {
    profileWrap.style.display = "none";
    authActions.style.display = "flex";
    return;
  }

  authActions.style.display = "none";
  profileWrap.style.display = "inline-block";

  document.getElementById("dropName").textContent = user.full_name || "User";
  document.getElementById("dropEmail").textContent = user.email || "";
}

function initDropdown() {
  const profileBtn = document.getElementById("profileBtn");
  const dropdown = document.getElementById("dropdown");

  profileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
  });

  document.addEventListener("click", () => {
    dropdown.style.display = "none";
  });
}

function requireLoginForChat() {
  const token = getToken();
  if (!token) {
    window.location.href = "login.html";
    return false;
  }
  const user = getUserFromToken(token);
  if (!user) {
    localStorage.removeItem("token");
    window.location.href = "login.html";
    return false;
  }
  return true;
}

// Buttons
document.getElementById("btnSignIn").addEventListener("click", () => {
  window.location.href = "login.html";
});
document.getElementById("btnSignUp").addEventListener("click", () => {
  window.location.href = "signup.html";
});
document.getElementById("logoutBtn").addEventListener("click", () => {
  localStorage.removeItem("token");
  window.location.href = "login.html";
});

document.getElementById("startChatBtn").addEventListener("click", () => {
  if (requireLoginForChat()) window.location.href = "chatbot.html";
});
document.getElementById("ctaChatBtn").addEventListener("click", () => {
  if (requireLoginForChat()) window.location.href = "chatbot.html";
});

// On load
const token = getToken();
const user = token ? getUserFromToken(token) : null;
showAuthUI(user);
initDropdown();
