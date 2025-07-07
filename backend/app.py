from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, make_response
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, time
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

def get_shift_from_time(check_time):
    """
    Calculate shift based on check-in time
    
    Shift Schedule:
    - Morning Shift: 06:00 AM – 12:00 PM
    - Afternoon Shift: 12:00 PM – 06:00 PM  
    - Evening Shift: 06:00 PM – 10:00 PM
    - Night Shift: 10:00 PM – 06:00 AM (next day)
    """
    if isinstance(check_time, str):
        # Parse time string
        if ' ' in check_time:
            check_time = datetime.strptime(check_time, "%Y-%m-%d %H:%M:%S").time()
        else:
            check_time = datetime.strptime(check_time, "%H:%M:%S").time()
    elif isinstance(check_time, datetime):
        check_time = check_time.time()
    
    morning_start = time(6, 0)    # 06:00 AM
    afternoon_start = time(12, 0) # 12:00 PM
    evening_start = time(18, 0)   # 06:00 PM
    night_start = time(22, 0)     # 10:00 PM
    
    # Determine shift based on check-in time
    if morning_start <= check_time < afternoon_start:
        return "Morning Shift"
    elif afternoon_start <= check_time < evening_start:
        return "Afternoon Shift"
    elif evening_start <= check_time < night_start:
        return "Evening Shift"
    else:
        # Night shift: 10:00 PM - 06:00 AM (covers late night and early morning)
        return "Night Shift"

app = Flask(__name__)
app.secret_key = 'printcare_admin_secret_key_2025'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database connection with error handling
def get_db_connection():
    """Get a fresh database connection with error handling"""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Tashini258258",
            database="AttendanceDB",
            autocommit=False,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        return connection
    except mysql.connector.Error as err:
        print(f"❌ Database connection error: {err}")
        return None
    except Exception as e:
        print(f"❌ Unexpected database error: {e}")
        return None

