import cv2
from ultralytics import YOLO

# LOAD MODEL
model = YOLO("AI_models/yolo11s.pt")

# VIDEO
video_path = "videos/test1.mp4"

cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Không mở được video!")
    exit()

# Đếm frame
frame_count = 0

# Lưu kết quả detect cũ
last_results = None

while True:

    ret, frame = cap.read()

    if not ret:
        print("Video kết thúc")
        break

    frame_count += 1

    # =========================
    # DETECT MỖI 5 FRAME
    # =========================
    if frame_count % 5 == 0:

        last_results = model(
            frame,
            imgsz=640,
            conf=0.5,
            verbose=False
        )

    # =========================
    # HIỂN THỊ KẾT QUẢ CŨ
    # =========================
    if last_results is not None:

        annotated_frame = last_results[0].plot()

    else:
        annotated_frame = frame

    cv2.imshow("Traffic Detection", annotated_frame)

    # ESC để thoát
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()