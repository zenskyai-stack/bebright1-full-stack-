import sqlite3
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / 'data' / 'enquiries.db'

app = Flask(__name__)
CORS(app)


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS enquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                grade TEXT,
                subject TEXT,
                interest TEXT,
                message TEXT,
                type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


init_db()


@app.route('/')
def home():
    # Important: do NOT use render_template here.
    # Your CSS contains {#loader...}, which Jinja reads as a template comment.
    # Sending the file directly avoids TemplateSyntaxError.
    return send_from_directory(BASE_DIR / 'templates', 'index.html')


@app.post('/api/enquiries')
def create_enquiry():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip()

    if not name or not email or not phone:
        return jsonify({'error': 'Name, email and phone are required'}), 400

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO enquiries (name, email, phone, grade, subject, interest, message, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                email,
                phone,
                data.get('grade', ''),
                data.get('subject', ''),
                data.get('interest', ''),
                data.get('message', ''),
                data.get('type', 'contact'),
            ),
        )
        conn.commit()

    return jsonify({'success': True, 'message': 'Enquiry saved successfully'}), 201


@app.get('/api/enquiries')
def get_enquiries():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM enquiries ORDER BY id DESC').fetchall()
    return jsonify([dict(row) for row in rows])


@app.delete('/api/enquiries')
def delete_enquiries():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('DELETE FROM enquiries')
        conn.commit()
    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
