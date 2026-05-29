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

        select.innerHTML = "";

        videos.forEach(video => {
            const option = document.createElement("option");
            option.value = video.id;
            option.textContent = video.name;
            select.appendChild(option);
        });

        if (videos.length > 0) {
            player.src = `http://127.0.0.1:5000/videos/${videos[0].path.replace("videos/", "")}`;
        }

        select.addEventListener("change", () => {
            const selectedVideo = videos.find(v => v.id == select.value);

            if (!selectedVideo) return;

            player.src = `http://127.0.0.1:5000/videos/${selectedVideo.path.replace("videos/", "")}`;
            player.load();
            player.play();
        });

        player.addEventListener("loadeddata", async () => {
            try {
                console.log("🔥 AI warming...");

                const tempCanvas = document.createElement("canvas");
                const tempCtx = tempCanvas.getContext("2d");

                tempCanvas.width = player.videoWidth;
                tempCanvas.height = player.videoHeight;

                tempCtx.drawImage(player, 0, 0, 640, 360);

                const blob = await new Promise(resolve => 
                    tempCanvas.toBlob(resolve, "image/jpeg", 0.5)
                );

                const formData = new FormData();
                formData.append("image", blob, "warmup.jpg");
                formData.append("video_id", "1");
                formData.append("mode", "video");

                await fetch("http://127.0.0.1:5000/api/scan", {
                    method: "POST",
                    body: formData
                });

                console.log("✅ AI READY");

                const status = document.getElementById("videoScanResult");
                if (status) {
                    status.innerHTML = "🟢 AI ĐÃ SẴN SÀNG";
                }
            } catch (err) {
                console.error("Warmup lỗi:", err);
            }
        });

    } catch (err) {
        console.error(err);
    }
});