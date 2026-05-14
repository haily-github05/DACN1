import cv2
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort
from datetime import datetime

from AI import utils

from api.services.license_plate_detector import LicensePlateDetector
from api.models.vehicles import VehicleModel
from api.models.violations import ViolationModel
from api.models.traffic_logs import TrafficLogModel

# ==========================
# INIT
# ==========================
model = YOLO("yolov8n.pt")
tracker = DeepSort(max_age=30)

lp_detector = LicensePlateDetector("yolov8n.pt")

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3308,
    "user": "root",
    "password": "",
    "database": "traffic_db"
}

v_db = VehicleModel(DB_CONFIG)
viol_db = ViolationModel(DB_CONFIG)
log_db = TrafficLogModel(DB_CONFIG)

# ==========================
# VIDEO
# ==========================
video_path = "videos/test1.mp4"
cap = cv2.VideoCapture(video_path)

line_y = 450
is_red_light = True

violated_ids = set()
vehicle_plates = {}
prev_positions = {}

print("🚀 AI đang chạy...")

# ==========================
# LOOP
# ==========================
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("❌ Không đọc được video")
        break

    results = model(frame, verbose=False)
    detections = []

    for r in results:
        for box in r.boxes:
            conf = float(box.conf[0])
            cls = int(box.cls[0])

            if conf > 0.5 and cls in [2, 3, 5, 7]:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detections.append([[x1, y1, x2-x1, y2-y1], conf, cls])

    tracks = tracker.update_tracks(detections, frame=frame)

    # vạch trắng
    cv2.line(frame, (0, line_y), (frame.shape[1], line_y), (255,255,255), 3)

    for track in tracks:
        if not track.is_confirmed():
            continue

        track_id = track.track_id
        x1, y1, x2, y2 = map(int, track.to_ltrb())

        center_point = (int((x1+x2)/2), int((y1+y2)/2))

        # ================= OCR =================
        if track_id not in vehicle_plates:
            roi = frame[y1:y2, x1:x2]

            if roi.size > 0:
                plate = lp_detector.detect_and_read(roi)

                if plate != "UNKNOWN":
                    vehicle_plates[track_id] = plate
                    v_db.update_vehicle(plate, "Vehicle")
                    log_db.add_log("Vehicle", "Lane_01")

        current_plate = vehicle_plates.get(track_id, "Scanning...")

        # ================= CHECK VẠCH =================
        crossed = False

        if track_id in prev_positions:
            prev_y = prev_positions[track_id]
            curr_y = center_point[1]

            if prev_y < line_y and curr_y >= line_y:
                crossed = True

        prev_positions[track_id] = center_point[1]

        # ================= VI PHẠM =================
        if is_red_light and crossed:
            if track_id not in violated_ids:
                print(f"🚨 Vi phạm: {current_plate}")

                time_str = datetime.now().strftime("%Y%m%d_%H%M%S")

                # crop xe
                vehicle_crop = frame[y1:y2, x1:x2]

                evidence_path = f"evidences/violation_{track_id}_{time_str}.jpg"
                cv2.imwrite(evidence_path, vehicle_crop)

                # lưu DB
                viol_db.log_violation(track_id, "Vượt đèn đỏ", "Ngã tư A", evidence_path)

                violated_ids.add(track_id)

                cv2.rectangle(frame, (x1,y1),(x2,y2),(0,0,255),3)
                cv2.putText(frame,"VIOLATION!",(x1,y1-20),
                            cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)

        else:
            cv2.rectangle(frame, (x1,y1),(x2,y2),(0,255,0),2)

        # hiển thị biển số
        cv2.putText(frame, current_plate, (x1,y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX,0.6,(0,255,0),2)

    cv2.imshow("Traffic AI", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()