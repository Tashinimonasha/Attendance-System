#!/usr/bin/env python3
"""
Simple Database Fix Script for Attendance System
This script creates a simple attendancerecords table like the original design
"""

import mysql.connector
import sys
from datetime import datetime, timedelta
import random

def fix_database():
    print("🔧 Starting Simple Database Fix...")
    
    try:
        # Connect to MySQL server
        print("📡 Connecting to MySQL server...")
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Tashini258258"
        )
        cursor = connection.cursor()
        print("✅ Connected to MySQL server successfully")
        
        # Create database if it doesn't exist
        print("🗄️ Creating database if not exists...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS AttendanceDB")
        cursor.execute("USE AttendanceDB")
        print("✅ Database AttendanceDB ready")
        
        # Drop and recreate tables
        print("🔨 Recreating AttendanceRecords table...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DROP TABLE IF EXISTS AttendanceRecords")
        cursor.execute("DROP TABLE IF EXISTS Workers")
        cursor.execute("DROP TABLE IF EXISTS attendancerecords")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        print("🗑️ Dropped existing tables")
        
        # Create AttendanceRecords table with all new modifications
        attendance_table = """
        CREATE TABLE `AttendanceRecords` (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            NIC VARCHAR(20) NOT NULL,
            Date DATE NOT NULL,
            InTime TIME,
            OutTime TIME,
            Shift VARCHAR(50) DEFAULT 'Morning',
            Status ENUM('Check in', 'Completed', 'Pending') DEFAULT 'Check in',
            Company ENUM('PUL', 'PCL', 'PPM', 'PDSL') DEFAULT 'PUL',
            FrontNICImage VARCHAR(255),
            BackNICImage VARCHAR(255),
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_nic (NIC),
            INDEX idx_date (Date),
            INDEX idx_shift (Shift),
            INDEX idx_company (Company),
            INDEX idx_status (Status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        cursor.execute(attendance_table)
        print("✅ AttendanceRecords table created with new columns (NIC images, updated companies, status)")
        
        # Insert your specific example data first (ID 1 and 2 with 2025-05-01)
        print("📅 Adding your example attendance records...")
        
        # Your specific example data with 2025-05-01 date
        example_data = [
            ('123456789V', '2025-05-01', '06:30:00', '14:30:00', 'Morning', 'Check in', 'PUL', 'front_123456789V.jpg', 'back_123456789V.jpg'),
            ('987654321V', '2025-05-01', '14:45:00', '22:00:00', 'Evening', 'Completed', 'PCL', 'front_987654321V.jpg', 'back_987654321V.jpg')
        ]
        
        # Insert example data with all new columns
        insert_example_query = """
        INSERT INTO `AttendanceRecords` (NIC, Date, InTime, OutTime, Shift, Status, Company, FrontNICImage, BackNICImage)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.executemany(insert_example_query, example_data)
        print(f"✅ Added {len(example_data)} example records")
        
        # Insert comprehensive attendance data from May to July 7th, 2025
        print("📅 Adding attendance records from May to July 7th...")
        
        attendance_data = []
        
        # Define workers with updated NIC format and companies
        workers = [
            {'nic': '200165432567', 'company': 'PUL'},
            {'nic': '123456789V', 'company': 'PCL'},
            {'nic': '987654321V', 'company': 'PPM'},
            {'nic': '456789123V', 'company': 'PDSL'},
            {'nic': '789123456V', 'company': 'PUL'},
            {'nic': '321654987V', 'company': 'PCL'},
            {'nic': '234567890V', 'company': 'PPM'},
            {'nic': '345678901V', 'company': 'PDSL'},
            {'nic': '567890123V', 'company': 'PUL'},
            {'nic': '678901234V', 'company': 'PCL'},
            {'nic': '890123456V', 'company': 'PPM'}
        ]
        
        # Define shift times
        shift_schedules = {
            'Morning Shift': [
                ('08:00:00', '17:00:00'),
                ('08:30:00', '17:30:00'),
                ('09:00:00', '18:00:00')
            ],
            'Afternoon Shift': [
                ('13:00:00', '22:00:00'),
                ('14:00:00', '23:00:00'),
                ('15:00:00', '00:00:00')
            ],
            'Evening Shift': [
                ('18:00:00', '03:00:00'),
                ('19:00:00', '04:00:00'),
                ('20:00:00', '05:00:00')
            ],
            'Night Shift': [
                ('22:00:00', '07:00:00'),
                ('23:00:00', '08:00:00'),
                ('00:00:00', '09:00:00')
            ]
        }
        
        # Generate data from May 1st to July 7th, 2025
        start_date = datetime(2025, 5, 1)
        end_date = datetime(2025, 7, 7)
        current_date = start_date
        
        while current_date <= end_date:
            # Skip some Sundays (70% chance to skip)
            if current_date.weekday() == 6 and random.random() < 0.7:
                current_date += timedelta(days=1)
                continue
                
            for worker in workers:
                # 88% attendance rate
                if random.random() < 0.88:
                    # Random shift assignment
                    shift = random.choice(list(shift_schedules.keys()))
                    times = random.choice(shift_schedules[shift])
                    
                    # Add time variation (±20 minutes)
                    in_hour, in_min, _ = map(int, times[0].split(':'))
                    variation = random.randint(-20, 20)
                    in_min += variation
                    
                    # Handle minute overflow
                    if in_min >= 60:
                        in_hour += 1
                        in_min -= 60
                    elif in_min < 0:
                        in_hour -= 1
                        in_min += 60
                        
                    if in_hour >= 24:
                        in_hour -= 24
                    elif in_hour < 0:
                        in_hour += 24
                        
                    actual_in_time = f"{in_hour:02d}:{in_min:02d}:00"
                    
                    # Calculate out time (90% chance of checking out)
                    actual_out_time = None
                    if random.random() < 0.90:
                        out_hour, out_min, _ = map(int, times[1].split(':'))
                        # Add working time (8-9 hours)
                        work_duration = random.randint(480, 540)  # 8-9 hours in minutes
                        
                        # Convert in_time to minutes
                        in_total_minutes = in_hour * 60 + in_min
                        out_total_minutes = in_total_minutes + work_duration
                        
                        # Handle day overflow
                        if out_total_minutes >= 1440:  # 24 hours = 1440 minutes
                            out_total_minutes -= 1440
                            
                        out_hour = out_total_minutes // 60
                        out_min = out_total_minutes % 60
                        
                        actual_out_time = f"{out_hour:02d}:{out_min:02d}:00"
                    
                    # Random status assignment
                    status_options = ['Check in', 'Completed', 'Pending']
                    status = random.choice(status_options)
                    
                    # Generate NIC image filenames
                    front_image = f"front_{worker['nic']}.jpg"
                    back_image = f"back_{worker['nic']}.jpg"
                    
                    attendance_data.append((
                        worker['nic'],
                        current_date.strftime('%Y-%m-%d'),
                        actual_in_time,
                        actual_out_time,
                        shift,
                        status,
                        worker['company'],
                        front_image,
                        back_image
                    ))
            
            current_date += timedelta(days=1)
        
        print(f"📊 Generated {len(attendance_data)} attendance records")
        
        # Insert all attendance data into AttendanceRecords table with all columns
        insert_query = """
        INSERT INTO `AttendanceRecords` (NIC, Date, InTime, OutTime, Shift, Status, Company, FrontNICImage, BackNICImage)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.executemany(insert_query, attendance_data)
        print(f"✅ Added {len(attendance_data)} attendance records")
        
        # Verify the data
        print("🔍 Verifying database...")
        
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"📋 Tables: {[table[0] for table in tables]}")
        
        cursor.execute("SELECT COUNT(*) FROM `AttendanceRecords`")
        total_records = cursor.fetchone()[0]
        print(f"📅 Total attendance records: {total_records}")
        
        cursor.execute("SELECT COUNT(DISTINCT NIC) FROM `AttendanceRecords`")
        unique_workers = cursor.fetchone()[0]
        print(f"👥 Unique workers: {unique_workers}")
        
        cursor.execute("SELECT COUNT(DISTINCT Company) FROM `AttendanceRecords`")
        unique_companies = cursor.fetchone()[0]
        print(f"🏢 Unique companies: {unique_companies}")
        
        # Sample data check
        cursor.execute("""
        SELECT NIC, Date, InTime, OutTime, Shift, Company 
        FROM `AttendanceRecords` 
        ORDER BY Date DESC, InTime DESC 
        LIMIT 5
        """)
        sample_data = cursor.fetchall()
        print("📊 Latest 5 records:")
        for record in sample_data:
            print(f"   {record}")
            
        # Display your specific example data (ID 1 and 2 with 2025-05-01)
        print("\n🧠 Your Example Values in AttendanceRecords (ID 1 & 2):")
        print("=" * 80)
        cursor.execute("""
        SELECT ID, NIC, Date, InTime, OutTime, Shift, Status, Company 
        FROM `AttendanceRecords` 
        WHERE NIC IN ('123456789V', '987654321V') AND Date = '2025-05-01'
        ORDER BY ID
        """)
        example_records = cursor.fetchall()
        print("ID\tNIC\t\tDate\t\tInTime\t\tOutTime\t\tShift\t\tStatus\t\tCompany")
        print("-" * 80)
        for record in example_records:
            id_val, nic, date, intime, outtime, shift, status, company = record
            print(f"{id_val}\t{nic}\t{date}\t{intime}\t\t{outtime}\t\t{shift}\t\t{status}\t\t{company}")
        print("=" * 80)
        
        connection.commit()
        print("✅ Database updated successfully!")
        
    except mysql.connector.Error as err:
        print(f"❌ MySQL Error: {err}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        print("🔐 Connection closed")
    
    print("🎉 Simple database fix completed!")
    return True

if __name__ == "__main__":
    success = fix_database()
    if not success:
        sys.exit(1)
