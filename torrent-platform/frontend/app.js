const API_BASE = "/api";

let currentUser = null;
let currentTorrentId = null;

// ------------ Gestione Auth ------------

function loadUserFromStorage() {
  const data = localStorage.getItem("currentUser");
  if (data) {
    currentUser = JSON.parse(data);
  }
  updateAuthUI();
}

function saveUserToStorage() {
  if (currentUser) {
    localStorage.setItem("currentUser", JSON.stringify(currentUser));
  } else {
    localStorage.removeItem("currentUser");
  }
}

function updateAuthUI() {
  const currentUserDiv = document.getElementById("current-user");
  const logoutBtn = document.getElementById("logout-btn");

  if (currentUser) {
    currentUserDiv.textContent = `Loggato come: ${currentUser.username} (${currentUser.role})`;
    logoutBtn.style.display = "inline-block";
  } else {
    currentUserDiv.textContent = "Non sei loggato.";
    logoutBtn.style.display = "none";
  }
}

async function registerUser(event) {
  event.preventDefault();
  const username = document.getElementById("reg-username").value;
  const email = document.getElementById("reg-email").value;
  const password = document.getElementById("reg-password").value;

  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password })
  });

  const data = await res.json();
  const msgDiv = document.getElementById("register-message");
  if (!res.ok) {
    msgDiv.textContent = data.error || "Errore registrazione";
  } else {
    msgDiv.textContent = "Registrazione completata. Ora sei loggato.";
    currentUser = data.user;
    saveUserToStorage();
    updateAuthUI();
  }
}

async function loginUser(event) {
  event.preventDefault();
  const username = document.getElementById("login-username").value;
  const password = document.getElementById("login-password").value;

  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password })
  });

  const data = await res.json();
  const msgDiv = document.getElementById("login-message");
  if (!res.ok) {
    msgDiv.textContent = data.error || "Errore login";
  } else {
    msgDiv.textContent = "Login effettuato.";
    currentUser = data.user;
    saveUserToStorage();
    updateAuthUI();
  }
}

function logoutUser() {
  currentUser = null;
  saveUserToStorage();
  updateAuthUI();
}

// ------------ Ricerca Torrent ------------

async function searchTorrents(event) {
  if (event) event.preventDefault();

  const title = document.getElementById("titleSearch").value;
  const desc = document.getElementById("descSearch").value;
  const category = document.getElementById("categorySearch").value;
  const sort = document.getElementById("sortField").value;
  const order = document.getElementById("sortOrder").value;

  const params = new URLSearchParams();
  if (title) params.append("title", title);
  if (desc) params.append("desc", desc);
  if (category) params.append("category", category);
  params.append("sort", sort);
  params.append("order", order);

  const res = await fetch(`${API_BASE}/torrents?` + params.toString());
  const data = await res.json();
  renderResults(data);
}

function renderResults(torrents) {
  const container = document.getElementById("results");
  container.innerHTML = "";

  if (!torrents.length) {
    container.textContent = "Nessun torrent trovato.";
    return;
  }

  torrents.forEach(t => {
    const div = document.createElement("div");
    div.className = "torrent-card";
    div.innerHTML = `
      <h3 class="torrent-title">${t.title}</h3>
      <p>${t.description || ""}</p>
      <p>Dimensione: ${t.sizeBytes} bytes</p>
      <p>Categorie: ${(t.categories || []).join(", ")}</p>
    `;
    div.addEventListener("click", () => {
      loadTorrentDetail(t._id);
    });
    container.appendChild(div);
  });
}

// ------------ Dettaglio torrent & download ------------

async function loadTorrentDetail(torrentId) {
  currentTorrentId = torrentId;

  const detailSection = document.getElementById("detail-section");
  detailSection.style.display = "block";

  const res = await fetch(`${API_BASE}/torrents/${torrentId}`);
  const torrent = await res.json();

  renderTorrentDetail(torrent);
  await loadComments(torrentId);
}

function renderTorrentDetail(t) {
  const detailDiv = document.getElementById("torrent-detail");
  const avg = t.ratingAvg != null ? t.ratingAvg.toFixed(2) : "N/D";

  detailDiv.innerHTML = `
    <h3>${t.title}</h3>
    <p>${t.description || ""}</p>
    <p>Dimensione: ${t.sizeBytes} bytes</p>
    <p>Categorie: ${(t.categories || []).join(", ")}</p>
    <p>Valutazione media: ${avg} (${t.ratingCount || 0} voti)</p>
    <button id="download-btn">Scarica torrent</button>
  `;

  document.getElementById("download-btn").addEventListener("click", () => {
    downloadTorrent(t._id);
  });
}

async function downloadTorrent(torrentId) {
  if (!currentUser) {
    alert("Devi essere loggato per scaricare.");
    return;
  }

  const headers = {};
  if (currentUser) {
    headers["X-User-Id"] = currentUser.id;
  }

  const res = await fetch(`${API_BASE}/torrents/${torrentId}/download`, {
    method: "GET",
    headers
  });

  if (res.headers.get("Content-Type") && res.headers.get("Content-Type").includes("application/json")) {
    const data = await res.json();
    alert(data.message || data.error || "Richiesta download effettuata.");
  } else {
    // qui potresti gestire il download del file .torrent
    alert("Download simulato (in verifica basta la registrazione nel DB).");
  }
}

// ------------ Commenti ------------

async function loadComments(torrentId) {
  const res = await fetch(`${API_BASE}/comments/by-torrent/${torrentId}`);
  const data = await res.json();
  renderComments(data);
}

function renderComments(comments) {
  const listDiv = document.getElementById("comments-list");
  listDiv.innerHTML = "";

  if (!comments.length) {
    listDiv.textContent = "Ancora nessun commento.";
    return;
  }

  comments.forEach(c => {
    const div = document.createElement("div");
    div.className = "comment";
    div.innerHTML = `
      <p>${c.text}</p>
      <small>Voto: ${c.rating} | Autore: ${c.userId} | ${c.createdAt}</small>
    `;
    listDiv.appendChild(div);
  });
}

async function submitComment(event) {
  event.preventDefault();
  if (!currentUser) {
    document.getElementById("comment-message").textContent = "Devi essere loggato.";
    return;
  }

  const text = document.getElementById("comment-text").value;
  const rating = document.getElementById("comment-rating").value;

  const headers = {
    "Content-Type": "application/json",
    "X-User-Id": currentUser.id
  };

  const res = await fetch(`${API_BASE}/comments`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      torrentId: currentTorrentId,
      text,
      rating
    })
  });

  const data = await res.json();
  const msgDiv = document.getElementById("comment-message");
  if (!res.ok) {
    msgDiv.textContent = data.error || "Errore invio commento";
  } else {
    msgDiv.textContent = "Commento inserito.";
    document.getElementById("comment-text").value = "";
    await loadComments(currentTorrentId);
    await loadTorrentDetail(currentTorrentId); // per aggiornare rating medio
  }
}

// ------------ Event listeners ------------

document.addEventListener("DOMContentLoaded", () => {
  loadUserFromStorage();

  document.getElementById("register-form").addEventListener("submit", registerUser);
  document.getElementById("login-form").addEventListener("submit", loginUser);
  document.getElementById("logout-btn").addEventListener("click", logoutUser);
  document.getElementById("search-form").addEventListener("submit", searchTorrents);
  document.getElementById("comment-form").addEventListener("submit", submitComment);

  // prima ricerca vuota (mostra tutti)
  searchTorrents();
});
