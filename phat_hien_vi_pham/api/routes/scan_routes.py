from flask import Blueprint, request, jsonify
import os
import time
import cv2
import numpy as np
import mysql.connector

from api.services.detector_service import detect_vehicles
from api.services.ocr_service import read_plate_crop
from api.services.traffic_light_service import detect_traffic_light
from api.routes.lane_routes import draw_zones, check_lane_violation
from api.services.red_light_service import (
    draw_stop_line,
    get_camera_config,
    check_red_light_violation
)

scan_bp = Blueprint("scan", __name__)

plate_cache = {}
best_plate_cache = {}
violated_tracks = {}
saved_violation_tracks = set()

db_config = {
    "host": "127.0.0.1",
    "port": 3308,
    "user": "root",
    "password": "",
    "database": "traffic_db"
}

vehicle_map = {
    "motorcycle": 1,
    "car": 2,
    "bus": 3,
    "truck": 4,
    "person": 5,
    "bicycle": 6
}

vehicle_name_vi = {
    "motorcycle": "Xe máy",
    "car": "Ô tô",
    "bus": "Xe buýt",
    "truck": "Xe tải",
    "person": "Người đi bộ",
    "bicycle": "Xe đạp"
}


def get_track_key(track_id, vehicle_type, x, y, w, h):
    if track_id not in [None, -1, ""]:
        return f"{vehicle_type}_{track_id}"

    cx = x + w // 2
    cy = y + h // 2

    return f"{vehicle_type}_{cx // 35}_{cy // 35}"


def limit_cache():
    if len(violated_tracks) > 1200:
        violated_tracks.clear()

    if len(saved_violation_tracks) > 1200:
        saved_violation_tracks.clear()

    if len(plate_cache) > 800:
        plate_cache.pop(next(iter(plate_cache)))

    if len(best_plate_cache) > 800:
        best_plate_cache.pop(next(iter(best_plate_cache)))


