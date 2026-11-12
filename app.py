import uuid
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file, url_for
from markupsafe import escape

from utils.database import add_request, clear_history, get_history, init_db
from utils.detector import DishDetector
from utils.report_export import export_history_to_excel


app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
RESULT_FOLDER = BASE_DIR / "static" / "results"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
RESULT_FOLDER.mkdir(parents=True, exist_ok=True)

app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

init_db()
model_file = BASE_DIR / "yolov8n.pt"
detector = DishDetector(str(model_file if model_file.exists() else "yolov8n.pt"))


def get_image_size_by_mode(mode: str) -> int:
    modes = {
        "fast": 416,
        "standard": 640,
        "accurate": 960,
    }
    return modes.get(mode, 640)


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({
        "success": False,
        "error": "Размер файла превышает 16 Мбайт.",
    }), 413


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process_image():
    if "image" not in request.files:
        return jsonify({"success": False, "error": "Файл изображения не найден."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"success": False, "error": "Файл не выбран."}), 400

    extension = Path(file.filename).suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        return jsonify({
            "success": False,
            "error": "Поддерживаются только JPG, JPEG, PNG и WEBP.",
        }), 400

    mode = request.form.get("mode", "standard")
    if mode not in {"fast", "standard", "accurate"}:
        mode = "standard"

    try:
        confidence_percent = float(request.form.get("confidence", 35))
    except ValueError:
        confidence_percent = 35

    confidence_percent = max(20, min(confidence_percent, 90))
    confidence = confidence_percent / 100
    image_size = get_image_size_by_mode(mode)

    file_id = uuid.uuid4().hex
    upload_filename = f"{file_id}{extension}"
    result_filename = f"{file_id}_result.jpg"
    upload_path = UPLOAD_FOLDER / upload_filename
    result_path = RESULT_FOLDER / result_filename
    original_filename = Path(file.filename).name[:255]

    file.save(upload_path)

    try:
        stats = detector.detect_dishes(
            input_path=upload_path,
            output_path=result_path,
            confidence=confidence,
            image_size=image_size,
        )
    except ValueError as error:
        upload_path.unlink(missing_ok=True)
        result_path.unlink(missing_ok=True)
        return jsonify({
            "success": False,
            "error": str(error),
        }), 400
    except Exception as error:
        upload_path.unlink(missing_ok=True)
        result_path.unlink(missing_ok=True)
        return jsonify({
            "success": False,
            "error": f"Ошибка при обработке изображения: {error}",
        }), 500

    add_request(
        original_filename=original_filename,
        upload_filename=upload_filename,
        result_filename=result_filename,
        dish_count=stats["count"],
        class_counts=stats["class_counts"],
        average_confidence=stats["average_confidence"],
        processing_time=stats["processing_time"],
        mode=mode,
        image_size=stats["image_size"],
        confidence=stats["confidence"],
    )

    return jsonify({
        "success": True,
        "count": stats["count"],
        "class_counts": stats["class_counts"],
        "average_confidence": stats["average_confidence"],
        "processing_time": stats["processing_time"],
        "image_size": stats["image_size"],
        "confidence": stats["confidence"],
        "mode": mode,
        "image_url": url_for("static", filename=f"results/{result_filename}"),
    })


@app.route("/history", methods=["GET"])
def history():
    records = get_history(limit=20)
    for record in records:
        record["result_url"] = url_for(
            "static", filename=f"results/{record['result_filename']}"
        )
    return jsonify({"success": True, "records": records})


@app.route("/clear-history", methods=["POST"])
def clear_history_route():
    clear_history()
    return jsonify({"success": True, "message": "История очищена."})


@app.route("/export-excel", methods=["GET"])
def export_excel():
    report_path = export_history_to_excel(get_history(limit=1000))
    return send_file(
        report_path,
        as_attachment=True,
        download_name="dish_counter_report.xlsx",
    )


@app.route("/readme", methods=["GET"])
def readme_page():
    readme_path = BASE_DIR / "README.md"
    content = "README.md не найден."
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")

    return f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>README — Dish Counter</title>
        <style>
            body {{ max-width: 900px; margin: 30px auto; padding: 0 20px;
                    font-family: Arial, sans-serif; line-height: 1.6; color: #222; }}
            a {{ color: #2459a9; }}
            pre {{ white-space: pre-wrap; word-wrap: break-word;
                   padding: 20px; background: #f4f6f8; border: 1px solid #d9dee5; }}
        </style>
    </head>
    <body>
        <p><a href="/">← Назад к приложению</a></p>
        <pre>{escape(content)}</pre>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)
