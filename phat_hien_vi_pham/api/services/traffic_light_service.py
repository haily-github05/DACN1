import cv2
import numpy as np

def detect_traffic_light(frame):

    h, w = frame.shape[:2]

    roi = frame[0:int(h * 0.4), 0:w]
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([0, 120, 120])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([160, 120, 120])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

    red_mask = mask1 + mask2

    kernel = np.ones((5,5), np.uint8)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(
        red_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    best_box = None
    max_area = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)

        if area < 80:
            continue

        x, y, w_box, h_box = cv2.boundingRect(cnt)

        if h_box / float(w_box) < 0.8:
            continue

        if area > max_area:
            max_area = area
            best_box = (x, y, w_box, h_box)

    if best_box:
        x, y, w_box, h_box = best_box
        return {
            "red": True,
            "box": {
                "x": x,
                "y": y,
                "w": w_box,
                "h": h_box
            }
        }

    return {
        "red": False,
        "box": None
    }