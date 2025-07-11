# Updated NIC Capture Workflow

## NEW WORKFLOW: Extract NIC First, Then Capture Images

### ✅ **Updated Flow for IN Action:**

#### **Step 1: Department Selection**
- Worker selects department/company
- Enables IN/OUT buttons

#### **Step 2: NIC Extraction**
- **Option A**: Camera scan of NIC → Extract NIC number using OCR
- **Option B**: Manual entry of NIC number
- **Result**: NIC number is obtained and stored

#### **Step 3: NIC Image Capture (NEW ORDER)**
- Show NIC number that was extracted
- **Front Image Capture**:
  - Open camera for front NIC capture
  - Save to `uploads/front/front_YYYYMMDD_HHMMSS.jpg`
  - Update progress indicator
- **Back Image Capture**:
  - Open camera for back NIC capture
  - Save to `uploads/back/back_YYYYMMDD_HHMMSS.jpg`
  - Update progress indicator

#### **Step 4: Verification & Submission**
- Display extracted NIC number
- Show confirmation that both images were captured
- Submit to database with:
  - NIC number (already extracted)
  - Front image path → `FrontNICImage` column
  - Back image path → `BackNICImage` column
  - All other attendance data

### ✅ **Key Changes Made:**

#### **Frontend Updates:**
1. **Modified workflow order**: NIC extraction → Image capture → Verification
2. **Enhanced UI**: Shows extracted NIC number during image capture
3. **Updated messages**: Clear indication of current step and NIC number
4. **Progress tracking**: Visual feedback for front/back capture completion
5. **Removed duplicate verification container**

#### **Backend Updates:**
1. **Modified `/save_nic_image`**: No longer requires NIC extraction from front image
2. **Optional NIC verification**: Can still extract from front image for verification
3. **Error handling**: Graceful handling if OCR fails during image save
4. **Path storage**: Correctly saves image paths to database columns

### ✅ **File Structure:**
```
uploads/
├── front/
│   └── front_20250711_143000.jpg (example)
├── back/
│   └── back_20250711_143030.jpg (example)
└── scan_*.jpg (temporary scan files)
```

### ✅ **Database Integration:**
```sql
INSERT INTO AttendanceRecords 
(NIC, Date, InTime, Shift, Status, Company, FrontNICImage, BackNICImage) 
VALUES 
('123456789V', '2025-07-11', '14:30:00', 'Afternoon Shift', 'Check in', 'PUL', 
 'uploads/front/front_20250711_143000.jpg', 
 'uploads/back/back_20250711_143030.jpg');
```

### ✅ **User Experience:**

#### **For IN (Check-in):**
1. Select department → Press IN
2. **Scan NIC or enter manually** → NIC number extracted/entered
3. **Capture front NIC image** → Image saved to uploads/front/
4. **Capture back NIC image** → Image saved to uploads/back/
5. **Verify NIC and images** → Confirm before submission
6. **Submit** → Record saved with NIC and image paths

#### **For OUT (Check-out):**
1. Select department → Press OUT
2. **Scan NIC or enter manually** → NIC number extracted/entered
3. **Verify and submit** → No image capture needed

### ✅ **Error Handling:**
- **Camera failure**: Skip image capture option available
- **OCR failure during scan**: Manual entry fallback
- **OCR failure during image save**: Continue without error (NIC already known)
- **Network issues**: Graceful error messages and retry options

### ✅ **Security & Privacy:**
- Images stored in dedicated folders with timestamp-based naming
- Database stores relative paths for portability
- Access controlled through admin dashboard
- No duplicate image processing

### 🚀 **Ready to Test:**
The application is running at **http://127.0.0.1:5001** with the updated workflow:
1. **Extract NIC first** (scan or manual)
2. **Then capture images** (front and back)
3. **Finally save to database** with paths stored

This provides a much clearer and more logical user experience!
