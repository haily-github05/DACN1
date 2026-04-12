import cv2
from ultralytics import YOLO

# Load model YOLO
model = YOLO("yolov8n.pt")

# Đường dẫn video (đổi tên file của bạn)
video_path = "videos\test1.mp4"

cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("Không mở được video!")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Video kết thúc")
        break

    # AI detect
    results = model(frame)

    # vẽ bounding box
    frame = results[0].plot()

    cv2.imshow("Video Detection", frame)

    # nhấn ESC để thoát
    if cv2.waitKey(25) == 27:
        break

cap.release()
cv2.destroyAllWindows()
