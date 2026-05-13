window.addEventListener(
    "load",
    async () => {

        const select =
            document.getElementById(
                "videoSelect"
            );

        const player =
            document.getElementById(
                "videoPlayer"
            );

        try {

            const response =
                await fetch(
                    "http://127.0.0.1:5000/videos"
                );

            const videos =
                await response.json();

            videos.forEach(video => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    video.path;

                option.textContent =
                    video.name;

                select.appendChild(
                    option
                );
            });

            if (videos.length > 0) {

                player.src =
                    `http://127.0.0.1:5000/videos/${videos[0].path}`;
            }

            select.addEventListener(
                "change",
                () => {

                    player.src =
                        `http://127.0.0.1:5000/videos/${select.value}`;

                    player.load();

                    player.play();
                }
            );

        } catch (err) {

            console.error(err);
        }
    }
);
function updateViolationTable(vehicles) {
    const tbody = document.getElementById("tableBody");
    vehicles.forEach(v => {
        if (v.violation) {
            const row = `<tr>
                <td><b>NEW</b></td>
                <td><span class="badge badge-red">${v.violation}</span></td>
                <td>${new Date().toLocaleTimeString()}</td>
                <td>Camera 01</td>
                <td><code>${v.plate}</code></td>
                <td><img src="evidences/${v.image}" class="violation-img"></td>
            </tr>`;
            tbody.insertAdjacentHTML('afterbegin', row);
        }
    });
}
