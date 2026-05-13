import easyocr
import cv2
import re
import numpy as np

# Khởi tạo Reader một lần duy nhất để tối ưu bộ nhớ
reader = easyocr.Reader(['en'], gpu=False)

def clean_plate(text):
    """
    Làm sạch chuỗi ký tự và chuẩn hóa định dạng biển số.
    """
    if not text:
        return ""
    
    # Chuyển thành chữ hoa và lọc bỏ mọi ký tự đặc biệt
    text = re.sub(r'[^A-Z0-9]', '', text.upper())

    # Sửa các lỗi nhầm lẫn ký tự phổ biến của OCR
    # Lưu ý: Bạn có thể mở rộng danh sách này dựa trên thực tế quét sai
    replacements = {
        "O": "0",
        "I": "1",
        "Z": "2",
        "S": "5",
        "B": "8",
        "G": "6",
        "D": "0"
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)

    return text

def preprocess_image(img):
    """
    Các bước tiền xử lý ảnh chuyên sâu để tăng độ nét cho chữ.
    """
    # 1. Chuyển xám
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Phóng to ảnh x3 lần với độ sắc nét cao
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

    # 3. Cân bằng ánh sáng (CLAHE) - xử lý vùng chói/tối
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # 4. Khử nhiễu nhưng giữ cạnh chữ (Bilateral Filter)
    gray = cv2.bilateralFilter(gray, 11, 17, 17)
    
    # 5. Nhị phân hóa thích nghi (Adaptive Thresholding)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    return thresh

def detect_plate(plate_crop):
    """
    Hàm chính: Nhận diện biển số (Hỗ trợ cả biển dài và biển vuông).
    """
    try:
        if plate_crop is None or plate_crop.size == 0:
            return "UNKNOWN"

        # Tiền xử lý ảnh crop từ YOLO
        processed_img = preprocess_image(plate_crop)
        h, w = processed_img.shape

        # KIỂM TRA LOẠI BIỂN SỐ (Dài hay Vuông)
        # Tỷ lệ Width/Height của biển dài VN ~ 4.0, biển vuông ~ 1.2
        ratio = w / h
        
        results = []
        
        if ratio < 2.0:  
            # TRƯỜNG HỢP BIỂN VUÔNG (2 dòng)
            # Cắt đôi ảnh theo chiều ngang để đọc dòng trên và dòng dưới riêng biệt
            mid = h // 2
            top_part = processed_img[0:mid, 0:w]
            bottom_part = processed_img[mid:h, 0:w]
            
            # Đọc dòng trên
            res_top = reader.readtext(top_part, detail=0)
            # Đọc dòng dưới
            res_bottom = reader.readtext(bottom_part, detail=0)
            
            combined_text = "".join(res_top) + "".join(res_bottom)
            if combined_text:
                return clean_plate(combined_text)

        # TRƯỜNG HỢP BIỂN DÀI (hoặc dự phòng cho biển vuông)
        results = reader.readtext(
            processed_img, 
            detail=1, 
            paragraph=False,
            allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        )

        if not results:
            return "UNKNOWN"

        # Lấy kết quả có độ tự tin (confidence score) cao nhất
        best_text = ""
        max_score = 0
        for r in results:
            text = clean_plate(r[1])
            score = r[2]
            if len(text) >= 5 and score > max_score:
                best_text = text
                max_score = score

        return best_text if best_text else "UNKNOWN"

    except Exception as e:
        print(f"OCR ERROR: {e}")
        return "UNKNOWN"