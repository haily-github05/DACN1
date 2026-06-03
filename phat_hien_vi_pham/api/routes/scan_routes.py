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
from api.services.red_light_service import draw_stop_line, check_red_light_violation
from api.services.red_light_service import get_camera_config

scan_bp = Blueprint("scan", __name__)

plate_cache = {}

# =========================
# DB CONFIG
# =========================
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


# =========================
# MAIN API
# =========================
@scan_bp.route("/api/scan", methods=["POST"])
def scan():

    conn = None
    cursor = None

    try:
        file = request.files.get("image")
        video_id = int(request.form.get("video_id", 1))
        mode = request.form.get("mode", "image")

        if not file:
            return jsonify({"success": False, "error": "No image"}), 400

        np_arr = np.frombuffer(file.read(), np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"success": False, "error": "Decode failed"}), 400

        # =========================
        # TRAFFIC LIGHT
        # =========================
        traffic = detect_traffic_light(frame, video_id)

        red_light = traffic["red"]
        light_box = traffic["box"]

        # =========================
        # VEHICLES
        # =========================
        detected = detect_vehicles(frame, mode=mode, imgsz=640, conf=0.4) or []

        frame_visual = frame.copy()

        draw_zones(frame_visual)
        draw_stop_line(frame_visual, red_light, video_id)

        # =========================
        # DRAW TRAFFIC LIGHT
        # =========================
        if isinstance(light_box, dict):
            lx, ly, lw, lh = light_box["x"], light_box["y"], light_box["w"], light_box["h"]
        else:
            lx = ly = lw = lh = 0

        # =========================
        # DB CONNECT
        # =========================
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        conn.autocommit = True

        vehicles = []

        # =========================
        # PROCESS VEHICLES
        # =========================
        for item in detected:

            plate = "Unknown"
            track_id = item.get("track_id")

            is_static = track_id in [None, -1, ""]

            plate_crop = item.get("plate_crop")

            # =========================
            # OCR
            # =========================
            if isinstance(plate_crop, np.ndarray) and plate_crop.size > 0:

                if is_static:
                    res = detect_plate(plate_crop)
                    if res != "Unknown":
                        plate = res
                else:
                    if track_id in plate_cache:
                        plate = plate_cache[track_id]
                    else:
                        res = detect_plate(plate_crop)
                        if res != "Unknown":
                            plate = res
                            plate_cache[track_id] = plate

                        if len(plate_cache) > 300:
                            plate_cache.pop(next(iter(plate_cache)))

            # =========================
            # BOX SAFE
            # =========================
            box = item.get("vehicle_box")

            if isinstance(box, dict):
                x, y, w, h = box["x"], box["y"], box["w"], box["h"]
            else:
                x, y, w, h = box

            center_y = y + h // 2
            bottom = y + h

            vehicle_type = item["vehicle_type"]
            vehicle_vi = vehicle_name_vi.get(vehicle_type, vehicle_type)

            # =========================
            # VIOLATION
            # =========================
            violations = []
            violations.extend(check_lane_violation(x + w // 2, center_y, vehicle_type))

            cfg = get_camera_config(video_id)
            stop_y = int(frame.shape[0] * cfg.get("stop_line_ratio", 0.5))

            if is_static and red_light and bottom > stop_y:
                violations.append("Vượt đèn đỏ")

            violation_type = violations[0] if violations else None

            image_name = ""

            # =========================
            # SAVE
            # =========================
            if violation_type:

                os.makedirs("evidences", exist_ok=True)

                image_name = f"{int(time.time()*1000)}_{plate}.jpg"
                path = os.path.join("evidences", image_name)

                evidence = frame_visual.copy()

                cv2.rectangle(evidence, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(evidence, f"{violation_type} ({plate})",
                            (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

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

            vehicles.append({
                "track_id": track_id,
                "plate": plate,
                "vehicle_type": vehicle_vi,
                "violation": violation_type,
                "image": image_name,
                "box": {"x": x, "y": y, "w": w, "h": h},
                "plate_box": item.get("plate_box"),
                "camera_name": "Camera Trục Chính",
                "status": "pending"
            })

        return jsonify({
            "success": True,
            "vehicles": vehicles,
            "red_light": red_light,
            "light": traffic["light"]
        })

    except Exception as e:
        print("SCAN ERROR =", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()