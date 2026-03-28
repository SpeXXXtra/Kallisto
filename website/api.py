from flask import Blueprint, request, jsonify
from . import db
from .model import User
import math

api = Blueprint("api", __name__, url_prefix="/")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EARTH_RADIUS_KM = 6371.0


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in kilometres between two coordinates."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))


def parse_float(value, field_name: str):
    """Return (float, None) on success or (None, error_response) on failure."""
    try:
        return float(value), None
    except (TypeError, ValueError):
        return None, (jsonify({"error": f"'{field_name}' must be a numeric value."}), 400)


def validate_coordinates(lat: float, lon: float):
    if not (-90 <= lat <= 90):
        return jsonify({"error": "latitude must be between -90 and 90."}), 400
    if not (-180 <= lon <= 180):
        return jsonify({"error": "longitude must be between -180 and 180."}), 400
    return None


def validate_radius(radius: float):
    if radius <= 0:
        return jsonify({"error": "service_radius must be a positive number."}), 400
    return None


# ---------------------------------------------------------------------------
# POST /users — register a new service provider
# ---------------------------------------------------------------------------

@api.route("/users", methods=["POST"])
def create_user():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    # --- name ---
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "'name' is required."}), 400
    if len(name) > 100:
        return jsonify({"error": "'name' must not exceed 100 characters."}), 400

    # --- latitude ---
    lat, err = parse_float(data.get("lat"), "lat")
    if err:
        return err

    # --- longitude ---
    lon, err = parse_float(data.get("long"), "long")
    if err:
        return err

    # --- coordinate bounds ---
    coord_err = validate_coordinates(lat, lon)
    if coord_err:
        return coord_err

    # --- service_radius ---
    radius, err = parse_float(data.get("service_radius"), "service_radius")
    if err:
        return err
    radius_err = validate_radius(radius)
    if radius_err:
        return radius_err

    user = User(name=name, latitude=lat, longitude=lon, service_radius=radius)
    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


# ---------------------------------------------------------------------------
# GET /users — list all service providers
# ---------------------------------------------------------------------------

@api.route("/users", methods=["GET"])
def get_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200


# ---------------------------------------------------------------------------
# PATCH /users/<id> — update an existing provider
# ---------------------------------------------------------------------------

@api.route("/users/<int:user_id>", methods=["PATCH"])
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": f"User with id {user_id} not found."}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON."}), 400

    if "name" in data:
        name = str(data["name"]).strip()
        if not name:
            return jsonify({"error": "'name' cannot be empty."}), 400
        if len(name) > 100:
            return jsonify({"error": "'name' must not exceed 100 characters."}), 400
        user.name = name

    if "lat" in data:
        lat, err = parse_float(data["lat"], "lat")
        if err:
            return err
        coord_err = validate_coordinates(lat, user.longitude)
        if coord_err:
            return coord_err
        user.latitude = lat

    if "long" in data:
        lon, err = parse_float(data["long"], "long")
        if err:
            return err
        coord_err = validate_coordinates(user.latitude, lon)
        if coord_err:
            return coord_err
        user.longitude = lon

    if "lat" in data and "long" in data:
        lat, _ = parse_float(data["lat"], "lat")
        lon, _ = parse_float(data["long"], "long")
        coord_err = validate_coordinates(lat, lon)
        if coord_err:
            return coord_err
        user.latitude = lat
        user.longitude = lon

    if "service_radius" in data:
        radius, err = parse_float(data["service_radius"], "service_radius")
        if err:
            return err
        radius_err = validate_radius(radius)
        if radius_err:
            return radius_err
        user.service_radius = radius

    db.session.commit()
    return jsonify(user.to_dict()), 200


# ---------------------------------------------------------------------------
# DELETE /users/<id> — remove a provider
# ---------------------------------------------------------------------------

@api.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": f"User with id {user_id} not found."}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User {user_id} deleted successfully."}), 200


# ---------------------------------------------------------------------------
# GET /search?lat=&long= — find providers whose radius covers a coordinate
# ---------------------------------------------------------------------------

@api.route("/search", methods=["GET"])
def search_users():
    raw_lat = request.args.get("lat")
    raw_lon = request.args.get("long")

    if raw_lat is None or raw_lon is None:
        return jsonify({"error": "'lat' and 'long' query parameters are required."}), 400

    lat, err = parse_float(raw_lat, "lat")
    if err:
        return err

    lon, err = parse_float(raw_lon, "long")
    if err:
        return err

    coord_err = validate_coordinates(lat, lon)
    if coord_err:
        return coord_err

    results = []
    for user in User.query.all():
        distance = haversine(lat, lon, user.latitude, user.longitude)
        if distance <= user.service_radius:
            entry = user.to_dict()
            entry["distance_km"] = round(distance, 4)
            results.append(entry)

    # Sort closest first
    results.sort(key=lambda x: x["distance_km"])

    return jsonify(results), 200