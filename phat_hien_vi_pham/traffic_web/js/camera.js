function formatStatus(status) {
    switch (status) {
        case "pending": return "Chờ xử lý";
        case "approved": return "Đã xử lý";
        case "rejected": return "Từ chối";
        default: return status || "Chờ xử lý";
    }
}

const video = document.getElementById("videoPlayer");
const overlay = document.getElementById("overlayCanvas");
const ctx = overlay.getContext("2d");

const captureCanvas = document.getElementById("captureCanvas");
const captureCtx = captureCanvas.getContext("2d");

const videoScanResult = document.getElementById("videoScanResult");
const imageScanResult = document.getElementById("imageScanResult");

const btnStartScan = document.getElementById("btnStartScan");
const btnStopScan = document.getElementById("btnStopScan");

const tableBody = document.getElementById("tableBody");

// IMAGE
const imageInput = document.getElementById("imageInput");
const btnScanImage = document.getElementById("btnScanImage");
const previewImage = document.getElementById("previewImage");
const imageCanvas = document.getElementById("imageCanvas");
const imageCtx = imageCanvas.getContext("2d");

// TABS
const tabVideo = document.getElementById("tabVideo");
const tabImage = document.getElementById("tabImage");
const videoSection = document.getElementById("videoSection");
const imageSection = document.getElementById("imageSection");

// =========================
// VIDEO STATE
// =========================
let autoScan = false;
let scanInterval = null;
let isVideoScanning = false;
const videoViolations = new Set();
let videoRequestId = 0;

// =========================
// IMAGE STATE
// =========================
const imageViolations = new Set();
let imageRequestId = 0;
let currentImageUrl = null;

// =========================
// RESIZE
// =========================
function resizeCanvas() {
    if (video.videoWidth > 0) {
        overlay.width = video.videoWidth;
        overlay.height = video.videoHeight;

        captureCanvas.width = video.videoWidth;
        captureCanvas.height = video.videoHeight;
    }
}

video.addEventListener("loadedmetadata", resizeCanvas);
window.addEventListener("resize", resizeCanvas);

// =========================
// VIDEO SCAN
// =========================
async function scanFrame() {
    if (isVideoScanning) return;
    isVideoScanning = true;

    const currentId = ++videoRequestId;

    try {
        captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);

        const blob = await new Promise(resolve =>
            captureCanvas.toBlob(resolve, "image/jpeg", 0.92)
        );

        const formData = new FormData();
        formData.append("image", blob, "frame.jpg");
        formData.append("video_id", "1");

        const response = await fetch("http://127.0.0.1:5000/api/scan", {
            method: "POST",
            body: formData
        });

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
// STOP LINE
// =========================
function drawStopLine(stopLineY, redLight, canvasCtx, canvasWidth) {
    if (!redLight) return;

    canvasCtx.beginPath();
    canvasCtx.moveTo(0, stopLineY);
    canvasCtx.lineTo(canvasWidth, stopLineY);
    canvasCtx.strokeStyle = "#FF0000";
    canvasCtx.lineWidth = 4;
    canvasCtx.stroke();
}

// =========================
// VIDEO RESULT
// =========================
function drawVideoResult(data) {
    if (!data.success || !data.vehicles) return;

    ctx.clearRect(0, 0, overlay.width, overlay.height);

    const stopLineY = data.stop_line?.y ?? overlay.height * 0.68;

    drawStopLine(stopLineY, data.red_light, ctx, overlay.width);

    drawVehicles(data.vehicles, ctx, 1, 1, "video");
}

// =========================
// IMAGE RESULT
// =========================
function drawImageResult(data) {
    imageCtx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);

    const scaleX = imageCanvas.width / previewImage.naturalWidth;
    const scaleY = imageCanvas.height / previewImage.naturalHeight;

    const stopLineY = data.stop_line?.y ?? 490;

    drawStopLine(stopLineY, data.red_light, imageCtx, imageCanvas.width);

    drawVehicles(data.vehicles, imageCtx, scaleX, scaleY, "image");
}

// =========================
// DRAW VEHICLES
// =========================
function drawVehicles(vehicles, canvasCtx, scaleX = 1, scaleY = 1, mode = "video") {

    const drawn = [];

    vehicles.forEach(v => {
        const b = v.box;
        if (!b) return;

        let x = Math.round(b.x * scaleX);
        let y = Math.round(b.y * scaleY);
        let w = Math.round(b.w * scaleX);
        let h = Math.round(b.h * scaleY);

        const px = Math.round(w * 0.05);
        const py = Math.round(h * 0.05);

        x += px; y += py;
        w -= px * 2;
        h -= py * 2;

        if (w < 35 || h < 35) return;

        const color = v.violation ? "#FF2D55" : "#00E676";

        canvasCtx.beginPath();
        canvasCtx.strokeStyle = color;
        canvasCtx.lineWidth = 2;

        if (canvasCtx.roundRect) {
            canvasCtx.roundRect(x, y, w, h, 6);
        } else {
            canvasCtx.rect(x, y, w, h);
        }
        canvasCtx.stroke();

        const label = `${v.vehicle_type || "Xe"} | ${v.plate || "Unknown"}`;

        canvasCtx.font = "500 12px Arial";
        const tw = canvasCtx.measureText(label).width + 12;
        const th = 22;

        let ly = y - th - 3;
        if (ly < 5) ly = y + 3;

        drawn.forEach(p => {
            if (Math.abs(p.x - x) < 80 && Math.abs(p.y - ly) < th) {
                ly = p.y - th - 3;
            }
        });

        drawn.push({ x, y: ly });

        canvasCtx.fillStyle = v.violation
            ? "rgba(255,45,85,0.8)"
            : "rgba(0,230,118,0.85)";

        canvasCtx.beginPath();
        if (canvasCtx.roundRect) {
            canvasCtx.roundRect(x, ly, tw, th, 4);
            canvasCtx.fill();
        } else {
            canvasCtx.fillRect(x, ly, tw, th);
        }

        canvasCtx.fillStyle = "#fff";
        canvasCtx.textBaseline = "middle";
        canvasCtx.fillText(label, x + 6, ly + th / 2);

        // =========================
        // VIOLATION STATE
        // =========================
        if (v.violation && v.plate && v.plate !== "Unknown") {

            const key = `${v.track_id || v.plate}_${v.violation}`;

            if (mode === "video") {
                if (!videoViolations.has(key)) {
                    videoViolations.add(key);
                    addViolationRow(v);
                }
            }

            if (mode === "image") {
                if (!imageViolations.has(key)) {
                    imageViolations.add(key);
                    addViolationRow(v);
                }
            }
        }
    });
}

