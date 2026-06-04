import cv2
import json
import os

config_path = os.path.join(
    os.path.dirname(__file__),
    "../../config/camera_config.json"
)

violated_ids = set()
vehicle_history = {}
def get_camera_config(video_id=1):
    global current_light, last_detect_time
    

    fallback = {
        "1": {
            "name": "Camera Ngũ Hành Sơn",
            "stop_line_ratio": 0.82,
            "roi_traffic_light": {
                "y1": 0.05,
                "y2": 0.45,
                "x1": 0.90,
                "x2": 1.00
            },
            "lane_config": {
                "is_three_lanes": False,
                "y_min_ratio": 0.30,
                "y_max_ratio": 0.90,
                "dir_top_ratio": 0.28,
                "dir_bottom_ratio": -0.08,
                "lane_top_ratio": 0.48,
                "lane_bottom_ratio": 0.33
            }
        },
        "2": {
            "name": "Camera Ngũ Hành Sơn - Video 2",
            "stop_line_ratio": 0.84,
            "roi_traffic_light": {"y1": 0.05, "y2": 0.45, "x1": 0.90, "x2": 1.00},
            "lane_config": {
                "is_three_lanes": False, 
                "y_min_ratio": 0.35, "y_max_ratio": 0.94,
                "dir_top_ratio": 0.22, "dir_bottom_ratio": 0.00,
                "lane_top_ratio": 0.45, "lane_bottom_ratio": 0.36
            }
        }
    }

    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        possible_paths = [
            os.path.join(base_dir, "config", "camera_config.json"),
            os.path.join(base_dir, "phat_hien_vi_pham", "config", "camera_config.json"),
            "config/camera_config.json",
            "camera_config.json"
        ]
        
        config_path = None
        for p in possible_paths:
            if os.path.exists(p):
                config_path = p
                break

        if config_path:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(str(video_id), fallback.get(str(video_id), fallback["1"]))
        else:
            raise FileNotFoundError("Không tìm thấy file JSON cấu hình hệ thống.")
            
    except Exception as e:
        print("CONFIG ERROR =", str(e))
        return fallback.get(str(video_id), fallback["1"])

def get_camera_config(video_id):
    default_config = {
        "stop_line_ratio": 0.5
    }

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            configs = json.load(f)
            return configs.get(str(video_id), default_config)

    except Exception as e:
        print("CAMERA CONFIG ERROR:", e)
        return default_config



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


def check_red_light_violation(
    track_id,
    bottom_y,
    frame_height,
    red_light,
    video_id=1
):
    if not red_light:
        return False

    if track_id is None or track_id == -1:
        return False

    cfg = get_camera_config(video_id)
    stop_ratio = cfg.get("stop_line_ratio", 0.5)
    stop_line_y = int(frame_height * stop_ratio)


    waiting_zone = 180

    if track_id not in vehicle_history:
        vehicle_history[track_id] = {
            "prev_bottom": bottom_y,
            "was_below_line": bottom_y > stop_line_y,
            "moving_up_count": 0
        }
        return False

    info = vehicle_history[track_id]
    prev_y = info["prev_bottom"]

    moving_up = bottom_y < prev_y - 5

    if moving_up:
        info["moving_up_count"] += 1
    else:
        info["moving_up_count"] = 0

    if bottom_y > stop_line_y:
        info["was_below_line"] = True

    crossed_line = (
        prev_y > stop_line_y
        and bottom_y <= stop_line_y
    )

    started_below_and_moving = (
        info["was_below_line"]
        and bottom_y > stop_line_y
        and bottom_y < stop_line_y + waiting_zone
        and info["moving_up_count"] >= 1
    )

    vehicle_history[track_id]["prev_bottom"] = bottom_y

    if track_id in violated_ids:
        return False

    if crossed_line or started_below_and_moving:
        violated_ids.add(track_id)
        return True

    return False

def check_red_light_static(
    bottom_y,
    frame_height,
    red_light,
    video_id=1
):
    if not red_light:
        return False

    cfg = get_camera_config(video_id)
    stop_ratio = cfg.get("stop_line_ratio", 0.5)
    stop_line_y = int(frame_height * stop_ratio)

    return bottom_y <= stop_line_y

def reset_red_light_cache():
    violated_ids.clear()
    vehicle_history.clear()