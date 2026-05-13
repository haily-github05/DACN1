# import base64
# import cv2
# import numpy as np
# from ultralytics import YOLO
# import easyocr
# import os
# from datetime import datetime

# from api.models.violations import ViolationModel

# # =========================
# # DATABASE
# # =========================
# db_config = {
#     "host": "localhost",
#     "user": "root",
#     "password": "",
#     "database": "traffic_db"
# }

# violation_model = ViolationModel(
#     db_config
# )

# # =========================
# # LOAD AI
# # =========================
# vehicle_model = YOLO(
#     "AI_models/yolov8n.pt"
# )

# plate_model = YOLO(
#     "AI_models/license_plate_detector.pt"
# )

# reader = easyocr.Reader(
#     ['en'],
#     gpu=False
# )

# # =========================
# # CONFIG
# # =========================
# LINE_Y_RATIO = 0.7

# # car, motorcycle, bus, truck
# VEHICLE_CLASSES = [2, 3, 5, 7]

# # =========================
# # READ PLATE
# # =========================
# def read_plate(plate_crop):

#     try:

#         if plate_crop.size == 0:
#             return "Unknown"

#         plate_crop = cv2.resize(
#             plate_crop,
#             None,
#             fx=2,
#             fy=2
#         )

#         results = reader.readtext(
#             plate_crop
#         )

#         if len(results) > 0:

#             return results[0][1]

#         return "Unknown"

#     except:

#         return "Unknown"

# # =========================
# # CHECK VIOLATION
# # =========================
# def is_violation(center_y, line_y):

#     return center_y > line_y

# # =========================
# # SAVE IMAGE
# # =========================
# def save_evidence(frame):

#     folder = "evidences"

#     os.makedirs(
#         folder,
#         exist_ok=True
#     )

#     filename = (
#         datetime.now().strftime(
#             "%Y%m%d_%H%M%S"
#         ) + ".jpg"
#     )

#     path = os.path.join(
#         folder,
#         filename
#     )

#     cv2.imwrite(path, frame)

#     return filename

# # =========================
# # MAIN PROCESS
# # =========================
# def process_frame(base64_image):

#     image_data = base64_image.split(",")[1]

#     image_bytes = base64.b64decode(
#         image_data
#     )

#     np_arr = np.frombuffer(
#         image_bytes,
#         np.uint8
#     )

#     frame = cv2.imdecode(
#         np_arr,
#         cv2.IMREAD_COLOR
#     )

#     line_y = int(
#         frame.shape[0] * LINE_Y_RATIO
#     )

#     results = vehicle_model(frame)

#     detections = []

#     vehicle_id = 1

#     for result in results:

#         for box in result.boxes:

#             conf = float(box.conf[0])

#             cls = int(box.cls[0])

#             if conf < 0.5:
#                 continue

#             if cls not in VEHICLE_CLASSES:
#                 continue

#             x1, y1, x2, y2 = map(
#                 int,
#                 box.xyxy[0]
#             )

#             vehicle_crop = frame[
#                 y1:y2,
#                 x1:x2
#             ]

#             plate_text = "Unknown"

#             # =========================
#             # DETECT PLATE
#             # =========================
#             plate_results = plate_model(
#                 vehicle_crop
#             )

#             for r in plate_results:

#                 for pbox in r.boxes:

#                     px1, py1, px2, py2 = map(
#                         int,
#                         pbox.xyxy[0]
#                     )

#                     plate_crop = vehicle_crop[
#                         py1:py2,
#                         px1:px2
#                     ]

#                     plate_text = read_plate(
#                         plate_crop
#                     )

#             center_y = (y1 + y2) // 2

#             violation = is_violation(
#                 center_y,
#                 line_y
#             )

#             evidence_image = None

#             # =========================
#             # SAVE VIOLATION
#             # =========================
#             if violation:

#                 evidence_image = save_evidence(
#                     frame
#                 )

#                 violation_model.log_violation(
#                     vehicle_id=vehicle_id,
#                     plate=plate_text,
#                     v_type="Vượt vạch",
#                     camera="Camera 01",
#                     image_path=evidence_image,
#                     status="NEW"
#                 )

#             detections.append({
#                 "bbox": [x1, y1, x2, y2],
#                 "plate": plate_text,
#                 "violation": violation,
#                 "confidence": round(conf, 2)
#             })

#             vehicle_id += 1

#     return {
#         "status": "success",
#         "detections": detections
#     }