import cv2
import numpy as np
from api.services.red_light_service import get_camera_config


def get_line_x(current_y, y_min, y_max, top_x, bottom_x):
    if y_max == y_min:
        return int(top_x)

    t = (current_y - y_min) / (y_max - y_min)
    return int(top_x + (bottom_x - top_x) * t)


def draw_dashed_line(
    frame,
    y_min,
    y_max,
    top_x,
    bottom_x,
    color=(0, 255, 255),
    thickness=2
):
    points_y = np.linspace(y_min, y_max, 15, dtype=int)

    for i in range(len(points_y) - 1):
        if i % 2 == 0:
            y_start = points_y[i]
            y_end = points_y[i + 1]

            x_start = get_line_x(
                y_start,
                y_min,
                y_max,
                top_x,
                bottom_x
            )

            x_end = get_line_x(
                y_end,
                y_min,
                y_max,
                top_x,
                bottom_x
            )

            cv2.line(
                frame,
                (x_start, y_start),
                (x_end, y_end),
                color,
                thickness,
                cv2.LINE_AA
            )


def draw_zones(frame, video_id=1):
    try:
        cfg = get_camera_config(video_id) or {}
        lane_cfg = cfg.get("lane_config")

        if not lane_cfg:
            print(f"⚠️ Không tìm thấy lane_config cho video_id={video_id}")
            return

        img_h, img_w = frame.shape[:2]

        y_min = int(lane_cfg.get("y_min_ratio", 0.35) * img_h)
        y_max = int(lane_cfg.get("y_max_ratio", 1.0) * img_h)

        x_dir_top = int(lane_cfg.get("dir_top_ratio", 0.26) * img_w)
        x_dir_bottom = int(lane_cfg.get("dir_bottom_ratio", -0.08) * img_w)

        x_lane_top = int(lane_cfg.get("lane_top_ratio", 0.42) * img_w)
        x_lane_bottom = int(lane_cfg.get("lane_bottom_ratio", 0.33) * img_w)

        is_three_lanes = lane_cfg.get("is_three_lanes", False)

        cv2.line(
            frame,
            (
                get_line_x(
                    y_min,
                    y_min,
                    y_max,
                    x_dir_top,
                    x_dir_bottom
                ),
                y_min
            ),
            (
                get_line_x(
                    y_max,
                    y_min,
                    y_max,
                    x_dir_top,
                    x_dir_bottom
                ),
                y_max
            ),
            (0, 0, 255),
            2,
            cv2.LINE_AA
        )

        if is_three_lanes:
            x_mid_top = int(lane_cfg.get("mid_top_ratio", 0.52) * img_w)
            x_mid_bottom = int(lane_cfg.get("mid_bottom_ratio", 0.00) * img_w)

            draw_dashed_line(
                frame,
                y_min,
                y_max,
                x_mid_top,
                x_mid_bottom,
                color=(255, 255, 255)
            )

            draw_dashed_line(
                frame,
y_min,
                y_max,
                x_lane_top,
                x_lane_bottom,
                color=(0, 255, 255)
            )

            cv2.putText(
                frame,
                "LAN 3 (OTO)",
                (max(10, x_mid_top - 90), y_min + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

            cv2.putText(
                frame,
                "LAN 2 (MIXED)",
                (x_mid_top + 20, y_min + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1,
                cv2.LINE_AA
            )

            cv2.putText(
                frame,
                "LAN 1 (XEMAY)",
                (x_lane_top + 30, y_min + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1,
                cv2.LINE_AA
            )

        else:
            draw_dashed_line(
                frame,
                y_min,
                y_max,
                x_lane_top,
                x_lane_bottom,
                color=(0, 255, 255)
            )

            cv2.putText(
                frame,
                "LAN 2 (OTO)",
                (x_lane_top - 100, y_min + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1,
                cv2.LINE_AA
            )

            cv2.putText(
                frame,
                "LAN 1 (XEMAY)",
                (x_lane_top + 20, y_min + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1,
                cv2.LINE_AA
            )

        cv2.putText(
            frame,
            "NGUOC CHIEU",
            (max(5, x_dir_top - 110), y_min + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            1,
            cv2.LINE_AA
        )

    except Exception as e:
        print(f"🚨 Lỗi tại draw_zones: {e}")


def check_lane_violation(
    vehicle_x,
    vehicle_y,
    vehicle_type,
    video_id=1,
    frame_width=1920,
    frame_height=1080
):
    violations = []

    vehicle_x = int(vehicle_x)
    vehicle_y = int(vehicle_y)

    cfg = get_camera_config(video_id) or {}
    lane_cfg = cfg.get("lane_config")

    if not lane_cfg:
        return violations

    y_min = int(lane_cfg.get("y_min_ratio", 0.35) * frame_height)
    y_max = int(lane_cfg.get("y_max_ratio", 1.0) * frame_height)

    if not (y_min <= vehicle_y <= y_max):
        return violations

    x_dir_top = int(lane_cfg.get("dir_top_ratio", 0.26) * frame_width)
    x_dir_bottom = int(lane_cfg.get("dir_bottom_ratio", -0.08) * frame_width)

    x_lane_top = int(lane_cfg.get("lane_top_ratio", 0.42) * frame_width)
    x_lane_bottom = int(lane_cfg.get("lane_bottom_ratio", 0.33) * frame_width)
    x_dir_boundary = get_line_x(
        vehicle_y,
        y_min,
        y_max,
        x_dir_top,
        x_dir_bottom
    )

    x_lane_boundary = get_line_x(
        vehicle_y,
        y_min,
        y_max,
        x_lane_top,
        x_lane_bottom
    )

    is_three_lanes = lane_cfg.get("is_three_lanes", False)

    if vehicle_x < x_dir_boundary:
        return violations

    if is_three_lanes:
        x_mid_top = int(lane_cfg.get("mid_top_ratio", 0.52) * frame_width)
        x_mid_bottom = int(lane_cfg.get("mid_bottom_ratio", 0.00) * frame_width)

        x_mid_boundary = get_line_x(
            vehicle_y,
            y_min,
            y_max,
            x_mid_top,
            x_mid_bottom
        )

        if vehicle_type in ["motorbike", "motorcycle"]:
            if vehicle_x < x_mid_boundary:
                violations.append(
                    "Xe máy đi sai phần đường (Vào làn ô tô)"
                )

        elif vehicle_type in ["car", "truck", "bus"]:
            if vehicle_x >= x_lane_boundary:
                violations.append(
                    "Ô tô  đi sai phần đường (Vào làn xe máy)"
                )

    else:
        if vehicle_type in ["motorbike", "motorcycle"]:
            if vehicle_x < x_lane_boundary:
                violations.append(
                    "Xe máy đi sai phần đường (Vào làn ô tô)"
                )

        elif vehicle_type in ["car", "truck", "bus"]:
            if vehicle_x >= x_lane_boundary:
                violations.append(
                    "Ô tô  đi sai phần đường (Vào làn xe máy)"
                )

    return violations


def check_helmet_violation(frame, box, vehicle_type, video_id=1):
    if vehicle_type not in ["motorbike", "motorcycle"]:
        return None

    x = int(box["x"])
    y = int(box["y"])
    w = int(box["w"])
    h = int(box["h"])

    try:
        from api.services.helmet_service import detect_helmet

        vehicle_crop = frame[
            max(0, y):min(frame.shape[0], y + h),
            max(0, x):min(frame.shape[1], x + w)
        ]

        if vehicle_crop.size > 0 and detect_helmet(vehicle_crop):
            return "Không đội mũ bảo hiểm"

    except Exception:
        pass

    return None
