let viewer = null;
let currentSceneId = null;
let tourJson = null;

async function loadTour(id) {
    const res = await fetch(`/api/tour/${id}`);
    tourJson = await res.json();

    const scenes = {};
    for (const [sceneId, scene] of Object.entries(tourJson.scenes)) {
        scenes[sceneId] = {
            title: scene.title,
            type: "equirectangular",
            panorama: `/static/tour/panoramas/${scene.image}`,
            hotSpots: (scene.hotspots || []).map(h => ({
                pitch: 0,
                yaw: Math.floor(Math.random()*360),
                type: "scene",
                text: h.text,
                sceneId: h.to
            }))
        };
    }

    viewer = pannellum.viewer("panorama", {
        default: {
            firstScene: tourJson.startScene,
            sceneFadeDuration: 800
        },
        scenes
    });

    currentSceneId = tourJson.startScene;

    viewer.on("scenechange", newSceneChangeHandler);
}

/* === РЕЧЬ АССИСТЕНТА === */
function assistantSpeak(text) {
    const bubble = document.getElementById("assistantSpeech");
    const bubbleText = document.getElementById("assistantSpeechText");

    bubbleText.innerText = text;
    bubble.style.display = "block";
    setTimeout(() => bubble.style.opacity = 1, 30);

    setTimeout(() => {
        bubble.style.opacity = 0;
        setTimeout(() => bubble.style.display = "none", 400);
    }, 6000);
}

/* === ЧАТ === */
function appendMessage(text, from="ai") {
    const box = document.getElementById("chatMessages");
    const msg = document.createElement("div");
    msg.className = "msg " + from;
    msg.innerText = text;
    box.appendChild(msg);
    box.scrollTop = box.scrollHeight;
}

async function sendToAssistant(message) {
    appendMessage(message, "user");

    const payload = {
        tour_id: TOUR_ID,
        current_scene: currentSceneId,
        message
    };

    const res = await fetch("/api/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    const data = await res.json();
    appendMessage(data.text || "Ошибка", "ai");
}

/* === ПЕРЕХОД СЦЕНЫ === */
async function newSceneChangeHandler(newSceneId) {
    currentSceneId = newSceneId;

    document.getElementById("aiAvatarImg").src = "/static/ai/thinking.png";

    const res = await fetch("/api/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            tour_id: TOUR_ID,
            current_scene: currentSceneId,
            message: "__mini_info__"
        })
    });

    const data = await res.json();
    document.getElementById("aiAvatarImg").src = "/static/ai/answer.png";

    assistantSpeak(data.text || "Описание места недоступно.");
}

/* === ИНИЦИАЛИЗАЦИЯ === */
document.addEventListener("DOMContentLoaded", () => {
    loadTour(TOUR_ID);

    document.getElementById("sendBtn").addEventListener("click", () => {
        const v = document.getElementById("chatText").value.trim();
        if (!v) return;
        sendToAssistant(v);
        document.getElementById("chatText").value = "";
    });
});
