import cv2
import easyocr
from ultralytics import YOLO

class LicensePlateDetector:
    # model_path ở đây PHẢI là file .pt (não bộ AI)
    # KHÔNG ĐƯỢC trỏ vào chính file .py này
    def __init__(self, model_path="models/license_plate_detector.pt"): 
        # Nạp trọng số mô hình từ file .pt
        self.plate_model = YOLO(model_path)
        
        # Khởi tạo bộ đọc chữ
        self.reader = easyocr.Reader(['en'], gpu=False) 

    def detect_and_read(self, vehicle_img):
        plate_text = "UNKNOWN"
        # Dự đoán vị trí biển số bằng model đã nạp
        results = self.plate_model(vehicle_img, verbose=False)
        
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                plate_crop = vehicle_img[y1:y2, x1:x2]
                
                if plate_crop.size > 0:
                    # Tiền xử lý ảnh xám để OCR tốt hơn
                    gray_plate = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
                    ocr_res = self.reader.readtext(gray_plate)
                    if ocr_res:
                        # Xử lý chuỗi kết quả
                        plate_text = ocr_res[0][-2].upper().replace(" ", "").replace(".", "")
                        return plate_text 
        return plate_text