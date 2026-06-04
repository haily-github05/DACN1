import easyocr
import cv2
import re
import numpy as np

reader = easyocr.Reader(["en"], gpu=False)


def clean_plate_keep_format(text):
    if not text:
        return ""

    text = text.upper()
    text = re.sub(r"[^A-Z0-9\-\.]", "", text)
    return text


def clean_plate_raw(text):
    if not text:
        return ""

    text = text.upper()
    text = re.sub(r"[^A-Z0-9]", "", text)
    return text


def normalize_plate(text):
    text = clean_plate_raw(text)

    text = text.replace("O", "0")
    text = text.replace("Q", "0")
    text = text.replace("I", "1")
    text = text.replace("L", "1")
    text = text.replace("Z", "2")
    text = text.replace("S", "5")

    return text


def preprocess_plate(img):
    if img is None or img.size == 0:
        return None

    img = cv2.resize(
        img,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    gray = clahe.apply(gray)

    return gray


def format_vn_plate(raw_text):
    text = normalize_plate(raw_text)

    if len(text) < 7:
        return "Unknown"


    if len(text) == 9:
        return f"{text[0:2]}-{text[2:4]} {text[4:7]}.{text[7:9]}"


    if len(text) == 8:
        return f"{text[0:2]}-{text[2:4]} {text[4:8]}"

    if len(text) == 10:
        return f"{text[0:2]}-{text[2:5]} {text[5:8]}.{text[8:10]}"

    return text


def detect_plate(plate_crop):
    try:
        if plate_crop is None or plate_crop.size == 0:
            return "Unknown"

        img = preprocess_plate(plate_crop)

        if img is None:
            return "Unknown"

        h, w = img.shape[:2]

        allowed = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-."

        candidates = []

        all_res = reader.readtext(
            img,
            detail=0,
            paragraph=False,
            allowlist=allowed
        )

        if all_res:
            candidates.append("".join(all_res))


        mid = h // 2

        top_img = img[0:mid, :]
        bot_img = img[mid:h, :]

        top_res = reader.readtext(
            top_img,
            detail=0,
            paragraph=False,
            allowlist=allowed
        )

        bot_res = reader.readtext(
            bot_img,
            detail=0,
            paragraph=False,
            allowlist=allowed
        )

        line1 = "".join(top_res)
        line2 = "".join(bot_res)

        if line1 or line2:
            candidates.append(line1 + line2)

        best = "Unknown"

        for c in candidates:
            formatted = format_vn_plate(c)

            if formatted != "Unknown":
                best = formatted

                raw = normalize_plate(c)
                if len(raw) == 9:
                    return formatted

        return best

    except Exception as e:
        print("OCR ERROR:", e)
        return "Unknown"