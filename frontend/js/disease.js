import { API_BASE } from "./api.js";

const token = localStorage.getItem("token");
if (!token) location.href = "login.html";

const headers = { Authorization: "Bearer " + token };

document.getElementById("logoutBtn").onclick = () => {
  localStorage.removeItem("token");
  location.href = "login.html";
};

const groupedEl = document.getElementById("grouped");
const searchEl = document.getElementById("search");
const catEl = document.getElementById("category");

function groupByCategory(items) {
  const g = {};
  for (const d of items) {
    (g[d.category] ||= []).push(d);
  }
  return g;
}

async function load() {
  const q = encodeURIComponent(searchEl.value.trim());
  const c = encodeURIComponent(catEl.value);

  const url = `${API_BASE}/diseases/list?q=${q}&category=${c}`;
  const res = await fetch(url, { headers });
  const data = await res.json();

  const groups = groupByCategory(data);

  groupedEl.innerHTML = "";

  Object.keys(groups).forEach(category => {
    const section = document.createElement("section");
    section.className = "group-section";
    section.innerHTML = `<h3 class="group-title">${category}</h3>`;

    const grid = document.createElement("div");
    grid.className = "disease-grid";

    groups[category].forEach(d => {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "disease-card";
      card.innerHTML = `
        <div class="disease-img">
          <img src="${d.image || ""}" alt="${d.name}" />
        </div>
        <div class="disease-meta">
          <div class="disease-name">${d.name}</div>
          <div class="disease-cat">${d.category}</div>
        </div>
      `;
      card.onclick = () => location.href = `disease_detail.html?id=${d.id}`;
      grid.appendChild(card);
    });

    section.appendChild(grid);
    groupedEl.appendChild(section);
  });
}

searchEl.addEventListener("input", load);
catEl.addEventListener("change", load);

load();