// =========================
// TABLE
// =========================
function addViolationRow(v) {
    const tr = document.createElement("tr");

    tr.innerHTML = `
        <td>📢 MỚI</td>
        <td><b style="color:red">${v.violation}</b></td>
        <td>${new Date().toLocaleTimeString()}</td>
        <td><code>${v.plate}</code></td>
        <td>
            <img src="http://127.0.0.1:5000/evidences/${v.image}"
                 style="width:90px;cursor:pointer;border-radius:8px"
                 onclick="window.open(this.src)">
        </td>
    `;

    tableBody.prepend(tr);

    if (tableBody.children.length > 15) {
        tableBody.removeChild(tableBody.lastChild);
    }
}

// =========================
// VIDEO CONTROL
// =========================
function startScanning() {
    if (autoScan) return;

    autoScan = true;
    videoScanResult.innerHTML = "🟢 AI ĐANG CHẠY";

    scanFrame();
    scanInterval = setInterval(scanFrame, 1500);
}

function stopScanning() {
    autoScan = false;
    clearInterval(scanInterval);

    videoScanResult.innerHTML = "⚪ AI ĐÃ DỪNG";
    ctx.clearRect(0, 0, overlay.width, overlay.height);
}

// =========================
// TAB SWITCH
// =========================
tabVideo.addEventListener("click", () => {
    videoSection.style.display = "flex";
    imageSection.style.display = "none";
});

tabImage.addEventListener("click", () => {
    videoSection.style.display = "none";
    imageSection.style.display = "flex";
});

// =========================
// IMAGE CHANGE (SỬA ĐỂ XÓA HẲN DẤU VẾT CŨ KHI CHỌN ẢNH MỚI)
// =========================
imageInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // 1. Xóa sạch box và trạng thái lưu vết cũ trên giao diện
    imageCtx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);
    imageViolations.clear();
    imageScanResult.innerHTML = "⚪ Ảnh mới đã sẵn sàng. Hãy bấm nút QUÉT ẢNH.";

    if (currentImageUrl) URL.revokeObjectURL(currentImageUrl);

    currentImageUrl = URL.createObjectURL(file);
    previewImage.src = currentImageUrl;

    document.getElementById("imageContainer").style.display = "block";

    // 2. Định dạng lại kích thước chuẩn chỉnh cho canvas đè khít lên ảnh
    previewImage.onload = () => {
        imageCanvas.width = previewImage.clientWidth;
        imageCanvas.height = previewImage.clientHeight;
        // Đảm bảo clear thêm một lần nữa sau khi canvas đổi kích thước
        imageCtx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);
    };
});
// =========================
// IMAGE SCAN (ĐÃ SỬA LỖI LƯU KẾT QUẢ CŨ)
// =========================
btnScanImage.addEventListener("click", async () => {
    
    const file = imageInput.files[0];
    if (!file) return alert("Vui lòng chọn ảnh!");

    try {
        // 1. XOÁ BỎ HOÀN TOÀN DỮ LIỆU CỦA LẦN QUÉT TRƯỚC NGAY LẬP TỨC
        imageCtx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);
        imageViolations.clear(); 
        imageScanResult.innerHTML = "🧠 AI đang phân tích ảnh...";

        // 2. Đảm bảo kích thước Canvas chuẩn khít theo ảnh hiển thị hiện tại
        imageCanvas.width = previewImage.clientWidth;
        imageCanvas.height = previewImage.clientHeight;

        const formData = new FormData();
        formData.append("image", file);
        formData.append("video_id", "1");

        // 3. GỌI API PHÂN TÍCH
        const response = await fetch("http://127.0.0.1:5000/api/scan", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            imageScanResult.innerHTML = "🔴 Lỗi kết nối hệ thống AI";
            return;
        }

        const data = await response.json();

        if (data && data.success) {
            // 4. VẼ KẾT QUẢ MỚI LÊN CANVAS
            drawImageResult(data);
            
            const count = data.vehicles ? data.vehicles.length : 0;
            imageScanResult.innerHTML = `🟢 Phát hiện ${count} phương tiện`;
        } else {
            imageScanResult.innerHTML = "🔴 AI không phản hồi kết quả hợp lệ";
        }

    } catch (err) {
        console.error(err);
        imageScanResult.innerHTML = "🔴 Lỗi AI không thể phân tích";
    }
});

// =========================
// EVENTS
// =========================
btnStartScan.addEventListener("click", startScanning);
btnStopScan.addEventListener("click", stopScanning);