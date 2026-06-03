from ultralytics import YOLO
import cv2

# =========================
# MODELS
# =========================
vehicle_model = YOLO("AI_models/yolo11s.pt")
plate_model = YOLO("AI_models/license_plate_detector.pt")

vehicle_names = {
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

# =========================
# MEMORY (TRACK STABILITY)
# =========================
active_tracks = {}

# =========================
# MAIN FUNCTION
# =========================
def detect_vehicles(
    frame,
    mode="video",
    imgsz=640,
    conf=0.25
):
    """
    mode:
    - video: dùng tracking + ổn định ID
    - image: detect độc lập
    """

    if mode == "video":
        results = vehicle_model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            imgsz=imgsz,
            conf=conf,
            iou=0.5,
            classes=[1, 2, 3, 5, 7],
            device="cpu",
            verbose=False
        )
    else:
        results = vehicle_model.predict(
            frame,
            imgsz=imgsz,
            conf=conf,
            iou=0.5,
            classes=[1, 2, 3, 5, 7],
            device="cpu",
            verbose=False
        )

    vehicles = []

    if not results or len(results[0].boxes) == 0:
        return vehicles

    for box in results[0].boxes:

        cls = int(box.cls[0])
        score = float(box.conf[0])

        if cls not in vehicle_names or score < 0.25:
            continue

        # =========================
        # TRACK ID
        # =========================
        track_id = -1
        if mode == "video" and box.id is not None:
            track_id = int(box.id[0])

            # ===== STABILITY FILTER (QUAN TRỌNG) =====
            x1_tmp, y1_tmp, x2_tmp, y2_tmp = map(int, box.xyxy[0])

            if track_id in active_tracks:
                px, py = active_tracks[track_id]

                # tránh nhảy ID
                if abs(px - x1_tmp) > 200 or abs(py - y1_tmp) > 200:
                    continue

            active_tracks[track_id] = (x1_tmp, y1_tmp)

        # =========================
        # BOX
        # =========================
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        h_frame, w_frame = frame.shape[:2]

        # =========================
        # PAD nhẹ để không mất biển số
        # =========================
        pad = 8
        x1 = max(0, x1 - pad)
        y1 = max(0, y1 - pad)
        x2 = min(w_frame, x2 + pad)
        y2 = min(h_frame, y2 + pad)

        w = x2 - x1
        h = y2 - y1

        if w < 20 or h < 20:
            continue

        vehicle_crop = frame[y1:y2, x1:x2]

        # =========================
        # PLATE DETECTION
        # =========================
        plate_crop = None
        plate_box = None

        if vehicle_crop.size > 0:

            plate_results = plate_model(
                vehicle_crop,
                conf=0.25,
                device="cpu",
                verbose=False
            )

            if plate_results and len(plate_results[0].boxes) > 0:

                best = max(
                    plate_results[0].boxes,
                    key=lambda b: float(b.conf[0])
                )

                px1, py1, px2, py2 = map(int, best.xyxy[0])

                # ===== PAD biển số (QUAN TRỌNG) =====
                p_pad = 6
                px1 = max(0, px1 - p_pad)
                py1 = max(0, py1 - p_pad)
                px2 = min(vehicle_crop.shape[1], px2 + p_pad)
                py2 = min(vehicle_crop.shape[0], py2 + p_pad)

                crop = vehicle_crop[py1:py2, px1:px2]

                if crop.size > 0:
                    plate_crop = cv2.resize(
                        crop,
                        None,
                        fx=2,
                        fy=2,
                        interpolation=cv2.INTER_CUBIC
                    )

                    plate_box = {
                        "x": x1 + px1,
                        "y": y1 + py1,
                        "w": px2 - px1,
                        "h": py2 - py1
                    }

        # =========================
        # OUTPUT FORMAT (FIX BUG tuple/dict)
        # =========================
        vehicles.append({
            "track_id": track_id,
            "vehicle_type": vehicle_names.get(cls, "unknown"),
            "vehicle_box": {
                "x": x1,
                "y": y1,
                "w": w,
                "h": h
            },
            "plate_crop": plate_crop,
            "plate_box": plate_box
        })

    return vehicles