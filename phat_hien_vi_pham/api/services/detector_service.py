from ultralytics import YOLO
import cv2
import numpy as np

vehicle_model = YOLO("AI_models/yolo11s.pt")
plate_model = YOLO("AI_models/license_plate_detector.pt")
vn_plate_model = YOLO("AI_models/vietnam-license-plate.pt")
vehicle_names = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

# Giữ cache toàn cục CHỈ dùng cho luồng VIDEO TRACKING
tracked_plates = {}

def detect_vehicles(frame):
    # Nhận diện phương tiện
    results = vehicle_model.track(
        frame,
        persist=True,
        tracker="bytetrack.yaml",
        imgsz=640,
        conf=0.4,
        iou=0.5,
        classes=[2, 3, 5, 7],
        device="mps", # Giữ nguyên mps cho MacBook Air Air Haily
        verbose=False
    )

    vehicles = []
    if not results or len(results) == 0:
        return vehicles

    for box in results[0].boxes:
        if box.cls is None:
            continue
            
        cls = int(box.cls[0])
        conf = float(box.conf[0])

        if cls not in vehicle_names or conf < 0.25:
            continue

        # Lấy track_id từ YOLO
        track_id = int(box.id[0]) if box.id is not None else -1

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)

        # -------------------------------------------------------------
        # ĐẶC BIỆT LƯU Ý: KIỂM TRA ĐÂY LÀ ẢNH TĨNH HAY VIDEO
        # Nếu frame được gửi từ hàm scan_frame của video thì track_id sẽ liên tục.
        # Ở đây ta check nếu track_id hợp lệ VÀ có trong cache thì mới lấy cache (dành cho Video).
        # Nếu là ảnh tĩnh ngẫu nhiên, ta BẮT BUỘC bỏ qua cache để quét mới hoàn toàn.
        # -------------------------------------------------------------
        
        # Biến để nhận biết luồng video (Bằng cách check xem có đang chạy autoScan không)
        # Cách an toàn nhất: Nếu là ảnh tĩnh, ta không dùng bộ nhớ đệm `tracked_plates`
        is_video = (box.id is not None) 

        # CHỈ ĐỌC CACHE NẾU LÀ LUỒNG VIDEO
        if is_video and track_id in tracked_plates:
            cached = tracked_plates[track_id]
            vehicles.append({
                "track_id": track_id,
                "vehicle_type": vehicle_names[cls],
                "vehicle_box": {"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1},
                "plate_crop": cached["plate_crop"],
                "plate_box": cached["plate_box"]
            })
            continue

        # -------------------------------------------------------------
        # XỬ LÝ CẮT BIỂN SỐ MỚI TOÀN BỘ (Dành cho ảnh tĩnh hoặc xe video mới)
        # -------------------------------------------------------------
        vehicle_crop = frame[y1:y2, x1:x2]
        if vehicle_crop.size == 0:
            continue

        plate_results = plate_model(vehicle_crop, conf=0.3, device="mps", verbose=False)
        
        plate_crop_final = None
        plate_box_final = None

        if plate_results and len(plate_results[0].boxes) > 0:
            best_box = max(plate_results[0].boxes, key=lambda b: float(b.conf[0]))
            px1, py1, px2, py2 = map(int, best_box.xyxy[0])
            
            # Padding
            pad = 10
            px1, py1 = max(0, px1 - pad), max(0, py1 - pad)
            px2, py2 = min(vehicle_crop.shape[1], px2 + pad), min(vehicle_crop.shape[0], py2 + pad)

            plate_crop = vehicle_crop[py1:py2, px1:px2]
            if plate_crop.size > 0:
                plate_crop_final = cv2.resize(plate_crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                
                plate_box_final = {
                    "x": x1 + px1,
                    "y": y1 + py1,
                    "w": px2 - px1,
                    "h": py2 - py1
                }

                # CHỈ LƯU VÀO CACHE KHI THỰC SỰ LÀ LUỒNG VIDEO TRACKING
                if is_video:
                    tracked_plates[track_id] = {
                        "plate_crop": plate_crop_final,
                        "plate_box": plate_box_final
                    }
                    if len(tracked_plates) > 200:
                        tracked_plates.pop(next(iter(tracked_plates)))

        # Trả dữ liệu phương tiện sạch sẽ
        vehicles.append({
            "track_id": track_id if is_video else -1, # Ép ảnh tĩnh trả về -1 để scan_routes xử lý chuẩn độc lập
            "vehicle_type": vehicle_names[cls],
            "vehicle_box": {"x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1},
            "plate_crop": plate_crop_final, 
            "plate_box": plate_box_final
        })

    return vehicles