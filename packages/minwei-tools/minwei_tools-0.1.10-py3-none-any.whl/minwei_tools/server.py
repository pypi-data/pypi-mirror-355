import zipfile
import os
import io

from flask import Flask, send_file, render_template_string, request, jsonify

app = Flask(__name__)

BASE_DIR = "D:/"

TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>File Transfer Server</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="container mt-4">
    <h2>📁 MinWei File Transfer Server</h2>

    <!-- 導覽按鈕 -->
    <div class="mb-3">
        <a href="/" class="btn btn-secondary btn-sm">🏠 首頁</a>
        {% if parent_path is not none %}
            <a href="/?path={{ parent_path }}" class="btn btn-secondary btn-sm">⬅️ 上一層</a>
        {% endif %}
    </div>

    <form id="downloadForm" method="POST" action="/download_zip">
        <ul class="list-group mt-3">
            {% for f in files %}
            <li class="list-group-item d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center">
                    <input type="checkbox" name="files" value="{{ current_path }}/{{ f['name'] }}" class="me-2">
                    {% if f['is_dir'] %}
                        <a href="/?path={{ current_path }}/{{ f['name'] }}">📂 {{ f['name'] }}</a>
                    {% else %}
                        <span>📄 {{ f['name'] }}</span>
                    {% endif %}
                </div>
                {% if not f['is_dir'] %}
                    <a href="/download?path={{ current_path }}/{{ f['name'] }}" class="btn btn-sm btn-primary">Download</a>
                {% endif %}
            </li>
            {% endfor %}
        </ul>
        <button type="submit" class="btn btn-success mt-3">Download Selected</button>
    </form>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    rel_path = request.args.get("path", "").strip("/")
    abs_path = os.path.join(BASE_DIR, rel_path)

    if not os.path.exists(abs_path):
        return "Path not found", 404

    # 計算 parent path
    if rel_path:
        parent = os.path.dirname(rel_path)
        # 明確處理 parent 是空字串的情況（代表根目錄）
        parent_path = parent if parent != rel_path else ""
    else:
        parent_path = None  # 已在根目錄

    items = []
    for entry in os.scandir(abs_path):
        items.append({"name": entry.name, "is_dir": entry.is_dir()})

    return render_template_string(
        TEMPLATE,
        files=items,
        current_path=rel_path,
        parent_path=parent_path
    )

@app.route("/download", methods=["GET"])
def download_file():
    rel_path = request.args.get("path", "").strip("/")
    abs_path = os.path.join(BASE_DIR, rel_path)

    if not os.path.isfile(abs_path):
        return "File not found", 404

    return send_file(abs_path, as_attachment=True)

@app.route("/download_zip", methods=["POST"])
def download_zip():
    file_paths = request.form.getlist("files")
    if not file_paths:
        return "No files selected", 400

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for rel_path in file_paths:
            abs_path = os.path.join(BASE_DIR, rel_path)
            if os.path.exists(abs_path):
                if os.path.isfile(abs_path):
                    zipf.write(abs_path, arcname=os.path.relpath(abs_path, BASE_DIR))
                elif os.path.isdir(abs_path):
                    for root, dirs, files in os.walk(abs_path):
                        for file in files:
                            full_path = os.path.join(root, file)
                            arcname = os.path.relpath(full_path, BASE_DIR)
                            zipf.write(full_path, arcname=arcname)

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name="files.zip")

if __name__ == "__main__":
    import argparse
    import colorama
    
    parser = argparse.ArgumentParser(description="MinWei File Transfer Server")
    parser.add_argument("-p", "--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="localhost", help="Host to run the server on")
    parser.add_argument("--debug", action="store_true", help="Run the server in debug mode")
    parser.add_argument("-d", "--base_dir", type=str, default=".", help="Base directory to serve files from")
    args = parser.parse_args()
    BASE_DIR = os.path.abspath(args.base_dir)
    if not os.path.exists(BASE_DIR):
        raise FileNotFoundError(f"Base directory '{BASE_DIR}' does not exist.")
    
    if not os.path.isdir(BASE_DIR):
        raise NotADirectoryError(f"Base directory '{BASE_DIR}' is not a directory.")
    
    if not os.access(BASE_DIR, os.R_OK):
        raise PermissionError(f"Base directory '{BASE_DIR}' is not readable.")
    
    print(f"\n * Starting {colorama.Back.YELLOW}MinWei File Transfer Server{colorama.Style.RESET_ALL} at {colorama.Back.YELLOW}{colorama.Fore.BLACK}http://{args.host}:{args.port}{colorama.Style.RESET_ALL} with base directory {colorama.Back.YELLOW}{colorama.Fore.BLACK}{BASE_DIR}{colorama.Style.RESET_ALL}")
    
    app.run(host=args.host, port=args.port, debug=args.debug)
    
    # app.run(host=args.host, port=args.port, debug=args.debug)