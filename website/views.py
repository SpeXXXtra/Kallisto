from flask import Blueprint, render_template, request, redirect, url_for
from . import db
from .model import User
import math

views = Blueprint("views", __name__)

EARTH_RADIUS_KM = 6371.0


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return EARTH_RADIUS_KM * 2 * math.asin(math.sqrt(a))


def parse_float(value, field_name):
    try:
        return float(value), None
    except (TypeError, ValueError):
        return None, f"'{field_name}' must be a numeric value."


def validate_coordinates(lat, lon):
    if not (-90 <= lat <= 90):
        return "Latitude must be between -90 and 90."
    if not (-180 <= lon <= 180):
        return "Longitude must be between -180 and 180."
    return None


def validate_radius(radius):
    if radius <= 0:
        return "Service radius must be a positive number."
    return None


@views.route("/", methods=["GET"])
def index():
    users = User.query.all()
    return render_template("index.html", users=users, search_results=None, search_error=None, form_error=None)


# ── Add User ──────────────────────────────────────────────────────────────────
@views.route("/add-user", methods=["POST"])
def add_user():
    users = User.query.all()

    name = request.form.get("name", "").strip()
    if not name:
        return render_template("index.html", users=users, form_error="Name is required.", search_results=None, search_error=None)
    if len(name) > 100:
        return render_template("index.html", users=users, form_error="Name must not exceed 100 characters.", search_results=None, search_error=None)

    lat, err = parse_float(request.form.get("lat"), "lat")
    if err:
        return render_template("index.html", users=users, form_error=err, search_results=None, search_error=None)

    lon, err = parse_float(request.form.get("long"), "long")
    if err:
        return render_template("index.html", users=users, form_error=err, search_results=None, search_error=None)

    coord_err = validate_coordinates(lat, lon)
    if coord_err:
        return render_template("index.html", users=users, form_error=coord_err, search_results=None, search_error=None)

    radius, err = parse_float(request.form.get("service_radius"), "service_radius")
    if err:
        return render_template("index.html", users=users, form_error=err, search_results=None, search_error=None)

    radius_err = validate_radius(radius)
    if radius_err:
        return render_template("index.html", users=users, form_error=radius_err, search_results=None, search_error=None)

    user = User(name=name, latitude=lat, longitude=lon, service_radius=radius)
    db.session.add(user)
    db.session.commit()

    return redirect(url_for("views.index"))


# ── Search ────────────────────────────────────────────────────────────────────
@views.route("/search-users", methods=["POST"])
def search_users():
    users = User.query.all()

    lat, err = parse_float(request.form.get("search_lat"), "lat")
    if err:
        return render_template("index.html", users=users, search_results=None, search_error=err, form_error=None)

    lon, err = parse_float(request.form.get("search_long"), "long")
    if err:
        return render_template("index.html", users=users, search_results=None, search_error=err, form_error=None)

    coord_err = validate_coordinates(lat, lon)
    if coord_err:
        return render_template("index.html", users=users, search_results=None, search_error=coord_err, form_error=None)

    results = []
    for u in users:
        distance = haversine(lat, lon, u.latitude, u.longitude)
        if distance <= u.service_radius:
            results.append({"user": u, "distance_km": round(distance, 4)})

    results.sort(key=lambda x: x["distance_km"])

    return render_template("index.html", users=users, search_results=results, search_error=None, form_error=None)


# ── Edit User ─────────────────────────────────────────────────────────────────
@views.route("/edit-user/<int:user_id>", methods=["POST"])
def edit_user(user_id):
    users = User.query.all()
    user = db.session.get(User, user_id)
    if not user:
        return render_template("index.html", users=users, form_error=f"User {user_id} not found.", search_results=None, search_error=None)

    name = request.form.get("name", "").strip()
    if not name:
        return render_template("index.html", users=users, form_error="Name is required.", search_results=None, search_error=None)
    if len(name) > 100:
        return render_template("index.html", users=users, form_error="Name must not exceed 100 characters.", search_results=None, search_error=None)

    lat, err = parse_float(request.form.get("lat"), "lat")
    if err:
        return render_template("index.html", users=users, form_error=err, search_results=None, search_error=None)

    lon, err = parse_float(request.form.get("long"), "long")
    if err:
        return render_template("index.html", users=users, form_error=err, search_results=None, search_error=None)

    coord_err = validate_coordinates(lat, lon)
    if coord_err:
        return render_template("index.html", users=users, form_error=coord_err, search_results=None, search_error=None)

    radius, err = parse_float(request.form.get("service_radius"), "service_radius")
    if err:
        return render_template("index.html", users=users, form_error=err, search_results=None, search_error=None)

    radius_err = validate_radius(radius)
    if radius_err:
        return render_template("index.html", users=users, form_error=radius_err, search_results=None, search_error=None)

    user.name = name
    user.latitude = lat
    user.longitude = lon
    user.service_radius = radius
    db.session.commit()

    return redirect(url_for("views.index"))


# ── Delete User ───────────────────────────────────────────────────────────────
@views.route("/delete-user/<int:user_id>", methods=["POST"])
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for("views.index"))