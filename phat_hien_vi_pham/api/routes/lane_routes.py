
import cv2
import numpy as np


# =========================
# ZONES
# =========================

sidewalk_zone = np.array([
    [0,720],
    [0,520],
    [250,450],
    [400,720]
], np.int32)

motor_lane = np.array([
    [250,720],
    [420,420],
    [720,420],
    [650,720]
], np.int32)

car_lane = np.array([
    [700,720],
    [820,420],
    [1280,420],
    [1280,720]
], np.int32)




# =========================
# DRAW ALL ZONES
# =========================

def draw_zones(frame):

    cv2.polylines(
        frame,
        [sidewalk_zone],
        True,
        (0,0,255),
        3
    )

    cv2.polylines(
        frame,
        [motor_lane],
        True,
        (0,255,0),
        3
    )

    cv2.polylines(
        frame,
        [car_lane],
        True,
        (255,0,0),
        3
    )

# =========================
# INSIDE POLYGON
# =========================

def inside_zone(point, polygon):

    result = cv2.pointPolygonTest(
        polygon,
        point,
        False
    )

    return result >= 0


# =========================
# CHECK LANE VIOLATIONS
# =========================

def check_lane_violation(
    center_x,
    center_y,
    vehicle_type,
    red_light=False
):

    point = (center_x, center_y)

    violations = []

    # xe máy đi trên lề
    if vehicle_type == "motorbike":

        if inside_zone(point, sidewalk_zone):

            violations.append(
                "SIDEWALK VIOLATION"
            )

    # xe máy đi làn ô tô
    if vehicle_type == "motorbike":

        if inside_zone(point, car_lane):

            violations.append(
                "WRONG CAR LANE"
            )

    # ô tô đi làn xe máy
    if vehicle_type in [
        "car",
        "truck",
        "bus"
    ]:

        if inside_zone(point, motor_lane):

            violations.append(
                "WRONG MOTOR LANE"
            )

    return violations
