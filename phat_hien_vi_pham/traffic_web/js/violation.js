function formatTime(gmtTime) {

    if (!gmtTime) return "-";

    const date = new Date(gmtTime);

    const day =
        String(date.getUTCDate()).padStart(2, "0");

    const month =
        String(date.getUTCMonth() + 1).padStart(2, "0");

    const year =
        date.getUTCFullYear();

    const hours =
        String(date.getUTCHours()).padStart(2, "0");

    const minutes =
        String(date.getUTCMinutes()).padStart(2, "0");

    const seconds =
        String(date.getUTCSeconds()).padStart(2, "0");

    return `
        <div style="line-height:1.4">
            <b>${hours}:${minutes}:${seconds}</b><br>
            <small style="color:gray">
                ${day}/${month}/${year}
            </small>
        </div>
    `;
}
async function loadViolations() {
    try {
        const response = await fetch(
            "http://127.0.0.1:5000/api/violations"
        );
        if (!response.ok) {
            throw new Error("API Error");
        }
        const data = await response.json();
        const tableBody =
            document.getElementById("tableBody");
        tableBody.innerHTML = "";
        if (!data || data.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align:center;padding:20px;">
                        No violations detected
                    </td>
                </tr>
            `;
            return;
        }
        data.forEach(v => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><b>${v.id}</b></td>
                <td><span class="badge badge-red">${v.type || "Unknown"}</span></td>
                <td>${formatTime(v.time)}</td>
                <td><code style="background:#eee;padding:3px 6px;border-radius:4px;">${v.plate || "N/A"}</code></td>
                <td>${v.image?`<img src="http://127.0.0.1:5000/evidences/${v.image}"class="violation-img"onerror="this.src='https://via.placeholder.com/120x80?text=No+Image'">`:"No Image"}</td>
            `;
            tableBody.appendChild(tr);
        });
    } catch (err) {
        console.error("Load violations failed:", err);
        const tableBody =
            document.getElementById("tableBody");
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align:center;color:red;padding:20px;">
                    Cannot connect to server
                </td>
            </tr>
        `;
    }
}
loadViolations();
setInterval(loadViolations, 5000);