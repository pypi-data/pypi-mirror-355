from pathlib import Path
from flask import send_from_directory

from lib.web import app

web_dir = Path(__file__).parent.parent.parent / "web"


@app.route("/", methods=["GET"])
def get_homepage():
    return send_from_directory(web_dir, "index.html")


@app.route("/<path:path>", methods=["GET"])
def get_page(path: str):
    if not path:
        path = "index.html"

    return send_from_directory(web_dir, path)


@app.route("/video/<string:provider>/<string:provider_id>", methods=["GET"])
def get_video(provider: str, provider_id: str):
    return send_from_directory(web_dir, "video_details.html")
