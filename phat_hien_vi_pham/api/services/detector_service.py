from ultralytics import YOLO
import cv2
import numpy as np

vehicle_model = YOLO("AI_models/yolo11s.pt")
plate_model = YOLO("AI_models/license_plate_detector.pt")

vehicle_names = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

# Giữ cache toàn cục ổn định
tracked_plates = {}

def detect_vehicles(frame):
    # Tăng imgsz lên một chút nếu cần chính xác, nhưng 640 là tối ưu tốc độ
    # Trong file detector_service.py, hãy cập nhật lại lệnh gọi model.track:

    results = vehicle_model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        imgsz=640,          # Giữ nguyên kích thước tối ưu
        conf=0.4,           # Tăng nhẹ conf lên 0.4 để lọc bớt nhiễu từ xa
        iou=0.5,            # Thêm giới hạn NMS IoU giúp giải phóng CPU/GPU tránh bị vượt quá time limit 2s
        classes=[2, 3, 5, 7], # CHỈ định vị xe cộ (ô tô, xe máy, xe buýt, xe tải). Bỏ qua các nhãn khác để giảm tải NMS
        device="mps",       # Đảm bảo giữ thiết bị xử lý mps cho chip M1
        verbose=False
    )

    vehicles = []
    if not results or len(results) == 0:
        return vehicles

    for box in results[0].boxes:
        if box.cls is None or box.id is None:
            continue
            
        cls = int(box.cls[0])
        track_id = int(box.id[0])
        conf = float(box.conf[0])

        if cls not in vehicle_names or conf < 0.25:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)

        # Nếu xe đã từng được quét biển số thành công trước đó -> Trả kết quả ngay lập tức (Tốc độ ~5ms)
        if track_id in tracked_plates:
            cached = tracked_plates[track_id]
            vehicles.append({
                "track_id": track_id,
                "vehicle_type": vehicle_names[cls],
                "vehicle_box": {"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1},
                "plate_crop": cached["plate_crop"],
                "plate_box": cached["plate_box"]
            })
            continue

        # Xử lý cắt ảnh xe (Chỉ chạy khi là XE MỚI XUẤT HIỆN)
        vehicle_crop = frame[y1:y2, x1:x2]
        if vehicle_crop.size == 0:
            continue

        # Tìm vị trí biển số trên xe mới
        plate_results = plate_model(vehicle_crop, conf=0.3,device="mps", verbose=False)
        
        plate_crop_final = None
        plate_box_final = None

        if plate_results and len(plate_results[0].boxes) > 0:
            best_box = max(plate_results[0].boxes, key=lambda b: float(b.conf[0]))
            px1, py1, px2, py2 = map(int, best_box.xyxy[0])
            
            # Padding hợp lý
            pad = 10
            px1, py1 = max(0, px1 - pad), max(0, py1 - pad)
            px2, py2 = min(vehicle_crop.shape[1], px2 + pad), min(vehicle_crop.shape[0], py2 + pad)

            plate_crop = vehicle_crop[py1:py2, px1:px2]
            if plate_crop.size > 0:
                # Upscale & Sharpen nhẹ để phục vụ EasyOCR ở bước sau
                plate_crop_final = cv2.resize(plate_crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                
                plate_box_final = {
                    "x": x1 + px1,
                    "y": y1 + py1,
                    "w": px2 - px1,
                    "h": py2 - py1
                }

                # Lưu vào cache để các frame sau của chính xe này ĐỒNG LOẠT BỎ QUA bước detect biển số
                tracked_plates[track_id] = {
                    "plate_crop": plate_crop_final,
                    "plate_box": plate_box_final
                }

                if len(tracked_plates) > 200:
                    tracked_plates.pop(next(iter(tracked_plates)))

        # Thêm vào mảng trả về
        vehicles.append({
            "track_id": track_id,
            "vehicle_type": vehicle_names[cls],
            "vehicle_box": {"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1},
            "plate_crop": plate_crop_final, 
            "plate_box": plate_box_final
        })

    return vehicles