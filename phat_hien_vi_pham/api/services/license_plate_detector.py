from ultralytics import YOLO
import cv2
import numpy as np

# =========================
# LOAD MODELS
# =========================

vehicle_model = YOLO(
    "AI_models/yolo11s.pt"
)

# model detect biển số thường
plate_model = YOLO(
    "AI_models/license_plate_detector.pt"
)

# model biển số Việt Nam
vn_plate_model = YOLO(
    "AI_models/vietnam-license-plate.pt"
)

# =========================
# VEHICLE CLASSES
# =========================

vehicle_names = {

    2: "car",

    3: "motorcycle",

    5: "bus",

    7: "truck"
}

# =========================
# CACHE TRACKED PLATES
# =========================

tracked_plates = {}

# =========================
# DETECT VEHICLES
# =========================

def detect_vehicles(
    frame,
    imgsz=416,
    conf=0.5,
    verbose=False
):

    vehicles = []

    try:

        results = vehicle_model.track(

            frame,

            persist=True,

            tracker="bytetrack.yaml",

            imgsz=640,

            conf=0.4,

            iou=0.5,

            classes=[2, 3, 5, 7],

            device="mps",

            verbose=False
        )

    except Exception as e:

        print("TRACK ERROR:", e)

        return vehicles

    if not results or len(results) == 0:
        return vehicles

    result = results[0]

    if result.boxes is None:
        return vehicles

    # =========================
    # LOOP VEHICLES
    # =========================

    for box in result.boxes:

        try:

            # =========================
            # CHECK VALID
            # =========================

            if box.cls is None:
                continue

            cls = int(box.cls[0])

            conf = float(box.conf[0])

            if cls not in vehicle_names:
                continue

            if conf < 0.25:
                continue

            # =========================
            # TRACK ID
            # =========================

            track_id = None

            if box.id is not None:
                track_id = int(box.id[0])

            # =========================
            # BOX
            # =========================

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            x1 = max(0, x1)
            y1 = max(0, y1)

            x2 = min(frame.shape[1], x2)
            y2 = min(frame.shape[0], y2)

            # =========================
            # CACHE
            # =========================

            if (
                track_id is not None and
                track_id in tracked_plates
            ):

                cached = tracked_plates[track_id]

                vehicles.append({

                    "track_id":
                        track_id,

                    "vehicle_type":
                        vehicle_names[cls],

                    "vehicle_box": {
                        "x": x1,
                        "y": y1,
                        "w": x2 - x1,
                        "h": y2 - y1
                    },

                    "plate_crop":
                        cached["plate_crop"],

                    "plate_box":
                        cached["plate_box"]
                })

                continue

            # =========================
            # VEHICLE CROP
            # =========================

            vehicle_crop = frame[
                y1:y2,
                x1:x2
            ]

            if vehicle_crop.size == 0:
                continue

            # =========================
            # DETECT VN PLATE
            # =========================

            plate_results = vn_plate_model(

                vehicle_crop,

                conf=0.35,

                imgsz=640,

                device="mps",

                verbose=False
            )

            # =========================
            # FALLBACK MODEL
            # =========================

            if (
                not plate_results or
                len(plate_results[0].boxes) == 0
            ):

                plate_results = plate_model(

                    vehicle_crop,

                    conf=0.25,

                    device="mps",

                    verbose=False
                )

            # =========================
            # DEFAULT
            # =========================

            plate_crop_final = None

            plate_box_final = None

            # =========================
            # PLATE FOUND
            # =========================

            if (
                plate_results and
                len(plate_results[0].boxes) > 0
            ):

                # best box
                best_box = max(

                    plate_results[0].boxes,

                    key=lambda b:
                        float(b.conf[0])
                )

                px1, py1, px2, py2 = map(
                    int,
                    best_box.xyxy[0]
                )

                # =========================
                # PADDING
                # =========================

                pad = 10

                px1 = max(0, px1 - pad)
                py1 = max(0, py1 - pad)

                px2 = min(
                    vehicle_crop.shape[1],
                    px2 + pad
                )

                py2 = min(
                    vehicle_crop.shape[0],
                    py2 + pad
                )

                # =========================
                # CROP PLATE
                # =========================

                plate_crop = vehicle_crop[
                    py1:py2,
                    px1:px2
                ]

                if plate_crop.size > 0:

                    # =========================
                    # UPSCALE
                    # =========================

                    plate_crop_final = cv2.resize(

                        plate_crop,

                        None,

                        fx=3,

                        fy=3,

                        interpolation=cv2.INTER_CUBIC
                    )

                    # =========================
                    # DENOISE
                    # =========================

                    plate_crop_final = cv2.fastNlMeansDenoisingColored(

                        plate_crop_final,

                        None,

                        10,

                        10,

                        7,

                        21
                    )

                    # =========================
                    # SHARPEN
                    # =========================

                    kernel = np.array([

                        [0, -1, 0],

                        [-1, 5, -1],

                        [0, -1, 0]
                    ])

                    plate_crop_final = cv2.filter2D(

                        plate_crop_final,

                        -1,

                        kernel
                    )

                    # =========================
                    # CONTRAST
                    # =========================

                    plate_crop_final = cv2.convertScaleAbs(

                        plate_crop_final,

                        alpha=1.2,

                        beta=10
                    )

                    # =========================
                    # SAVE PLATE BOX
                    # =========================

                    plate_box_final = {

                        "x": x1 + px1,

                        "y": y1 + py1,

                        "w": px2 - px1,

                        "h": py2 - py1
                    }

                    # =========================
                    # CACHE
                    # =========================

                    if track_id is not None:

                        tracked_plates[track_id] = {

                            "plate_crop":
                                plate_crop_final,

                            "plate_box":
                                plate_box_final
                        }

                        # limit cache
                        if len(tracked_plates) > 200:

                            tracked_plates.pop(
                                next(iter(tracked_plates))
                            )

            # =========================
            # APPEND
            # =========================

            vehicles.append({

                "track_id":
                    track_id,

                "vehicle_type":
                    vehicle_names[cls],

                "vehicle_box": {

                    "x": x1,

                    "y": y1,

                    "w": x2 - x1,

                    "h": y2 - y1
                },

                "plate_crop":
                    plate_crop_final,

                "plate_box":
                    plate_box_final
            })

        except Exception as e:

            print("BOX ERROR:", e)

    return vehicles