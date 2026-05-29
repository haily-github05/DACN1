from ultralytics import YOLO
import cv2
import numpy as np

vehicle_model = YOLO("AI_models/yolo11s.pt")
plate_model = YOLO("AI_models/license_plate_detector.pt")
vn_plate_model = YOLO("AI_models/vietnam-license-plate.pt")

vehicle_names = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

# =========================
# CACHE VIDEO TRACKING
# =========================
tracked_plates = {}

def detect_vehicles(
    frame,
    mode="image",
    imgsz=640,
    conf=0.4,
    verbose=False
):

    # =========================
    # IMAGE -> predict()
    # VIDEO -> track()
    # =========================
    if mode == "video":

        results = vehicle_model.track(
            frame,
            persist=True,
            tracker="botsort.yaml",
            imgsz=imgsz,
            conf=conf,
            iou=0.5,
            classes=[2, 3, 5, 7],
            device="mps",
            verbose=False
        )

    else:

        results = vehicle_model.predict(
            frame,
            imgsz=imgsz,
            conf=conf,
            iou=0.45,
            classes=[2, 3, 5, 7],
            device="mps",
            verbose=False
        )

    vehicles = []

    if not results or len(results) == 0:
        return vehicles

    # =========================
    # LOOP OBJECTS
    # =========================
    for box in results[0].boxes:

        if box.cls is None:
            continue

        cls = int(box.cls[0])
        score = float(box.conf[0])

        if cls not in vehicle_names:
            continue

        if score < 0.25:
            continue

        # =========================
        # TRACK ID
        # =========================
        track_id = -1

        if mode == "video" and box.id is not None:
            track_id = int(box.id[0])

        # =========================
        # BOX
        # =========================
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        x1 = max(0, x1)
        y1 = max(0, y1)

        x2 = min(frame.shape[1], x2)
        y2 = min(frame.shape[0], y2)

        w = x2 - x1
        h = y2 - y1

        # =========================
        # FILTER BOX SAI
        # =========================
        frame_h, frame_w = frame.shape[:2]

        # box quá lớn
        if w > frame_w * 0.7:
            continue

        if h > frame_h * 0.9:
            continue

        # box quá nhỏ
        if w < 40 or h < 40:
            continue

        # =========================
        # VIDEO MODE ?
        # =========================
        is_video = (mode == "video")

        # =========================
        # CACHE
        # =========================
        if is_video and track_id in tracked_plates:

            cached = tracked_plates[track_id]

            vehicles.append({
                "track_id": track_id,
                "vehicle_type": vehicle_names[cls],
                "vehicle_box": {
                    "x": x1,
                    "y": y1,
                    "w": w,
                    "h": h
                },
                "plate_crop": cached["plate_crop"],
                "plate_box": cached["plate_box"]
            })

            continue

        # =========================
        # VEHICLE CROP
        # =========================
        vehicle_crop = frame[y1:y2, x1:x2]

        if vehicle_crop.size == 0:
            continue

        # =========================
        # PLATE DETECTION
        # =========================
        plate_results = plate_model(
            vehicle_crop,
            conf=0.3,
            device="mps",
            verbose=False
        )

        plate_crop_final = None
        plate_box_final = None

        if (
            plate_results
            and len(plate_results[0].boxes) > 0
        ):

            best_box = max(
                plate_results[0].boxes,
                key=lambda b: float(b.conf[0])
            )

            px1, py1, px2, py2 = map(
                int,
                best_box.xyxy[0]
            )

            # =========================
            # PADDING NHỎ
            # =========================
            pad = 4

            px1 = max(0, px1 - pad)
            py1 = max(0, py1 - pad)

            px2 = min(vehicle_crop.shape[1], px2 + pad)
            py2 = min(vehicle_crop.shape[0], py2 + pad)

            plate_crop = vehicle_crop[
                py1:py2,
                px1:px2
            ]

            if plate_crop.size > 0:

                # upscale OCR
                plate_crop_final = cv2.resize(
                    plate_crop,
                    None,
                    fx=2,
                    fy=2,
                    interpolation=cv2.INTER_CUBIC
                )

                plate_box_final = {
                    "x": x1 + px1,
                    "y": y1 + py1,
                    "w": px2 - px1,
                    "h": py2 - py1
                }

                # =========================
                # CACHE VIDEO
                # =========================
                if is_video:

                    tracked_plates[track_id] = {
                        "plate_crop": plate_crop_final,
                        "plate_box": plate_box_final
                    }

                    if len(tracked_plates) > 200:
                        tracked_plates.pop(
                            next(iter(tracked_plates))
                        )

        # =========================
        # RESPONSE
        # =========================
        vehicles.append({
            "track_id": track_id if is_video else -1,
            "vehicle_type": vehicle_names[cls],
            "vehicle_box": {
                "x": x1,
                "y": y1,
                "w": w,
                "h": h
            },
            "plate_crop": plate_crop_final,
            "plate_box": plate_box_final
        })

    return vehicles