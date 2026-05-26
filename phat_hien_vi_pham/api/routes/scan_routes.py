# from flask import Blueprint, request, jsonify
# import os
# import time
# import cv2
# import numpy as np
# import mysql.connector

# from api.services.detector_service import detect_vehicles
# from api.services.ocr_service import detect_plate
# from api.services.traffic_light_service import detect_traffic_light
# from api.services.lane_service import LaneService
# from api.routes.red_light_routes import (draw_stop_line, check_red_light_violation)

# lane_service = LaneService("AI_models/lane_detection_best.pt")
# scan_bp = Blueprint("scan", __name__)

# plate_cache = {}

# db_config = {
#     "host": "127.0.0.1",
#     "port": 3308,
#     "user": "root",
#     "password": "",
#     "database": "traffic_db"
# }

# vehicle_map = {"motorcycle": 1, "car": 2, "bus": 3, "truck": 4, "person": 5}
# vehicle_name_vi = {"motorcycle": "Xe máy", "car": "Ô tô", "bus": "Xe buýt", "truck": "Xe tải", "person": "Người đi bộ"}

# @scan_bp.route("/api/scan", methods=["POST"])
# def scan():
#     conn = None
#     cursor = None
#     try:
#         file = request.files.get("image")
#         video_id = request.form.get("video_id", 1)

#         if not file:
#             return jsonify({"success": False, "error": "No image"}), 400

#         np_arr = np.frombuffer(file.read(), np.uint8)
#         frame_raw = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

#         if frame_raw is None:
#             return jsonify({"success": False, "error": "Decode failed"}), 400

#         # Nhận diện đèn & Lane
#         traffic_light = detect_traffic_light(frame_raw) or {"red": False, "box": None}
#         red_light, light_box = traffic_light["red"], traffic_light["box"]
        
#         detected = detect_vehicles(frame_raw) or []
#         lane_polygons = lane_service.get_lane_polygons(frame_raw)

#         # KHỞI TẠO FRAME VISUAL
#         frame_visual = frame_raw.copy()
#         draw_stop_line(frame_visual, red_light)
#         lane_service.draw_lanes(frame_visual, lane_polygons)

#         if light_box:
#             lx, ly, lw, lh = light_box["x"], light_box["y"], light_box["w"], light_box["h"]
#             cv2.rectangle(frame_visual, (lx, ly), (lx + lw, ly + lh), (0, 0, 255) if red_light else (0, 255, 0), 2)

#         conn = mysql.connector.connect(**db_config)
#         cursor = conn.cursor()
#         conn.autocommit = True

#         vehicles = []

#         for item in detected:
#             plate = "Unknown"
#             track_id = item.get("track_id")
#             is_static_image = (track_id is None or track_id == -1 or str(track_id).strip() == "")

#             plate_crop = item.get("plate_crop")
#             if plate_crop is not None and isinstance(plate_crop, np.ndarray) and plate_crop.size > 0:
#                 if is_static_image:
#                     ocr_res = detect_plate(plate_crop)
#                     if ocr_res and ocr_res != "Unknown": plate = ocr_res
#                 else:
#                     track_id = int(track_id)
#                     if track_id in plate_cache:
#                         plate = plate_cache[track_id]
#                     else:
#                         ocr_res = detect_plate(plate_crop)
#                         if ocr_res and ocr_res != "Unknown": plate = ocr_res
#                         plate_cache[track_id] = plate
#                         if len(plate_cache) > 300: plate_cache.pop(next(iter(plate_cache)))
            
#             if is_static_image: track_id = int(time.time() * 1000) + len(vehicles)

#             box = item["vehicle_box"]
#             x, y, w, h = box["x"], box["y"], box["w"], box["h"]
#             center_y = y + h // 2
            
#             # Logic vi phạm
#             violations = []
#             lane_id = lane_service.check_lane_id((x + w // 2, center_y), lane_polygons)
#             if lane_id == -1 and item["vehicle_type"] in ["motorcycle", "car", "bus", "truck"]:
#                 violations.append("Sai làn đường")

#             if is_static_image:
#                 if red_light and center_y > int(frame_raw.shape[0] * 0.68): violations.append("Vượt đèn đỏ")
#             else:
#                 if check_red_light_violation(track_id, center_y, red_light): violations.append("Vượt đèn đỏ")

#             violation_type = violations[0] if violations else None
            
#             if violation_type:
#                 os.makedirs("evidences", exist_ok=True)
#                 image_name = f"{int(time.time()*1000)}_{plate}.jpg"
#                 path = os.path.join("evidences", image_name)
#                 evidence = frame_visual.copy()
#                 cv2.rectangle(evidence, (x, y), (x + w, y + h), (0, 0, 255), 2)
#                 cv2.putText(evidence, f"{violation_type} ({plate})", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
#                 cv2.imwrite(path, evidence)
                
