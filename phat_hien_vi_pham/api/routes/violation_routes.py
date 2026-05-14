from flask import Blueprint, jsonify, request
import mysql.connector

violation_bp = Blueprint("violation_bp", __name__)

# =========================
# LẤY DANH SÁCH VI PHẠM
# =========================
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

@violation_bp.route(
    "/api/violations/<int:id>/status",
    methods=["PUT"]
)
def update_violation_status(id):

    try:

        data = request.get_json()

        status = data.get("status")

        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3308,
            user="root",
            password="",
            database="traffic_db"
        )

        cursor = conn.cursor()

        query = """
        UPDATE violations
        SET status = %s
        WHERE id = %s
        """

        cursor.execute(query, (status, id))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Cập nhật trạng thái thành công"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500