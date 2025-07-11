# NIC Number Filename Implementation

## Overview
Updated the attendance system to save captured NIC images using the NIC number as the filename instead of timestamp-based names. This makes it easier to identify and manage images.

## Changes Made

### 🗂️ **Frontend Changes (index.html)**
1. **Updated Form Data Submission:**
   - Changed filename from `nic_${nicCaptureStep}_${Date.now()}.jpg` to `${currentNic}_${nicCaptureStep}.jpg`
   - Added `nic_number` field to FormData for backend processing
   - Updated success message to show the actual filename saved

2. **Enhanced Frame Dimensions:**
   - Updated capture dimensions to match the new larger yellow frame
   - Front: 288×384px (w-72 h-96)
   - Back: 384×288px (w-96 h-72)

### 🗄️ **Backend Changes (app.py)**
1. **Updated save_nic_image Endpoint:**
   - Modified filename generation to use NIC number
   - Front images: `{nic_number}_front.jpg`
   - Back images: `{nic_number}_back.jpg`
   - Added NIC number validation (required field)
   - Files are saved in respective folders with overwrite capability

2. **Enhanced Error Handling:**
   - Added validation for NIC number presence
   - Better error messages for debugging
   - Improved response messaging

## New File Naming Convention

### **Before:**
```
uploads/
├── front/
│   ├── front_20250711_143022.jpg
│   ├── front_20250711_143125.jpg
│   └── front_20250711_143230.jpg
└── back/
    ├── back_20250711_143045.jpg
    ├── back_20250711_143148.jpg
    └── back_20250711_143253.jpg
```

### **After:**
```
uploads/
├── front/
│   ├── 200167901631_front.jpg
│   ├── 123456789V_front.jpg
│   └── 987654321X_front.jpg
└── back/
    ├── 200167901631_back.jpg
    ├── 123456789V_back.jpg
    └── 987654321X_back.jpg
```

## Benefits

### ✅ **For Administrators:**
- **Easy Identification:** Files are named with the actual NIC number
- **Better Organization:** No need to check database to match files with records
- **File Management:** Easy to find, backup, or manage specific person's images
- **Overwrite Protection:** New captures replace old ones for the same NIC

### ✅ **For System:**
- **Consistent Naming:** Predictable filename structure
- **Database Integration:** Filenames match database NIC fields
- **Backup & Recovery:** Easy to identify and restore specific images
- **Audit Trails:** Clear connection between NIC and image files

### ✅ **For Users:**
- **Visual Feedback:** Success message shows actual filename saved
- **Transparency:** Users know exactly how their images are stored
- **Confidence:** Clear confirmation of what was captured

## File Structure
```
backend/
├── app.py                    # Updated save_nic_image endpoint
├── templates/
│   └── index.html           # Updated capture functionality
└── uploads/
    ├── front/               # Front NIC images: {nic}_front.jpg
    └── back/                # Back NIC images: {nic}_back.jpg
```

## Technical Details

### **Frontend (JavaScript)**
```javascript
// New filename generation
const nicFilename = `${currentNic}_${nicCaptureStep}.jpg`;
formData.append('nic_image', blob, nicFilename);
formData.append('nic_number', currentNic);
```

### **Backend (Python)**
```python
# New filename logic
nic_number = request.form.get('nic_number', '')
if image_type == 'front':
    filename = f"{nic_number}_front.jpg"
else:
    filename = f"{nic_number}_back.jpg"
```

### **Database Storage**
- The database continues to store the full filepath
- FrontNICImage: `uploads/front/200167901631_front.jpg`
- BackNICImage: `uploads/back/200167901631_back.jpg`

## Usage Examples

### **For NIC: 200167901631**
- Front image: `200167901631_front.jpg`
- Back image: `200167901631_back.jpg`

### **For NIC: 123456789V**
- Front image: `123456789V_front.jpg`  
- Back image: `123456789V_back.jpg`

## Future Enhancements
1. **Version Control:** Add timestamp suffix for multiple captures per day
2. **Compression:** Implement image compression to save storage
3. **Cleanup:** Automatic deletion of old images after certain period
4. **Thumbnails:** Generate smaller preview images for faster loading
5. **Metadata:** Store capture timestamp and device info in image EXIF data

## Testing Checklist
- ✅ Front image saves with correct NIC filename
- ✅ Back image saves with correct NIC filename  
- ✅ Files are saved in correct directories
- ✅ Database stores correct filepaths
- ✅ Success messages show actual filenames
- ✅ Error handling works for missing NIC
- ✅ File overwrite works for same NIC
- ✅ Special characters in NIC handled properly
