document.addEventListener("DOMContentLoaded", () => {

    let path = window.location.pathname
        .replace(/\/+$/, "")       // убираем лишний / в конце
        .split("/")[1] || "home";  // получаем сегмент

    document.querySelectorAll(".menu a").forEach(link => {

        let page = link.dataset.page;

        // точное совпадение или вложенный путь
        if (page === path || window.location.pathname.startsWith("/" + page)) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");  // предотвращает двойную подсветку
        }
    });
});












document.addEventListener("DOMContentLoaded", () => {
    const btn = document.getElementById("lang-btn");
    const menu = document.querySelector(".lang-menu");

    btn.addEventListener("click", () => {
        menu.style.display = menu.style.display === "block" ? "none" : "block";
    });

    menu.querySelectorAll("div").forEach(option => {
        option.addEventListener("click", () => {
            btn.innerText = option.innerText.split(" ")[0];
            localStorage.setItem("language", option.dataset.lang);
            menu.style.display = "none";
        });
    });

    let saved = localStorage.getItem("language");
    if (saved) btn.innerText = saved.toUpperCase();
});


















async function searchUniversities() {
    let q = document.getElementById("searchInput").value;
    let city = document.getElementById("citySelect").value;

    let res = await fetch(`/api/search?q=${encodeURIComponent(q)}&city=${encodeURIComponent(city)}`);
    let data = await res.json();

    let info = document.getElementById("resultInfo");
    let grid = document.getElementById("resultsGrid");

    grid.innerHTML = "";

    if (data.length > 0) {
        info.textContent = `Найдено ${data.length} университетов по вашему запросу`;
    } else {
        info.textContent = "Ничего не найдено. Попробуйте изменить запрос.";
    }

    data.forEach(u => {
        let card = `
            <div class="card">
                <img src="${u.image}">
                <div class="card-content">
                    <h3 class="card-title">${u.name}</h3>
                    <p class="card-city">${u.city}</p>
                    <p class="card-desc">${u.description}</p>
                </div>
            </div>
        `;
        grid.innerHTML += card;
    });
}

// live search
document.getElementById("searchInput").addEventListener("input", searchUniversities);
document.getElementById("citySelect").addEventListener("change", searchUniversities);