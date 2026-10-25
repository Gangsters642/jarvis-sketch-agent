from flask import Flask, jsonify, render_template, request, send_file
from engine.svg_engine import generate_sketch
from engine.exporter import (
    get_safe_sketch_path,
    list_saved_sketches,
    open_in_android_app,
    save_sketch,
)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json(silent=True) or {}
    raw_code = data.get("code", "")
    fmt = data.get("format", "svg")
    sketch_name = data.get("name", "jarvis_sketch")
    save_file = data.get("save", True)

    ok, msg, svg_content = generate_sketch(raw_code, fmt)
    if not ok:
        return jsonify({"success": False, "message": msg}), 400

    file_info = None
    if save_file:
        file_info = save_sketch(svg_content, sketch_name)

    return jsonify(
        {
            "success": True,
            "message": msg,
            "svg": svg_content,
            "file_info": file_info,
        }
    )


@app.route("/api/projects", methods=["GET"])
def api_projects():
    return jsonify({"success": True, "projects": list_saved_sketches()})


@app.route("/api/projects/<filename>", methods=["GET"])
def api_load_project(filename):
    path = get_safe_sketch_path(filename)
    if not path:
        return jsonify({"success": False, "message": "Project file nahi mili."}), 404
    svg_text = path.read_text(encoding="utf-8")
    return jsonify(
        {
            "success": True,
            "filename": path.name,
            "svg": svg_text,
        }
    )


@app.route("/api/download/<filename>", methods=["GET"])
def api_download(filename):
    path = get_safe_sketch_path(filename)
    if not path:
        return jsonify({"success": False, "message": "File nahi mili."}), 404
    return send_file(path, mimetype="image/svg+xml", as_attachment=True, download_name=path.name)


@app.route("/api/open-android", methods=["POST"])
def api_open_android():
    data = request.get_json(silent=True) or {}
    filename = data.get("filename", "")
    ok, msg = open_in_android_app(filename)
    status = 200 if ok else 400
    return jsonify({"success": ok, "message": msg}), status


if __name__ == "__main__":
    print("==========================================")
    print(" JARVIS SKETCH AGENT ONLINE")
    print(" Open in Android Browser: http://127.0.0.1:5000")
    print("==========================================")
    app.run(host="127.0.0.1", port=5000, debug=False)
