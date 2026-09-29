from flask import (
    Flask,
    request,
    jsonify,
    send_from_directory
)

from flask_cors import CORS

from pathlib import Path
from datetime import datetime
import uuid

from database import (
    get_db,
    initialize_database
)


# ==========================================
# APP CONFIGURATION
# ==========================================

app = Flask(__name__)

CORS(app)


BASE_DIR = Path(__file__).resolve().parent

UPLOAD_FOLDER = BASE_DIR / "uploads"

UPLOAD_FOLDER.mkdir(
    exist_ok=True
)


app.config["UPLOAD_FOLDER"] = str(
    UPLOAD_FOLDER
)


# ==========================================
# ALLOWED FILES
# ==========================================

ALLOWED_EXTENSIONS = {
    "pdf"
}


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ==========================================
# HOME
# ==========================================

@app.route("/")
def home():

    return jsonify({
        "application": "CloudNotes",
        "message": "CloudNotes API is running",
        "status": "success"
    })


# ==========================================
# HEALTH CHECK
# ==========================================

@app.route("/api/health")
def health():

    return jsonify({
        "status": "healthy",
        "database": "SQLite"
    })


# ==========================================
# LOGIN
# ==========================================

@app.route(
    "/api/login",
    methods=["POST"]
)
def login():

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "Request data is missing"
        }), 400


    email = data.get("email", "").strip()

    password = data.get("password", "")


    if not email or not password:

        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400


    connection = get_db()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT id, name, email
        FROM users
        WHERE email = ?
        AND password = ?
    """, (
        email,
        password
    ))


    user = cursor.fetchone()

    connection.close()


    if user is None:

        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401


    return jsonify({

        "success": True,

        "message": "Login successful",

        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }

    })


# ==========================================
# GET ALL FILES
# ==========================================

@app.route(
    "/api/files",
    methods=["GET"]
)
def get_files():

    connection = get_db()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *
        FROM files
        ORDER BY upload_date DESC
    """)


    rows = cursor.fetchall()

    connection.close()


    files = []


    for row in rows:

        files.append({

            "id": row["id"],

            "title": row["title"],

            "subject": row["subject"],

            "description":
                row["description"],

            "filename":
                row["filename"],

            "uploadedBy":
                row["uploaded_by"],

            "date":
                row["upload_date"],

            "size":
                row["size"]

        })


    return jsonify({
        "success": True,
        "files": files
    })


# ==========================================
# UPLOAD FILE
# ==========================================

