
const data = [
    {plate:"43A-12345", type:"Red Light", time:"10:20"},
    {plate:"92B-56789", type:"Speeding", time:"11:00"}
];

// let html="";
// data.forEach(v=>{
//     html+=`
//     <tr>
//         <td>${v.plate}</td>
//         <td>${v.type}</td>
//         <td>${v.time}</td>
//     </tr>`;
// });

document.getElementById("violationTable").innerHTML = html;
document.getElementById("total").innerText = data.length;
async function loadViolations() {
    try {
        const response = await fetch("http://127.0.0.1:5000/api/violations");
        const result = await response.json();

        let html = "";

        result.forEach((v, index) => {
            html += `
                <tr>
                    <td>${v.id ?? index + 1}</td>
                    <td>${v.plate || v.vehicle_id || "N/A"}</td>
                    <td>${v.violation_type || "Unknown"}</td>
                    <td>${v.timestamp || ""}</td>
                    <td>
                        <span class="status ${v.status || "pending"}">
                            ${v.status || "pending"}
                        </span>
                    </td>
                </tr>
            `;
        });

        document.getElementById("violationTable").innerHTML = html;
        document.getElementById("total").innerText = result.length;

    } catch (error) {
        console.error("Lỗi load violations:", error);
    }
}

// gọi khi load trang
document.addEventListener("DOMContentLoaded", loadViolations);