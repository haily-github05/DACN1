import easyocr
import cv2
import re
import numpy as np

reader = easyocr.Reader(["en"], gpu=False)

ALLOWLIST = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

NOISE_WORDS = [
    "VIETNAM",
    "VN",
    "MDCRDR",
    "MOTOR",
    "HONDA",
    "YAMAHA"
]


def clean_plate(text):
    if not text:
        return ""

    text = text.upper()
    text = re.sub(r"[^A-Z0-9]", "", text)

    for noise in NOISE_WORDS:
        text = text.replace(noise, "")

    return text


def fix_common_errors(text):
    text = clean_plate(text)

    if len(text) < 5:
        return text

    chars = list(text)

    for i in range(min(2, len(chars))):
        if chars[i] in ["O", "Q", "D"]:
            chars[i] = "0"
        elif chars[i] in ["I", "L"]:
            chars[i] = "1"
        elif chars[i] == "S":
            chars[i] = "5"
        elif chars[i] == "B":
            chars[i] = "8"

    for i in range(3, len(chars)):
        if chars[i] in ["O", "Q", "D"]:
            chars[i] = "0"
        elif chars[i] in ["I", "L"]:
            chars[i] = "1"
        elif chars[i] == "S":
            chars[i] = "5"
        elif chars[i] == "B":
            chars[i] = "8"

    return "".join(chars)


def is_valid_plate(text):
    text = clean_plate(text)

    if not (6 <= len(text) <= 10):
        return False

    digits = sum(c.isdigit() for c in text)

    if digits < 4:
        return False

    return True


def score_plate(text, conf):
    text = clean_plate(text)
    score = conf

    if is_valid_plate(text):
        score += 5

    if 7 <= len(text) <= 9:
        score += 2

    if len(text) >= 2 and text[:2].isdigit():
        score += 1

    score += sum(c.isdigit() for c in text) * 0.1

    return score


def preprocess_versions(plate_crop):
    versions = []

    if plate_crop is None or plate_crop.size == 0:
        return versions

    img = cv2.resize(
        plate_crop,
        None,
        fx=3,
        fy=3,
        interpolation=cv2.INTER_CUBIC
    )

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    versions.append(gray)

    clahe = cv2.createCLAHE(
        clipLimit=2.5,
        tileGridSize=(8, 8)
    )
    clahe_img = clahe.apply(gray)
    versions.append(clahe_img)

    kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ])

    sharp = cv2.filter2D(clahe_img, -1, kernel)
    versions.append(sharp)

    _, otsu = cv2.threshold(
        sharp,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    versions.append(otsu)

    adaptive = cv2.adaptiveThreshold(
        sharp,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        9
    )
    versions.append(adaptive)

    return versions


def crop_center(img):
    h, w = img.shape[:2]

    if h <= 0 or w <= 0:
        return img

    x_margin = int(w * 0.05)
    y_margin = int(h * 0.05)

    return img[
        y_margin:h - y_margin,
        x_margin:w - x_margin
    ]


def split_lines(img):
    h, w = img.shape[:2]

    if h <= 0 or w <= 0:
        return [img]

    img = crop_center(img)

    h, w = img.shape[:2]
    mid = h // 2

    top = img[0:mid, :]
    bottom = img[mid:h, :]

    return [img, top, bottom]


def easyocr_read(img):
    try:
        results = reader.readtext(
            img,
            detail=1,
            paragraph=False,
            allowlist=ALLOWLIST
        )

        texts = []
        total_conf = 0

        for item in results:
            text = clean_plate(item[1])
            conf = float(item[2])

            if text:
                texts.append(text)
                total_conf += conf

        return "".join(texts), total_conf

    except Exception:
        return "", 0


def read_plate_crop(plate_crop):
    try:
        if plate_crop is None or plate_crop.size == 0:
            return "Unknown"

        candidates = []

        versions = preprocess_versions(plate_crop)

        for img in versions:
            parts = split_lines(img)

            for p in parts:
                text, conf = easyocr_read(p)

                if text:
                    fixed = fix_common_errors(text)

                    candidates.append({
                        "text": fixed,
                        "score": score_plate(fixed, conf)
                    })

            if len(parts) >= 3:
                top_text, top_conf = easyocr_read(parts[1])
                bottom_text, bottom_conf = easyocr_read(parts[2])

                merged = fix_common_errors(
                    top_text + bottom_text
                )

                if merged:
                    candidates.append({
                        "text": merged,
                        "score": score_plate(
                            merged,
                            top_conf + bottom_conf
                        ) + 1
                    })

        if not candidates:
            return "Unknown"

        candidates = sorted(
            candidates,
            key=lambda x: x["score"],
            reverse=True
        )

        best = candidates[0]["text"]

        if 6 <= len(best) <= 10:
            return best

        return "Unknown"

    except Exception as e:
        print("EASYOCR ERROR =", e)
        return "Unknown"


def detect_plate(plate_crop):
    return read_plate_crop(plate_crop)