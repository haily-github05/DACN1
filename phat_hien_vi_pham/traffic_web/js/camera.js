function formatStatus(status) {
    switch (status) {
        case "pending":
            return "Chờ xử lý";

        case "approved":
            return "Đã xử lý";

        case "rejected":
            return "Từ chối";
        case "unknown": return "Không xác định";
        default:
            return status || "Chờ xử lý";
    }
}
// =========================
// ELEMENTS
// =========================
const video = document.getElementById("videoPlayer");
video.playbackRate = 0.5;
const overlay = document.getElementById("overlayCanvas");
const ctx = overlay.getContext("2d");
const captureCanvas = document.getElementById("captureCanvas");
const captureCtx = captureCanvas.getContext("2d");

const videoScanResult = document.getElementById("videoScanResult");
const imageScanResult = document.getElementById("imageScanResult");

const btnStartScan = document.getElementById("btnStartScan");
const btnStopScan = document.getElementById("btnStopScan");
const btnPlayPause = document.getElementById("btnPlayPause"); 

const tableBody = document.getElementById("tableBody");

// IMAGE & TABS
const imageInput = document.getElementById("imageInput");
const btnScanImage = document.getElementById("btnScanImage");
const previewImage = document.getElementById("previewImage");
const imageCanvas = document.getElementById("imageCanvas");
const imageCtx = imageCanvas.getContext("2d");

const tabVideo = document.getElementById("tabVideo");
const tabImage = document.getElementById("tabImage");
const videoSection = document.getElementById("videoSection");
const imageSection = document.getElementById("imageSection");

// =========================
// STATE & CONFIG
// =========================
let autoScan = false;
let isVideoScanning = false;
let videoRequestId = 0;
let scanLoopTimeout = null;
const videoViolations = new Set();
const imageViolations = new Set();
let currentImageUrl = null;

const API_URL = "http://127.0.0.1:5000/api/scan";
let cameraConfig = null;
async function loadConfig(videoId) {
    try {

        const res =
            await fetch("/config/camera_config.json");

        const allConfigs =
            await res.json();

        cameraConfig =
            allConfigs[videoId];

        console.log(
            "Camera Config:",
            cameraConfig
        );

    } catch (err) {

        console.error(
            "Không tải được config",
            err
        );
    }
}
const videoSelect =
    document.getElementById("videoSelect");

videoSelect.addEventListener(
    "change",
    async () => {

        await loadConfig(
            videoSelect.value
        );
    }
);
// =========================
// VIDEO CONTROL (PLAY/PAUSE & NO AUTOPLAY)
// =========================
video.autoplay = false; 
video.loop = false;

btnPlayPause.addEventListener("click", () => {
    if (video.paused) {
        video.play();
    } else {
        video.pause();
    }
});

video.addEventListener("play", () => { btnPlayPause.textContent = "TẠM DỪNG VIDEO"; });
video.addEventListener("pause", () => { btnPlayPause.textContent = "PHÁT VIDEO"; });

// =========================
// RESIZE
// =========================
function resizeCanvas() {
    if (video.videoWidth <= 0) return;
    const rect = video.getBoundingClientRect();
    overlay.width = video.videoWidth;
    overlay.height = video.videoHeight;
    overlay.style.width = rect.width + "px";
    overlay.style.height = rect.height + "px";
    captureCanvas.width = video.videoWidth;
    captureCanvas.height = video.videoHeight;
}

video.addEventListener("loadedmetadata", resizeCanvas);
window.addEventListener("resize", resizeCanvas);

// =========================
// SCAN LOOP
// =========================
async function loopScan() {
    if (!autoScan) return;

    await scanFrame();

    const baseFPS = 1000;
    const speedFactor = video.playbackRate || 1;

    scanLoopTimeout = setTimeout(loopScan, baseFPS / speedFactor);
}

