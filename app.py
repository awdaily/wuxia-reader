"""Local dev server. Vercel deployment uses api/fetch.py instead."""
import os
import sys

from flask import Flask, request, jsonify, send_from_directory

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api"))
from fetch import fetch_chapter  # type: ignore

ROOT = os.path.dirname(__file__)
app = Flask(__name__)


@app.route("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.route("/api/fetch", methods=["POST"])
def api_fetch():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    if not url or not url.startswith("http"):
        return jsonify({"error": "URL ไม่ถูกต้อง"}), 400
    result, status = fetch_chapter(url)
    return jsonify(result), status


if __name__ == "__main__":
    app.run(debug=True, port=5000)