#                 vehicle_id = vehicle_map.get(item["vehicle_type"])
#                 if vehicle_id:
#                     cursor.execute("INSERT INTO violations (vehicle_id, type, time, video_id, plate, image, status) VALUES (%s, %s, NOW(), %s, %s, %s, 'pending')", 
#                                    (vehicle_id, violation_type, video_id, plate, image_name))

#             vehicles.append({
#                 "track_id": track_id, "plate": plate, "vehicle_type": vehicle_name_vi.get(item["vehicle_type"], item["vehicle_type"]),
#                 "lane_id": int(lane_id), "violation": violation_type, "box": {"x": x, "y": y, "w": w, "h": h}
#             })

#         return jsonify({"success": True, "vehicles": vehicles, "red_light": red_light})

#     except Exception as e:
#         print("SCAN ERROR =", str(e))
#         return jsonify({"success": False, "error": str(e)}), 500
#     finally:
#         if cursor: cursor.close()
#         if conn: conn.close()
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

# =========================
# CACHE (video tracking)
# =========================
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

        # =========================
        # TRAFFIC LIGHT
        # =========================
        traffic_light = detect_traffic_light(frame_raw) or {
            "red": False,
            "box": None
        }

        red_light = traffic_light["red"]
        light_box = traffic_light["box"]

        # =========================
        # VEHICLE DETECTION
        # =========================
        detected = detect_vehicles(frame_raw) or []

        # =========================
        # DRAW FRAME
        # =========================
        frame_visual = frame_raw.copy()

        draw_zones(frame_visual)
        draw_stop_line(frame_visual, red_light)

        if light_box:
            lx, ly, lw, lh = (
                light_box["x"],
                light_box["y"],
                light_box["w"],
                light_box["h"]
            )

            cv2.rectangle(
                frame_visual,
                (lx, ly),
                (lx + lw, ly + lh),
                (0, 0, 255) if red_light else (0, 255, 0),
                2
            )

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

            is_static_image = (
                track_id is None
                or track_id == -1
                or str(track_id).strip() == ""
            )

            # =========================
            # PLATE OCR
            # =========================
            plate_crop = item.get("plate_crop")

            if plate_crop is not None and isinstance(plate_crop, np.ndarray) and plate_crop.size > 0:

                if is_static_image:
                    ocr_res = detect_plate(plate_crop)
                    if ocr_res and ocr_res != "Unknown":
                        plate = ocr_res

                else:
                    track_id = int(track_id)

                    if track_id in plate_cache:
                        plate = plate_cache[track_id]
                    else:
                        ocr_res = detect_plate(plate_crop)

                        if ocr_res and ocr_res != "Unknown":
                            plate = ocr_res

                        plate_cache[track_id] = plate

                        if len(plate_cache) > 300:
                            plate_cache.pop(next(iter(plate_cache)))
            else:
                plate = "Unknown"

            if is_static_image:
                track_id = int(time.time() * 1000) + len(vehicles)

            # =========================
            # VEHICLE BOX
            # =========================
            box = item["vehicle_box"]
            x, y, w, h = box["x"], box["y"], box["w"], box["h"]

            center_y = y + h // 2

            vehicle_type_en = item["vehicle_type"]
            vehicle_type_vi = vehicle_name_vi.get(vehicle_type_en, vehicle_type_en)

            # =========================
            # VIOLATIONS
            # =========================
            violations = []

            violations.extend(
                check_lane_violation(x + w // 2, center_y, vehicle_type_en)
            )

            if is_static_image:
                if red_light and center_y > int(frame_raw.shape[0] * 0.68):
                    violations.append("Vượt đèn đỏ")
            else:
                if check_red_light_violation(track_id, center_y, red_light):
                    violations.append("Vượt đèn đỏ")

            violation_type = violations[0] if violations else None
            image_name = ""

            # =========================
            # SAVE EVIDENCE
            # =========================
            if violation_type:
                os.makedirs("evidences", exist_ok=True)

                image_name = f"{int(time.time()*1000)}_{plate}.jpg"
                path = os.path.join("evidences", image_name)

                evidence = frame_visual.copy()

                cv2.rectangle(evidence, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(
                    evidence,
                    f"{violation_type} ({plate})",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )

                cv2.imwrite(path, evidence)

                vehicle_id = vehicle_map.get(vehicle_type_en)

                if vehicle_id:
                    cursor.execute("""
                        INSERT INTO violations (vehicle_id, type, time, video_id, plate, image, status)
                        VALUES (%s, %s, NOW(), %s, %s, %s, %s)
                    """, (
                        vehicle_id,
                        violation_type,
                        video_id,
                        plate,
                        image_name,
                        "pending"
                    ))

            # =========================
            # RESPONSE
            # =========================
            vehicles.append({
                "track_id": track_id,
                "plate": plate,
                "vehicle_type": vehicle_type_vi,
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
            "stop_line": {"y": int(frame_raw.shape[0] * 0.68)}
        })

    except Exception as e:
        print("SCAN ERROR =", str(e))
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()