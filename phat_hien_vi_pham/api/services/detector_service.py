from ultralytics import YOLO
import cv2

# =========================
# MODELS
# =========================
vehicle_model = YOLO("AI_models/yolo11m.pt")
plate_model = YOLO("AI_models/license_plate_detector.pt")

vehicle_names = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

# =========================
# MEMORY
# =========================
active_tracks = {}
fake_track_memory = {}
next_fake_id = 10000


def get_iou(boxA, boxB):
    ax1, ay1, ax2, ay2 = boxA
    bx1, by1, bx2, by2 = boxB

    ix1 = max(ax1, bx1)
    iy1 = max(ay1, by1)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)

    iw = max(0, ix2 - ix1)
    ih = max(0, iy2 - iy1)

    inter = iw * ih
    areaA = max(1, (ax2 - ax1) * (ay2 - ay1))
    areaB = max(1, (bx2 - bx1) * (by2 - by1))

    return inter / float(areaA + areaB - inter)


def get_fake_track_id(xyxy):
    global next_fake_id

    best_id = None
    best_iou = 0

    for tid, old_xyxy in fake_track_memory.items():
        iou = get_iou(xyxy, old_xyxy)

        if iou > best_iou:
            best_iou = iou
            best_id = tid

    if best_iou > 0.25 and best_id is not None:
        fake_track_memory[best_id] = xyxy
        return best_id

    new_id = next_fake_id
    next_fake_id += 1

    fake_track_memory[new_id] = xyxy

    if len(fake_track_memory) > 200:
        fake_track_memory.pop(next(iter(fake_track_memory)))

    return new_id


def crop_plate_fallback(vehicle_crop):
    """
    Fallback khi YOLO biển số không detect được.
    Chỉ crop vùng dưới giữa xe, tránh lấy chữ HONDA phía trên.
    """
    if vehicle_crop is None or vehicle_crop.size == 0:
        return None, None

    vh, vw = vehicle_crop.shape[:2]

    # vùng dưới giữa xe máy
    fx1 = int(vw * 0.25)
    fx2 = int(vw * 0.75)
    fy1 = int(vh * 0.55)
    fy2 = int(vh * 0.88)

    crop = vehicle_crop[fy1:fy2, fx1:fx2]

    if crop is None or crop.size == 0:
        return None, None

    return crop, {
        "x": fx1,
        "y": fy1,
        "w": fx2 - fx1,
        "h": fy2 - fy1
    }


