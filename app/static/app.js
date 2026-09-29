// Универсальные функции
async function api(path, body) {
    const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    const text = await res.text();
    const data = text ? JSON.parse(text) : {};
    if (!res.ok) {
        throw new Error(data.detail || `HTTP ${res.status}`);
    }
    return data;
}

async function gql(query, variables = {}) {
    const token = localStorage.getItem("token");
    const res = await fetch("/graphql/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...(token ? { "Authorization": `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ query, variables }),
    });
    const data = await res.json();
    if (data.errors && data.errors.length) {
        throw new Error(data.errors.map(e => e.message).join("; "));
    }
    return data.data;
}

// UI helpers
const $ = (id) => document.getElementById(id);

function showError(msg) {
    $("error").textContent = msg || "";
}

function showStatus(msg) {
    $("status").textContent = msg || "";
}

function setLoggedIn(loggedIn) {
    $("login-block").classList.toggle("hidden", loggedIn);
    $("admin-block").classList.toggle("hidden", !loggedIn);
}

// Логин
$("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    showError("");
    showStatus("Входим...");
    try {
        const data = await api("/auth/login", {
            email: $("email").value,
            password: $("password").value,
        });
        localStorage.setItem("token", data.access_token);
        showStatus("Вошли");
        setLoggedIn(true);
        await loadClients();
    } catch (err) {
        showStatus("");
        showError("Ошибка входа: " + err.message);
    }
});

// Выход
$("logout-btn").addEventListener("click", () => {
    localStorage.removeItem("token");
    setLoggedIn(false);
    showStatus("");
    showError("");
});

// Загрузка клиентов
async function loadClients() {
    showError("");
    try {
        const data = await gql(`query { clients { id clientId name isConfidential createdAt } }`);
        const tbody = document.querySelector("#clients-table tbody");
        tbody.innerHTML = "";
        for (const c of data.clients) {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${c.id}</td>
                <td>${c.clientId}</td>
                <td>${c.name}</td>
                <td>${c.isConfidential}</td>
                <td>${c.createdAt}</td>
            `;
            tbody.appendChild(tr);
        }
    } catch (err) {
        showError("Ошибка загрузки клиентов: " + err.message);
    }
}

// Создать клиента
$("create-client-btn").addEventListener("click", async () => {
    const name = prompt("Имя клиента:");
    if (!name) return;
    showError("");
    try {
        await gql(
            `mutation($name: String!) { createClient(name: $name) { id clientId name } }`,
            { name }
        );
        await loadClients();
    } catch (err) {
        showError("Ошибка создания клиента: " + err.message);
    }
});

// Автологин при загрузке (если токен есть)
window.addEventListener("DOMContentLoaded", async () => {
    const token = localStorage.getItem("token");
    if (token) {
        setLoggedIn(true);
        await loadClients();
    }
});