def save_violation(
    cursor,
    frame_visual,
    x,
    y,
    w,
    h,
    plate,
    violation_type,
    video_id,
    vehicle_type
):
    os.makedirs("evidences", exist_ok=True)

    safe_plate = plate if plate != "Unknown" else "unknown"
    image_name = f"{int(time.time() * 1000)}_{safe_plate}.jpg"
    path = os.path.join("evidences", image_name)

    evidence = frame_visual.copy()

    cv2.rectangle(
        evidence,
        (x, y),
        (x + w, y + h),
        (0, 0, 255),
        3
    )

    cv2.putText(
        evidence,
        f"{violation_type} ({plate})",
        (x, max(30, y - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2
    )

    cv2.imwrite(path, evidence)

    vehicle_id = vehicle_map.get(vehicle_type)

    if vehicle_id:
        cursor.execute("""
            INSERT INTO violations
            (vehicle_id, type, time, video_id, plate, image, status)
            VALUES (%s, %s, NOW(), %s, %s, %s, %s)
        """, (
            vehicle_id,
            violation_type,
            video_id,
            plate,
            image_name,
            "pending"
        ))

    return image_name


@scan_bp.route("/api/scan", methods=["POST"])
def scan():
    conn = None
    cursor = None

    try:
        file = request.files.get("image")
        video_id = int(request.form.get("video_id", 1))
        mode = request.form.get("mode", "image")

        if not file:
            return jsonify({
                "success": False,
                "error": "No image"
            }), 400

        np_arr = np.frombuffer(file.read(), np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({
                "success": False,
                "error": "Decode failed"
            }), 400

        if mode == "video":
            traffic = detect_traffic_light(frame, video_id)
            red_light = traffic.get("red", False)
        else:
            traffic = {
                "light": "unknown",
                "red": False
            }
            red_light = False

        if mode == "video":
            detected = detect_vehicles(
                frame,
                mode="video",
                imgsz=640,
                conf=0.1
            ) or []
        else:
            detected = detect_vehicles(
                frame,
                mode="image",
                imgsz=1280,
                conf=0.4
            ) or []

        frame_visual = frame.copy()

        if mode == "video":
            draw_zones(frame_visual)
            draw_stop_line(
                frame_visual,
                red_light,
                video_id
            )

        if mode == "video":
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()
            conn.autocommit = True

        vehicles = []
        cfg = get_camera_config(video_id)

        for item in detected:
            plate = "Unknown"
            image_name = ""
            violations = []

            track_id = item.get("track_id", -1)
            plate_crop = item.get("plate_crop")
            box = item.get("vehicle_box") or item.get("box")

            if not box:
                continue

            if isinstance(box, dict):
                x = int(box["x"])
                y = int(box["y"])
                w = int(box["w"])
                h = int(box["h"])
            else:
                x, y, w, h = map(int, box)

            if w <= 0 or h <= 0:
                continue

            center_x = x + w // 2
            center_y = y + h // 2

            # Xe đi từ dưới lên: đầu xe là y trên cùng
            vehicle_check_y = y + h // 4

            vehicle_type = item.get("vehicle_type", "unknown")
            vehicle_vi = vehicle_name_vi.get(vehicle_type, vehicle_type)

            track_key = get_track_key(
                track_id,
                vehicle_type,
                x,
                y,
                w,
                h
            )

            # =========================
            # OCR + CACHE BIỂN SỐ
            # =========================
            ocr_plate = "Unknown"

            if (
                isinstance(plate_crop, np.ndarray)
                and plate_crop.size > 0
            ):

                try:
                    ocr_plate = read_plate_crop(plate_crop)

                except Exception as e:
                    print("OCR ERROR =", e)
                    ocr_plate = "Unknown"

                if ocr_plate != "Unknown":

                    plate = ocr_plate

                    plate_cache[track_key] = plate
                    best_plate_cache[track_key] = plate

                elif track_key in best_plate_cache:

                    plate = best_plate_cache[track_key]

                elif track_key in plate_cache:

                    plate = plate_cache[track_key]

            elif track_key in best_plate_cache:

                plate = best_plate_cache[track_key]

            elif track_key in plate_cache:

                plate = plate_cache[track_key]

            # =========================
            # IMAGE MODE: KHÔNG CHECK LỖI
            # =========================
            if mode == "image":
                vehicles.append({
                    "track_id": track_id,
                    "track_key": track_key,
                    "plate": plate,
                    "vehicle_type": vehicle_vi,
                    "violation": None,
                    "locked_violation": False,
                    "image": "",
                    "box": {
                        "x": x,
                        "y": y,
                        "w": w,
                        "h": h
                    },
                    "plate_box": item.get("plate_box"),
                    "camera_name": cfg.get("name", "Camera Trục Chính"),
                    "status": "unknown"
                })
                continue

            # =========================
            # CHECK SAI LÀN
            # =========================
            lane_violations = check_lane_violation(
                center_x,
                center_y,
                vehicle_type
            )

            if lane_violations:
                violations.extend(lane_violations)

            # =========================
            # CHECK VƯỢT ĐÈN ĐỎ
            # =========================
            is_red_violation = check_red_light_violation(
                track_key,
                vehicle_check_y,
                frame.shape[0],
                red_light,
                video_id
            )

            if is_red_violation:
                violations.append("Vượt đèn đỏ")

            violation_type = violations[0] if violations else None

            # =========================
            # GIỮ ĐỎ ĐẾN HẾT VIDEO
            # =========================
            if track_key in violated_tracks:
                violation_type = violated_tracks[track_key]

            elif violation_type:
                violated_tracks[track_key] = violation_type

            # =========================
            # LƯU DB 1 LẦN
            # =========================
            if violation_type and track_key not in saved_violation_tracks:
                image_name = save_violation(
                    cursor,
                    frame_visual,
                    x,
                    y,
                    w,
                    h,
                    plate,
                    violation_type,
                    video_id,
                    vehicle_type
                )

                saved_violation_tracks.add(track_key)

            limit_cache()

            vehicles.append({
                "track_id": track_id,
                "track_key": track_key,
                "plate": plate,
                "vehicle_type": vehicle_vi,
                "violation": violation_type,
                "locked_violation": True if violation_type else False,
                "image": image_name,
                "box": {
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h
                },
                "plate_box": item.get("plate_box"),
                "camera_name": cfg.get("name", "Camera Trục Chính"),
                "status": "pending" if violation_type else "unknown"
            })

        return jsonify({
            "success": True,
            "vehicles": vehicles,
            "red_light": red_light,
            "light": traffic.get("light", "unknown")
        })

    except Exception as e:
        print("SCAN ERROR =", str(e))

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()