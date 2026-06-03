import cv2
import json
import os

# =========================
# CONFIG
# =========================
config_path = os.path.join(
    os.path.dirname(__file__),
    "../../config/camera_config.json"
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

        return configs.get(str(video_id), default_config)

    except Exception as e:
        print("CONFIG ERROR =", e)
        return default_config


# =========================
# DRAW STOP LINE
# =========================
def draw_stop_line(frame, red_light=False, video_id=1):
    h, w = frame.shape[:2]

    cfg = get_camera_config(video_id)
    stop_ratio = cfg.get("stop_line_ratio", 0.5)

    stop_line_y = int(h * stop_ratio)

    color = (0, 0, 255) if red_light else (0, 255, 0)

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
# CHECK RED LIGHT VIOLATION
# =========================
def check_red_light_violation(
    track_key,
    vehicle_y,
    frame_height,
    red_light,
    video_id=1
):
    """
    Tối ưu cho camera xe đi từ dưới lên:
    - Không cần vẽ mũi xe.
    - Dùng cạnh trên bbox của xe làm điểm kiểm tra ảo.
    - Chỉ báo lỗi khi xe đang di chuyển lên và cắt qua vạch lúc đèn đỏ.
    """

    if track_key in [None, -1, ""]:
        return False

    cfg = get_camera_config(video_id)
    stop_ratio = cfg.get("stop_line_ratio", 0.5)
    stop_line_y = int(frame_height * stop_ratio)

    prev_y = vehicle_history.get(track_key)

    # lưu vị trí hiện tại
    vehicle_history[track_key] = vehicle_y

    if prev_y is None:
        return False

    if not red_light:
        return False

    # xe đi từ dưới lên => y giảm
    moving_up = vehicle_y < prev_y

    if not moving_up:
        return False

    # cắt qua vạch từ dưới lên
    crossed_line = (
        prev_y >= stop_line_y
        and vehicle_y <= stop_line_y
    )

    # trường hợp scan chậm, xe nhảy qua vạch giữa 2 frame
    jumped_over_line = (
        prev_y > stop_line_y + 40
        and vehicle_y < stop_line_y - 40
    )

    if (
        track_key not in violated_ids
        and (crossed_line or jumped_over_line)
    ):
        violated_ids.add(track_key)
        return True

    return False
# =========================
# RESET CACHE
# =========================
def reset_red_light_cache():
    violated_ids.clear()
    vehicle_history.clear()