
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

// =========================
// VIDEO
// =========================

const video =
    document.getElementById("videoPlayer");

const overlay =
    document.getElementById("overlayCanvas");

const ctx =
    overlay.getContext("2d");

const captureCanvas =
    document.getElementById("captureCanvas");

const captureCtx =
    captureCanvas.getContext("2d");

const videoScanResult =
    document.getElementById("videoScanResult");

const imageScanResult =
    document.getElementById("imageScanResult");

const btnStartScan =
    document.getElementById("btnStartScan");

const btnStopScan =
    document.getElementById("btnStopScan");

const tableBody =
    document.getElementById("tableBody");

// =========================
// IMAGE
// =========================

const imageInput =
    document.getElementById("imageInput");

const btnScanImage =
    document.getElementById("btnScanImage");

const previewImage =
    document.getElementById("previewImage");

const imageCanvas =
    document.getElementById("imageCanvas");

const imageCtx =
    imageCanvas.getContext("2d");

// =========================
// TAB
// =========================

const tabVideo =
    document.getElementById("tabVideo");

const tabImage =
    document.getElementById("tabImage");

const videoSection =
    document.getElementById("videoSection");

const imageSection =
    document.getElementById("imageSection");

// =========================
// STATES
// =========================

let autoScan = false;

let scanInterval = null;

let isScanning = false;

const addedViolations =
    new Set();

// =========================
// RESIZE VIDEO CANVAS
// =========================

function resizeCanvas() {

    if (video.videoWidth > 0) {

        overlay.width =
            video.videoWidth;

        overlay.height =
            video.videoHeight;

        captureCanvas.width =
            video.videoWidth;

        captureCanvas.height =
            video.videoHeight;
    }
}

video.addEventListener(
    "loadedmetadata",
    resizeCanvas
);

window.addEventListener(
    "resize",
    resizeCanvas
);

// =========================
// VIDEO SCAN
// =========================

async function scanFrame() {

    if (isScanning) return;

    isScanning = true;

    try {

        captureCtx.drawImage(
            video,
            0,
            0,
            captureCanvas.width,
            captureCanvas.height
        );

        const blob =
            await new Promise(resolve =>
                captureCanvas.toBlob(
                    resolve,
                    "image/jpeg",
                    0.92
                )
            );

        if (!blob) return;

        const formData =
            new FormData();

        formData.append(
            "image",
            blob,
            "frame.jpg"
        );

        formData.append(
            "video_id",
            "1"
        );

        const response =
            await fetch(
                "http://127.0.0.1:5000/api/scan",
                {
                    method: "POST",
                    body: formData
                }
            );

        if (!response.ok) {

            videoScanResult.innerHTML =
                "🔴 AI LỖI";

            return;
        }

        const data =
            await response.json();

        drawVideoResult(data);

    } catch(err) {

        console.error(err);

        videoScanResult.innerHTML =
            "🔴 AI LỖI";

    } finally {

        isScanning = false;
    }
}

// =========================
// DRAW STOP LINE
// =========================
function drawStopLine(
    stopLineY,
    redLight,
    canvasCtx,
    canvasWidth
) {
    // CHỈ vẽ khi có đèn đỏ
    if (!redLight) return;

    canvasCtx.beginPath();
    canvasCtx.moveTo(0, stopLineY);
    canvasCtx.lineTo(canvasWidth, stopLineY);

    canvasCtx.strokeStyle = "#FF0000";
    canvasCtx.lineWidth = 4;
    canvasCtx.stroke();
}

// =========================
// DRAW VIDEO RESULT
// =========================

function drawVideoResult(data) {

    if (!data.success ||
        !data.vehicles) return;

    ctx.clearRect(
        0,
        0,
        overlay.width,
        overlay.height
    );

    const stopLineY =
        data.stop_line
            ? data.stop_line.y
            : overlay.height * 0.68;

    const redLight =
        data.red_light || false;

    drawStopLine(
        stopLineY,
        redLight,
        ctx,
        overlay.width
    );

    drawVehicles(
        data.vehicles,
        ctx,
        1,
        1
    );
}

