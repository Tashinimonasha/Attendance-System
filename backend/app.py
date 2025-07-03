from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, make_response
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from PIL import Image, ImageEnhance
import pytesseract
import re
import os
import mysql.connector
import webbrowser
import threading
import hashlib
from functools import wraps
import logging

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)
app.secret_key = 'printcare_admin_secret_key_2025'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database connection with error handling
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Tashini258258",
        database="AttendanceDB"
    )
    cursor = db.cursor()
    print("✅ Database connected successfully")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    db = None
    cursor = None

# Enhanced security configuration
ADMIN_CONFIG = {
    'username': 'admin',
    'password_hash': hashlib.sha256('printcare2025'.encode()).hexdigest(),
    'session_timeout': 480,  # 8 hours (480 minutes)
    'max_failed_attempts': 3,
    'lockout_duration': 15  # minutes
}

# Security tracking
security_log = []
failed_attempts = {}
locked_accounts = {}

def log_security_event(event_type, details="", ip_address="unknown"):
    """Log security events"""
    event = {
        'timestamp': datetime.now(),
        'type': event_type,
        'details': details,
        'ip_address': ip_address
    }
    security_log.append(event)
    print(f"🔒 SECURITY LOG: {event_type} - {details}")

def check_account_lockout(username):
    """Check if account is locked"""
    if username in locked_accounts:
        lockout_time = locked_accounts[username]
        if datetime.now() < lockout_time:
            return True
        else:
            del locked_accounts[username]
    return False

