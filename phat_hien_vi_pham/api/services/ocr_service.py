import easyocr
import cv2
import re
import numpy as np

# =========================
# EASY OCR
# =========================

print("⚙️ EasyOCR chạy bằng CPU")

reader = easyocr.Reader(
    ['en'],
    gpu=False
)

# =========================
# CLEAN TEXT
# =========================

def clean_plate(text):

    if not text:
        return ""

    return re.sub(
        r'[^A-Z0-9]',
        '',
        text.upper()
    )

# =========================
# PREPROCESS
# =========================

def preprocess_image(img):

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )

    gray = cv2.resize(
        gray,
        None,
        fx=2.5,
        fy=2.5,
        interpolation=cv2.INTER_CUBIC
    )

    clahe = cv2.createCLAHE(
        clipLimit=3.0,
        tileGridSize=(8, 8)
    )

    gray = clahe.apply(gray)

    gray = cv2.bilateralFilter(
        gray,
        9,
        75,
        75
    )

    return gray

# =========================
# OCR
# =========================

def detect_plate(plate_crop):

    try:

        if plate_crop is None:
            return "UNKNOWN"

        if plate_crop.size == 0:
            return "UNKNOWN"

        h_orig, w_orig = plate_crop.shape[:2]

        ratio = w_orig / h_orig

        processed = preprocess_image(
            plate_crop
        )

        # =====================
        # BIỂN SỐ VUÔNG
        # =====================

        if ratio < 1.7:

            h, w = processed.shape

            mid = int(h * 0.48)

            top_part = processed[
                0:mid,
                0:w
            ]

            bottom_part = processed[
                mid:h,
                0:w
            ]

            top_text = reader.readtext(
                top_part,
                detail=0,
                allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            )

            bottom_text = reader.readtext(
                bottom_part,
                detail=0,
                allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            )

            combined = (
                "".join(top_text) +
                "".join(bottom_text)
            )

            cleaned = clean_plate(
                combined
            )

            if len(cleaned) >= 5:
                return cleaned

        # =====================
        # BIỂN DÀI
        # =====================

        results = reader.readtext(
            processed,
            detail=1,
            paragraph=False,
            allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        )

        if not results:
            return "UNKNOWN"

        results.sort(
            key=lambda x: x[0][0][0]
        )

        full_text = ""

        for r in results:

            text = clean_plate(r[1])

            confidence = r[2]

            if confidence > 0.35:

                full_text += text

        if len(full_text) >= 5:
            return full_text

        return "UNKNOWN"

    except Exception as e:

        print(f"OCR ERROR: {e}")

        return "UNKNOWN"