def detect_plate_crop(vehicle_crop):
    """
    Trả về plate_crop và plate_box tương đối trong vehicle_crop.
    Ưu tiên YOLO biển số, nếu fail thì fallback crop vùng dưới xe.
    """
    if vehicle_crop is None or vehicle_crop.size == 0:
        return None, None

    plate_crop = None
    plate_box = None

    # =========================
    # 1. YOLO LICENSE PLATE
    # =========================
    plate_results = plate_model(
        vehicle_crop,
        conf=0.35,
        device="cpu",
        verbose=False
    )

    if plate_results and len(plate_results[0].boxes) > 0:
        best = max(
            plate_results[0].boxes,
            key=lambda b: float(b.conf[0])
        )

        px1, py1, px2, py2 = map(int, best.xyxy[0])

        # chỉ pad nhẹ, không lấy quá rộng
        p_pad = 4

        px1 = max(0, px1 - p_pad)
        py1 = max(0, py1 - p_pad)
        px2 = min(vehicle_crop.shape[1], px2 + p_pad)
        py2 = min(vehicle_crop.shape[0], py2 + p_pad)

        crop = vehicle_crop[py1:py2, px1:px2]

        if crop is not None and crop.size > 0:
            plate_crop = crop
            plate_box = {
                "x": px1,
                "y": py1,
                "w": px2 - px1,
                "h": py2 - py1
            }

    # =========================
    # 2. FALLBACK
    # =========================
    if plate_crop is None:
        plate_crop, plate_box = crop_plate_fallback(vehicle_crop)

    if plate_crop is None:
        return None, None

    plate_crop = cv2.resize(
        plate_crop,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    return plate_crop, plate_box


def remove_duplicate_boxes(vehicles):
    """
    Xoá box nhỏ bị chồng lên box lớn cùng loại.
    Tránh 1 xe hiện 2 khung.
    """
    result = []

    for i, a in enumerate(vehicles):
        ab = a["vehicle_box"]
        ax1 = ab["x"]
        ay1 = ab["y"]
        ax2 = ab["x"] + ab["w"]
        ay2 = ab["y"] + ab["h"]
        a_area = ab["w"] * ab["h"]

        remove = False

        for j, b in enumerate(vehicles):
            if i == j:
                continue

            if a["vehicle_type"] != b["vehicle_type"]:
                continue

            bb = b["vehicle_box"]
            bx1 = bb["x"]
            by1 = bb["y"]
            bx2 = bb["x"] + bb["w"]
            by2 = bb["y"] + bb["h"]
            b_area = bb["w"] * bb["h"]

            ix1 = max(ax1, bx1)
            iy1 = max(ay1, by1)
            ix2 = min(ax2, bx2)
            iy2 = min(ay2, by2)

            iw = max(0, ix2 - ix1)
            ih = max(0, iy2 - iy1)
            inter = iw * ih

            if inter <= 0:
                continue

            overlap_small = inter / max(1, min(a_area, b_area))

            if overlap_small > 0.6 and a_area < b_area:
                remove = True
                break

        if not remove:
            result.append(a)

    return result


def detect_vehicles(
    frame,
    mode="video",
    imgsz=640,
    conf=0.35
):
    if frame is None:
        return []

    if mode == "video":
        results = vehicle_model.track(
            frame,
            persist=True,
            tracker="trackers/bytetrack.yaml",
            imgsz=960,
            conf=0.35,
            iou=0.5,
            classes=[2, 3, 5, 7],
            device="cpu",
            verbose=False
        )
    else:
        results = vehicle_model.predict(
            frame,
            imgsz=1280,
            conf=0.30,
            iou=0.40,
            classes=[2,3,5,7]
        )

    vehicles = []

    if not results or len(results[0].boxes) == 0:
        return vehicles

    h_frame, w_frame = frame.shape[:2]

    for box in results[0].boxes:
        cls = int(box.cls[0])
        score = float(box.conf[0])

        if cls not in vehicle_names or score < conf:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        # bỏ box ma dính mép dưới
        if y2 >= h_frame - 3:
            continue

        track_id = -1

        if mode == "video":
            if box.id is not None:
                track_id = int(box.id[0])
            else:
                track_id = get_fake_track_id((x1, y1, x2, y2))

            active_tracks[track_id] = (x1, y1, x2, y2)

        # pad nhẹ cho box xe
        pad = 2

        x1 = max(0, x1 - pad)
        y1 = max(0, y1 - pad)
        x2 = min(w_frame, x2 + pad)
        y2 = min(h_frame, y2 + pad)

        w = x2 - x1
        h = y2 - y1

        if w < 20 or h < 20:
            continue

        vehicle_crop = frame[y1:y2, x1:x2]

        plate_crop = None
        plate_box = None

        if vehicle_crop.size > 0:
            plate_crop, local_plate_box = detect_plate_crop(vehicle_crop)

            if local_plate_box:
                plate_box = {
                    "x": x1 + local_plate_box["x"],
                    "y": y1 + local_plate_box["y"],
                    "w": local_plate_box["w"],
                    "h": local_plate_box["h"]
                }

        vehicles.append({
            "track_id": track_id,
            "vehicle_type": vehicle_names.get(cls, "unknown"),
            "confidence": score,
            "vehicle_box": {
                "x": x1,
                "y": y1,
                "w": w,
                "h": h
            },
            "plate_crop": plate_crop,
            "plate_box": plate_box
        })

    return remove_duplicate_boxes(vehicles)