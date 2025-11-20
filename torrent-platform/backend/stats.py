from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta

from db import downloads_col, torrents_col
from auth import get_current_user

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/top-torrents", methods=["GET"])
def top_torrents():
    user = get_current_user()
    if not user or user.get("role") != "admin":
        return jsonify({"error": "Solo admin"}), 403

    by = request.args.get("by", "downloads")  # "downloads" | "rating"
    limit = int(request.args.get("limit", 10))

    if by == "downloads":
        pipeline = [
            {"$group": {"_id": "$torrentId", "downloadCount": {"$sum": 1}}},
            {"$sort": {"downloadCount": -1}},
            {"$limit": limit}
        ]
        agg = list(downloads_col.aggregate(pipeline))
        result = []
        for row in agg:
            torrent = torrents_col.find_one({"_id": row["_id"]}, {"title": 1})
            result.append(
                {
                    "torrentId": str(row["_id"]),
                    "title": torrent["title"] if torrent else "N/A",
                    "downloadCount": row["downloadCount"]
                }
            )
        return jsonify(result), 200

    elif by == "rating":
        torrents = list(
            torrents_col.find({"ratingCount": {"$gt": 0}}).sort("ratingAvg", -1).limit(limit)
        )
        result = [
            {
                "torrentId": str(t["_id"]),
                "title": t["title"],
                "ratingAvg": t.get("ratingAvg"),
                "ratingCount": t.get("ratingCount")
            }
            for t in torrents
        ]
        return jsonify(result), 200

    else:
        return jsonify({"error": "Valore 'by' non valido"}), 400


@stats_bp.route("/new-torrents-per-category", methods=["GET"])
def new_torrents_per_category():
    user = get_current_user()
    if not user or user.get("role") != "admin":
        return jsonify({"error": "Solo admin"}), 403

    days = int(request.args.get("days", 7))
    since = datetime.utcnow() - timedelta(days=days)

    pipeline = [
        {"$match": {"uploadDate": {"$gte": since}}},
        {"$unwind": "$categories"},
        {"$group": {"_id": "$categories", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]

    agg = list(torrents_col.aggregate(pipeline))
    result = [{"category": row["_id"], "count": row["count"]} for row in agg]
    return jsonify(result), 200


@stats_bp.route("/popular-categories", methods=["GET"])
def popular_categories():
    user = get_current_user()
    if not user or user.get("role") != "admin":
        return jsonify({"error": "Solo admin"}), 403

    from_str = request.args.get("from")
    to_str = request.args.get("to")

    date_filter = {}
    if from_str:
        try:
            date_filter["$gte"] = datetime.fromisoformat(from_str)
        except Exception:
            pass
    if to_str:
        try:
            date_filter["$lte"] = datetime.fromisoformat(to_str)
        except Exception:
            pass

    match_stage = {}
    if date_filter:
        match_stage["uploadDate"] = date_filter

    pipeline = []
    if match_stage:
        pipeline.append({"$match": match_stage})

    pipeline.extend(
        [
            {"$unwind": "$categories"},
            {"$group": {"_id": "$categories", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
    )

    agg = list(torrents_col.aggregate(pipeline))
    result = [{"category": row["_id"], "count": row["count"]} for row in agg]
    return jsonify(result), 200
