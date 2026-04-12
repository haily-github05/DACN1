import cv2
import pandas as pd
from datetime import datetime
import os

# Tạo thư mục lưu trữ nếu chưa có
if not os.path.exists('outputs/violations'):
    os.makedirs('outputs/violations')

def is_crossing_line(point, line_y):
    """Kiểm tra tâm xe đã vượt qua vạch ngang line_y chưa"""
    return point[1] > line_y

def save_violation(frame, track_id, vehicle_type, plate_text="UNKNOWN"):
    """Lưu ảnh vi phạm và ghi log vào CSV"""
    time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_name = f"violation_{track_id}_{time_str}.jpg"
    img_path = os.path.join('outputs/violations', img_name)
    
    # Lưu ảnh bằng chứng
    cv2.imwrite(img_path, frame)
    
    # Ghi log vào file CSV
    log_data = {
        'Time': [time_str],
        'Vehicle_ID': [track_id],
        'Type': [vehicle_type],
        'Plate': [plate_text],
        'Image_Path': [img_path]
    }
    df = pd.DataFrame(log_data)
    # Nếu file chưa tồn tại thì ghi cả header, nếu có rồi thì append
    df.to_csv('outputs/violation_logs.csv', mode='a', index=False, header=not os.path.exists('outputs/violation_logs.csv'))
    
    return img_path