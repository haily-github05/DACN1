import cv2
import json
import os

# =========================
# CONFIG
# =========================
config_path = os.path.join(
    os.path.dirname(__file__),
    "../config/camera_config.json"
)

violated_ids = set()

vehicle_history = {}


# =========================
# GET CONFIG
# =========================
def get_camera_config(video_id):

    default_config = {
        "stop_line_ratio": 0.5
    }

    try:

        with open(config_path, "r", encoding="utf-8") as f:

            configs = json.load(f)

            return configs.get(
                str(video_id),
                default_config
            )

    except:

        return default_config


# =========================
# DRAW STOP LINE
# =========================
def draw_stop_line(
    frame,
    red_light=False,
    video_id=1
):

    h, w = frame.shape[:2]

    cfg = get_camera_config(video_id)

    stop_ratio = cfg.get(
        "stop_line_ratio",
        0.5
    )

    stop_line_y = int(h * stop_ratio)

    color = (
        (0, 0, 255)
        if red_light
        else (0, 255, 0)
    )

    cv2.line(
        frame,
        (0, stop_line_y),
        (w, stop_line_y),
        color,
        4
    )

    cv2.putText(
        frame,
        "STOP LINE",
        (20, stop_line_y - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        color,
        2
    )

    return stop_line_y


# =========================
# CHECK VIOLATION
# =========================
def check_red_light_violation(
    track_id,
    center_y,
    frame_height,
    red_light,
    video_id=1
):

    if not red_light:
        return False

    if track_id is None:
        return False

    cfg = get_camera_config(video_id)

    stop_ratio = cfg.get(
        "stop_line_ratio",
        0.5
    )

    stop_line_y = int(
        frame_height * stop_ratio
    )

    # lần đầu xuất hiện
    if track_id not in vehicle_history:

        vehicle_history[track_id] = center_y

        return False

    prev_y = vehicle_history[track_id]

    vehicle_history[track_id] = center_y

    crossed = (
        prev_y < stop_line_y
        and center_y >= stop_line_y
    )

    if (
        crossed
        and track_id not in violated_ids
    ):

        violated_ids.add(track_id)

        return True

    return False


# =========================
# RESET
# =========================
def reset_red_light_cache():

    violated_ids.clear()

    vehicle_history.clear()