async function scanFrame() {
    if (isVideoScanning || video.paused || video.ended) return;
    isVideoScanning = true;
    const currentId = ++videoRequestId;

    try {
        captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);
        const blob = await new Promise(resolve => captureCanvas.toBlob(resolve, "image/jpeg", 0.92));
        
        const formData = new FormData();
        formData.append("image", blob, "frame.jpg");
        formData.append(
            "video_id",
            videoSelect.value
        );
        formData.append("mode", "video");

        const response = await fetch(API_URL, { method: "POST", body: formData });
        if (!response.ok) throw new Error("SERVER_ERROR");

        const data = await response.json();
        if (currentId !== videoRequestId) return;
        drawVideoResult(data);
    } catch (err) {
        console.error(err);
        videoScanResult.innerHTML = "🔴 AI LỖI";
    } finally {
        isVideoScanning = false;
    }
}

// =========================
// DRAWING UTILS
// =========================
function drawTrafficLight(light, canvasCtx) {
    const configs = {
        red: { color: "#FF3B30", text: "ĐÈN ĐỎ", bg: "rgba(255,59,48,0.15)", border: "#FF3B30" },
        yellow: { color: "#FFD60A", text: "ĐÈN VÀNG", bg: "rgba(255,214,10,0.15)", border: "#FFD60A" },
        green: { color: "#34C759", text: "ĐÈN XANH", bg: "rgba(52,199,89,0.15)", border: "#34C759" },
        unknown: { color: "#808080", text: "CHƯA XÁC ĐỊNH", bg: "rgba(128,128,128,0.15)", border: "#808080" } 
    };

    const cfg = configs[light] || configs.unknown;
    canvasCtx.save();
    canvasCtx.fillStyle = cfg.bg;
    canvasCtx.strokeStyle = cfg.border;
    canvasCtx.lineWidth = 2;
    canvasCtx.beginPath();
    canvasCtx.roundRect(20, 20, 220, 60, 12);
    canvasCtx.fill();
    canvasCtx.stroke();
    // Vẽ đèn LED
    canvasCtx.beginPath();
    canvasCtx.arc(45, 50, 12, 0, Math.PI * 2);
    canvasCtx.fillStyle = cfg.color;
    canvasCtx.fill();
    // Vẽ Text
    canvasCtx.fillStyle = "#ffffff";
    canvasCtx.font = "bold 16px Segoe UI";
    canvasCtx.fillText("TRẠNG THÁI ĐÈN:", 70, 40);
    canvasCtx.fillStyle = cfg.color;
    canvasCtx.font = "bold 20px Segoe UI";
    canvasCtx.fillText(cfg.text, 70, 65);
    canvasCtx.restore();
}
// =========================
// STOP LINE
// =========================
function drawStopLine(
    canvasCtx,
    canvasWidth,
    canvasHeight
) {

    if (!cameraConfig) return;

    const y =
        canvasHeight *
        cameraConfig.stop_line_ratio;

    canvasCtx.save();

    canvasCtx.strokeStyle = "#ff0000";
    canvasCtx.lineWidth = 4;

    canvasCtx.beginPath();
    canvasCtx.moveTo(0, y);
    canvasCtx.lineTo(canvasWidth, y);
    canvasCtx.stroke();

    canvasCtx.fillStyle = "#ff0000";
    canvasCtx.font = "bold 18px Arial";
    canvasCtx.fillText("STOP LINE", 20, y - 10);

    canvasCtx.restore();
}

// =========================
// VIDEO RESULT
// =========================
function drawVideoResult(data) {
    if (!data || !data.success || !data.vehicles) return;
    ctx.clearRect(0, 0, overlay.width, overlay.height);
    drawTrafficLight(data.light, ctx);
    drawStopLine(
        ctx,
        overlay.width,
        overlay.height
    );
    drawVehicles(data.vehicles, ctx, 1, 1, "video");
}
// =========================
// IMAGE RESULT
// =========================
function drawImageResult(data) {
    if (!data || !data.success || !data.vehicles) return;

    imageCtx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);

    const scaleX = imageCanvas.width / previewImage.naturalWidth;
    const scaleY = imageCanvas.height / previewImage.naturalHeight;

    // ❌ KHÔNG vẽ đèn giao thông trong chế độ image
    // drawTrafficLight(data.light, imageCtx);

    // (optional) nếu muốn chắc chắn bỏ luôn dữ liệu lỗi từ backend
    const cleanVehicles = data.vehicles.map(v => ({
        ...v,
        violation: null,   // chặn vi phạm
    }));

    drawVehicles(cleanVehicles, imageCtx, scaleX, scaleY, "image");
}

