from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image, ImageEnhance
import pytesseract
import re
import os
import mysql.connector

# Set Tesseract path (✅ yours is correct)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ✅ MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Tashini258258",
    database="AttendanceDB"
)
cursor = db.cursor()

# ✅ OCR function
def extract_nic(img_path):
    try:
        img = Image.open(img_path)
        img = img.convert('L')
        img = img.resize((img.width * 2, img.height * 2))
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        text = pytesseract.image_to_string(img, config='--psm 6 -c tessedit_char_whitelist=0123456789VXvx')
        print("🔍 OCR Output:", text)
        match = re.search(r'\b\d{9}[VvXx]?\b|\b\d{12}\b', text)
        return match.group(0).upper() if match else None
    except Exception as e:
        print("❌ OCR error:", e)
        return None

# ✅ Home
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    action = request.form.get('action', '').lower()
    nic = None

    if 'id_card' in request.files:
        file = request.files['id_card']
        if file.filename:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            nic = extract_nic(path)

    if not nic:
        return jsonify({"message": "NIC not found."}), 422

    today = datetime.today().date()
    now = datetime.now().time()

    try:
        if action == 'in':
            cursor.execute("INSERT INTO AttendanceRecords (NIC, Date, InTime) VALUES (%s, %s, %s)", (nic, today, now))
        elif action == 'out':
            cursor.execute("UPDATE AttendanceRecords SET OutTime = %s WHERE NIC = %s AND Date = %s AND OutTime IS NULL ORDER BY InTime DESC LIMIT 1", (now, nic, today))
            if cursor.rowcount == 0:
                return jsonify({"message": "No IN record found for this NIC."}), 400
        else:
            return jsonify({"message": "Invalid action."}), 400

        db.commit()
        return jsonify({"message": f"{action.upper()} recorded for NIC: {nic}"})
    except Exception as e:
        db.rollback()
        return jsonify({"message": f"Database error: {str(e)}"}), 500


 

    # First try OCR
    if 'id_card' in request.files:
        file = request.files['id_card']
        if file.filename:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            nic = extract_nic(path)

    # Fallback to manual
    if not nic:
        nic = request.form.get('nic_manual')
 

    if not nic:
        return jsonify({"message": "NIC not found. Please enter manually."}), 422

    today = datetime.today().date()
    now = datetime.now().time()

    try:
        if action == 'in':
            cursor.execute("""
                INSERT INTO AttendanceRecords (NIC, Date, InTime)
                VALUES (%s, %s, %s)
            """, (nic, today, now))
        elif action == 'out':
            cursor.execute("""
                UPDATE AttendanceRecords
                SET OutTime = %s
                WHERE NIC = %s AND Date = %s AND OutTime IS NULL
                ORDER BY InTime DESC LIMIT 1
            """, (now, nic, today))
            if cursor.rowcount == 0:
                return jsonify({"message": "No IN record found for this NIC."}), 400
        else:
            return jsonify({"message": "Invalid action. Choose IN or OUT."}), 400

        db.commit()
        return jsonify({"message": f"{action.upper()} recorded for NIC: {nic}"})
    except Exception as e:
        db.rollback()
        return jsonify({"message": f"Database error: {str(e)}"}), 500


if __name__ == '__main__':
    print("✅ Flask server running...")
    app.run(debug=True)