@app.route(
    "/api/files",
    methods=["POST"]
)
def upload_file():

    title = request.form.get(
        "title",
        ""
    ).strip()


    subject = request.form.get(
        "subject",
        ""
    ).strip()


    description = request.form.get(
        "description",
        ""
    ).strip()


    uploaded_by = request.form.get(
        "uploadedBy",
        "Imad Khan"
    ).strip()


    file = request.files.get(
        "file"
    )


    # Validate fields

    if not title:

        return jsonify({
            "success": False,
            "message": "Title is required"
        }), 400


    if not subject:

        return jsonify({
            "success": False,
            "message": "Subject is required"
        }), 400


    if file is None:

        return jsonify({
            "success": False,
            "message": "Please select a file"
        }), 400


    if file.filename == "":

        return jsonify({
            "success": False,
            "message": "Invalid filename"
        }), 400


    if not allowed_file(file.filename):

        return jsonify({
            "success": False,
            "message": "Only PDF files are allowed"
        }), 400


    # Check size

    file.seek(0, 2)

    file_size = file.tell()

    file.seek(0)


    max_size = 10 * 1024 * 1024


    if file_size > max_size:

        return jsonify({
            "success": False,
            "message": "File must be smaller than 10 MB"
        }), 400


    # Generate safe stored filename

    original_name = file.filename

    extension = original_name.rsplit(
        ".",
        1
    )[1].lower()


    stored_filename = (
        str(uuid.uuid4())
        + "."
        + extension
    )


    save_path = (
        UPLOAD_FOLDER
        / stored_filename
    )


    file.save(save_path)


    size_mb = round(
        file_size / (1024 * 1024),
        2
    )


    upload_date = (
        datetime.now()
        .strftime("%Y-%m-%d")
    )


    # Store metadata

    connection = get_db()

    cursor = connection.cursor()


    cursor.execute("""
        INSERT INTO files
        (
            title,
            subject,
            description,
            filename,
            stored_filename,
            uploaded_by,
            upload_date,
            size
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        title,
        subject,
        description,
        original_name,
        stored_filename,
        uploaded_by,
        upload_date,
        size_mb

    ))


    file_id = cursor.lastrowid


    connection.commit()

    connection.close()


    return jsonify({

        "success": True,

        "message":
            "File uploaded successfully",

        "file": {

            "id": file_id,

            "title": title,

            "subject": subject,

            "filename": original_name,

            "uploadedBy": uploaded_by,

            "date": upload_date,

            "size": size_mb

        }

    }), 201


# ==========================================
# DOWNLOAD FILE
# ==========================================

@app.route(
    "/api/files/<int:file_id>/download",
    methods=["GET"]
)
def download_file(file_id):

    connection = get_db()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *
        FROM files
        WHERE id = ?
    """, (
        file_id,
    ))


    file = cursor.fetchone()

    connection.close()


    if file is None:

        return jsonify({
            "success": False,
            "message": "File not found"
        }), 404


    return send_from_directory(

        app.config["UPLOAD_FOLDER"],

        file["stored_filename"],

        as_attachment=True,

        download_name=file["filename"]

    )


# ==========================================
# DELETE FILE
# ==========================================

@app.route(
    "/api/files/<int:file_id>",
    methods=["DELETE"]
)
def delete_file(file_id):

    connection = get_db()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT stored_filename
        FROM files
        WHERE id = ?
    """, (
        file_id,
    ))


    file = cursor.fetchone()


    if file is None:

        connection.close()

        return jsonify({
            "success": False,
            "message": "File not found"
        }), 404


    stored_filename = file[
        "stored_filename"
    ]


    cursor.execute("""
        DELETE FROM files
        WHERE id = ?
    """, (
        file_id,
    ))


    connection.commit()

    connection.close()


    file_path = (
        UPLOAD_FOLDER
        / stored_filename
    )


    if file_path.exists():

        file_path.unlink()


    return jsonify({

        "success": True,

        "message":
            "File deleted successfully"

    })


# ==========================================
# DASHBOARD STATISTICS
# ==========================================

@app.route(
    "/api/dashboard",
    methods=["GET"]
)
def dashboard():

    connection = get_db()

    cursor = connection.cursor()


    cursor.execute(
        "SELECT COUNT(*) AS total FROM files"
    )

    total_files = cursor.fetchone()[
        "total"
    ]


    cursor.execute("""
        SELECT COUNT(*)
        AS total
        FROM files
        WHERE uploaded_by = ?
    """, (
        "Imad Khan",
    ))

    my_uploads = cursor.fetchone()[
        "total"
    ]


    cursor.execute("""
        SELECT COALESCE(
            SUM(size),
            0
        ) AS total_size
        FROM files
    """)

    storage_used = cursor.fetchone()[
        "total_size"
    ]


    cursor.execute("""
        SELECT COUNT(
            DISTINCT subject
        ) AS total
        FROM files
    """)

    total_subjects = cursor.fetchone()[
        "total"
    ]


    connection.close()


    return jsonify({

        "success": True,

        "stats": {

            "totalFiles":
                total_files,

            "myUploads":
                my_uploads,

            "storageUsed":
                round(
                    storage_used,
                    2
                ),

            "totalSubjects":
                total_subjects

        }

    })


# ==========================================
# START SERVER
# ==========================================

if __name__ == "__main__":

    initialize_database()

    print()
    print("==============================")
    print("      CLOUDNOTES API")
    print("==============================")
    print("Database: SQLite")
    print("Server: http://127.0.0.1:5000")
    print("==============================")
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )