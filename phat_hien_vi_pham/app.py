from flask import Flask
from flask import jsonify
from flask import request
from flask import send_from_directory

from flask_cors import CORS

import os
import mysql.connector

from api.routes.scan_routes import scan_bp
from api.routes.violation_routes import violation_bp
from api.models.violations import ViolationModel

from camera import camera_bp
import warnings

warnings.filterwarnings(
    "ignore",
    message=".*pin_memory.*"
)
app = Flask(__name__)

# =========================
# CONFIG
# =========================

app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

CORS(app, resources={
    r"/*": {
        "origins": "*"
    }
})

# =========================
# REGISTER BLUEPRINT
# =========================

app.register_blueprint(scan_bp)
app.register_blueprint(violation_bp)
app.register_blueprint(camera_bp)

# =========================
# DATABASE
# =========================

db_config = {
    "host": "127.0.0.1",
    "port": 3308,
    "user": "root",
    "password": "",
    "database": "traffic_db"
}

violation_model = ViolationModel(db_config)

# =========================
# EVIDENCE IMAGE
# =========================

@app.route('/evidences/<path:filename>')
def get_image(filename):

    evidence_dir = os.path.join(
        os.getcwd(),
        'evidences'
    )

    response = send_from_directory(
        evidence_dir,
        filename
    )

    response.headers[
        "Access-Control-Allow-Origin"
    ] = "*"

    return response

# =========================
# GET VIOLATION DETAIL
# =========================

@app.route('/api/violations/<int:id>', methods=['GET'])
def get_violation(id):

    try:

        conn = mysql.connector.connect(
            **db_config
        )

        cursor = conn.cursor(
            dictionary=True
        )

        query = """
        SELECT

            violations.*,

            videos.name AS camera_name,
            videos.location AS camera_location,

            vehicles.vehicle_type AS vehicle_type

        FROM violations

        LEFT JOIN videos
        ON violations.video_id = videos.id

        LEFT JOIN vehicles
        ON violations.vehicle_id = vehicles.id

        WHERE violations.id = %s
        """

        cursor.execute(query, (id,))

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify(row)

    except Exception as e:

        print("GET VIOLATION ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================
# VIDEO STREAM
# =========================

@app.route('/videos/<path:filename>')
def serve_video(filename):

    video_dir = os.path.join(
        os.getcwd(),
        'traffic_web',
        'videos'
    )

    response = send_from_directory(
        video_dir,
        filename
    )

    response.headers[
        "Access-Control-Allow-Origin"
    ] = "*"

    response.headers[
        "Cross-Origin-Resource-Policy"
    ] = "cross-origin"

    response.headers[
        "Accept-Ranges"
    ] = "bytes"

    return response

# =========================
# GET VIDEO LIST
# =========================

@app.route('/videos', methods=['GET'])
def get_videos():

    try:

        conn = mysql.connector.connect(
            **db_config
        )

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                name,
                path,
                location,
                created_at
            FROM videos
        """)

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

        cursor.close()
        conn.close()

        return jsonify(videos)

    except Exception as e:

        print("GET VIDEOS ERROR:", e)

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# =========================
# HOME
# =========================

@app.route("/")
def home():

    return send_from_directory(
        "traffic_web",
        "index.html"
    )

# =========================
# STATIC FILES
# =========================

@app.route("/<path:path>")
def static_files(path):

    return send_from_directory(
        "traffic_web",
        path
    )

# =========================
# RUN APP
# =========================

if __name__ == "__main__":

    print("===================================")
    print(" TRAFFIC AI SERVER RUNNING ")
    print(" http://127.0.0.1:5000 ")
    print("===================================")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )