import easyocr
import cv2
import re
import numpy as np
from ultralytics import YOLO

# Khởi tạo
plate_model = YOLO("AI_models/license_plate_detector.pt")
reader = easyocr.Reader(['en'], gpu=False)

def clean_plate(text):
    if not text: return ""
    return re.sub(r'[^A-Z0-9]', '', text.upper())

def preprocess_image(img):
    if img is None or img.size == 0: return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Làm sắc nét chữ
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    gray = cv2.filter2D(gray, -1, kernel)
    
    # Cân bằng sáng
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    # Tăng cường độ tương phản (Binarization)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def detect_plate(frame):
    try:
        if frame is None: return "Unknown"

        results = plate_model.predict(frame, conf=0.4, verbose=False)
        if not results[0].boxes: return "Unknown"

        best_box = max(results[0].boxes, key=lambda b: float(b.conf[0]))
        x1, y1, x2, y2 = map(int, best_box.xyxy[0])

        # CẢI TIẾN 1: Thu nhỏ box một chút (thay vì -5 thì để nguyên hoặc +2)
        # Điều này giúp tránh lấy phải mép nhựa biển số có chữ lạ
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = max(0, x1+2), max(0, y1+2), min(w, x2-2), min(h, y2-2)
        plate_crop = frame[y1:y2, x1:x2]
        
        processed = preprocess_image(plate_crop)
        h_crop, w_crop = processed.shape

        # CẢI TIẾN 2: Chia dòng và TẬP TRUNG vào trung tâm của mỗi dòng
        # (Bỏ qua 10% chiều rộng mỗi bên để tránh logo ở rìa)
        w_margin = int(w_crop * 0.1)
        mid = h_crop // 2
        
        top_img = processed[0:mid, w_margin:w_crop-w_margin]
        bot_img = processed[mid:h_crop, w_margin:w_crop-w_margin]

        allowed = '0123456789ABCDEFHKLMNPRSTUVXYZ'
        top_res = reader.readtext(top_img, detail=0, allowlist=allowed)
        bot_res = reader.readtext(bot_img, detail=0, allowlist=allowed)

        line1 = clean_plate("".join(top_res))
        line2 = clean_plate("".join(bot_res))
        
        # CẢI TIẾN 3: Sử dụng Regex để ép buộc định dạng
        # Biển xe máy 2 dòng thường: Dòng 1 (2-4 ký tự), Dòng 2 (4-5 ký tự)
        full_plate = f"{line1}{line2}"
        
        # Kiểm tra nếu có MDCRDR thì cắt bỏ phần đầu (nếu nó xuất hiện)
        if full_plate.startswith("MDCRDR"):
            full_plate = full_plate.replace("MDCRDR", "")
            
        if 7 <= len(full_plate) <= 10:
            return full_plate
        
        return "Unknown"

    except Exception as e:
        print("OCR ERROR:", e)
        return "Unknown"