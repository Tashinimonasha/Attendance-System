import mysql.connector
from datetime import datetime

def setup_database():
    """Setup AttendanceDB and create required tables"""
    print("🔧 ATTENDANCE DATABASE SETUP")
    print("=" * 50)
    
    try:
        # Connect to MySQL server (without specifying database)
        print("Connecting to MySQL server...")
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Tashini258258"
        )
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        print("Creating database 'AttendanceDB' if not exists...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS AttendanceDB")
        cursor.execute("USE AttendanceDB")
        print("✅ Database 'AttendanceDB' ready")
        
        # Create attendance table
        print("Creating attendance table...")
        create_attendance_table = """
        CREATE TABLE IF NOT EXISTS attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nic VARCHAR(20) NOT NULL,
            action ENUM('IN', 'OUT') NOT NULL,
            time DATETIME NOT NULL,
            company VARCHAR(10) NOT NULL,
            INDEX idx_nic (nic),
            INDEX idx_time (time),
            INDEX idx_company (company)
        )
        """
        cursor.execute(create_attendance_table)
        print("✅ Attendance table ready")
        
        # Create admin_users table
        print("Creating admin_users table...")
        create_admin_table = """
        CREATE TABLE IF NOT EXISTS admin_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(64) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_admin_table)
        print("✅ Admin users table ready")
        
        # Insert default admin user if not exists
        print("Setting up default admin user...")
        cursor.execute("SELECT COUNT(*) FROM admin_users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO admin_users (username, password) 
                VALUES ('admin', SHA2('printcare2025', 256))
            """)
            print("✅ Default admin user created (admin/printcare2025)")
        else:
            print("✅ Admin user already exists")
        
        # Test insert
        print("Testing database operations...")
        test_time = datetime.now()
        cursor.execute("""
            INSERT INTO attendance (nic, action, time, company) 
            VALUES (%s, %s, %s, %s)
        """, ("999999999V", "IN", test_time, "TEST"))
        
        # Verify insert
        cursor.execute("SELECT * FROM attendance WHERE nic = '999999999V'")
        result = cursor.fetchone()
        if result:
            print(f"✅ Test record created: {result}")
            
            # Clean up test record
            cursor.execute("DELETE FROM attendance WHERE nic = '999999999V'")
            print("✅ Test record cleaned up")
        
        connection.commit()
        connection.close()
        
        print("\n🎉 DATABASE SETUP COMPLETE!")
        print("✅ Database: AttendanceDB")
        print("✅ Tables: attendance, admin_users")
        print("✅ Admin login: admin / printcare2025")
        print("✅ Ready for attendance recording!")
        
        return True
        
    except mysql.connector.Error as err:
        print(f"❌ MySQL Error: {err}")
        print("\n🔧 Please check:")
        print("1. MySQL service is running")
        print("2. Username/password: root/Tashini258258")
        print("3. MySQL accepts connections on localhost:3306")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = setup_database()
    print("\n" + "=" * 50)
    if success:
        print("✅ You can now run the attendance system!")
    else:
        print("❌ Please fix database issues before running the system")
    
    input("Press Enter to exit...")
