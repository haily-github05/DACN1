from flask import Flask, jsonify, Response, request, send_from_directory
from flask_cors import CORS
import cv2
import os
from api.models.violations import ViolationModel
import mysql.connector
app = Flask(__name__)
CORS(app)

@app.route('/evidences/<path:filename>')
def get_image(filename):
    return send_from_directory('../evidences', filename)

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

def detect_violation(frame):
    person = 1
    helmet = 0

    if person == 1 and helmet == 0:
        return "NO_HELMET"
    return None
@app.route('/api/violations/<int:id>', methods=['GET'])
def get_violation(id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM violations WHERE id = %s", (id,))
    row = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify(row)
#camera
@app.route('/videos/<path:filename>')
def serve_video(filename):
    video_dir = os.path.join(os.getcwd(), 'traffic_web', 'videos')
    return send_from_directory(video_dir, filename)
@app.route('/videos', methods=['GET'])
def get_videos():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="traffic_db"
        )
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, path, location, created_at FROM videos")
        rows = cursor.fetchall()

        videos = []
        for row in rows:
            videos.append({
                "id": row[0],
                "name": row[1],
                "path": row[2].replace("videos/", ""),
                "location": row[3],
                "created_at": str(row[4])
            })

        conn.close()
        return jsonify(videos)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(debug=True)
    