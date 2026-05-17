
from flask import Blueprint, request, jsonify

import cv2
import base64
import numpy as np

from ultralytics import YOLO
import easyocr

# =========================
# BLUEPRINT
# =========================

camera_bp = Blueprint(
    "camera",
    __name__
)

# =========================
# LOAD MODEL
# =========================

model = YOLO("yolo11s.pt")

reader = easyocr.Reader(
    ['en'],
    gpu=False
)

# =========================
# API SCAN
# =========================

@camera_bp.route(
    "/api/scan",
    methods=["POST"]
)
def scan_vehicle():

    try:

        data = request.json

        image_data = data["image"]

        # remove base64 header
        image_data = image_data.split(",")[1]

        image_bytes = base64.b64decode(
            image_data
        )

        np_arr = np.frombuffer(
            image_bytes,
            np.uint8
        )

        frame = cv2.imdecode(
            np_arr,
            cv2.IMREAD_COLOR
        )

        results = vehicle_model(frame)

        vehicles = []

        for r in results:

            for box in r.boxes:

                cls = int(box.cls[0])

                conf = float(box.conf[0])

                # car motorcycle bus truck
                if cls in [2, 3, 5, 7] and conf > 0.4:

                    x1, y1, x2, y2 = map(
                        int,
                        box.xyxy[0]
                    )

                    crop = frame[
                        y1:y2,
                        x1:x2
                    ]

                    # OCR
                    text = reader.readtext(crop)

                    plate = "UNKNOWN"

                    if len(text) > 0:

                        plate = text[0][1]

                    vehicles.append({

                        "plate": plate,

                        "box": {
                            "x": x1,
                            "y": y1,
                            "w": x2 - x1,
                            "h": y2 - y1
                        }
                    })

        return jsonify({
            "success": True,
            "vehicles": vehicles
        })

    except Exception as e:

        print("AI ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        })
