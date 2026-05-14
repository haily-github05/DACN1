from flask import Blueprint, jsonify
import mysql.connector

violation_bp = Blueprint("violation_bp", __name__)

@violation_bp.route("/api/violations", methods=["GET"])
def get_violations():

    try:

        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3308,
            user="root",
            password="",
            database="traffic_db"
        )

        cursor = conn.cursor(dictionary=True)

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

        ORDER BY violations.time DESC
        """

        cursor.execute(query)

        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(data)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500