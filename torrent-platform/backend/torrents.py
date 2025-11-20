from flask import Blueprint, request, jsonify, send_file
from bson import ObjectId
from datetime import datetime
import os

from db import torrents_col, downloads_col
from auth import get_current_user

torrents_bp = Blueprint("torrents", __name__)

TORRENTS_DIR = os.getenv("TORRENTS_DIR", "torrents_files")


def torrent_to_public(t):
    t["_id"] = str(t["_id"])
    if "uploadedBy" in t:
        t["uploadedBy"] = str(t["uploadedBy"])
    return t


@torrents_bp.route("", methods=["GET"])
def search_torrents():
    title = request.args.get("title")
    desc = request.args.get("desc")
    categories = request.args.getlist("category")
    after = request.args.get("after")
    before = request.args.get("before")
    sort = request.args.get("sort", "date")  # "date" | "size"
    order = request.args.get("order", "desc")  # "asc" | "desc"

    query = {}

    if title:
        query["title"] = {"$regex": title, "$options": "i"}

    if desc:
        query["description"] = {"$regex": desc, "$options": "i"}

    if categories:
        query["categories"] = {"$in": categories}

    date_filter = {}
    if after:
        try:
            date_filter["$gte"] = datetime.fromisoformat(after)
        except Exception:
            pass
    if before:
        try:
            date_filter["$lte"] = datetime.fromisoformat(before)
        except Exception:
            pass
    if date_filter:
        query["uploadDate"] = date_filter

    if sort == "size":
        sort_field = "sizeBytes"
    else:
        sort_field = "uploadDate"

    sort_order = 1 if order == "asc" else -1

    torrents = list(torrents_col.find(query).sort(sort_field, sort_order))
    torrents = [torrent_to_public(t) for t in torrents]
    return jsonify(torrents), 200


@torrents_bp.route("/<torrent_id>", methods=["GET"])
def get_torrent_detail(torrent_id):
    try:
        obj_id = ObjectId(torrent_id)
    except Exception:
        return jsonify({"error": "ID non valido"}), 400

    torrent = torrents_col.find_one({"_id": obj_id})
    if not torrent:
        return jsonify({"error": "Torrent non trovato"}), 404

    return jsonify(torrent_to_public(torrent)), 200


@torrents_bp.route("", methods=["POST"])
def create_torrent():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Non autorizzato"}), 401
    if user.get("banned"):
        return jsonify({"error": "Utente bannato"}), 403

    data = request.json or {}
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()[:160]
    sizeBytes = data.get("sizeBytes")
    categories = data.get("categories", [])
    images = data.get("images", [])
    torrentFileName = data.get("torrentFileName")  # nome del file .torrent sul server

    if not title or sizeBytes is None:
        return jsonify({"error": "Dati obbligatori mancanti"}), 400

    torrent = {
        "title": title,
        "description": description,
        "sizeBytes": int(sizeBytes),
        "categories": categories,
        "images": images,
        "uploadDate": datetime.utcnow(),
        "uploadedBy": user["_id"],
        "torrentFilePath": os.path.join(TORRENTS_DIR, torrentFileName) if torrentFileName else None,
        "ratingAvg": None,
        "ratingCount": 0
    }

    result = torrents_col.insert_one(torrent)
    torrent["_id"] = result.inserted_id
    return jsonify(torrent_to_public(torrent)), 201


@torrents_bp.route("/<torrent_id>", methods=["DELETE"])
def delete_torrent(torrent_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Non autorizzato"}), 401
    if user.get("role") not in ["moderator", "admin"]:
        return jsonify({"error": "Permesso negato"}), 403

    try:
        obj_id = ObjectId(torrent_id)
    except Exception:
        return jsonify({"error": "ID non valido"}), 400

    result = torrents_col.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Torrent non trovato"}), 404

    return jsonify({"message": "Torrent cancellato"}), 200


@torrents_bp.route("/<torrent_id>/download", methods=["GET"])
def download_torrent(torrent_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Solo utenti registrati possono scaricare"}), 401
    if user.get("banned"):
        return jsonify({"error": "Utente bannato"}), 403

    try:
        obj_id = ObjectId(torrent_id)
    except Exception:
        return jsonify({"error": "ID non valido"}), 400

    torrent = torrents_col.find_one({"_id": obj_id})
    if not torrent:
        return jsonify({"error": "Torrent non trovato"}), 404

    # registra download
    downloads_col.insert_one(
        {
            "torrentId": torrent["_id"],
            "userId": user["_id"],
            "downloadedAt": datetime.utcnow()
        }
    )

    file_path = torrent.get("torrentFilePath")
    if not file_path or not os.path.exists(file_path):
        return jsonify({"message": "Download registrato, ma file torrent non presente sul server"}), 200

    return send_file(file_path, as_attachment=True)