def security_required(f):
    """Decorator for secure admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            log_security_event('UNAUTHORIZED_ACCESS', f'Attempt to access {request.endpoint}')
            return redirect(url_for('admin_login'))
        
        # Check session timeout
        if 'admin_login_time' in session:
            login_time = datetime.fromisoformat(session['admin_login_time'])
            if datetime.now() - login_time > timedelta(minutes=ADMIN_CONFIG['session_timeout']):
                session.clear()
                log_security_event('SESSION_TIMEOUT', 'Admin session expired')
                flash('Session expired for security. Please login again.', 'warning')
                return redirect(url_for('admin_login'))
        
        return f(*args, **kwargs)
    return decorated_function

def verify_admin_credentials(username, password):
    """Enhanced admin verification with security features"""
    # Check account lockout
    if check_account_lockout(username):
        log_security_event('LOCKOUT_ATTEMPT', f'Login attempt on locked account: {username}')
        return False
    
    # Verify credentials
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    is_valid = (username == ADMIN_CONFIG['username'] and 
                password_hash == ADMIN_CONFIG['password_hash'])
    
    if not is_valid:
        # Track failed attempts
        if username not in failed_attempts:
            failed_attempts[username] = []
        
        failed_attempts[username].append(datetime.now())
        
        # Clean old attempts (older than 1 hour)
        failed_attempts[username] = [
            attempt for attempt in failed_attempts[username]
            if datetime.now() - attempt < timedelta(hours=1)
        ]
        
        # Lock account if too many failures
        if len(failed_attempts[username]) >= ADMIN_CONFIG['max_failed_attempts']:
            lockout_until = datetime.now() + timedelta(minutes=ADMIN_CONFIG['lockout_duration'])
            locked_accounts[username] = lockout_until
            log_security_event('ACCOUNT_LOCKED', f'Account {username} locked due to failed attempts')
        
        log_security_event('LOGIN_FAILED', f'Failed login attempt for: {username}')
        return False
    else:
        # Clear failed attempts on successful login
        if username in failed_attempts:
            del failed_attempts[username]
        log_security_event('LOGIN_SUCCESS', f'Successful admin login: {username}')
        return True

def extract_nic_from_text(text):
    """Extract NIC from OCR text using regex patterns"""
    if not text:
        return None
        
    # Clean text - remove spaces and normalize
    cleaned_text = ''.join(text.replace('\n', ' ').replace('\r', ' ').split()).upper()
    print(f"Cleaned text: {cleaned_text}")
    
    # Old NIC format: 9 digits + V/X
    old_nic_match = re.search(r'(\d{9})[VX]', cleaned_text)
    if old_nic_match:
        result = old_nic_match.group(0)
        print(f"✅ Old NIC found: {result}")
        return result
    
    # New NIC format: 12 digits
    new_nic_match = re.search(r'\b(\d{12})\b', cleaned_text)
    if new_nic_match:
        result = new_nic_match.group(1)
        print(f"✅ New NIC found: {result}")
        return result
    
    print("❌ No NIC pattern found")
    return None

def extract_nic(img_path):
    """Simple NIC extraction from image"""
    try:
        print(f"🔍 Processing image: {img_path}")
        img = Image.open(img_path)
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Enhance image for better OCR
        enhanced_img = ImageEnhance.Contrast(img).enhance(2.0)
        enhanced_img = ImageEnhance.Sharpness(enhanced_img).enhance(1.5)
        enhanced_img = enhanced_img.convert('L')  # Convert to grayscale
        
        # Extract text using Tesseract
        text = pytesseract.image_to_string(enhanced_img, 
            config='--psm 6 -c tessedit_char_whitelist=0123456789VXvx --dpi 200')
        
        print(f"OCR Text: {text.strip()}")
        
        # Extract NIC from text
        nic = extract_nic_from_text(text)
        return nic
        
    except Exception as e:
        print(f"❌ OCR error: {e}")
        return None

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/scan', methods=['POST'])
def scan():
    """Scan ID card and extract NIC"""
    if 'id_card' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"}), 400
    
    file = request.files['id_card']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract NIC from image
        start_time = datetime.now()
        nic = extract_nic(filepath)
        end_time = datetime.now()
        
        extraction_time = (end_time - start_time).total_seconds()
        
        if nic:
            return jsonify({
                "success": True,
                "nic": nic,
                "extraction_time": round(extraction_time, 2),
                "message": "NIC extracted successfully"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Could not extract NIC from image"
            }), 422
            
    except Exception as e:
        print(f"Scan error: {e}")
        return jsonify({
            "success": False,
            "message": f"Error processing image: {str(e)}"
        }), 500

@app.route('/record_attendance', methods=['POST'])
def record_attendance():
    """Record attendance to database"""
    try:
        data = request.get_json()
        action = data.get('action', '').upper()
        nic = data.get('nic', '').strip()
        company = data.get('company', '').strip()
        
        if not all([action, nic, company]):
            return jsonify({
                "status": "error",
                "message": "Missing required fields"
            }), 400
        
        if not db or not cursor:
            return jsonify({
                "status": "success", 
                "message": f"✅ {action} recorded for {nic} at {company} (Demo Mode - DB not connected)",
                "time": datetime.now().strftime("%H:%M:%S")
            })
        
        today = datetime.today().date()
        now = datetime.now().time()
        
        if action == 'IN':
            cursor.execute(
                "INSERT INTO AttendanceRecords (NIC, Date, InTime, Company) VALUES (%s, %s, %s, %s)", 
                (nic, today, now, company)
            )
            db.commit()
            
            return jsonify({
                "status": "success",
                "message": f"✅ IN recorded for {nic} at {company}",
                "time": now.strftime("%H:%M:%S")
            })
            
        elif action == 'OUT':
            # Find matching IN record
            cursor.execute("""
                SELECT Id, InTime FROM AttendanceRecords
                WHERE NIC = %s AND Date = %s AND OutTime IS NULL
                ORDER BY InTime DESC LIMIT 1
            """, (nic, today))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({
                    "status": "warning",
                    "message": f"⚠️ No IN record found for {nic} today"
                })
            
            record_id, in_time = row
            
            # Update with OUT time
            cursor.execute(
                "UPDATE AttendanceRecords SET OutTime = %s WHERE Id = %s", 
                (now, record_id)
            )
            db.commit()
            
            # Calculate work hours
            if isinstance(in_time, timedelta):
                in_seconds = int(in_time.total_seconds())
                in_time = datetime.min.time().replace(
                    hour=in_seconds // 3600,
                    minute=(in_seconds % 3600) // 60,
                    second=in_seconds % 60
                )
            
            in_datetime = datetime.combine(today, in_time)
            out_datetime = datetime.combine(today, now)
            work_duration = out_datetime - in_datetime
            
            hours = int(work_duration.total_seconds() // 3600)
            minutes = int((work_duration.total_seconds() % 3600) // 60)
            work_hours = f"{hours}h {minutes}m"
            
            return jsonify({
                "status": "success",
                "message": f"✅ OUT recorded for {nic} at {company}",
                "time": now.strftime("%H:%M:%S"),
                "work_hours": work_hours
            })
        
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({
            "status": "error",
            "message": f"Database error: {str(e)}"
        }), 500

@app.route('/admin')
def admin_login():
    """Secure admin login page"""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    """Handle admin login with secure verification"""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if verify_admin_credentials(username, password):
        session['admin_logged_in'] = True
        session['admin_username'] = username
        session['admin_login_time'] = datetime.now().isoformat()
        flash('Login successful!', 'success')
        return redirect(url_for('admin_dashboard'))
    else:
        flash('Invalid username or password!', 'error')
        return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    """Admin logout - redirect to main page with success message"""
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    session.pop('admin_login_time', None)
    flash('Logged out successfully!', 'success')
    return redirect('/')  # Redirect to main attendance page

@app.route('/admin/dashboard')
def admin_dashboard():
    """Modern admin dashboard with secure access"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    return render_template('modern_admin_dashboard.html')

