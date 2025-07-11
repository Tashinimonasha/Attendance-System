# Enhanced NIC Capture System - Yellow Frame Focus

## Overview
The attendance system has been significantly enhanced to provide **highly accurate and user-friendly NIC scanning and image capture**. The system now features an **enhanced yellow frame focus** that guides users to capture perfect NIC images with maximum clarity and user experience.

## Key Features

### 🎯 Enhanced Yellow Frame Focus
- **Prominent yellow frame** with pulsing animation to guide users
- **Dark overlay** that dims everything except the yellow capture area
- **Live preview section** showing exactly what will be captured
- **Real-time cropped preview** with enhanced visual feedback
- **Animated corner indicators** for better alignment guidance

### 📱 Live Preview System
- **Dedicated preview area** below the main camera view
- **Real-time processing** with image enhancement filters
- **Visual capture feedback** with flash effect
- **Live indicator** showing active capture status
- **Enhanced image quality** with contrast and brightness optimization

### 🔄 Updated Workflow for IN Action

### 1. Department Selection
- Choose your department from dropdown

### 2. Press IN/OUT
- Select your desired action

### 3. NIC Extraction  
- **Auto-scan** using enhanced camera detection
- **Manual entry** as fallback option
- **Progressive feedback** during scanning

### 4. Enhanced Image Capture (IN only)
- **Position NIC within pulsing yellow frame**
- **Watch live preview** for perfect alignment  
- **Capture front image** with visual feedback
- **Flip NIC and capture back image**
- **Progress indicators** show completion status

### 5. Verification & Submission
- Review extracted NIC number
- **View actual captured images** in preview
- Submit to database with image paths stored

## New Database Fields
- `FrontNICImage`: Path to front NIC image
- `BackNICImage`: Path to back NIC image

## File Storage Structure
```
uploads/
├── front/
│   └── front_YYYYMMDD_HHMMSS.jpg
└── back/
    └── back_YYYYMMDD_HHMMSS.jpg
```

## New API Endpoints

### 1. `/capture_nic_images` (POST)
- Initiates NIC capture process
- Returns timestamp for unique filenames
- Only for IN actions

### 2. `/save_nic_image` (POST)
- Saves captured NIC image (front or back)
- Extracts NIC number from front image
- Returns image path and extracted NIC

### 3. `/record_attendance` (POST) - Updated
- Now accepts `front_image_path` and `back_image_path` for IN actions
- Validates that images are provided for check-in
- Stores image paths in database

## Key Features

### ✅ For IN (Check-in) Actions:
1. **Mandatory NIC Images**: Both front and back images required
2. **OCR Integration**: Extracts NIC number from front image
3. **Visual Progress**: Shows capture progress with indicators
4. **Error Handling**: Skip option if camera fails
5. **Database Storage**: Image paths stored with attendance record

### ✅ For OUT (Check-out) Actions:
- No image capture required (works as before)
- Only needs NIC number for matching existing record

## User Interface Updates

### New UI Components:
- **NIC Capture Container**: Dedicated interface for image capture
- **Progress Indicators**: Visual feedback for front/back capture
- **Camera Controls**: Capture, skip, and cancel buttons
- **Image Preview**: Confirmation that images were captured

### Enhanced Verification:
- Shows NIC number extracted from front image
- Displays confirmation of captured images
- Success message includes image capture confirmation

## Technical Implementation

### Frontend Changes:
- New capture workflow for IN actions only
- Enhanced camera handling for dual capture
- Progress tracking and visual feedback
- Error handling and skip options

### Backend Changes:
- New routes for image capture and saving
- OCR integration for front image processing
- Database schema supports image path storage
- Enhanced attendance recording with images

## Usage Instructions

### For Workers (IN Action):
1. Select your department
2. Press **IN** button
3. Scan or enter your NIC number
4. **NEW**: Capture front of NIC when prompted
5. **NEW**: Capture back of NIC when prompted
6. Verify NIC number and submit
7. Success! Images and attendance recorded

### For Workers (OUT Action):
1. Select your department
2. Press **OUT** button
3. Scan or enter your NIC number
4. Verify and submit (no image capture needed)

## Error Handling
- Camera access denied: Option to skip image capture
- OCR failure: Manual NIC entry still available
- Network issues: Graceful error messages
- Database errors: Comprehensive error reporting

## Security & Privacy
- Images stored locally in secure folders
- Database paths track image locations
- Access controlled through admin dashboard
- Images linked to specific attendance records

## Admin Dashboard Integration
- View attendance records with image indicators
- Export functionality includes image path data
- Comprehensive reporting with image capture status
