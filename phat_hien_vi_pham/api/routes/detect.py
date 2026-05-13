from flask import Blueprint, request, jsonify
import cv2
import numpy as np
from ultralytics import YOLO
import easyocr

detect_bp = Blueprint("detect", __name__)

model = YOLO("yolov8n.pt")   # hoặc model biển số của bạn
reader = easyocr.Reader(['en'])

@detect_bp.route("/detect", methods=["POST"])
def detect():

    file = request.files["frame"]
    img_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)

    results = model(img)[0]

    detections = []

    for box in results.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cls = int(box.cls[0])

        label = model.names[cls]

        if label in ["car", "motorcycle", "truck"]:

            crop = img[y1:y2, x1:x2]

            # OCR biển số (demo đơn giản)
            ocr_result = reader.readtext(crop)

            plate_text = ""
            if ocr_result:
                plate_text = ocr_result[0][1]

            detections.append({
                "type": label,
                "bbox": [x1, y1, x2, y2],
                "plate": plate_text
            })

    return jsonify(detections)