import cv2
import numpy as np

# Định vị vị trí vạch dừng đèn đỏ chính xác theo góc nhìn Camera 4
# Vạch này nằm ngay sát phía trên đầu các phương tiện đang dừng chờ đèn
STOP_LINE_Y = 490

# Bộ nhớ lưu trữ vị trí cũ của các xe để tính toán hướng di chuyển qua vạch
vehicle_history = {}

def draw_stop_line(frame, red_light=False):
    """
    Vẽ duy nhất một vạch dừng nằm ngang rõ ràng và vùng phủ shadow phía sau vạch
    """
    h, w = frame.shape[:2]
    color = (0, 0, 255) if red_light else (0, 255, 0) # Đỏ nếu đèn đỏ, Xanh nếu đèn xanh

    # 1. Vẽ một vùng phủ mờ (Shadow) phía sau vạch dừng để UI nhìn trực quan
    # overlay = frame.copy()
    # Vùng vi phạm tính từ vạch dừng đổ lên phía giao lộ (phía xa)
    # cv2.rectangle(overlay, (0, 0), (w, STOP_LINE_Y), color, -1)
    # cv2.addWeighted(overlay, 0.12, frame, 0.88, 0, frame)

    # 2. Vẽ vạch kẻ dừng đậm nét
    cv2.line(frame, (0, STOP_LINE_Y), (w, STOP_LINE_Y), color, 4)


def check_red_light_violation(track_id, center_y, red_light):
    """
    Logic bắt lỗi vượt đèn đỏ chuẩn: 
    Chỉ phạt khi đèn đang ĐỎ và chiếc xe có hành vi di chuyển CẮT QUA VẠCH (từ dưới lên trên)
    """
    # Nếu đèn xanh hoặc vàng, không bắt lỗi
    if not red_light:
        if track_id in vehicle_history:
            del vehicle_history[track_id]
        return False

    prev_y = vehicle_history.get(track_id)
    vehicle_history[track_id] = center_y

    if prev_y is None:
        return False

    # Do camera quay từ phía sau, xe đi tới giao lộ nghĩa là tọa độ Y giảm dần (Ví dụ: từ 600 về 400)
    # Hành vi vượt đèn đỏ: Frame trước xe ở dưới vạch (prev_y > STOP_LINE_Y) 
    # và Frame này xe đã vượt lên trên vạch (center_y <= STOP_LINE_Y)
    if prev_y > STOP_LINE_Y and center_y <= STOP_LINE_Y:
        return True

    return False