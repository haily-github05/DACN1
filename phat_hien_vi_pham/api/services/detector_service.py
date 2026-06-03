from ultralytics import YOLO
import cv2
import torch

vehicle_model = YOLO("AI_models/yolo11m.pt")
plate_model = YOLO("AI_models/license_plate_detector.pt")

vehicle_names = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}


def get_device():
    try:
        if torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


def detect_plate_in_vehicle(vehicle_crop, x1, y1, device):
    plate_crop = None
    plate_box = None

    if vehicle_crop is None or vehicle_crop.size == 0:
        return plate_crop, plate_box

    results = plate_model.predict(
        vehicle_crop,
        imgsz=640,
        conf=0.12,
        iou=0.4,
        device=device,
        verbose=False
    )

    if not results or len(results[0].boxes) == 0:
        return plate_crop, plate_box

    best = max(results[0].boxes, key=lambda b: float(b.conf[0]))
    px1, py1, px2, py2 = map(int, best.xyxy[0])

    pad = 12
    px1 = max(0, px1 - pad)
    py1 = max(0, py1 - pad)
    px2 = min(vehicle_crop.shape[1], px2 + pad)
    py2 = min(vehicle_crop.shape[0], py2 + pad)

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

    return plate_crop, plate_box


def box_iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)

    inter = iw * ih

    area_a = max(1, (ax2 - ax1) * (ay2 - ay1))
    area_b = max(1, (bx2 - bx1) * (by2 - by1))

    return inter / float(area_a + area_b - inter + 1e-6)


def inside_ratio(inner, outer):
    ix1, iy1, ix2, iy2 = inner
    ox1, oy1, ox2, oy2 = outer

    x1 = max(ix1, ox1)
    y1 = max(iy1, oy1)
    x2 = min(ix2, ox2)
    y2 = min(iy2, oy2)

    inter = max(0, x2 - x1) * max(0, y2 - y1)
    inner_area = max(1, (ix2 - ix1) * (iy2 - iy1))

    return inter / inner_area


def remove_duplicate_detections(detections):
    detections = sorted(
        detections,
        key=lambda d: (
            d["score"],
            (d["box"][2] - d["box"][0]) * (d["box"][3] - d["box"][1])
        ),
        reverse=True
    )

    kept = []

    for det in detections:
        duplicate = False

        for old in kept:
            iou = box_iou(det["box"], old["box"])
            inside = inside_ratio(det["box"], old["box"])

            if iou > 0.35 or inside > 0.75:
                duplicate = True
                break

        if not duplicate:
            kept.append(det)

    return kept


def detect_vehicles(
    frame,
    mode="video",
    imgsz=640,
    conf=0.12
):
    if frame is None:
        return []

    device = get_device()

    if mode == "video":
        results = vehicle_model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            imgsz=imgsz,
            conf=max(conf, 0.12),
            iou=0.45,
            classes=[2, 3, 5, 7],
            device=device,
            verbose=False
        )
    else:
        results = vehicle_model.predict(
            frame,
            imgsz=imgsz,
            conf=conf,
            iou=0.35,
            classes=[2, 3, 5, 7],
            device=device,
            verbose=False
        )

    if not results or len(results[0].boxes) == 0:
        return []

    h_frame, w_frame = frame.shape[:2]
    raw = []

    for box in results[0].boxes:
        cls = int(box.cls[0])
        score = float(box.conf[0])

        if cls not in vehicle_names:
            continue

        if score < conf:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        pad = 6
        x1 = max(0, x1 - pad)
        y1 = max(0, y1 - pad)
        x2 = min(w_frame, x2 + pad)
        y2 = min(h_frame, y2 + pad)

        w = x2 - x1
        h = y2 - y1

        if w < 15 or h < 15:
            continue

        track_id = -1

        if mode == "video" and box.id is not None:
            track_id = int(box.id[0])

        raw.append({
            "track_id": track_id,
            "cls": cls,
            "score": score,
            "box": (x1, y1, x2, y2)
        })

    raw = remove_duplicate_detections(raw)

    vehicles = []

    for det in raw:
        x1, y1, x2, y2 = det["box"]
        cls = det["cls"]
        score = det["score"]
        track_id = det["track_id"]

        w = x2 - x1
        h = y2 - y1

        vehicle_crop = frame[y1:y2, x1:x2]

        plate_crop, plate_box = detect_plate_in_vehicle(
            vehicle_crop,
            x1,
            y1,
            device
        )

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
            "plate_box": plate_box,
            "confidence": round(score, 3),
            "score": round(score, 3)
        })

    return vehicles