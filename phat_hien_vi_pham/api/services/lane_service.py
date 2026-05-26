# import cv2
# import numpy as np
# from ultralytics import YOLO

# class LaneService:
#     def __init__(self, model_path="AI_models/lane_detection_best.pt"):
#         # Load YOLO model
#         self.model = YOLO(model_path)
#         self.cached_polygons = []
#         self.frame_count = 0

#     def get_lane_polygons(self, frame, force_update=False):
#         # Tối ưu: Cứ mỗi 30 frames mới quét model 1 lần (realtime)
#         self.frame_count += 1
#         if not force_update and len(self.cached_polygons) > 0 and self.frame_count % 30 != 0:
#             return self.cached_polygons

#         polygons = []
#         results = self.model.predict(frame, conf=0.25, device="cpu", verbose=False)

#         for result in results:
#             if result.masks is not None and result.masks.xy is not None:
#                 for mask in result.masks.xy:
#                     h, w = frame.shape[:2]
#                     poly = np.array(mask, dtype=np.float32)

#                     # đảm bảo scale đúng (nếu cần)
#                     poly[:, 0] = np.clip(poly[:, 0], 0, w - 1)
#                     poly[:, 1] = np.clip(poly[:, 1], 0, h - 1)

#                     poly = poly.astype(np.int32)
#                     if len(poly) >= 3:
#                         polygons.append(poly)
        
#         if len(polygons) > 0:
#             self.cached_polygons = polygons
            
#         self.frame_count += 1
#         return self.cached_polygons

#     def check_lane_id(self, vehicle_center, lane_polygons):
#         x, y = vehicle_center
#         best_id = -1
#         best_score = 0

#         for i, poly in enumerate(lane_polygons):
#             dist = cv2.pointPolygonTest(poly, (x, y), False)

#             if dist >= 0:
#                 return i  # inside thì ưu tiên luôn

#             if abs(dist) < best_score or best_score == 0:
#                 best_score = abs(dist)
#                 best_id = i

#         return best_id

#     def draw_lanes(self, frame, lane_polygons):
#         for poly in lane_polygons:
#             cv2.polylines(frame, [poly], True, (255, 0, 0), 2)