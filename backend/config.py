# Configuration file for the attendance system

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Tashini258258',
    'database': 'AttendanceDB',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

# Admin configuration
ADMIN_CONFIG = {
    'username': 'admin',
    'password_hash': '26a61439f232320bfebbc7fb3a6dfb0d20ba673deaf3f261f11205007c72f8e0',  # printcare2025
    'session_timeout': 480,  # 8 hours (480 minutes)
    'max_failed_attempts': 3,
    'lockout_duration': 15  # minutes
}

# Company mapping
COMPANY_MAPPING = {
    'Printcare Solutions': 'PUL',
    'Tech Division': 'PCL', 
    'Design Team': 'PPM',
    'Operations': 'PDSL',
    'HR Department': 'PUL',
    'Finance Team': 'PCL',
    'Marketing': 'PPM',
    'IT Support': 'PDSL',
    'Quality Assurance': 'PUL',
    # Direct department codes
    'PUL': 'PUL',
    'PCL': 'PCL',
    'PPM': 'PPM',
    'PDSL': 'PDSL'
}

COMPANY_DISPLAY_NAMES = {
    'PUL': 'PUL',
    'PCL': 'PCL', 
    'PPM': 'PPM',
    'PDSL': 'PDSL'
}

# Tesseract configuration
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Upload folder
UPLOAD_FOLDER = 'uploads'
