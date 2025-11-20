from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime

from db import comments_col, torrents_col
from auth import get_current_user

comments_bp = Blueprint("comments", __name__)


def comment_to_public(c):
    c["_id"] = str(c["_id"])
    c["torrentId"] = str(c["torrentId"])
    c["userId"] = str(c["userId"])
    if c.get("createdAt"):
        c["createdAt"] = c["createdAt"].isoformat()
    if c.get("updatedAt"):
        c["updatedAt"] = c["updatedAt"].isoformat()
    return c


def recalc_torrent_rating(torrent_id):
    pipeline = [
        {"$match": {"torrentId": torrent_id}},
        {"$group": {"_id": "$torrentId", "avgRating": {"$avg": "$rating"}, "count": {"$sum": 1}}}
    ]
    agg = list(comments_col.aggregate(pipeline))
    if agg:
        ratingAvg = agg[0]["avgRating"]
        ratingCount = agg[0]["count"]
    else:
        ratingAvg = None
        ratingCount = 0

    torrents_col.update_one(
        {"_id": torrent_id},
        {"$set": {"ratingAvg": ratingAvg, "ratingCount": ratingCount}}
    )


@comments_bp.route("/by-torrent/<torrent_id>", methods=["GET"])
def get_comments_for_torrent(torrent_id):
    try:
        t_id = ObjectId(torrent_id)
    except Exception:
        return jsonify({"error": "ID non valido"}), 400

    comments = list(comments_col.find({"torrentId": t_id}).sort("createdAt", 1))
    comments = [comment_to_public(c) for c in comments]
    return jsonify(comments), 200


@comments_bp.route("", methods=["POST"])
def add_comment():
    user = get_current_user()
    if not user:
        return jsonify({"error": "Non autorizzato"}), 401
    if user.get("banned"):
        return jsonify({"error": "Utente bannato"}), 403

    data = request.json or {}
    torrent_id = data.get("torrentId")
    text = data.get("text", "").strip()
    rating = data.get("rating")

    if not torrent_id or not text or rating is None:
        return jsonify({"error": "Dati mancanti"}), 400

    try:
        t_id = ObjectId(torrent_id)
    except Exception:
        return jsonify({"error": "ID torrent non valido"}), 400

    rating = int(rating)
    if rating < 1 or rating > 5:
        return jsonify({"error": "Rating deve essere tra 1 e 5"}), 400

    comment = {
        "torrentId": t_id,
        "userId": user["_id"],
        "text": text[:160],
        "rating": rating,
        "createdAt": datetime.utcnow(),
        "updatedAt": None
    }

    result = comments_col.insert_one(comment)
    comment["_id"] = result.inserted_id

    recalc_torrent_rating(t_id)

    return jsonify(comment_to_public(comment)), 201


@comments_bp.route("/<comment_id>", methods=["PUT"])
def update_comment(comment_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Non autorizzato"}), 401

    try:
        c_id = ObjectId(comment_id)
    except Exception:
        return jsonify({"error": "ID commento non valido"}), 400

    comment = comments_col.find_one({"_id": c_id})
    if not comment:
        return jsonify({"error": "Commento non trovato"}), 404

    if comment["userId"] != user["_id"] and user.get("role") not in ["moderator", "admin"]:
        return jsonify({"error": "Permesso negato"}), 403

    data = request.json or {}
    text = data.get("text")
    rating = data.get("rating")

    update = {"updatedAt": datetime.utcnow()}
    if text is not None:
        update["text"] = text[:160]
    if rating is not None:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return jsonify({"error": "Rating deve essere tra 1 e 5"}), 400
        update["rating"] = rating

    comments_col.update_one({"_id": c_id}, {"$set": update})

    comment = comments_col.find_one({"_id": c_id})
    recalc_torrent_rating(comment["torrentId"])

    return jsonify(comment_to_public(comment)), 200


@comments_bp.route("/<comment_id>", methods=["DELETE"])
def delete_comment(comment_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "Non autorizzato"}), 401

    try:
        c_id = ObjectId(comment_id)
    except Exception:
        return jsonify({"error": "ID commento non valido"}), 400

    comment = comments_col.find_one({"_id": c_id})
    if not comment:
        return jsonify({"error": "Commento non trovato"}), 404

    if comment["userId"] != user["_id"] and user.get("role") not in ["moderator", "admin"]:
        return jsonify({"error": "Permesso negato"}), 403

    comments_col.delete_one({"_id": c_id})

    recalc_torrent_rating(comment["torrentId"])

    return jsonify({"message": "Commento cancellato"}), 200
