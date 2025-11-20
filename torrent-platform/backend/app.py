from flask import Flask, send_from_directory
from flask_cors import CORS

from auth import auth_bp
from torrents import torrents_bp
from comments import comments_bp
from stats import stats_bp

# static_folder punta alla cartella frontend
app = Flask(__name__, static_folder="../frontend", static_url_path="")

# CORS solo sulle API (non serve più, ma non dà fastidio)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ====== FRONTEND (SPA) ======

@app.route("/")
def index():
    # serve frontend/index.html
    return send_from_directory(app.static_folder, "index.html")


# Se vuoi essere sicuro che JS e CSS vengano serviti:
@app.route("/app.js")
def send_app_js():
    return send_from_directory(app.static_folder, "app.js")


@app.route("/styles.css")
def send_styles_css():
    return send_from_directory(app.static_folder, "styles.css")


# ====== API REST (BACKEND) ======

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(torrents_bp, url_prefix="/api/torrents")
app.register_blueprint(comments_bp, url_prefix="/api/comments")
app.register_blueprint(stats_bp, url_prefix="/api/stats")


if __name__ == "__main__":
    # in Codespaces usiamo 0.0.0.0 e port 5000
    app.run(host="0.0.0.0", port=5000, debug=True)
