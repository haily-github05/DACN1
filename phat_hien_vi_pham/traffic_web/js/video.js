const videoSelect = document.getElementById("videoSelect");
const videoPlayer = document.getElementById("videoPlayer");
const videoSource = document.getElementById("videoSource");
const cameraStream = document.getElementById("cameraStream");

// ======================
// VIDEO LOCAL
// ======================
function loadVideo(src) {
    videoPlayer.style.display = "block";
    cameraStream.style.display = "none";

    videoSource.src = src;
    videoPlayer.load();
    videoPlayer.play();
}

// ======================
// AI STREAM
// ======================
function loadStream(cam) {
    videoPlayer.style.display = "none";
    cameraStream.style.display = "block";

    cameraStream.src = `http://127.0.0.1:5000/video_feed?cam=${cam}`;
}

// ======================
// SWITCH
// ======================
videoSelect.addEventListener("change", function () {
    const value = this.value;

    if (value.includes("videos")) {
        loadVideo(value);
    } else {
        loadStream(value);
    }
});

// ======================
// AUTO LOAD
// ======================
window.onload = function () {
    videoSelect.value = "videos/test1.mp4";
    loadVideo(videoSelect.value);
};