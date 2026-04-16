import os
import sqlite3
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure the upload folder exists
if not os.path.exists('static/uploads'):
    os.makedirs('static/uploads')

def init_db():
    conn = sqlite3.connect('database.db')
    # Updated table structure for the full app cycle
    conn.execute('''CREATE TABLE IF NOT EXISTS reports 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  animal TEXT, injury TEXT, location TEXT, 
                  image TEXT, first_aid TEXT, status TEXT,
                  lat TEXT, lon TEXT, rescue_image TEXT)''')
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/report', methods=['POST'])
def report():
    animal = request.form.get('animal_type')
    injury = request.form.get('injury')
    location = request.form.get('location')
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    photo = request.files.get('photo')

    if photo:
        filename = secure_filename(photo.filename)
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        filename = "no_image.png"

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reports (animal, injury, location, image, first_aid, status, lat, lon) VALUES (?,?,?,?,?,?,?,?)",
                 (animal, injury, location, filename, "Check Track Page", 'Pending', lat, lon))
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return render_template('success.html', report_id=report_id)

@app.route('/admin')
def admin():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Fetch all reports
    reports = cursor.execute("SELECT * FROM reports ORDER BY id DESC").fetchall()
    
    # Calculate Statistics for the Dashboard
    total = len(reports)
    rescued = len([r for r in reports if r[6] == 'RESCUED'])
    pending = total - rescued
    
    conn.close()
    return render_template('admin.html', reports=reports, total=total, rescued=rescued, pending=pending)

@app.route('/track/<int:id>')
def track(id):
    conn = sqlite3.connect('database.db')
    report = conn.execute("SELECT * FROM reports WHERE id = ?", (id,)).fetchone()
    conn.close()
    return render_template('track.html', report=report)

@app.route('/upload_rescue/<int:id>', methods=['POST'])
def upload_rescue(id):
    photo = request.files.get('rescue_photo')
    if photo:
        filename = "rescue_" + secure_filename(photo.filename)
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        conn = sqlite3.connect('database.db')
        conn.execute("UPDATE reports SET status = 'RESCUED', rescue_image = ? WHERE id = ?", (filename, id))
        conn.commit()
        conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)