from flask import Blueprint, request, jsonify

import os
import time
import base64
import cv2
import numpy as np
import mysql.connector

from api.services.detector_service import detect_vehicles
from api.services.ocr_service import detect_plate

from api.routes.lane_routes import (
    draw_zones,
    check_lane_violation
)

from api.routes.red_light_routes import (
    draw_stop_line,
    check_red_light_violation
)

scan_bp = Blueprint("scan", __name__)

# =========================
# DATABASE
# =========================

db_config = {
    "host": "127.0.0.1",
    "port": 3308,
    "user": "root",
    "password": "",
    "database": "traffic_db"
}

# =========================
# MAP
# =========================

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
    "person": "Ngừơi đi bộ"
}

# =========================
# API SCAN
# =========================

@scan_bp.route("/api/scan", methods=["POST"])
def scan():

    conn = None
    cursor = None

    try:

        data = request.json or {}

        video_id = data.get("video_id")
        if not video_id:
            return jsonify({
                "success": False,
                "error": "Missing video_id"
            })
            
        if "image" not in data:
            return jsonify({
                "success": False,
                "error": "No image"
            })

        # =========================
        # BASE64 -> FRAME
        # =========================

        image_data = data["image"].split(",")[1]

        image_bytes = base64.b64decode(image_data)

        np_arr = np.frombuffer(image_bytes, np.uint8)

        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({
                "success": False,
                "error": "Frame decode failed"
            })

        # =========================
        # DRAW ZONES
        # =========================

        draw_zones(frame)
        draw_stop_line(frame)

        # =========================
        # DETECT VEHICLES
        # =========================

        try:
            detected = detect_vehicles(frame)
            print("DETECTED:", len(detected))
        except Exception as e:
            print("DETECT ERROR:", e)
            detected = []

        vehicles = []

        # =========================
        # DB CONNECT
        # =========================

        conn = mysql.connector.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()

        # =========================
        # LOOP
        # =========================

        for item in detected:

            try:

                # ================= OCR =================
                plate = detect_plate(item["plate_crop"])

                # ================= BOX =================
                box = item["vehicle_box"]

                x, y, w, h = box["x"], box["y"], box["w"], box["h"]

                center_x = x + w // 2
                center_y = y + h // 2

                # ================= TYPE =================
                vehicle_type_en = item["vehicle_type"]
                vehicle_type_vi = vehicle_name_vi.get(vehicle_type_en, vehicle_type_en)

                # ================= VIOLATION CHECK =================
                red_light_violation = check_red_light_violation(center_y, red_light=True)

                violations = check_lane_violation(
                    center_x,
                    center_y,
                    vehicle_type_en,   # ❗ PHẢI EN
                    red_light=True
                )

                if red_light_violation:
                    violations.append("Vượt đèn đỏ")

                violation_type = violations[0] if violations else None

                image_name = ""

                # ================= SAVE =================
                if violation_type:

                    save_dir = "evidences"
                    os.makedirs(save_dir, exist_ok=True)

                    image_name = f"{int(time.time()*1000)}.jpg"
                    filepath = os.path.join(save_dir, image_name)

                    frame_copy = frame.copy()

                    # BOX
                    cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (0, 255, 0), 3)

                    # TEXT
                    cv2.putText(
                        frame_copy,
                        violation_type,
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 0, 255),
                        2
                    )

                    # PLATE BOX
                    if "plate_box" in item:
                        p = item["plate_box"]

                        cv2.rectangle(
                            frame_copy,
                            (p["x"], p["y"]),
                            (p["x"] + p["w"], p["y"] + p["h"]),
                            (0, 0, 255),
                            3
                        )

                        cv2.putText(
                            frame_copy,
                            plate,
                            (p["x"], p["y"] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.9,
                            (0, 255, 255),
                            2
                        )

                    cv2.imwrite(filepath, frame_copy)

                    # ================= VEHICLE ID =================
                    vehicle_id = vehicle_map.get(vehicle_type_en)

                    if vehicle_id is None:
                        continue  # ❗ tránh FK lỗi

                    # ================= INSERT DB =================
                    cursor.execute(
                        """
                        INSERT INTO violations
                        (vehicle_id, type, time, video_id, plate, image, status)
                        VALUES (%s, %s, NOW(), %s, %s, %s, %s)
                        """,
                        (
                            vehicle_id,
                            violation_type,
                            video_id,
                            plate,
                            image_name,
                            "pending"
                        )
                    )

                # ================= RETURN =================
                vehicles.append({
                    "plate": plate,
                    "vehicle_type": vehicle_type_vi,
                    "violation": violation_type,
                    "image": image_name,
                    "box": item["vehicle_box"],
                    "plate_box": item.get("plate_box")
                })

            except Exception as e:
                print("ITEM ERROR:", e)

        return jsonify({
            "success": True,
            "vehicles": vehicles
        })

    except Exception as e:
        print("SCAN ERROR:", e)
        return jsonify({
            "success": False,
            "error": str(e)
        })

    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except:
            pass