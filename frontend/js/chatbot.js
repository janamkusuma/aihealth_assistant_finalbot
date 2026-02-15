import { API_BASE } from "./api.js";

const getToken = () => localStorage.getItem("token");

const authHeaders = () => ({
  "Content-Type": "application/json",
  Authorization: "Bearer " + getToken(),
});

const esc = (s) =>
  (s || "").replace(/[&<>"']/g, (m) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[m]));
function formatIST(isoString) {
  if (!isoString) return "";

  // If backend sends naive ISO like "2026-02-14T13:51:00"
  // treat it as UTC by appending "Z"
  let s = String(isoString).trim();
  if (/^\d{4}-\d{2}-\d{2}T/.test(s) && !/[zZ]|[+\-]\d{2}:\d{2}$/.test(s)) {
    s = s + "Z"; // force UTC
  }

  const d = new Date(s);

  return d.toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true
  }).toLowerCase();
}


let currentChatId = null;
let isSending = false;

const chatListEl = document.getElementById("chatList");
const messagesEl = document.getElementById("messages");
const textInput = document.getElementById("textInput");
const sendBtn = document.getElementById("sendBtn");
const newChatBtn = document.getElementById("newChatBtn");
const logoutBtn = document.getElementById("logout");
const uploadBtn = document.getElementById("uploadBtn");
const fileInput = document.getElementById("fileInput");
const micBtn = document.getElementById("micBtn");
const langSel = document.getElementById("lang");
// ✅ stop current speech when language changes
langSel.addEventListener("change", () => {
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
});

const composerForm = document.getElementById("composerForm");
const soundBtn = document.getElementById("soundBtn");

// ✅ voice on/off (default ON)
let voiceEnabled = localStorage.getItem("voiceEnabled");
voiceEnabled = voiceEnabled === null ? false : voiceEnabled === "true";
setSoundIcon();

// ✅ Protect page
if (!getToken()) window.location.href = "login.html";

// ✅ Logout
logoutBtn.addEventListener("click", () => {
  localStorage.removeItem("token");
  window.location.href = "login.html";
});

// ✅ Close menus on outside click
document.addEventListener("click", () => {
  document.querySelectorAll(".menu-pop").forEach((x) => (x.style.display = "none"));
});

// ✅ sound toggle
soundBtn.addEventListener("click", () => {
  voiceEnabled = !voiceEnabled;
  localStorage.setItem("voiceEnabled", String(voiceEnabled));
  if (!voiceEnabled && "speechSynthesis" in window) window.speechSynthesis.cancel();
  setSoundIcon();
});

function setSoundIcon() {
  soundBtn.textContent = voiceEnabled ? "🔊" : "🔇";
}

// ✅ Smooth scroll
function smoothScrollToBottom() {
  messagesEl.lastElementChild?.scrollIntoView({ behavior: "smooth", block: "end" });
}

// ✅ UI bubbles
function addBubble(role, text) {
  const div = document.createElement("div");
  div.className = "bubble " + (role === "user" ? "user" : "bot");

  if (role !== "user") {
    div.innerHTML = `<div class="doctor-tag">🩺 Doctor</div>${esc(text)}`;
  } else {
    div.textContent = text;
  }

  messagesEl.appendChild(div);
  smoothScrollToBottom();
}

function addTypingBubble() {
  const typing = document.createElement("div");
  typing.className = "bubble bot";
  typing.innerHTML = `
    <div class="doctor-tag">🩺 Doctor</div>
    <span class="typing">
      <span class="dot"></span><span class="dot"></span><span class="dot"></span>
    </span>
  `;
  messagesEl.appendChild(typing);
  smoothScrollToBottom();
  return typing;
}

function setSending(v) {
  isSending = v;
  sendBtn.disabled = v;
  textInput.disabled = v;
}

