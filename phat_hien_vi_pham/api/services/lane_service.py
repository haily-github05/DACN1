# import cv2
# import numpy as np


# # =========================
# # ZONES
# # =========================

# # LỀ ĐƯỜNG
# sidewalk_zone = np.array([
#     [0, 720],
#     [0, 520],
#     [250, 450],
#     [400, 720]
# ], np.int32)

# # LÀN XE MÁY
# motor_lane = np.array([
#     [250, 720],
#     [420, 420],
#     [720, 420],
#     [650, 720]
# ], np.int32)

# # LÀN Ô TÔ
# car_lane = np.array([
#     [700, 720],
#     [820, 420],
#     [1280, 420],
#     [1280, 720]
# ], np.int32)

# # VẠCH DỪNG
# stop_line_y = 420


# # =========================
# # DRAW ZONES
# # =========================

# def draw_zones(frame):

#     # sidewalk
#     cv2.polylines(
#         frame,
#         [sidewalk_zone],
#         True,
#         (0, 0, 255),
#         3
#     )

#     cv2.putText(
#         frame,
#         "SIDEWALK",
#         (50, 500),
#         cv2.FONT_HERSHEY_SIMPLEX,
#         0.8,
#         (0, 0, 255),
#         2
#     )

#     # motor lane
#     cv2.polylines(
#         frame,
#         [motor_lane],
#         True,
#         (0, 255, 0),
#         3
#     )

#     cv2.putText(
#         frame,
#         "MOTOR LANE",
#         (400, 450),
#         cv2.FONT_HERSHEY_SIMPLEX,
#         0.8,
#         (0, 255, 0),
#         2
#     )

#     # car lane
#     cv2.polylines(
#         frame,
#         [car_lane],
#         True,
#         (255, 0, 0),
#         3
#     )

#     cv2.putText(
#         frame,
#         "CAR LANE",
#         (900, 450),
#         cv2.FONT_HERSHEY_SIMPLEX,
#         0.8,
#         (255, 0, 0),
#         2
#     )

#     # stop line
#     cv2.line(
#         frame,
#         (0, stop_line_y),
#         (1280, stop_line_y),
#         (0, 255, 255),
#         4
#     )

#     cv2.putText(
#         frame,
#         "STOP LINE",
#         (20, stop_line_y - 10),
#         cv2.FONT_HERSHEY_SIMPLEX,
#         0.8,
#         (0, 255, 255),
#         2
#     )


# # =========================
# # CHECK INSIDE POLYGON
# # =========================

# def inside_zone(point, polygon):

#     result = cv2.pointPolygonTest(
#         polygon,
#         point,
#         False
#     )

#     return result >= 0


# # =========================
# # CHECK VIOLATIONS
# # =========================

# def check_violation(
#     center_x,
#     center_y,
#     vehicle_type,
#     red_light=False
# ):

#     point = (center_x, center_y)

#     violations = []

#     # =====================
#     # XE MÁY ĐI TRÊN LỀ
#     # =====================
#     if vehicle_type == "motorbike":

#         if inside_zone(point, sidewalk_zone):

#             violations.append(
#                 "SIDEWALK VIOLATION"
#             )

#     # =====================
#     # XE MÁY ĐI SAI LÀN
#     # =====================
#     if vehicle_type == "motorbike":

#         if inside_zone(point, car_lane):

#             violations.append(
#                 "WRONG CAR LANE"
#             )

#     # =====================
#     # Ô TÔ ĐI SAI LÀN
#     # =====================
#     if vehicle_type in [
#         "car",
#         "truck",
#         "bus"
#     ]:

#         if inside_zone(point, motor_lane):

#             violations.append(
#                 "WRONG MOTOR LANE"
#             )

#     # =====================
#     # VƯỢT ĐÈN ĐỎ
#     # =====================
#     if red_light:

#         if center_y < stop_line_y:

#             violations.append(
#                 "Vượt đèn đỏ"
#             )

#     return violations