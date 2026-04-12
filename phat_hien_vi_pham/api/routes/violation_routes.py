from flask import Blueprint, jsonify
from models.violation_model import get_all_violations

violation_bp = Blueprint("violations", __name__)

@violation_bp.route("/api/violations", methods=["GET"])
def get_violations():
    data = get_all_violations()
    return jsonify(data)