@app.route('/admin/api/stats')
def admin_stats():
    """API endpoint for admin statistics with date filtering"""
    if 'admin_logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        cursor = db.cursor()
        
        # Get date parameter (default to today)
        selected_date = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
        
        # Get total unique employees for selected date (using AttendanceRecords table)
        cursor.execute("SELECT COUNT(DISTINCT NIC) FROM attendancerecords WHERE Date = %s", (selected_date,))
        total_employees = cursor.fetchone()[0] or 0
        
        # Get selected date's unique workers who attended  
        cursor.execute("SELECT COUNT(DISTINCT NIC) FROM attendancerecords WHERE Date = %s", (selected_date,))
        date_attendance = cursor.fetchone()[0] or 0
        
        # Get completed sessions (workers who have both IN and OUT times on selected date)
        cursor.execute("""
            SELECT COUNT(DISTINCT NIC) as completed_sessions
            FROM attendancerecords 
            WHERE Date = %s 
            AND InTime IS NOT NULL 
            AND OutTime IS NOT NULL
        """, (selected_date,))
        completed_sessions = cursor.fetchone()[0] or 0
        
        # Calculate total work hours for completed sessions
        cursor.execute("""
            SELECT SUM(TIME_TO_SEC(TIMEDIFF(OutTime, InTime))) / 3600 as total_hours
            FROM attendancerecords 
            WHERE Date = %s 
            AND InTime IS NOT NULL 
            AND OutTime IS NOT NULL
        """, (selected_date,))
        result = cursor.fetchone()
        date_hours = round(result[0] if result[0] else 0, 1)
        
        # Get currently checked in for selected date (IN but no OUT)
        cursor.execute("""
            SELECT COUNT(DISTINCT NIC) FROM attendancerecords
            WHERE Date = %s 
            AND InTime IS NOT NULL 
            AND OutTime IS NULL
        """, (selected_date,))
        currently_in = cursor.fetchone()[0] or 0
        
        return jsonify({
            "selected_date": selected_date,
            "total_employees": total_employees,
            "date_attendance": date_attendance,
            "completed_sessions": completed_sessions,
            "date_hours": date_hours,
            "currently_in": currently_in
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/api/reports')
def admin_reports():
    """API endpoint for admin reports"""
    if 'admin_logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    report_type = request.args.get('type', 'daily')
    
    try:
        cursor = db.cursor()
        
        if report_type == 'daily':
            # Get last 7 days attendance
            cursor.execute("""
                SELECT DATE(time) as date, COUNT(DISTINCT nic) as attendance_count
                FROM attendance 
                WHERE DATE(time) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                GROUP BY DATE(time) 
                ORDER BY date DESC
            """)
            
        elif report_type == 'weekly':
            # Get last 8 weeks attendance (by week)
            cursor.execute("""
                SELECT 
                    YEARWEEK(time) as week_year,
                    MIN(DATE(time)) as week_start,
                    COUNT(DISTINCT nic) as attendance_count
                FROM attendance 
                WHERE DATE(time) >= DATE_SUB(CURDATE(), INTERVAL 8 WEEK)
                GROUP BY YEARWEEK(time) 
                ORDER BY week_year DESC
            """)
            
        elif report_type == 'monthly':
            # Get last 12 months attendance (by month)
            cursor.execute("""
                SELECT 
                    DATE_FORMAT(time, '%Y-%m') as month,
                    COUNT(DISTINCT nic) as attendance_count
                FROM attendance 
                WHERE DATE(time) >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                GROUP BY DATE_FORMAT(time, '%Y-%m') 
            """)
        else:
            return jsonify({"error": "Invalid report type"}), 400
        
        results = cursor.fetchall()
        
        # Format the data for charts
        data = []
        for row in results:
            if report_type == 'daily':
                data.append({
                    "date": str(row[0]),
                    "attendance": row[1],
                    "hours": round(row[2] if row[2] else 0, 2)
                })
            elif report_type == 'weekly':
                data.append({
                    "week": f"Week {row[0]}",
                    "date": str(row[1]),
                    "attendance": row[2],
                    "hours": round(row[3] if row[3] else 0, 2)
                })
            else:  # monthly
                data.append({
                    "month": row[0],
                    "date": str(row[1]),
                    "attendance": row[2],
                    "hours": round(row[3] if row[3] else 0, 2)
                })
        
        return jsonify({"data": data, "type": report_type})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/api/recent-attendance')
def get_recent_attendance():
    """Get recent attendance records for dashboard"""
    if 'admin_logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        cursor = db.cursor()
        
        # Get recent attendance records (last 50 records)
        cursor.execute("""
            SELECT nic, company, DATE(time) as date, time, action
            FROM attendance 
            ORDER BY time DESC 
            LIMIT 50
        """)
        
        records = cursor.fetchall()
        
        recent_data = []
        for record in records:
            recent_data.append({
                'nic': record[0],
                'company': record[1] or 'N/A',
                'date': str(record[2]),
                'time': str(record[3]),
                'action': record[4]
            })
        
        return jsonify({
            "success": True,
            "records": recent_data
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/api/search-attendance')
def search_attendance():
    """Enhanced search attendance records with multiple filters"""
    if 'admin_logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        cursor = db.cursor()
        
        # Get filter parameters
        nic_query = request.args.get('nic', '').strip()
        company_query = request.args.get('company', '').strip()
        date_query = request.args.get('date', '').strip()
        status_query = request.args.get('status', '').strip()
        
        # Build dynamic query
        base_query = """
            SELECT NIC, Company, Date, InTime, OutTime, 
                   CASE WHEN OutTime IS NULL THEN 'IN' ELSE 'COMPLETED' END as status
            FROM attendancerecords 
            WHERE 1=1
        """
        
        params = []
        
        if nic_query:
            base_query += " AND NIC LIKE %s"
            params.append(f'%{nic_query}%')
        
        if company_query:
            base_query += " AND Company LIKE %s"
            params.append(f'%{company_query}%')
        
        if date_query:
            base_query += " AND Date = %s"
            params.append(date_query)
        
        if status_query:
            if status_query == 'IN':
                base_query += " AND OutTime IS NULL"
            elif status_query == 'COMPLETED':
                base_query += " AND OutTime IS NOT NULL"
        
        base_query += " ORDER BY Date DESC, InTime DESC LIMIT 100"
        
        cursor.execute(base_query, params)
        records = cursor.fetchall()
        
        search_data = []
        for record in records:
            search_data.append({
                'nic': record[0],
                'company': record[1] or 'N/A',
                'date': str(record[2]),
                'in_time': str(record[3]) if record[3] else 'N/A',
                'out_time': str(record[4]) if record[4] else 'N/A',
                'status': record[5]
            })
        
        return jsonify({
            "success": True,
            "records": search_data,
            "count": len(search_data)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/api/workers')
def get_workers():
    """API endpoint for Workers information"""
    if 'admin_logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        if not db or not db.is_connected():
            return jsonify({'error': 'Database connection lost'}), 500
            
        cursor = db.cursor()
        
        # Get all unique workers with their latest data - Fixed SQL for MySQL
        cursor.execute('''
            SELECT 
                NIC,
                Company,
                MAX(Date) as last_active,
                COUNT(*) as total_sessions,
                CASE 
                    WHEN MAX(Date) = CURDATE() AND COUNT(CASE WHEN OutTime IS NULL THEN 1 END) > 0 THEN 'IN'
                    WHEN MAX(Date) = CURDATE() AND COUNT(CASE WHEN OutTime IS NOT NULL THEN 1 END) > 0 THEN 'ACTIVE'
                    ELSE 'INACTIVE'
                END as status
            FROM attendancerecords 
            GROUP BY NIC, Company
            ORDER BY MAX(Date) DESC, NIC
        ''')
        
        records = cursor.fetchall()
        
        workers_data = []
        for record in records:
            workers_data.append({
                'nic': record[0] if record[0] else 'N/A',
                'company': record[1] if record[1] else 'N/A',
                'last_active': str(record[2]) if record[2] else 'Never',
                'total_hours': record[3] if record[3] else 0,  # Using session count
                'status': record[4] if record[4] else 'INACTIVE'
            })
        
        print(f"✅ Workers API: Found {len(workers_data)} workers")
        
        return jsonify({
            'success': True,
            'workers': workers_data,
            'count': len(workers_data)
        })
        
    except Exception as e:
        print(f"❌ Error fetching workers: {e}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/admin/api/analytics')
def get_analytics():
    """API endpoint for Analytics data"""
    if 'admin_logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        filter_type = request.args.get('filter', 'daily')
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        cursor = db.cursor()
        
        if filter_type == 'daily':
            # Daily hourly breakdown
            cursor.execute('''
                SELECT 
                    HOUR(in_time) as hour_period,
                    COUNT(*) as attendance_count,
                    SUM(COALESCE(workhours, 0)) as total_hours
                FROM attendancerecords 
                WHERE date = %s
                GROUP BY HOUR(in_time)
                ORDER BY hour_period
            ''', (date_param,))
            
        elif filter_type == 'weekly':
            # Weekly breakdown (7 days from selected date)
            cursor.execute('''
                SELECT 
                    DAYNAME(date) as day_name,
                    COUNT(DISTINCT nic) as attendance_count,
                    SUM(COALESCE(workhours, 0)) as total_hours
                FROM attendancerecords 
                WHERE date BETWEEN DATE_SUB(%s, INTERVAL 6 DAY) AND %s
                GROUP BY date, DAYNAME(date)
                ORDER BY date
            ''', (date_param, date_param))
            
        else:  # monthly
            # Monthly breakdown (6 months from selected date)
            cursor.execute('''
                SELECT 
                    MONTHNAME(date) as month_name,
                    COUNT(DISTINCT nic) as attendance_count,
                    SUM(COALESCE(workhours, 0)) as total_hours
                FROM attendancerecords 
                WHERE date BETWEEN DATE_SUB(%s, INTERVAL 5 MONTH) AND %s
                GROUP BY YEAR(date), MONTH(date), MONTHNAME(date)
                ORDER BY date
            ''', (date_param, date_param))
        
        results = cursor.fetchall()
        
        # Format data for charts
        labels = []
        attendance = []
        hours = []
        
        for row in results:
            if filter_type == 'daily':
                labels.append(f"{row['hour_period']:02d}:00")
            elif filter_type == 'weekly':
                labels.append(row['day_name'][:3])
            else:
                labels.append(row['month_name'][:3])
            
            attendance.append(row['attendance_count'])
            hours.append(float(row['total_hours'] or 0))
        
        return jsonify({
            'success': True,
            'analytics': {
                'labels': labels,
                'attendance': attendance,
                'hours': hours
            }
        })
        
    except Exception as e:
        return jsonify({'error': 'Database error'}), 500

@app.route('/admin/api/export-worker')
def export_worker():
    """API endpoint to export worker data as CSV"""
    if 'admin_logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    nic = request.args.get('nic')
    if not nic:
        return jsonify({'error': 'NIC required'}), 400
    
    try:
        cursor = db.cursor()
        cursor.execute('''
            SELECT * FROM attendancerecords 
            WHERE nic = %s 
            ORDER BY date DESC, in_time DESC
        ''', (nic,))
        
        records = cursor.fetchall()
        
        # Convert to CSV format
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['nic', 'company', 'date', 'in_time', 'out_time', 'workhours', 'status'])
        writer.writeheader()
        
        for record in records:
            writer.writerow(record)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=worker_{nic}_data.csv'
        
        return response
        
    except Exception as e:
        return jsonify({'error': 'Export failed'}), 500

@app.route('/admin/api/check-auth')
def check_auth():
    """API endpoint to check if admin is authenticated"""
    try:
        if 'admin_logged_in' not in session:
            return jsonify({"authenticated": False}), 401
        
        # Check session timeout
        if 'admin_login_time' in session:
            login_time = datetime.fromisoformat(session['admin_login_time'])
            if datetime.now() - login_time > timedelta(minutes=ADMIN_CONFIG['session_timeout']):
                session.clear()
                log_security_event('SESSION_TIMEOUT', 'Admin session expired via API check')
                return jsonify({"authenticated": False, "reason": "session_expired"}), 401
        
        return jsonify({
            "authenticated": True,
            "username": session.get('admin_username', 'admin'),
            "login_time": session.get('admin_login_time')
        })
        
    except Exception as e:
        print(f"❌ Error checking authentication: {e}")
        return jsonify({"authenticated": False, "error": str(e)}), 500

def open_browser():
    """Open browser after server starts"""
    threading.Timer(1.5, lambda: webbrowser.open('http://127.0.0.1:5001')).start()

if __name__ == '__main__':
    print("🚀 ATTENDANCE SYSTEM STARTING...")
    print("📊 Simple NIC extraction")
    if db:
        print("💾 Database: ✅ Connected")
    else:
        print("💾 Database: ❌ Running in Demo Mode")
    
    open_browser()
    app.run(debug=True, host='127.0.0.1', port=5001)
