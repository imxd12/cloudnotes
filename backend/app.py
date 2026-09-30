from flask import (
    Flask,
    request,
    redirect,
    jsonify,
    send_from_directory,
    send_file
)

from flask_cors import CORS
import jwt
import os
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

def get_current_user():
    auth_header = request.headers.get("Authorization")

    token = None

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]

    if not token:
        token = request.cookies.get("cloudnotes_token")

    if not token:
        return None

    try:
        return jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=["HS256"]
        )
    except jwt.InvalidTokenError:
        return None
from werkzeug.security import check_password_hash, generate_password_hash

from pathlib import Path
from datetime import datetime
import uuid
import io
import boto3
from botocore.exceptions import ClientError

from database import (
    get_db,
    initialize_database
)


# ==========================================
# APP CONFIGURATION
# ==========================================

app = Flask(__name__)

CORS(app, origins=["http://52.66.133.0"])


BASE_DIR = Path(__file__).resolve().parent

UPLOAD_FOLDER = BASE_DIR / "uploads"

UPLOAD_FOLDER.mkdir(
    exist_ok=True
)


app.config["UPLOAD_FOLDER"] = str(
    UPLOAD_FOLDER
)

# AWS S3 Configuration
S3_BUCKET = "cloudnotes-437982993423"
S3_REGION = "ap-south-1"
S3_FOLDER = "notes"

s3 = boto3.client(
    "s3",
    region_name=S3_REGION
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
# REGISTER
# ==========================================

@app.route(
    "/api/register",
    methods=["POST"]
)
def register():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request data is missing"
        }), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({
            "success": False,
            "message": "Name, email and password are required"
        }), 400

    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({
            "success": False,
            "message": "Enter a valid email address"
        }), 400

    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "Password must be at least 6 characters"
        }), 400

    connection = get_db()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    )

    existing_user = cursor.fetchone()

    if existing_user:
        connection.close()
        return jsonify({
            "success": False,
            "message": "An account with this email already exists"
        }), 409

    hashed_password = generate_password_hash(password)

    cursor.execute("""
        INSERT INTO users (name, email, password)
        VALUES (?, ?, ?)
    """, (
        name,
        email,
        hashed_password
    ))

    user_id = cursor.lastrowid
    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Account created successfully",
        "user": {
            "id": user_id,
            "name": name,
            "email": email
        }
    }), 201


# ==========================================
# LOGIN
# ==========================================


# ==========================================
# PROTECTED FRONTEND PAGES
# ==========================================

def serve_protected_page(filename):
    current_user = get_current_user()

    if not current_user:
        return redirect("/index.html")

    return send_from_directory(
        "/home/ubuntu/cloudnotes/frontend",
        filename
    )


@app.route("/dashboard.html")
def protected_dashboard_page():
    return serve_protected_page("dashboard.html")


@app.route("/files.html")
def protected_files_page():
    return serve_protected_page("files.html")


@app.route("/upload.html")
def protected_upload_page():
    return serve_protected_page("upload.html")


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
        SELECT id, name, email, password
        FROM users
        WHERE email = ?
    """, (
        email,
    ))


    user = cursor.fetchone()

    connection.close()


    if user is None or not check_password_hash(user["password"], password):

        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401


    token = jwt.encode(
        {
            "user_id": user["id"],
            "email": user["email"]
        },
        JWT_SECRET_KEY,
        algorithm="HS256"
    )

    response = jsonify({
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    })

    response.set_cookie(
        "cloudnotes_token",
        token,
        httponly=True,
        samesite="Lax",
        secure=False,
        max_age=86400
    )

    return response



# ==========================================
# LOGOUT
# ==========================================

@app.route("/api/logout", methods=["POST"])
def logout():
    response = jsonify({
        "success": True,
        "message": "Logged out successfully"
    })

    response.delete_cookie(
        "cloudnotes_token",
        samesite="Lax"
    )

    return response


# ==========================================
# GET ALL FILES
# ==========================================

@app.route("/api/files", methods=["GET"])
def get_files():
    current_user = get_current_user()

    if not current_user:
        return jsonify({
            "success": False,
            "message": "Authentication required"
        }), 401

    connection = get_db()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *
        FROM files
        WHERE uploaded_by = ?
        ORDER BY upload_date DESC
    """, (str(current_user["user_id"]),))


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
    current_user = get_current_user()

    if not current_user:
        return jsonify({"success": False, "message": "Authentication required"}), 401


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


    uploaded_by = str(current_user["user_id"])


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

    # Upload PDF to Amazon S3
    s3_key = f"{S3_FOLDER}/{stored_filename}"

    s3.upload_fileobj(
        file,
        S3_BUCKET,
        s3_key,
        ExtraArgs={
            "ContentType": "application/pdf"
        }
    )

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

@app.route("/api/files/<int:file_id>/download", methods=["GET"])
def download_file(file_id):
    current_user = get_current_user()

    if not current_user:
        return jsonify({
            "success": False,
            "message": "Authentication required"
        }), 401

    connection = get_db()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT *
        FROM files
        WHERE id = ?
        AND uploaded_by = ?
    """, (
        file_id,
        str(current_user["user_id"]),
    ))


    file = cursor.fetchone()

    connection.close()


    if file is None:

        return jsonify({
            "success": False,
            "message": "File not found"
        }), 404


    s3_key = f"{S3_FOLDER}/{file['stored_filename']}"

    s3_object = s3.get_object(
        Bucket=S3_BUCKET,
        Key=s3_key
    )

    return send_file(
        io.BytesIO(s3_object["Body"].read()),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=file["filename"]
    )


# ==========================================
# DELETE FILE
# ==========================================

@app.route("/api/files/<int:file_id>", methods=["DELETE"])

def delete_file(file_id):

    current_user = get_current_user()

    if not current_user:
        return jsonify({
            "success": False,
            "message": "Authentication required"
        }), 401

    connection = get_db()

    cursor = connection.cursor()


    cursor.execute("""
        SELECT stored_filename
        FROM files
        WHERE id = ?
        AND uploaded_by = ?
    """, (
        file_id,
        str(current_user["user_id"]),
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
        AND uploaded_by = ?
    """, (
        file_id,
        str(current_user["user_id"]),
    ))


    connection.commit()

    connection.close()


    s3_key = f"{S3_FOLDER}/{stored_filename}"

    try:
        s3.delete_object(
            Bucket=S3_BUCKET,
            Key=s3_key
        )
    except ClientError as e:
        print(f"S3 delete error: {e}")

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

    current_user = get_current_user()

    if not current_user:
        return jsonify({
            "success": False,
            "message": "Authentication required"
        }), 401

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
        debug=False
    )
