from flask import Flask, jsonify, Response, request, send_from_directory
from flask_cors import CORS
import cv2

from api.models.violations import ViolationModel

app = Flask(__name__)
CORS(app)

# ======================
# 📁 IMAGE EVIDENCE
# ======================
@app.route('/evidences/<path:filename>')
def get_image(filename):
    return send_from_directory('../evidences', filename)

# ======================
# 🗄 DB CONFIG
# ======================
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "traffic_db"
}

violation_model = ViolationModel(db_config)

@app.route("/api/violations", methods=["GET"])
def get_violations():
    return jsonify(violation_model.get_all_violations())

# ======================
# 🚦 AI DETECT (DEMO)
# ======================
def detect_violation(frame):
    person = 1
    helmet = 0

    if person == 1 and helmet == 0:
        return "NO_HELMET"
    return None

# ======================
# 🎥 CAMERA SOURCE SELECT
# ======================
def get_video_source(cam):
    if cam == "Camera 1":
        return "videos/test1.mp4"
    elif cam == "Camera 2":
        return "videos/test2.mp4"
    return "videos/test1.mp4"

# ======================
# 📹 STREAM GENERATOR
# ======================
def generate_frames(cam):
    cap = cv2.VideoCapture(get_video_source(cam))

    while True:
        success, frame = cap.read()
        if not success:
            break

        violation = detect_violation(frame)

        if violation:
            cv2.putText(
                frame,
                f"VIOLATION: {violation}",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# ======================
# 🌐 STREAM API
# ======================
@app.route('/video_feed')
def video_feed():
    cam = request.args.get("cam")
    return Response(
        generate_frames(cam),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
# =======================
# GET SETTINGS
# =======================
@app.route("/api/settings", methods=["GET"])
def get_settings():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM settings")
    rows = cursor.fetchall()

    result = {}
    for r in rows:
        result[r["setting_key"]] = r["setting_value"]

    return jsonify(result)

# =======================
# SAVE SETTINGS
# =======================
@app.route("/api/settings", methods=["POST"])
def save_settings():
    data = request.json
    cursor = db.cursor()

    for key, value in data.items():
        cursor.execute("""
            INSERT INTO settings (setting_key, setting_value)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE setting_value=%s
        """, (key, value, value))

    db.commit()

    return jsonify({"message": "Lưu settings thành công"})

# ======================
# 🚀 RUN SERVER
# ======================
if __name__ == "__main__":
    app.run(debug=True)
    