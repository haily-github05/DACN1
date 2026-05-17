from flask import Blueprint, request, jsonify
import os
import time
import cv2
import numpy as np
import mysql.connector

from api.services.detector_service import detect_vehicles
from api.services.ocr_service import detect_plate
from api.services.traffic_light_service import detect_traffic_light

from api.routes.lane_routes import draw_zones, check_lane_violation
from api.routes.red_light_routes import (
    draw_stop_line,
    check_red_light_violation
)

scan_bp = Blueprint("scan", __name__)

plate_cache = {}

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
    "person": 5
}

vehicle_name_vi = {
    "motorcycle": "Xe máy",
    "car": "Ô tô",
    "bus": "Xe buýt",
    "truck": "Xe tải",
    "person": "Người đi bộ"
}

@scan_bp.route("/api/scan", methods=["POST"])
def scan():

    conn = None
    cursor = None

    try:

        file = request.files.get("image")
        video_id = request.form.get("video_id", 1)

        if not file:
            return jsonify({"success": False, "error": "No image"}), 400

        np_arr = np.frombuffer(file.read(), np.uint8)
        frame_raw = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame_raw is None:
            return jsonify({"success": False, "error": "Decode failed"}), 400

        # ================= TRAFFIC LIGHT =================
        traffic_light = detect_traffic_light(frame_raw) or {"red": False, "box": None}

        red_light = traffic_light["red"]
        light_box = traffic_light["box"]

        # ================= VEHICLES =================
        detected = detect_vehicles(frame_raw) or []

        # ================= DRAW =================
        frame_visual = frame_raw.copy()

        draw_zones(frame_visual)
        draw_stop_line(frame_visual, red_light)

        # vẽ đèn
        if light_box:
            lx = light_box["x"]
            ly = light_box["y"]
            lw = light_box["w"]
            lh = light_box["h"]

            color = (0, 0, 255) if red_light else (0, 255, 0)

            cv2.rectangle(
                frame_visual,
                (lx, ly),
                (lx + lw, ly + lh),
                color,
                2
            )

        # ================= DB =================
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        conn.autocommit = True

        vehicles = []

        for item in detected:

            track_id = item.get("track_id", -1)

            # OCR cache
            if track_id in plate_cache:
                plate = plate_cache[track_id]
            else:
                plate_crop = item.get("plate_crop")

                if plate_crop is not None:
                    plate = detect_plate(plate_crop)
                else:
                    plate = "UNKNOWN"

                plate_cache[track_id] = plate

                if len(plate_cache) > 300:
                    plate_cache.pop(next(iter(plate_cache)))

            # box
            box = item["vehicle_box"]
            x, y, w, h = box["x"], box["y"], box["w"], box["h"]

            center_y = y + h // 2

            vehicle_type_en = item["vehicle_type"]
            vehicle_type_vi = vehicle_name_vi.get(vehicle_type_en, vehicle_type_en)

            # ================= VIOLATIONS =================
            violations = []

            violations.extend(
                check_lane_violation(
                    x + w // 2,
                    center_y,
                    vehicle_type_en
                )
            )

            if check_red_light_violation(track_id, center_y, red_light):
                violations.append("Vượt đèn đỏ")

            violation_type = violations[0] if violations else None

            image_name = ""

            # ================= SAVE =================
            if violation_type:

                os.makedirs("evidences", exist_ok=True)

                image_name = f"{int(time.time()*1000)}_{plate}.jpg"

                path = os.path.join("evidences", image_name)

                evidence = frame_visual.copy()

                cv2.rectangle(
                    evidence,
                    (x, y),
                    (x + w, y + h),
                    (0, 0, 255),
                    2
                )

                cv2.putText(
                    evidence,
                    violation_type,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )

                cv2.imwrite(path, evidence)

                vehicle_id = vehicle_map.get(vehicle_type_en)

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

            vehicles.append({
                "track_id": track_id,
                "plate": plate,
                "vehicle_type": vehicle_type_vi,
                "violation": violation_type,
                "image": image_name,
                "box": box,
                "camera_name": "Camera Trục Chính",
                "status": "pending"
            })

        # Tìm dòng này ở gần cuối hàm scan() trong file của bạn và cập nhật:
        return jsonify({
            "success": True,
            "vehicles": vehicles,
            "red_light": red_light,              # <<< THÊM DÒNG NÀY để truyền trạng thái đèn về FE
            "stop_line": {"y": 490}              # <<< THÊM DÒNG NÀY để đồng bộ vạch vẽ trên FE
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()