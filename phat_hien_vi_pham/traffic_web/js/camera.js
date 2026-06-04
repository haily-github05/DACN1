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

const video = document.getElementById("videoPlayer");
video.playbackRate = 0.2;
video.defaultPlaybackRate = 0.2;
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

const imageInput = document.getElementById("imageInput");
const btnScanImage = document.getElementById("btnScanImage");
const previewImage = document.getElementById("previewImage");
const imageCanvas = document.getElementById("imageCanvas");
const imageCtx = imageCanvas.getContext("2d");

const tabVideo = document.getElementById("tabVideo");
const tabImage = document.getElementById("tabImage");
const videoSection = document.getElementById("videoSection");
const imageSection = document.getElementById("imageSection");

let autoScan = false;
let isVideoScanning = false;
let videoRequestId = 0;
let scanLoopTimeout = null;
let currentImageUrl = null;

const videoViolations = new Set();
const imageViolations = new Set();

const violatedTrackCache = new Map();

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
//
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

//
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

//
async function loopScan() {

    if (!autoScan) return;

    await scanFrame();
    scanLoopTimeout = setTimeout(
        loopScan,
        80
    );
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
    canvasCtx.lineWidth = 3;
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
    drawStopLine(ctx, overlay.width, overlay.height);

    const currentIds = new Set(data.vehicles.map(v => v.track_id));

    violatedTrackCache.forEach((cached, id) => {
        if (!currentIds.has(id)) {
            cached.missed++;

            if (cached.missed <= 20 && cached.box) {
                data.vehicles.push({
                    track_id: id,
                    vehicle_type: "Xe máy",
                    plate: cached.plate,
                    violation: cached.violation,
                    image: cached.image,
                    box: cached.box
                });
            } else {
                violatedTrackCache.delete(id);
            }
        }
    });

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
    canvasCtx.font = "bold 18px Arial";
    canvasCtx.textBaseline = "middle";
    function filterDuplicateBoxes(vehicles) {
        return vehicles.filter((a, i) => {
            const ab = a.vehicle_box || a.box;
            if (!ab) return false;

            const ax1 = ab.x;
            const ay1 = ab.y;
            const ax2 = ab.x + ab.w;
            const ay2 = ab.y + ab.h;
            const aArea = ab.w * ab.h;

            for (let j = 0; j < vehicles.length; j++) {
                if (i === j) continue;

                const b = vehicles[j];
                const bb = b.vehicle_box || b.box;
                if (!bb) continue;

                const bx1 = bb.x;
                const by1 = bb.y;
                const bx2 = bb.x + bb.w;
                const by2 = bb.y + bb.h;
                const bArea = bb.w * bb.h;

                const ix1 = Math.max(ax1, bx1);
                const iy1 = Math.max(ay1, by1);
                const ix2 = Math.min(ax2, bx2);
                const iy2 = Math.min(ay2, by2);

                const iw = Math.max(0, ix2 - ix1);
                const ih = Math.max(0, iy2 - iy1);
                const inter = iw * ih;

                if (inter <= 0) continue;

                const overlapSmall = inter / Math.min(aArea, bArea);

                // nếu box nhỏ chồng nhiều với box lớn => bỏ box nhỏ
                if (overlapSmall > 0.25 && aArea < bArea) {
                    return false;
                }
            }

            return true;
        });
    }
    vehicles = filterDuplicateBoxes(vehicles);

    vehicles.forEach(v => {
        // Kiểm tra xem dữ liệu box nằm ở đâu (v.box hoặc v.vehicle_box)
        const b = v.vehicle_box || v.box; 
        if (!b) return;
        if (mode === "video" && v.violation && v.track_id !== undefined) {
            const boxNow = { ...(v.vehicle_box || v.box) };
            const old = violatedTrackCache.get(v.track_id);

            violatedTrackCache.set(v.track_id, {
                violation: v.violation,
                plate: v.plate,
                image: v.image,
                box: boxNow,
                vx: old ? boxNow.x - old.box.x : 0,
                vy: old ? boxNow.y - old.box.y : -8,
                missed: 0
            });
        }

        if (mode === "video" && violatedTrackCache.has(v.track_id)) {
            const cached = violatedTrackCache.get(v.track_id);
            const boxNow = v.vehicle_box || v.box;

            cached.vx = boxNow.x - cached.box.x;
            cached.vy = boxNow.y - cached.box.y;
            cached.box = { ...boxNow };
            cached.missed = 0;

            v.violation = cached.violation;
            v.plate = cached.plate || v.plate;
            v.image = cached.image || v.image;
        }
       

        let x = Math.round(b.x * scaleX);
        let y = Math.round(b.y * scaleY);
        let w = Math.round(b.w * scaleX);
        let h = Math.round(b.h * scaleY);
        // Thu nhỏ box khoảng 10%
        const shrinkX = Math.round(w * 0.05);
        const shrinkY = Math.round(h * 0.05);

        x += shrinkX;
        y += shrinkY;

        w -= shrinkX * 2;
        h -= shrinkY * 2;

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
        canvasCtx.lineWidth = 3;
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
        canvasCtx.strokeStyle = "#000";
        canvasCtx.lineWidth = 3;
        canvasCtx.strokeText(label, x + 10, ly + th / 2);
        canvasCtx.fillText(label, x + 10, ly + th / 2);

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
    drawStopLine(ctx, overlay.width, overlay.height);
    drawLaneLines(ctx, overlay.width, overlay.height);
}
//
function drawDashedLaneLine(
    canvasCtx,
    yMin,
    yMax,
    topX,
    bottomX,
    color = "#ffff00",
    thickness = 2
) {
    const segmentCount = 15;

    canvasCtx.save();

    canvasCtx.strokeStyle = color;
    canvasCtx.lineWidth = thickness;
    canvasCtx.lineCap = "round";

    for (let i = 0; i < segmentCount - 1; i++) {
        if (i % 2 !== 0) continue;

        const yStart = yMin + ((yMax - yMin) * i) / segmentCount;
        const yEnd = yMin + ((yMax - yMin) * (i + 1)) / segmentCount;

        const xStart = getLineX(yStart, yMin, yMax, topX, bottomX);
        const xEnd = getLineX(yEnd, yMin, yMax, topX, bottomX);

        canvasCtx.beginPath();
        canvasCtx.moveTo(xStart, yStart);
        canvasCtx.lineTo(xEnd, yEnd);
        canvasCtx.stroke();
    }

    canvasCtx.restore();
}

function drawLaneLines(canvasCtx, canvasWidth, canvasHeight) {
    if (!cameraConfig || !cameraConfig.lane_config) return;

    const lane = cameraConfig.lane_config;

    const yMin = (lane.y_min_ratio ?? 0.35) * canvasHeight;
    const yMax = (lane.y_max_ratio ?? 1.0) * canvasHeight;

    const xDirTop = (lane.dir_top_ratio ?? 0.41) * canvasWidth;
    const xDirBottom = (lane.dir_bottom_ratio ?? 0.06) * canvasWidth;

    const xLaneTop = (lane.lane_top_ratio ?? 0.45) * canvasWidth;
    const xLaneBottom = (lane.lane_bottom_ratio ?? 0.36) * canvasWidth;

    const isThreeLanes = lane.is_three_lanes === true;

    canvasCtx.save();

    // Vạch đỏ chia chiều ngược chiều
    canvasCtx.strokeStyle = "#ff0000";
    canvasCtx.lineWidth = 2;
    canvasCtx.beginPath();
    canvasCtx.moveTo(xDirTop, yMin);
    canvasCtx.lineTo(xDirBottom, yMax);
    canvasCtx.stroke();

    drawTextWithBg(
        canvasCtx,
        "NGƯỢC CHIỀU",
        xDirTop - 110,
        yMin + 28,
        "#ff0000"
    );

    if (isThreeLanes) {
        const xMidTop = (lane.mid_top_ratio ?? 0.52) * canvasWidth;
        const xMidBottom = (lane.mid_bottom_ratio ?? 0.0) * canvasWidth;

        // Vạch trắng phân làn 3 và 2
        drawDashedLaneLine(
            canvasCtx,
            yMin,
            yMax,
            xMidTop,
            xMidBottom,
            "#ffffff",
            2
        );

        // Vạch vàng phân làn 2 và 1
        drawDashedLaneLine(
            canvasCtx,
            yMin,
            yMax,
            xLaneTop,
            xLaneBottom,
            "#ffff00",
            2
        );

        drawTextWithBg(
            canvasCtx,
            "LÀN 3 (Ô TÔ)",
            xMidTop - 90,
            yMin + 28,
            "#ffffff"
        );

        drawTextWithBg(
            canvasCtx,
            "LÀN 2 (MIXED)",
            xMidTop + 20,
            yMin + 28,
            "#ffff00"
        );

        drawTextWithBg(
            canvasCtx,
            "LÀN 1 (XE MÁY)",
            xLaneTop + 30,
            yMin + 28,
            "#ffff00"
        );
    } else {
        // Camera 2 làn
        drawDashedLaneLine(
            canvasCtx,
            yMin,
            yMax,
            xLaneTop,
            xLaneBottom,
            "#ffff00",
            2
        );

        drawTextWithBg(
            canvasCtx,
            "LÀN 2 (Ô TÔ)",
            xLaneTop - 110,
            yMin + 28,
            "#ffff00"
        );

        drawTextWithBg(
            canvasCtx,
            "LÀN 1 (XE MÁY)",
            xLaneTop + 20,
            yMin + 28,
            "#ffff00"
        );
    }

    canvasCtx.restore();
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