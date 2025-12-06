document.addEventListener("DOMContentLoaded", () => {

    const navLinks = document.querySelectorAll(".nav-link");

    // 1) Подсветка при клике
    navLinks.forEach(link => {
        link.addEventListener("click", () => {
            navLinks.forEach(l => l.classList.remove("active"));
            link.classList.add("active");
        });
    });

    // 2) Автоматическая подсветка по URL
    let path = window.location.pathname
        .replace(/\/+$/, "")      // удаляем лишний слэш
        .split("/")[1] || "home"; // получаем сегмент

    navLinks.forEach(link => {
        let page = link.dataset.page; // берем у ссылки data-page

        if (page === path || window.location.pathname.startsWith("/" + page)) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
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














const track = document.querySelector('.carousel-track');
const leftBtn = document.querySelector('.arrow.left');
const rightBtn = document.querySelector('.arrow.right');

let cards = Array.from(track.children);
let total = cards.length;
let index = 0;
let gap = 40;

// клонируем карточки
cards.forEach(card => {
    track.appendChild(card.cloneNode(true));
});

let cardWidth = cards[0].offsetWidth + gap;

function move() {
    track.style.transition = "transform 0.5s ease";
    track.style.transform = `translateX(${-index * cardWidth}px)`;
}

rightBtn.addEventListener("click", () => {
    index++;
    move();

    if (index >= total) {
        setTimeout(() => {
            track.style.transition = "none";
            index = 0;
            track.style.transform = `translateX(0px)`;
        }, 500);
    }
});

leftBtn.addEventListener("click", () => {
    if (index <= 0) {
        track.style.transition = "none";
        index = total;
        track.style.transform = `translateX(${-index * cardWidth}px)`;
        setTimeout(() => {
            track.style.transition = "transform 0.5s ease";
            index--;
            move();
        }, 20);
    } else {
        index--;
        move();
    }
});

window.addEventListener("resize", () => {
    cardWidth = cards[0].offsetWidth + gap;
    move();
});









document.addEventListener("DOMContentLoaded", () => {

    const text =
        "Edu Navigator KZ — это не просто каталог вузов. " +
        "Это инструмент, который помогает молодым людям увидеть варианты будущего, " +
        "понять себя и сделать осознанный выбор.";

    const typingElement = document.getElementById("typing-text");
    let started = false; // защита — одна печать

    function typeWriter(i = 0) {
        if (i < text.length) {
            typingElement.textContent += text.charAt(i);
            setTimeout(() => typeWriter(i + 1), 45);
        } else {
            typingElement.style.borderRight = "none";
        }
    }

    function checkVisible() {
        const rect = typingElement.getBoundingClientRect();

        if (!started && rect.top < window.innerHeight * 0.85) {
            started = true;
            typeWriter();
        }
    }

    window.addEventListener("scroll", checkVisible);
    checkVisible();
});