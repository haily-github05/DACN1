from ultralytics import YOLO
import time
import json
import os

# =========================
# CONFIG
# =========================

# Thay dòng config_path hiện tại bằng dòng này:
config_path = "/Users/hohaily/Documents/github/DACN1/phat_hien_vi_pham/config/camera_config.json"

traffic_model = YOLO("AI_models/traffic-light.pt")

current_light = "unknown"

last_detect_time = 0

HOLD_SECONDS = 2


# =========================
# LOAD CAMERA CONFIG
# =========================
def get_roi_config(video_id):

    default_config = {
        "stop_line_ratio": 0.5,
        "roi_traffic_light": {
            "y1": 0.0,
            "y2": 0.3,
            "x1": 0.25,
            "x2": 0.75
        }
    }

    try:

        with open(config_path, "r", encoding="utf-8") as f:

            configs = json.load(f)

            return configs.get(
                str(video_id),
                default_config
            )
            print(f"DEBUG: Đang load config cho camera {video_id} -> {cfg}")

    except Exception as e:

        print("CONFIG ERROR =", e)

        return default_config


# =========================
# DETECT TRAFFIC LIGHT
# =========================
def detect_traffic_light(frame, video_id=1):

    global current_light
    global last_detect_time

    h, w = frame.shape[:2]

    cfg = get_roi_config(video_id)


    print(cfg)

    roi_cfg = cfg.get(
        "roi_traffic_light",
        {}
    )

    # =========================
    # ROI
    # =========================
    roi_y1 = int(
        roi_cfg.get("y1", 0.0) * h
    )

    roi_y2 = int(
        roi_cfg.get("y2", 0.3) * h
    )

    roi_x1 = int(
        roi_cfg.get("x1", 0.25) * w
    )

    roi_x2 = int(
        roi_cfg.get("x2", 0.75) * w
    )

    roi = frame[
        roi_y1:roi_y2,
        roi_x1:roi_x2
    ]

    # ROI lỗi
    if roi.size == 0:

        return {
            "red": False,
            "light": "unknown",
            "box": None
        }

    # =========================
    # YOLO
    # =========================
    results = traffic_model(
        roi,
        imgsz=320,
        conf=0.4,
        verbose=False
    )

    detected_color = None

    best_conf = 0

    best_box = None

    for result in results:

        for box in result.boxes:

            cls_id = int(box.cls[0])

            conf = float(box.conf[0])

            class_name = traffic_model.names[
                cls_id
            ].lower()

            if conf > best_conf:

                best_conf = conf

                if "red" in class_name:
                    detected_color = "red"

                elif "yellow" in class_name:
                    detected_color = "yellow"

                elif "green" in class_name:
                    detected_color = "green"

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )

                best_box = {
                    "x": x1 + roi_x1,
                    "y": y1 + roi_y1,
                    "w": x2 - x1,
                    "h": y2 - y1
                }

    # =========================
    # HOLD LAST STATE
    # =========================
    if detected_color:

        current_light = detected_color

        last_detect_time = time.time()

    elif (
        time.time() - last_detect_time
        > HOLD_SECONDS
    ):

        current_light = "unknown"

    return {
        "red": current_light == "red",
        "light": current_light,
        "box": best_box
    }