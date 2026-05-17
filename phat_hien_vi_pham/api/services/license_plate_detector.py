import cv2
import easyocr
from ultralytics import YOLO

class LicensePlateDetector:
    # model_path ở đây PHẢI trỏ đến file .pt (ví dụ: yolov8n.pt)
    def __init__(self, model_path="yolo11s.pt"): 
        # 1. Khởi tạo model YOLO (Nạp file nặng, chứa dữ liệu AI)
        self.plate_model = YOLO(model_path)
        
        # 2. Khởi tạo bộ đọc chữ EasyOCR
        self.reader = easyocr.Reader(['en'], gpu=False) 

    def detect_and_read(self, vehicle_img):
        plate_text = "UNKNOWN"
        
        # Bước 1: Dự đoán vị trí biển số
        results = self.plate_model(vehicle_img, verbose=False)
        
        for result in results:
            for box in result.boxes:
                px1, py1, px2, py2 = map(int, box.xyxy[0])
                plate_crop = vehicle_img[py1:py2, px1:px2]
                
                if plate_crop.size > 0:
                    gray_plate = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
                    ocr_res = self.reader.readtext(gray_plate)
                    if ocr_res:
                        plate_text = ocr_res[0][-2].upper().replace(" ", "").replace(".", "")
                        return plate_text 
                        
        return plate_text