// =========================
// DRAW VEHICLES
// =========================
function drawVehicles(vehicles, canvasCtx, scaleX = 1, scaleY = 1, mode = "video") {
    const drawn = [];

    canvasCtx.imageSmoothingEnabled = true;
    canvasCtx.font = "500 12px Arial";
    canvasCtx.textBaseline = "middle";

    vehicles.forEach(v => {
        // Kiểm tra xem dữ liệu box nằm ở đâu (v.box hoặc v.vehicle_box)
        const b = v.vehicle_box || v.box; 
        if (!b) return;

        let x = Math.round(b.x * scaleX);
        let y = Math.round(b.y * scaleY);
        let w = Math.round(b.w * scaleX);
        let h = Math.round(b.h * scaleY);

        // Lọc các box quá nhỏ (nhiễu)
        if (w < 35 || h < 35) return;

        // Logic màu sắc: Nếu là chế độ ảnh, luôn là màu xanh. 
        // Nếu video, xanh là an toàn, đỏ là vi phạm.
        const isViolation = mode === "video" && v.violation;
        const color = isViolation ? "#FF2D55" : "#00E676";

        // =========================
        // 1. VẼ BOX
        // =========================
        canvasCtx.beginPath();
        canvasCtx.strokeStyle = color;
        canvasCtx.lineWidth = 2;
        canvasCtx.lineJoin = "round";
        canvasCtx.lineCap = "round";
        canvasCtx.shadowColor = color;
        canvasCtx.shadowBlur = 8;

        if (canvasCtx.roundRect) {
            canvasCtx.roundRect(x, y, w, h, 6);
        } else {
            canvasCtx.rect(x, y, w, h);
        }
        canvasCtx.stroke();
        canvasCtx.shadowBlur = 0;

        // =========================
        // 2. VẼ LABEL
        // =========================
        const label = `${v.vehicle_type || "Xe"} | ${v.plate || "Unknown"}`;
        const tw = canvasCtx.measureText(label).width + 12;
        const th = 22;
        let ly = y - th - 3;

        if (ly < 5) ly = y + 3;

        // Tránh ghi đè các nhãn lên nhau
        drawn.forEach(p => {
            if (Math.abs(p.x - x) < tw && Math.abs(p.y - ly) < th) {
                ly = p.y - th - 3;
            }
        });
        drawn.push({ x, y: ly });

        canvasCtx.fillStyle = isViolation ? "rgba(255,45,85,0.85)" : "rgba(0,230,118,0.85)";
        canvasCtx.beginPath();
        if (canvasCtx.roundRect) {
            canvasCtx.roundRect(x, ly, tw, th, 4);
            canvasCtx.fill();
        } else {
            canvasCtx.fillRect(x, ly, tw, th);
        }
        canvasCtx.fillStyle = "#fff";
        canvasCtx.fillText(label, x + 6, ly + th / 2);

        // =========================
        // 3. XỬ LÝ VIOLATION TABLE (Chỉ chạy với Video)
        // =========================
        if (mode === "video" && v.violation && v.plate && v.plate !== "Unknown") {
            const key = `${v.track_id || v.plate}_${v.violation}`;
            if (!videoViolations.has(key)) {
                videoViolations.add(key);
                addViolationRow(v); // Chỉ thêm vào bảng khi đang quét video
            }
        }
    });
}

// =========================
// TABLE
// =========================
function addViolationRow(v) {

    const tr =
        document.createElement("tr");

    tr.innerHTML = `
        <td>📢 MỚI</td>

        <td>
            <b style="color:red">
                ${v.violation}
            </b>
        </td>

        <td>
            ${new Date().toLocaleTimeString()}
        </td>

        <td>
            <code>${v.plate}</code>
        </td>

        <td>
            <img
                src="http://127.0.0.1:5000/evidences/${v.image}"
                style="
                    width:90px;
                    border-radius:8px;
                    cursor:pointer
                "
                onclick="window.open(this.src, '_blank')"
            >
        </td>
    `;

    tableBody.prepend(tr);

    if (
        tableBody.children.length > 15
    ) {

        tableBody.removeChild(
            tableBody.lastChild
        );
    }
}

