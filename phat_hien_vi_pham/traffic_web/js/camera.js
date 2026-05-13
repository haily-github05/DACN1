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

const scanResult =
    document.getElementById("scanResult");

const btnStartScan =
    document.getElementById("btnStartScan");

const btnStopScan =
    document.getElementById("btnStopScan");

const tableBody =
    document.getElementById("tableBody");

let scanning = false;
let autoScan = false;
let scanInterval = null;

function resizeCanvas() {

    overlay.width =
        video.videoWidth;

    overlay.height =
        video.videoHeight;

    captureCanvas.width =
        video.videoWidth;

    captureCanvas.height =
        video.videoHeight;
}

video.addEventListener(
    "loadedmetadata",
    resizeCanvas
);

async function scanFrame() {

    if (
        scanning ||
        video.paused ||
        video.ended ||
        !autoScan
    ) return;

    scanning = true;

    try {

        captureCtx.drawImage(
            video,
            0,
            0,
            captureCanvas.width,
            captureCanvas.height
        );
        const camera = document.getElementById("videoSelect").value;
        const image =
            captureCanvas.toDataURL(
                "image/png",
                0.95
            );

        scanResult.innerHTML =
            "🤖 AI đang quét...";

        const response =
            await fetch(
                "http://127.0.0.1:5000/api/scan",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        image,
                        camera
                    })
                }
            );

        const data =
            await response.json();

        drawResult(data);

    } catch (err) {

        console.log(err);

        scanResult.innerHTML =
            "❌ Lỗi kết nối AI";
    }

    scanning = false;
}

function drawResult(data) {
    ctx.clearRect(0, 0, overlay.width, overlay.height);

    if (!data.success) {
        scanResult.innerHTML = "❌ Không phát hiện";
        return;
    }

    if (!data.vehicles || data.vehicles.length === 0) {
        scanResult.innerHTML = "✅ Không có xe";
        return;
    }

    scanResult.innerHTML = `🚗 ${data.vehicles.length} phương tiện`;

    data.vehicles.forEach(v => {
        // 1. VẼ KHUNG XE (Vehicle Box)
        const b = v.box;
        ctx.strokeStyle = v.violation ? "#ff4d4d" : "#00ff00"; // Đỏ nếu vi phạm, xanh nếu bình thường
        ctx.lineWidth = 3;
        ctx.strokeRect(b.x, b.y, b.w, b.h);

        // 2. VẼ NHÃN THÔNG TIN (Label)
        ctx.fillStyle = v.violation ? "#ff4d4d" : "#00ff00";
        ctx.font = "bold 16px Inter, Arial";
        const labelText = `${v.vehicle_type.toUpperCase()} | ${v.plate}`;
        const labelWidth = ctx.measureText(labelText).width + 10;
        
        ctx.fillRect(b.x, b.y - 25, labelWidth, 25); // Vẽ nền cho chữ
        ctx.fillStyle = "white";
        ctx.fillText(labelText, b.x + 5, b.y - 7);

        // // 3. VẼ KHUNG BIỂN SỐ CHI TIẾT (License Plate Box)
        // // Lưu ý: v.plate_box phải được Server trả về chính xác tọa độ trên ảnh gốc
        // if (v.plate_box) {
        //     const p = v.plate_box;
            
        //     // Vẽ khung nhỏ màu vàng bao quanh biển số để kiểm tra độ chính xác
        //     ctx.strokeStyle = "#ffeb3b"; 
        //     ctx.lineWidth = 2;
        //     ctx.setLineDash([5, 3]); // Vẽ nét đứt cho biển số nhìn chuyên nghiệp hơn
        //     ctx.strokeRect(p.x, p.y, p.w, p.h);
        //     ctx.setLineDash([]); // Reset lại nét liền cho các lần vẽ sau
            
        //     // Thêm một điểm chấm nhỏ ở góc biển số để xác nhận AI đã focus vào đây
        //     ctx.fillStyle = "#ffeb3b";
        //     ctx.beginPath();
        //     ctx.arc(p.x, p.y, 3, 0, 2 * Math.PI);
        //     ctx.fill();
        // }

        // Cập nhật bảng realtime nếu có vi phạm
        if (v.violation) {
            addViolationRow(v);
        }
    });
}

function addViolationRow(v) {

    const tr =
        document.createElement("tr");

    tr.innerHTML = `
        <td><b>#NEW</b></td>

        <td>
            <span class="badge badge-red">
                ${v.violation}
            </span>
        </td>

        <td>
            ${new Date().toLocaleTimeString()}
        </td>

        <td>Camera 1</td>

        <td>
            <code style="background:#eee;padding:3px 6px;">
                ${v.plate}
            </code>
        </td>

        <td>
            <img
                src="http://127.0.0.1:5000/evidences/${v.image}"
                class="violation-img"
            >
        </td>

        <td>
            <span class="badge badge-green">
                Chờ xử lý
            </span>
        </td>
    `;

    tableBody.prepend(tr);
}

function startScanning() {

    if (autoScan) return;

    autoScan = true;

    scanResult.innerHTML =
        "🚀 Bắt đầu quét";

    scanFrame();

    scanInterval = setInterval(() => {

        scanFrame();

    }, 1000);
}

function stopScanning() {

    autoScan = false;

    clearInterval(scanInterval);

    scanResult.innerHTML =
        "⏹ Đã dừng quét";

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