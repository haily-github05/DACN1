const videoSelect = document.getElementById("videoSelect");
const videoPlayer = document.getElementById("videoPlayer");

async function loadVideos() {
    try {
        const res = await fetch("http://127.0.0.1:5000/videos");

        if (!res.ok) {
            throw new Error("Không thể lấy danh sách video!");
        }

        const data = await res.json();

        // reset dropdown
        videoSelect.innerHTML = "";

        if (data.length === 0) {
            const option = document.createElement("option");
            option.textContent = "Không có video";
            videoSelect.appendChild(option);
            return;
        }

        // add option
        data.forEach(video => {
            const option = document.createElement("option");
            option.value = video.path;
            option.textContent = video.name;
            videoSelect.appendChild(option);
        });

        // autoplay video đầu tiên
        playVideo(data[0].path);

    } catch (error) {
        console.error("❌ Lỗi load video:", error);
        showError("Không tải được danh sách video!");
    }
}

function playVideo(path) {
    if (!path) return;

    videoPlayer.style.display = "block";

    // ✅ FIX Ở ĐÂY
    const videoURL = `http://127.0.0.1:5000/videos/${path}`;

    videoPlayer.src = videoURL;
    videoPlayer.load();

    videoPlayer.play().catch(err => {
        console.warn("⚠️ Autoplay bị chặn:", err);
    });

    console.log("🎬 Đang phát:", videoURL);
}

videoSelect.addEventListener("change", function () {
    const selectedPath = this.value;
    playVideo(selectedPath);
});

function showError(message) {
    videoPlayer.style.display = "none";

    let errorBox = document.getElementById("videoError");

    if (!errorBox) {
        errorBox = document.createElement("div");
        errorBox.id = "videoError";
        errorBox.style.color = "red";
        errorBox.style.marginTop = "15px";
        errorBox.style.fontWeight = "600";
        videoPlayer.parentElement.appendChild(errorBox);
    }

    errorBox.textContent = message;
}

videoPlayer.addEventListener("error", () => {
    console.error("❌ Không load được video");
    showError("Video không tồn tại hoặc lỗi server!");
});
videoPlayer.addEventListener("waiting", () => {
    console.log("⏳ Đang load video...");
});

videoPlayer.addEventListener("playing", () => {
    console.log("✅ Video đang chạy");
});

window.addEventListener("DOMContentLoaded", () => {
    loadVideos();
});