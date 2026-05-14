window.addEventListener("load", async () => {

    const select = document.getElementById("videoSelect");
    const player = document.getElementById("videoPlayer");

    try {
        const response = await fetch("http://127.0.0.1:5000/videos");
        const videos = await response.json();

        if (!Array.isArray(videos)) {
            console.error("API lỗi:", videos);
            return;
        }

        // CLEAR trước khi add
        select.innerHTML = "";

        videos.forEach(video => {

            const option = document.createElement("option");

            // ⭐ QUAN TRỌNG NHẤT: phải là ID
            option.value = video.id;

            option.textContent = video.name;

            select.appendChild(option);
        });

        // set video mặc định
        if (videos.length > 0) {
            player.src = `http://127.0.0.1:5000/videos/${videos[0].path.replace("videos/", "")}`;
        }

        // change video preview
        select.addEventListener("change", () => {

            const selectedVideo = videos.find(v => v.id == select.value);

            if (!selectedVideo) return;

            player.src = `http://127.0.0.1:5000/videos/${selectedVideo.path.replace("videos/", "")}`;

            player.load();
            player.play();
        });

    } catch (err) {
        console.error(err);
    }
});