// =========================
// VIDEO CONTROL
// =========================
function startScanning() {

    if (autoScan) return;

    autoScan = true;

    videoScanResult.innerHTML =
        "🟢 AI ĐANG CHẠY";

    loopScan();
}

function stopScanning() {

    autoScan = false;

    clearTimeout(
        scanLoopTimeout
    );

    videoScanResult.innerHTML =
        "⚪ AI ĐÃ DỪNG";

    ctx.clearRect(
        0,
        0,
        overlay.width,
        overlay.height
    );
}

// =========================
// TAB SWITCH
// =========================
tabVideo.addEventListener(
    "click",
    () => {

        videoSection.style.display =
            "flex";

        imageSection.style.display =
            "none";
    }
);

tabImage.addEventListener(
    "click",
    () => {

        videoSection.style.display =
            "none";

        imageSection.style.display =
            "flex";
    }
);

// =========================
// IMAGE CHANGE
// =========================
imageInput.addEventListener(
    "change",
    e => {

        const file =
            e.target.files[0];

        if (!file) return;

        imageCtx.clearRect(
            0,
            0,
            imageCanvas.width,
            imageCanvas.height
        );

        imageViolations.clear();

        imageScanResult.innerHTML =
            "⚪ Ảnh mới đã sẵn sàng.";

        if (currentImageUrl) {

            URL.revokeObjectURL(
                currentImageUrl
            );
        }

        currentImageUrl =
            URL.createObjectURL(
                file
            );

        previewImage.src =
            currentImageUrl;

        document.getElementById(
            "imageContainer"
        ).style.display = "block";

        previewImage.onload = () => {

            imageCanvas.width =
                previewImage.clientWidth;

            imageCanvas.height =
                previewImage.clientHeight;

            imageCtx.clearRect(
                0,
                0,
                imageCanvas.width,
                imageCanvas.height
            );
        };
    }
);

// =========================
// IMAGE SCAN
// =========================
btnScanImage.addEventListener(
    "click",
    async () => {

        const file =
            imageInput.files[0];

        if (!file) {

            return alert(
                "Vui lòng chọn ảnh!"
            );
        }

        try {

            imageCtx.clearRect(
                0,
                0,
                imageCanvas.width,
                imageCanvas.height
            );

            imageViolations.clear();

            imageScanResult.innerHTML =
                "🧠 AI đang phân tích ảnh...";

            imageCanvas.width =
                previewImage.clientWidth;

            imageCanvas.height =
                previewImage.clientHeight;

            const formData =
                new FormData();

            formData.append(
                "image",
                file
            );

            formData.append(
                "video_id",
                videoSelect.value
            );

            formData.append(
                "mode",
                "image"
            );

            const response =
                await fetch(API_URL, {
                    method: "POST",
                    body: formData
                });

            if (!response.ok) {

                throw new Error(
                    "SERVER_ERROR"
                );
            }

            const data =
                await response.json();

            if (
                data &&
                data.success
            ) {

                drawImageResult(
                    data
                );

                const count =
                    data.vehicles
                        ? data.vehicles.length
                        : 0;

                imageScanResult.innerHTML =
                    `🟢 Phát hiện ${count} phương tiện`;

            } else {

                imageScanResult.innerHTML =
                    "🔴 AI không phản hồi";
            }

        } catch (err) {

            console.error(err);

            imageScanResult.innerHTML =
                "🔴 Lỗi AI";
        }
    }
);

// =========================
// EVENTS
// =========================
btnStartScan.addEventListener(
    "click",
    startScanning
);

btnStopScan.addEventListener(
    "click",
    stopScanning
); 
window.addEventListener("load", async () => {
    if (videoSelect.value) {
        await loadConfig(videoSelect.value);
    }
});