// =========================
// DRAW VEHICLES (KHUNG LIỀN MẠCH, THANH MẢNH, CHỐNG ĐÈ CHỮ)
// =========================

function drawVehicles(
    vehicles,
    canvasCtx,
    scaleX = 1,
    scaleY = 1
) {
    // Mảng lưu vị trí các label đã vẽ để tính toán chống đè chữ lên nhau
    const drawnLabelPositions = [];

    vehicles.forEach(v => {
        const b = v.box;
        if (!b) return;

        // =========================
        // SCALE & SHRINK BOX (Ôm sát dáng xe)
        // =========================
        let x = Math.round(b.x * scaleX);
        let y = Math.round(b.y * scaleY);
        let w = Math.round(b.w * scaleX);
        let h = Math.round(b.h * scaleY);

        // Thu gọn nhẹ mép box để bám sát form xe hơn
        const paddingX = Math.round(w * 0.05);
        const paddingY = Math.round(h * 0.05);

        x += paddingX;
        y += paddingY;
        w -= paddingX * 2;
        h -= paddingY * 2;

        // Tránh lỗi box quá nhỏ
        if (w < 35 || h < 35) return;

        // =========================
        // COLOR (Neon hiện đại, dịu mắt)
        // =========================
        const color = v.violation ? "#FF2D55" : "#00E676";

        // =========================
        // MAIN BOX: KHUNG HỘP LIỀN MẠCH THANH MẢNH
        // =========================
        canvasCtx.beginPath();
        canvasCtx.strokeStyle = color;
        canvasCtx.lineWidth = 2; // Hạ xuống 2px giúp đường nét thanh mảnh, cực kỳ rõ ràng

        // Vẽ khung hộp liền mạch có bo góc nhẹ (6px) cho chuyên nghiệp
        if (typeof canvasCtx.roundRect === "function") {
            canvasCtx.roundRect(x, y, w, h, 6);
        } else {
            canvasCtx.rect(x, y, w, h);
        }
        canvasCtx.stroke();

        // =========================
        // LABEL & XỬ LÝ CHỐNG ĐÈ NHAU
        // =========================
        const label = `${v.vehicle_type || "Xe"} | ${v.plate || "Unknown"}`;
        canvasCtx.font = "500 12px Inter, Arial, sans-serif"; // Chữ gọn gàng

        const textMetrics = canvasCtx.measureText(label);
        const textWidth = textMetrics.width + 12;
        const labelHeight = 22;

        // Vị trí Y mặc định cho nhãn (nằm trên đỉnh box xe)
        let labelY = y - labelHeight - 3;
        if (labelY < 5) {
            labelY = y + 3; // Nếu chạm đỉnh màn hình thì đẩy vào trong lòng box
        }

        // --- THUẬT TOÁN XẾP TẦNG CHỮ (ANTI-OVERLAP) ---
        // Nếu khu vực này đã có chữ của xe khác, tự động xếp chồng lên trên để không bị nhem nhuốc
        drawnLabelPositions.forEach(pos => {
            if (Math.abs(pos.x - x) < 80 && Math.abs(pos.y - labelY) < labelHeight) {
                labelY = pos.y - labelHeight - 3; // Đẩy chữ lên tầng trên
            }
        });
        // Lưu vị trí chữ vừa tính vào mảng
        drawnLabelPositions.push({ x: x, y: labelY });

        // NỀN LABEL: Dạng bán trong suốt (Alpha 0.8), lỡ có đè nhau vẫn nhìn xuyên qua được
        canvasCtx.fillStyle = v.violation ? "rgba(255, 45, 85, 0.8)" : "rgba(0, 230, 118, 0.85)";
        canvasCtx.beginPath();
        
        if (typeof canvasCtx.roundRect === "function") {
            canvasCtx.roundRect(x, labelY, textWidth, labelHeight, 4);
            canvasCtx.fill();
        } else {
            canvasCtx.fillRect(x, labelY, textWidth, labelHeight);
        }

        // CHỮ HIỂN THỊ
        canvasCtx.fillStyle = "#FFFFFF";
        canvasCtx.textBaseline = "middle";
        canvasCtx.fillText(label, x + 6, labelY + (labelHeight / 2));
        canvasCtx.textBaseline = "alphabetic"; // Trả lại baseline mặc định

        // =========================
        // TABLE LOGIC (Giữ nguyên phần lưu trữ của bạn)
        // =========================
        if (v.violation && v.plate && v.plate !== "Unknown") {
            const key = `${v.track_id || v.plate}_${v.violation}`;
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
                    cursor:pointer;
                    border-radius:8px;
                "
                onclick="window.open(this.src)"
            >
        </td>
    `;

    tableBody.prepend(tr);

    if (tableBody.children.length > 15) {

        tableBody.removeChild(
            tableBody.lastChild
        );
    }
}

// =========================
// START / STOP
// =========================

function startScanning() {

    if (autoScan) return;

    autoScan = true;

    videoScanResult.innerHTML =
        "🟢 AI ĐANG CHẠY";

    scanFrame();

    scanInterval =
        setInterval(
            scanFrame,
            1500
        );
}

function stopScanning() {

    autoScan = false;

    clearInterval(scanInterval);

    videoScanResult.innerHTML =
        "⚪ AI ĐÃ DỪNG";

    ctx.clearRect(
        0,
        0,
        overlay.width,
        overlay.height
    );
}

btnStartScan.addEventListener(
    "click",
    startScanning
);

btnStopScan.addEventListener(
    "click",
    stopScanning
);

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

        tabVideo.classList.add(
            "active-mode"
        );

        tabImage.classList.remove(
            "active-mode"
        );
    }
);

tabImage.addEventListener(
    "click",
    () => {

        videoSection.style.display =
            "none";

        imageSection.style.display =
            "flex";

        tabImage.classList.add(
            "active-mode"
        );

        tabVideo.classList.remove(
            "active-mode"
        );
    }
);

// =========================
// IMAGE PREVIEW
// =========================

imageInput.addEventListener(
    "change",
    (e) => {

        const file =
            e.target.files[0];

        if (!file) return;

        const imageContainer =
            document.getElementById("imageContainer");

        previewImage.src =
            URL.createObjectURL(file);

        imageContainer.style.display =
            "block";

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

            alert("Vui lòng chọn ảnh!");

            return;
        }

        try {

            imageScanResult.innerHTML =
                "🧠 AI đang phân tích ảnh...";

            const formData =
                new FormData();

            formData.append(
                "image",
                file
            );

            formData.append(
                "video_id",
                "1"
            );

            const response =
                await fetch(
                    "http://127.0.0.1:5000/api/scan",
                    {
                        method: "POST",
                        body: formData
                    }
                );

            if (!response.ok) {

                imageScanResult.innerHTML =
                    "🔴 API ERROR";

                return;
            }

            const data =
                await response.json();


            imageCtx.clearRect(
                0,
                0,
                imageCanvas.width,
                imageCanvas.height
            );

            const scaleX =
                imageCanvas.width /
                previewImage.naturalWidth;

            const scaleY =
                imageCanvas.height /
                previewImage.naturalHeight;

            const stopLineY =
                data.stop_line?.y ?? 490;

            drawStopLine(
                stopLineY,
                data.red_light,
                imageCtx,
                imageCanvas.width
            );

            drawVehicles(
                data.vehicles,
                imageCtx,
                scaleX,
                scaleY
            );

            imageScanResult.innerHTML =
                `🟢 Phát hiện ${data.vehicles.length} phương tiện`;

        } catch(err) {

            console.error(err);

            imageScanResult.innerHTML =
                "🔴 Lỗi AI";
        }
    }
);
