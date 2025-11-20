from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
import bcrypt

from db import users_col

auth_bp = Blueprint("auth", __name__)


def user_to_public(user):
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "role": user.get("role", "user"),
        "banned": user.get("banned", False),
        "createdAt": user.get("createdAt").isoformat() if user.get("createdAt") else None,
    }


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "Dati mancanti"}), 400

    if users_col.find_one({"username": username}):
        return jsonify({"error": "Username già esistente"}), 400

    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    user = {
        "username": username,
        "email": email,
        "passwordHash": pw_hash,
        "role": "user",
        "banned": False,
        "createdAt": datetime.utcnow(),
    }

    result = users_col.insert_one(user)
    user["_id"] = result.inserted_id

    return jsonify({"message": "Registrazione ok", "user": user_to_public(user)}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = users_col.find_one({"username": username})
    if not user:
        return jsonify({"error": "Credenziali non valide"}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user["passwordHash"].encode("utf-8")):
        return jsonify({"error": "Credenziali non valide"}), 401

    if user.get("banned"):
        return jsonify({"error": "Utente bannato"}), 403

    return jsonify({"message": "Login ok", "user": user_to_public(user)}), 200


def get_current_user():
    """
    Legge l'header X-User-Id inviato dalla SPA
    e restituisce l'utente dal DB (o None).
    """
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return None

    try:
        obj_id = ObjectId(user_id)
    except Exception:
        return None

    user = users_col.find_one({"_id": obj_id})
    return user
