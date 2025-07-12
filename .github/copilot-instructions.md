# AI Coding Agent Instructions - Attendance System

## Project Architecture

This is a **Flask-based attendance tracking system** with OCR-powered NIC (National Identity Card) scanning for Sri Lankan employee attendance management.

### Core Components
- **Backend**: Flask web app (`backend/app.py`) with MySQL database integration
- **Database**: AttendanceDB with `AttendanceRecords` table and 4 company divisions (PUL, PCL, PPM, PDSL)  
- **OCR Engine**: Tesseract OCR for extracting NIC numbers from ID card images
- **Frontend**: HTML templates with Tailwind CSS and vanilla JavaScript camera integration
- **Admin Panel**: Secure dashboard with analytics, reporting, and data export features

### Database Schema Essentials
```sql
AttendanceRecords: ID, NIC, Date, InTime, OutTime, Shift, Status, Company, FrontNICImage, BackNICImage
Companies: PUL, PCL, PPM, PDSL (enum values)
Shifts: Morning/Afternoon/Evening/Night Shift (4 standardized types only)
Status: 'Check in', 'Completed', 'Pending'
```

## Critical Development Patterns

### 1. NIC Format Recognition
The system handles **both old (9 digits + V/X) and new (12 digits) Sri Lankan NIC formats**:
```python
# Old format: 123456789V or 123456789X  
# New format: 200012345678 (12 digits)
```

### 2. Shift Assignment Logic
**Time-based automatic shift calculation** in `get_shift_from_time()`:
- Morning: 06:00-12:00, Afternoon: 12:00-18:00, Evening: 18:00-22:00, Night: 22:00-06:00
- Department-specific shift preferences in `populate_sample_data()`

### 3. Image Processing Pipeline
**Multi-method OCR approach** in `extract_nic()`:
- 4 different Tesseract PSM modes (6,7,8,13) 
- 4 image enhancement methods (contrast, sharpness, grayscale variations)
- Character whitelist: `0123456789VXvx`

### 4. Database Connection Pattern
**Connection-per-request** with error handling:
```python
def get_db_connection():
    # Fresh connection with utf8mb4 charset
    # Always use this instead of global db cursor
```

### 5. Security Implementation
**Session-based admin authentication** with:
- SHA256 password hashing
- Failed attempt tracking with account lockout
- Session timeout (8 hours)
- Security event logging

## Key Workflows

### Running the Application
```bash
cd backend
python app.py
# Server starts on http://localhost:5000 with auto browser opening
# Default admin: username=admin, password=printcare2025
```

### Adding New API Endpoints
- All admin routes require `@security_required` decorator
- Use `get_db_connection()` for database operations
- Return JSON with consistent `{"success": boolean, "message": string}` format

### Database Operations
- **Never use global `db` cursor directly** - it may be stale
- Always use `get_db_connection()` in route handlers
- Use parameterized queries to prevent SQL injection
- Close connections in try/finally blocks

### Frontend Camera Integration
- Camera workflows in `templates/index.html` follow 6-step process:
  1. Company selection → 2. Camera scanning → 3. Manual entry (fallback) → 4. NIC verification → 5. NIC image capture (IN only) → 6. Success
- Use `startScanning(action)` for IN/OUT workflows
- Fast scanning: 300ms intervals with automatic retry

## Project-Specific Conventions

### File Organization
```
backend/
├── app.py (main Flask app - 1800+ lines)
├── templates/ (HTML with embedded JavaScript)
├── uploads/ (NIC images: front/ and back/ subdirectories)
└── static/ (if needed - currently using CDN resources)
```

### Error Handling Patterns
- **OCR failures**: Try multiple processing methods before giving up
- **Database errors**: Always return user-friendly messages, log technical details
- **Camera access**: Graceful fallback to manual NIC entry

### Data Validation
- **NIC validation**: Regex patterns for both old/new formats
- **Company mapping**: Human-readable names → database enum values
- **Time calculations**: Handle day overflow for night shifts

### Testing & Debugging
- Extensive console logging with emoji prefixes (✅ ❌ 🔍 📊)
- Sample data generation for testing (`populate_sample_data()`)
- Admin dashboard provides real-time statistics and filtering

## Integration Points

### External Dependencies
- **Tesseract OCR**: Must be installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`
- **MySQL**: Local instance required (user: root, password: Tashini258258)
- **Camera API**: Browser webcam access for ID scanning

### API Endpoints Structure
- `/scan` - OCR processing for NIC extraction
- `/record_attendance` - Main attendance recording
- `/admin/api/*` - All admin dashboard APIs (stats, reports, analytics)
- `/admin/api/export/*` - Data export functionality

When modifying this system, prioritize data consistency in the AttendanceRecords table and maintain the existing 4-shift standardization. Always test OCR functionality with both NIC formats and ensure camera workflows gracefully handle access denials.
