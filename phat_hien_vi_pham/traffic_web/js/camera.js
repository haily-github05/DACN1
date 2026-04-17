// const videoSelect = document.getElementById('videoSelect');
// const videoPlayer = document.getElementById('videoPlayer');
// const cameraStream = document.getElementById('cameraStream');

// // 1. Lấy dữ liệu từ SQL thông qua API
// async function loadCameraSources() {
//     try {
//         const response = await fetch('/api/cameras'); // Đường dẫn API của bạn
//         const cameras = await response.json();

//         videoSelect.innerHTML = '<option value="">-- Chọn Camera --</option>';

//         cameras.forEach(cam => {
//             const option = document.createElement('option');
//             option.value = cam.video_url;
//             option.textContent = cam.camera_name;
//             option.dataset.type = cam.is_live ? 'live' : 'recorded';
//             videoSelect.appendChild(option);
//         });
//     } catch (error) {
//         console.error("Lỗi khi tải danh sách camera:", error);
//     }
// }

// // 2. Xử lý sự kiện khi chọn Camera
// videoSelect.addEventListener('change', (e) => {
//     const selectedUrl = e.target.value;
//     const selectedOption = e.target.selectedOptions[0];

//     if (!selectedUrl) return;

//     if (selectedOption.dataset.type === 'recorded') {
//         // Nếu là video file (mp4)
//         cameraStream.style.display = 'none';
//         videoPlayer.style.display = 'block';
//         videoPlayer.src = selectedUrl;
//         videoPlayer.play();
//     } else {
//         // Nếu là luồng Live (mjpeg hoặc stream khác)
//         videoPlayer.style.display = 'none';
//         cameraStream.style.display = 'block';
//         cameraStream.src = selectedUrl;
//     }
// });

// // Khởi chạy
// loadCameraSources();