
import cv2


# =========================
# STOP LINE
# =========================

stop_line_y = 420


# =========================
# DRAW STOP LINE
# =========================

def draw_stop_line(frame):

    cv2.line(
        frame,
        (0, stop_line_y),
        (1280, stop_line_y),
        (0,255,255),
        4
    )

    cv2.putText(
        frame,
        "STOP LINE",
        (20, stop_line_y - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0,255,255),
        2
    )


# =========================
# CHECK RED LIGHT
# =========================

def check_red_light_violation(
    center_y,
    red_light=False
):

    if red_light:

        if center_y < stop_line_y:

            return True

    return False
