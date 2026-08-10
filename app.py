import os
import psycopg2
import psycopg2.extras
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Vercel/Neon sets this automatically once the database is connected in the dashboard.
DATABASE_URL = os.environ["DATABASE_URL"]

app = Flask(__name__)
CORS(app)


def get_conn():
    # Neon requires SSL - sslmode=require handles that even if the URL doesn't already specify it.
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS enquiries (
                    id SERIAL PRIMARY KEY,
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


@app.route('/robots.txt')
def robots():
    return send_from_directory(BASE_DIR / 'static', 'robots.txt', mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(BASE_DIR / 'static', 'sitemap.xml', mimetype='application/xml')



@app.post('/api/enquiries')
def create_enquiry():
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    phone = (data.get('phone') or '').strip()

    if not name or not email or not phone:
        return jsonify({'error': 'Name, email and phone are required'}), 400

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO enquiries (name, email, phone, grade, subject, interest, message, type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT * FROM enquiries ORDER BY id DESC')
            rows = cur.fetchall()

    return jsonify([dict(row) for row in rows])


@app.delete('/api/enquiries')
def delete_enquiries():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM enquiries')
        conn.commit()

    return jsonify({'success': True})


if __name__ == '__main__':
    app.run(debug=True, port=5000)

