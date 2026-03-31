from flask import Flask, render_template, request, redirect, send_file, Response
import sqlite3
import csv
from io import StringIO
from datetime import datetime

DB = 'expenses.db'
app = Flask(__name__)


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute(
            'CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT, value REAL, category TEXT, date DATE)'
        )


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        value = request.form.get('value', '0').strip()
        category = request.form.get('category', '').strip()
        date = request.form.get('date', '').strip()
        try:
            value = float(value)
            datetime.strptime(date, '%Y-%m-%d')
            with get_db() as conn:
                conn.execute(
                    'INSERT INTO expenses (description, value, category, date) VALUES (?, ?, ?, ?)',
                    (description, value, category, date),
                )
        except (ValueError, sqlite3.DatabaseError):
            pass
        return redirect('/')

    with get_db() as conn:
        expenses = conn.execute(
            'SELECT * FROM expenses ORDER BY date DESC, id DESC LIMIT 10'
        ).fetchall()
    return render_template('index.html', expenses=expenses)


@app.route('/report')
def report():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT category, SUM(value) AS total FROM expenses WHERE date >= date('now','start of month') GROUP BY category"
        ).fetchall()
    totals = [{'category': row['category'], 'total': row['total']} for row in rows]
    return render_template('report.html', totals=totals)


@app.route('/export')
def export():
    with get_db() as conn:
        rows = conn.execute('SELECT * FROM expenses ORDER BY date DESC').fetchall()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'description', 'value', 'category', 'date'])
    for row in rows:
        writer.writerow([row['id'], row['description'], row['value'], row['category'], row['date']])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=expenses.csv'},
    )


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
