from flask import Blueprint, jsonify

bp = Blueprint("routes", __name__)


@bp.get("/health")
def health():
    return jsonify({"status": "ok"})