// ✅ API helper
async function api(path, opts = {}) {
  const res = await fetch(API_BASE + path, opts);

  if (!res.ok) {
    let msg = "Request failed";
    try {
      msg = (await res.json()).detail || msg;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

/* ---------------- Sidebar ---------------- */

function setActiveChatUI(chatId) {
  document.querySelectorAll(".chatitem").forEach((el) => el.classList.remove("active"));
  const active = document.querySelector(`.chatitem[data-id="${chatId}"]`);
  if (active) active.classList.add("active");
}

function updateActiveChatTitleLocally(newTitle) {
  const titleEl = document.querySelector(`.chatitem[data-id="${currentChatId}"] .chat-title`);
  if (titleEl) titleEl.textContent = newTitle;
}

function updateActiveChatTimeFromBackend(updated_at) {
  const metaEl = document.querySelector(`.chatitem[data-id="${currentChatId}"] .chat-meta`);
  if (metaEl && updated_at) metaEl.textContent = formatIST(updated_at);
}


function renderChatList(chats) {
  chatListEl.innerHTML = "";

  chats.forEach((c) => {
    const item = document.createElement("div");
    item.className = "chatitem" + (c.id === currentChatId ? " active" : "");
    item.dataset.id = c.id;

    item.innerHTML = `
      <div class="chat-title">${esc(c.title)}</div>
      <div class="chat-meta">${esc(formatIST(c.updated_at))}</div>

      <button class="chatmenu" type="button">⋮</button>
      <div class="menu-pop" style="display:none">
        <button type="button" data-action="rename">Rename</button>
        <button type="button" data-action="share">Share</button>
        <button type="button" data-action="delete">Delete</button>
      </div>
    `;

    item.addEventListener("click", (e) => {
      if (e.target.classList.contains("chatmenu")) return;
      openChat(c.id);
    });

    const menuBtn = item.querySelector(".chatmenu");
    const pop = item.querySelector(".menu-pop");

    menuBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      document.querySelectorAll(".menu-pop").forEach((x) => {
        if (x !== pop) x.style.display = "none";
      });
      pop.style.display = pop.style.display === "block" ? "none" : "block";
    });

    pop.addEventListener("click", async (e) => {
      e.stopPropagation();
      const action = e.target?.dataset?.action;
      pop.style.display = "none";
      if (!action) return;

      if (action === "rename") {
        const title = prompt("New chat name:");
        if (title) {
          await api(`/chat/${c.id}/rename`, {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({ title }),
          });
          item.querySelector(".chat-title").textContent = title;
        }
      }

      if (action === "delete") {
        if (confirm("Delete this chat?")) {
          await api(`/chat/${c.id}`, {
            method: "DELETE",
            headers: { Authorization: "Bearer " + getToken() },
          });

          item.remove();

          if (currentChatId === c.id) {
            currentChatId = null;
            messagesEl.innerHTML = "";
          }
        }
      }

      if (action === "share") {
        const out = await api(`/chat/${c.id}/share`, {
          method: "POST",
          headers: authHeaders(),
        });
        const shareText = `Share ID: ${out.share_id}`;
        try {
          await navigator.clipboard.writeText(shareText);
          alert("Copied: " + shareText);
        } catch {
          alert(shareText);
        }
      }
    });

    chatListEl.appendChild(item);
  });
}

async function refreshChats(keepScroll = true) {
  const oldScroll = chatListEl.scrollTop;
  const chats = await api("/chat/list", { headers: authHeaders() });
  renderChatList(chats);
  if (keepScroll) chatListEl.scrollTop = oldScroll;
}

/* ---------------- Chat ---------------- */

async function openChat(chatId) {
  currentChatId = chatId;
  setActiveChatUI(chatId);

  messagesEl.innerHTML = "";

  const msgs = await api(`/chat/${chatId}/messages`, { headers: authHeaders() });
  msgs.forEach((m) => addBubble(m.role, m.content));
}

let creatingChat = false;

async function createNewChat() {
  if (creatingChat) return;
  creatingChat = true;

  try {
    const out = await api("/chat/new", { method: "POST", headers: authHeaders() });
    currentChatId = out.id;

    await refreshChats(false);
    await openChat(currentChatId);
  } catch (e) {
    alert("New chat failed: " + e.message);
  } finally {
    creatingChat = false;
  }
}


newChatBtn.addEventListener("click", (e) => {
  e.preventDefault();
  e.stopPropagation();
  createNewChat();
});

/* ---------------- TTS (Bot Voice) ---------------- */

// ---------- LANGUAGE MAPS ----------
const voiceMap = {
  en: "en-IN",
  te: "te-IN",
  hi: "hi-IN",
  ta: "ta-IN",
  kn: "kn-IN",
  ml: "ml-IN",
  mr: "mr-IN",
  bn: "bn-IN",
  gu: "gu-IN",
  ur: "ur-PK" // ur-IN rarely available
};


let availableVoices = [];

function loadVoices() {
  availableVoices = window.speechSynthesis?.getVoices?.() || [];
}
if ("speechSynthesis" in window) {
  loadVoices();
  window.speechSynthesis.onvoiceschanged = loadVoices;
}

function pickVoice(langTag) {
  if (!availableVoices.length) loadVoices();
  if (!availableVoices.length) return null;

  const target = (langTag || "").toLowerCase();

  // 1) exact match
  let v = availableVoices.find(x => (x.lang || "").toLowerCase() === target);
  if (v) return v;

  // 2) match by language prefix (hi, te, en)
  const prefix = target.split("-")[0];
  v = availableVoices.find(x => (x.lang || "").toLowerCase().startsWith(prefix));
  if (v) return v;

  // 3) try India voices
  v = availableVoices.find(x => (x.lang || "").toLowerCase().endsWith("-in"));
  if (v) return v;

  // 4) fallback any English voice
  v = availableVoices.find(x => (x.lang || "").toLowerCase().startsWith("en"));
  return v || null;
}


// remove bullet/number formatting so it won’t read "1 2 3 4"
function cleanForSpeech(text) {
  let t = (text || "").trim();

  // Remove markdown bullets like "- ", "* ", "• "
  t = t.replace(/^\s*[-*•]\s+/gm, "");

  // Remove numbering like "1) ", "1. "
  t = t.replace(/^\s*\d+\s*[\.\)]\s+/gm, "");

  // remove extra symbols
  t = t.replace(/[#*_`~]/g, "");
  return t;
}

function speakText(text) {
  if (!voiceEnabled) return;
  if (!("speechSynthesis" in window)) return;

  window.speechSynthesis.cancel();

  const langCode = langSel.value;
  const langTag = voiceMap[langCode] || "en-IN";

  const utter = new SpeechSynthesisUtterance(cleanForSpeech(text));
  utter.lang = langTag;

  const voice = pickVoice(langTag);
  if (voice) utter.voice = voice;

  utter.rate = 1;
  utter.pitch = 1;

  window.speechSynthesis.speak(utter);
}


/* ---------------- Send Message ---------------- */

async function sendMessage() {
  if (isSending) return;

  const text = (textInput.value || "").trim();
  if (!text) return;

  if (!currentChatId) await createNewChat();

  addBubble("user", text);
  textInput.value = "";

  const typing = addTypingBubble();
  setSending(true);

  try {
    const out = await api(`/chat/${currentChatId}/send`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ message: text, language: langSel.value }),
    });

    typing.remove();
    const reply = out.reply || "No response";
    addBubble("assistant", out.reply || "No response");
    speakText(out.reply || "");


    if (out.chat_title) updateActiveChatTitleLocally(out.chat_title);
    if (out.updated_at) updateActiveChatTimeFromBackend(out.updated_at);
  } catch (e) {
    typing.remove();
    addBubble("assistant", "Error: " + e.message);
  } finally {
    setSending(false);
    textInput.focus();
  }
}

