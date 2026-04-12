document.addEventListener("DOMContentLoaded", () => {
    console.log("🔥 violation.js loaded");
    loadViolations();

    setInterval(loadViolations, 3000);
});

function loadViolations() {
    fetch("http://127.0.0.1:5000/api/violations")
    
        .then(res => res.json())
        .then(data => {
            console.log("DATA FROM API:", data);

            const table = document.getElementById("tableBody");

            if (!table) {
                console.log("❌ tableBody not found");
                return;
            }

            table.innerHTML = "";
data.sort((a, b) => {
            return new Date(b.time) - new Date(a.time);
        });
            data.forEach(v => {
                table.innerHTML += `
                    <tr>
                        <td>${v.id}</td>
                        <td>${v.type}</td>
                        <td>${v.time}</td>
                        <td>${v.camera || ""}</td>
                        <td>${v.plate || ""}</td>
                        <td>
                            <img src="http://127.0.0.1:5000${v.image}" width="80">
                        </td>
                        <td>${v.status || "NEW"}</td>
                    </tr>
                `;
            });
        })
        .catch(err => {
            console.log("❌ API ERROR:", err);
        });
}