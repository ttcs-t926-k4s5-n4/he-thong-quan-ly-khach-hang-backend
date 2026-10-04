from flask import current_app, jsonify, request


def validate_api_origin():
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return None
    if not request.path.startswith("/api/"):
        return None

    origin = request.headers.get("Origin")
    if not origin:
        return None

    allowed = {value.rstrip("/") for value in current_app.config["FRONTEND_ORIGINS"]}
    if origin.rstrip("/") not in allowed:
        return jsonify({"message": "Nguồn yêu cầu không được phép."}), 403
    return None