sendBtn.addEventListener("click", (e) => {
  e.preventDefault();
  e.stopPropagation();
  sendMessage();
});

textInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    e.stopPropagation();
    sendMessage();
  }
});

composerForm.addEventListener("submit", (e) => {
  e.preventDefault();
  sendMessage();
});

/* ---------------- Upload ---------------- */

uploadBtn.addEventListener("click", (e) => {
  e.preventDefault();
  e.stopPropagation();

  if (!currentChatId) {
    alert("Create a chat first (New Chat).");
    return;
  }
  fileInput.click();
});

fileInput.addEventListener("change", async () => {
  if (!fileInput.files?.length) return;
  if (!currentChatId) return;

  for (const file of fileInput.files) {
    const fd = new FormData();
    fd.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/chat/${currentChatId}/upload`, {
        method: "POST",
        headers: { Authorization: "Bearer " + getToken() },
        body: fd,
      });
      if (!res.ok) throw new Error("Upload failed");
      addBubble("assistant", `✅ Uploaded: ${file.name}`);
    } catch {
      addBubble("assistant", `❌ Upload failed: ${file.name}`);
    }
  }
  fileInput.value = "";
});

/* ---------------- Mic (Speech to Text) ---------------- */

let recog = null;

micBtn.addEventListener("click", (e) => {
  e.preventDefault();
  e.stopPropagation();

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    alert("Mic not supported. Use Chrome.");
    return;
  }

  if (!recog) {
    recog = new SR();
    recog.continuous = false;
    recog.interimResults = false;

    recog.onresult = (event) => {
      let spoken = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        spoken += event.results[i][0].transcript;
      }
      spoken = (spoken || "").trim();
      if (!spoken) return;

      textInput.value = spoken;
      sendMessage();
    };

    recog.onerror = (err) => {
      console.log("Mic error:", err);
      alert("Mic error: " + err.error);
    };
  }

  recog.lang = voiceMap[langSel.value] || "en-IN";
  recog.start();
});

/* ---------------- Init ---------------- */

(async function init() {
  await refreshChats(false);
})();
