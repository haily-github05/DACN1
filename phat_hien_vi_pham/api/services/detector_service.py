from ultralytics import YOLO

vehicle_model = YOLO(
    "AI_models/yolov8n.pt"
)

plate_model = YOLO(
    "AI_models/license_plate_detector.pt"
)

vehicle_names = {

    2: "car",

    3: "motorcycle",

    5: "bus",

    7: "truck"
}

def detect_vehicles(frame):

    results = vehicle_model(
        frame,
        imgsz=640,
        conf=0.4,
        verbose=False
    )

    vehicles = []

    for r in results:

        for box in r.boxes:

            cls = int(box.cls[0])

            conf = float(box.conf[0])

            if cls not in vehicle_names:
                continue

            if conf < 0.25:
                continue

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            x1 = max(0, x1)
            y1 = max(0, y1)

            x2 = min(frame.shape[1], x2)
            y2 = min(frame.shape[0], y2)

            vehicle_crop = frame[
                y1:y2,
                x1:x2
            ]

            plate_results = plate_model(
                vehicle_crop
            )

            for pr in plate_results:

                for pb in pr.boxes:

                    px1, py1, px2, py2 = map(
                        int,
                        pb.xyxy[0]
                    )

                    pad = 10

                    px1 = max(0, px1 - pad)
                    py1 = max(0, py1 - pad)

                    px2 = min(
                        vehicle_crop.shape[1],
                        px2 + pad
                    )

                    py2 = min(
                        vehicle_crop.shape[0],
                        py2 + pad
                    )

                    plate_crop = vehicle_crop[
                        py1:py2,
                        px1:px2
                    ]

                    vehicles.append({

                        "vehicle_type":
                            vehicle_names[cls],

                        "vehicle_box": {
                            "x": x1,
                            "y": y1,
                            "w": x2 - x1,
                            "h": y2 - y1
                        },

                        "plate_crop":
                            plate_crop,

                        "plate_box": {
                            "x": x1 + px1,
                            "y": y1 + py1,
                            "w": px2 - px1,
                            "h": py2 - py1
                        }
                    })

    return vehicles