# Initialize database connection
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
        
        # Map company names to database ENUM values
        company_mapping = {
            'Printcare Solutions': 'PUL',
            'Tech Division': 'PCL', 
            'Design Team': 'PPM',
            'Operations': 'PDSL',
            'HR Department': 'PUL',
            'Finance Team': 'PCL',
            'Marketing': 'PPM',
            'IT Support': 'PDSL',
            'Quality Assurance': 'PUL'
        }
        
        # Map the company to database enum value
        db_company = company_mapping.get(company, 'PUL')  # Default to PUL
        
        if action == 'IN':
            # Calculate shift from time
            shift = get_shift_from_time(now)
            
            cursor.execute(
                "INSERT INTO AttendanceRecords (NIC, Date, InTime, Shift, Status, Company) VALUES (%s, %s, %s, %s, %s, %s)", 
                (nic, today, now, shift, 'Check in', db_company)
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
                SELECT ID, InTime FROM AttendanceRecords
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
            
            # Update with OUT time and status
            cursor.execute(
                "UPDATE AttendanceRecords SET OutTime = %s, Status = %s WHERE ID = %s", 
                (now, 'Completed', record_id)
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
        
        # Build dynamic query for AttendanceRecords table
        base_query = """
            SELECT NIC, Company, Date, InTime, OutTime, Shift, Status
            FROM AttendanceRecords 
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
            elif status_query == 'OUT':
                base_query += " AND OutTime IS NOT NULL"
            else:
                base_query += " AND Status = %s"
                params.append(status_query)
        
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
                'shift': record[5] or 'N/A',
                'status': record[6]
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
    """API endpoint for Workers information - simplified for attendancerecords table"""
    if 'admin_logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        if not db or not db.is_connected():
            return jsonify({'error': 'Database connection lost'}), 500
            
        cursor = db.cursor()
        
        # Get all unique workers from AttendanceRecords table
        cursor.execute('''
            SELECT 
                NIC,
                Company,
                MAX(Date) as last_active,
                COUNT(*) as total_sessions,
                CASE 
                    WHEN MAX(Date) = CURDATE() AND COUNT(CASE WHEN OutTime IS NULL THEN 1 END) > 0 THEN 'IN'
                    WHEN MAX(Date) = CURDATE() AND COUNT(CASE WHEN OutTime IS NOT NULL THEN 1 END) > 0 THEN 'OUT'
                    ELSE 'INACTIVE'
                END as current_status
            FROM AttendanceRecords 
            GROUP BY NIC, Company
            ORDER BY MAX(Date) DESC, NIC
        ''')
        
        records = cursor.fetchall()
        
        workers_data = []
        for record in records:
            workers_data.append({
                'nic': record[0] if record[0] else 'N/A',
                'name': f'Worker {record[0][-3:]}' if record[0] else 'Unknown',  # Generate name from NIC
                'company': record[1] if record[1] else 'N/A',
                'position': 'Employee',  # Default position
                'phone': 'N/A',  # No phone in simple structure
                'last_active': str(record[2]) if record[2] else 'Never',
                'total_sessions': record[3] if record[3] else 0,
                'current_status': record[4] if record[4] else 'INACTIVE'
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
    """API endpoint for Analytics data with updated AttendanceRecords table"""
    if 'admin_logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        filter_type = request.args.get('filter', 'daily')
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Get fresh connection
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cursor = connection.cursor(dictionary=True)
        
        if filter_type == 'daily':
            # Daily hourly breakdown
            cursor.execute('''
                SELECT 
                    HOUR(InTime) as hour_period,
                    COUNT(*) as attendance_count,
                    COUNT(CASE WHEN OutTime IS NOT NULL THEN 1 END) as completed_count,
                    COUNT(CASE WHEN Status = 'Check in' THEN 1 END) as checkin_count,
                    COUNT(CASE WHEN Status = 'Completed' THEN 1 END) as completed_status_count
                FROM `AttendanceRecords`
                WHERE Date = %s AND InTime IS NOT NULL
                GROUP BY HOUR(InTime)
                ORDER BY hour_period
            ''', (date_param,))
            
        elif filter_type == 'weekly':
            # Weekly breakdown (7 days from selected date)
            cursor.execute('''
                SELECT 
                    DAYNAME(Date) as day_name,
                    COUNT(DISTINCT NIC) as attendance_count,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN OutTime IS NOT NULL THEN 1 END) as completed_count
                FROM `AttendanceRecords`
                WHERE Date BETWEEN DATE_SUB(%s, INTERVAL 6 DAY) AND %s
                GROUP BY Date, DAYNAME(Date)
                ORDER BY Date
            ''', (date_param, date_param))
            
        else:  # monthly
            # Monthly breakdown (6 months from selected date)
            cursor.execute('''
                SELECT 
                    MONTHNAME(Date) as month_name,
                    COUNT(DISTINCT NIC) as attendance_count,
                    COUNT(*) as total_records,
                    COUNT(CASE WHEN OutTime IS NOT NULL THEN 1 END) as completed_count
                FROM `AttendanceRecords`
                WHERE Date BETWEEN DATE_SUB(%s, INTERVAL 5 MONTH) AND %s
                GROUP BY YEAR(Date), MONTH(Date), MONTHNAME(Date)
                ORDER BY Date
            ''', (date_param, date_param))
        
        results = cursor.fetchall()
        
        # Format data for charts
        labels = []
        attendance = []
        completed = []
        
        for row in results:
            if filter_type == 'daily':
                labels.append(f"{row['hour_period']:02d}:00")
                attendance.append(row['attendance_count'])
                completed.append(row.get('completed_count', 0))
            elif filter_type == 'weekly':
                labels.append(row['day_name'][:3])
                attendance.append(row['attendance_count'])
                completed.append(row.get('completed_count', 0))
            else:
                labels.append(row['month_name'][:3])
                attendance.append(row['attendance_count'])
                completed.append(row.get('completed_count', 0))
        
        # Get department/company distribution
        cursor.execute('''
            SELECT 
                Company,
                COUNT(DISTINCT NIC) as worker_count,
                COUNT(*) as total_records
            FROM `AttendanceRecords`
            WHERE Date >= DATE_SUB(%s, INTERVAL 30 DAY)
            GROUP BY Company
            ORDER BY Company
        ''', (date_param,))
        
        dept_results = cursor.fetchall()
        
        # Format department data
        dept_labels = []
        dept_data = []
        
        for row in dept_results:
            dept_labels.append(row['Company'])
            dept_data.append(row['worker_count'])
        
        # Ensure all departments are represented
        all_companies = ['PCL', 'PUL', 'PPM', 'PDSL']
        dept_labels_complete = []
        dept_data_complete = []
        
        for company in all_companies:
            if company in dept_labels:
                idx = dept_labels.index(company)
                dept_labels_complete.append(company)
                dept_data_complete.append(dept_data[idx])
            else:
                dept_labels_complete.append(company)
                dept_data_complete.append(0)
        
        return jsonify({
            'success': True,
            'analytics': {
                'labels': labels,
                'attendance': attendance,
                'completed': completed,
                'departments': {
                    'labels': dept_labels_complete,
                    'data': dept_data_complete
                }
            }
        })
        
    except Exception as e:
        print(f"❌ Analytics error: {e}")
        return jsonify({'error': 'Database error'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

# New comprehensive reporting endpoints
@app.route('/admin/api/reports/daily')
def daily_report():
    """Generate daily attendance report"""
    if 'admin_logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        company = request.args.get('company', '')
        shift = request.args.get('shift', '')
        
        # Get fresh connection
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cursor = connection.cursor(dictionary=True)
        
        # Build query with filters
        query = """
        SELECT 
            NIC, Date, InTime, OutTime, Shift, Status, Company,
            CASE 
                WHEN InTime IS NOT NULL AND OutTime IS NOT NULL 
                THEN TIMEDIFF(OutTime, InTime)
                ELSE NULL 
            END as WorkDuration
        FROM `AttendanceRecords`
        WHERE Date = %s
        """
        params = [date_param]
        
        if company:
            query += " AND Company = %s"
            params.append(company)
            
        if shift:
            query += " AND Shift = %s"
            params.append(shift)
            
        query += " ORDER BY InTime"
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        # Calculate summary statistics
        total_records = len(records)
        checked_in = len([r for r in records if r['Status'] == 'Check in'])
        completed = len([r for r in records if r['Status'] == 'Completed'])
        pending = len([r for r in records if r['Status'] == 'Pending'])
        
        # Convert timedelta to string for JSON serialization
        for record in records:
            if record['WorkDuration']:
                record['WorkDuration'] = str(record['WorkDuration'])
            if record['InTime']:
                record['InTime'] = str(record['InTime'])
            if record['OutTime']:
                record['OutTime'] = str(record['OutTime'])
        
        return jsonify({
            'success': True,
            'date': date_param,
            'summary': {
                'total_records': total_records,
                'checked_in': checked_in,
                'completed': completed,
                'pending': pending
            },
            'records': records
        })
        
    except Exception as e:
        print(f"❌ Daily report error: {e}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/admin/api/reports/weekly')
def weekly_report():
    """Generate weekly attendance report"""
    if 'admin_logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        company = request.args.get('company', '')
        
        # Get fresh connection
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cursor = connection.cursor(dictionary=True)
        
        # Weekly summary by day
        query = """
        SELECT 
            Date,
            DAYNAME(Date) as DayName,
            COUNT(*) as TotalRecords,
            COUNT(DISTINCT NIC) as UniqueWorkers,
            COUNT(CASE WHEN Status = 'Check in' THEN 1 END) as CheckedIn,
            COUNT(CASE WHEN Status = 'Completed' THEN 1 END) as Completed,
            COUNT(CASE WHEN Status = 'Pending' THEN 1 END) as Pending
        FROM `AttendanceRecords`
        WHERE Date BETWEEN DATE_SUB(%s, INTERVAL 6 DAY) AND %s
        """
        params = [date_param, date_param]
        
        if company:
            query += " AND Company = %s"
            params.append(company)
            
        query += " GROUP BY Date ORDER BY Date"
        
        cursor.execute(query, params)
        daily_summary = cursor.fetchall()
        
        # Convert dates to strings
        for record in daily_summary:
            record['Date'] = str(record['Date'])
        
        return jsonify({
            'success': True,
            'week_ending': date_param,
            'daily_summary': daily_summary
        })
        
    except Exception as e:
        print(f"❌ Weekly report error: {e}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/admin/api/reports/monthly')
def monthly_report():
    """Generate monthly attendance report"""
    if 'admin_logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        company = request.args.get('company', '')
        
        # Get fresh connection
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cursor = connection.cursor(dictionary=True)
        
        # Get the first day of the month
        date_obj = datetime.strptime(date_param, '%Y-%m-%d')
        first_day = date_obj.replace(day=1).strftime('%Y-%m-%d')
        last_day = (date_obj.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        last_day = last_day.strftime('%Y-%m-%d')
        
        # Monthly summary by company and shift
        query = """
        SELECT 
            Company,
            Shift,
            COUNT(*) as TotalRecords,
            COUNT(DISTINCT NIC) as UniqueWorkers,
            COUNT(CASE WHEN Status = 'Check in' THEN 1 END) as CheckedIn,
            COUNT(CASE WHEN Status = 'Completed' THEN 1 END) as Completed,
            COUNT(CASE WHEN Status = 'Pending' THEN 1 END) as Pending,
            AVG(CASE 
                WHEN InTime IS NOT NULL AND OutTime IS NOT NULL 
                THEN TIME_TO_SEC(TIMEDIFF(OutTime, InTime))/3600 
                ELSE NULL 
            END) as AvgWorkHours
        FROM `AttendanceRecords`
        WHERE Date BETWEEN %s AND %s
        """
        params = [first_day, last_day]
        
        if company:
            query += " AND Company = %s"
            params.append(company)
            
        query += " GROUP BY Company, Shift ORDER BY Company, Shift"
        
        cursor.execute(query, params)
        company_summary = cursor.fetchall()
        
        # Round average work hours
        for record in company_summary:
            if record['AvgWorkHours']:
                record['AvgWorkHours'] = round(record['AvgWorkHours'], 2)
        
        return jsonify({
            'success': True,
            'month': date_obj.strftime('%B %Y'),
            'period': f"{first_day} to {last_day}",
            'company_summary': company_summary
        })
        
    except Exception as e:
        print(f"❌ Monthly report error: {e}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

@app.route('/admin/api/export/excel')
def export_excel():
    """Export attendance data to Excel"""
    if 'admin_logged_in' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        report_type = request.args.get('type', 'daily')
        date_param = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        company = request.args.get('company', '')
        
        # Get fresh connection
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cursor = connection.cursor(dictionary=True)
        
        if report_type == 'daily':
            query = """
            SELECT 
                NIC, Date, InTime, OutTime, Shift, Status, Company,
                CASE 
                    WHEN InTime IS NOT NULL AND OutTime IS NOT NULL 
                    THEN TIMEDIFF(OutTime, InTime)
                    ELSE NULL 
                END as WorkDuration
            FROM `AttendanceRecords`
            WHERE Date = %s
            """
            params = [date_param]
            filename = f"daily_report_{date_param}.xlsx"
            
        elif report_type == 'weekly':
            query = """
            SELECT 
                Date, NIC, InTime, OutTime, Shift, Status, Company
            FROM `AttendanceRecords`
            WHERE Date BETWEEN DATE_SUB(%s, INTERVAL 6 DAY) AND %s
            """
            params = [date_param, date_param]
            filename = f"weekly_report_{date_param}.xlsx"
            
        else:  # monthly
            date_obj = datetime.strptime(date_param, '%Y-%m-%d')
            first_day = date_obj.replace(day=1).strftime('%Y-%m-%d')
            last_day = (date_obj.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            last_day = last_day.strftime('%Y-%m-%d')
            
            query = """
            SELECT 
                Date, NIC, InTime, OutTime, Shift, Status, Company
            FROM `AttendanceRecords`
            WHERE Date BETWEEN %s AND %s
            """
            params = [first_day, last_day]
            filename = f"monthly_report_{date_obj.strftime('%Y-%m')}.xlsx"
            
        if company:
            query += " AND Company = %s"
            params.append(company)
            
        query += " ORDER BY Date, InTime"
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        # Create Excel file
        import openpyxl
        from openpyxl.utils.dataframe import dataframe_to_rows
        import pandas as pd
        from io import BytesIO
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Create workbook and worksheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"{report_type.capitalize()} Report"
        
        # Add data to worksheet
        for r in dataframe_to_rows(df, index=False, header=True):
            ws.append(r)
        
        # Style the header
        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True)
            cell.fill = openpyxl.styles.PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        
        # Save to BytesIO
        excel_file = BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)
        
        response = make_response(excel_file.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        print(f"❌ Excel export error: {e}")
        return jsonify({'error': f'Export error: {str(e)}'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()

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
