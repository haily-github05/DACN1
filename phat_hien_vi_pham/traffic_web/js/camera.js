const cameraStream = document.getElementById("cameraStream");
const cameraSelect = document.getElementById("cameraSelect");

// ======================
// LOAD CAMERA AI STREAM
// ======================
function loadCamera(cam) {
    cameraStream.src = `http://127.0.0.1:5000/video_feed?cam=${cam}`;
}

// default load
window.addEventListener("DOMContentLoaded", () => {
    loadCamera("Camera 1");
});

// change camera
cameraSelect.addEventListener("change", function () {
    loadCamera(this.value);
});