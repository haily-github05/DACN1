function formatStatus(status) {
    switch (status) {
        case "pending":
            return "Chờ xử lý";
        case "approved":
            return "Đã xử lý";
        case "rejected":
            return "Từ chối";
        default:
            return status || "Chờ xử lý";
    }
}

const video = document.getElementById("videoPlayer");
const overlay = document.getElementById("overlayCanvas");
const ctx = overlay.getContext("2d");

const captureCanvas = document.getElementById("captureCanvas");
const captureCtx = captureCanvas.getContext("2d");

const scanResult = document.getElementById("scanResult");
const btnStartScan = document.getElementById("btnStartScan");
const btnStopScan = document.getElementById("btnStopScan");
const tableBody = document.getElementById("tableBody");

let autoScan = false;
let scanInterval = null;
let isScanning = false;

const addedViolations = new Set();

// ================= RESIZE =================
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

// ================= SCAN =================
async function scanFrame() {

    if (isScanning) return;
    isScanning = true;

    try {

        captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);

        const blob = await new Promise(resolve =>
            captureCanvas.toBlob(resolve, "image/jpeg", 0.92)
        );

        if (!blob) return;

        const formData = new FormData();
        formData.append("image", blob, "frame.jpg");
        formData.append("video_id", "1");

        const response = await fetch("http://127.0.0.1:5000/api/scan", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            scanResult.innerHTML = "🔴 AI LỖI";
            return;
        }

        const data = await response.json();
        drawResult(data);

    } catch (err) {
        console.error(err);
        scanResult.innerHTML = "🔴 AI LỖI";
    } finally {
        isScanning = false;
    }
}

// ================= DRAW STOP LINE =================
function drawStopLine(stopLineY, redLight) {
    ctx.beginPath();
    ctx.moveTo(0, stopLineY);
    ctx.lineTo(overlay.width, stopLineY);

    // Xác định màu sắc theo trạng thái đèn
    ctx.strokeStyle = redLight ? "#FF0000" : "#00E676";
    ctx.lineWidth = 4;
    ctx.stroke();
}

// ================= DRAW RESULT =================
function drawResult(data) {

    if (!data.success || !data.vehicles) return;

    ctx.clearRect(0, 0, overlay.width, overlay.height);
    const stopLineY = data.stop_line ? data.stop_line.y : overlay.height * 0.68;
    const redLight = data.red_light || false;

    // Tiến hành vẽ vạch dừng dạng đường thẳng gọn gàng
    drawStopLine(stopLineY, redLight);

    data.vehicles.forEach(v => {

        const p = v.box;
        if (!p) return;

        const color = v.violation ? "#FF3333" : "#00E676";

        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.strokeRect(p.x, p.y, p.w, p.h);

        const label = `${v.vehicle_type} | ${v.plate || "Đang đọc"}`;

        ctx.font = "bold 14px Arial";

        const textWidth = ctx.measureText(label).width + 12;

        ctx.fillStyle = color;
        ctx.fillRect(p.x, p.y - 24, textWidth, 24);

        ctx.fillStyle = "#fff";
        ctx.fillText(label, p.x + 6, p.y - 7);

        // bảng vi phạm
        if (v.violation && v.plate && v.plate !== "UNKNOWN") {

            const key = `${v.track_id}_${v.violation}`;

            if (!addedViolations.has(key)) {
                addedViolations.add(key);
                addViolationRow(v);

                if (addedViolations.size > 200) {
                    addedViolations.delete(addedViolations.values().next().value);
                }
            }
        }
    });
}

// ================= TABLE =================
function addViolationRow(v) {

    const tr = document.createElement("tr");

    tr.innerHTML = `
        <td>📢 MỚI</td>
        <td><b style="color:red">${v.violation}</b></td>
        <td>${new Date().toLocaleTimeString()}</td>
        <td>${v.camera_name}</td>
        <td><code>${v.plate}</code></td>
        <td>
            <img src="http://127.0.0.1:5000/evidences/${v.image}"
                 style="width:90px;cursor:pointer"
                 onclick="window.open(this.src)">
        </td>
        <td>${formatStatus(v.status)}</td>
    `;

    tableBody.prepend(tr);

    if (tableBody.children.length > 15) {
        tableBody.removeChild(tableBody.lastChild);
    }
}

function startScanning() {
    if (autoScan) return;

    autoScan = true;
    scanResult.innerHTML = "🟢 AI ĐANG CHẠY";

    scanFrame();
    scanInterval = setInterval(scanFrame, 800);
}

function stopScanning() {
    autoScan = false;
    clearInterval(scanInterval);
    scanResult.innerHTML = "⚪ AI ĐÃ DỪNG";
    ctx.clearRect(0, 0, overlay.width, overlay.height);
}

btnStartScan.addEventListener("click", startScanning);
btnStopScan.addEventListener("click", stopScanning);