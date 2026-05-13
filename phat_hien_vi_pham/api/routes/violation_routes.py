from flask import Blueprint, jsonify
import mysql.connector

violation_bp = Blueprint("violation_bp", __name__)

@violation_bp.route("/api/violations", methods=["GET"])
def get_violations():

    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="traffic_db"
        )

        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM violations")

        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(data)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500