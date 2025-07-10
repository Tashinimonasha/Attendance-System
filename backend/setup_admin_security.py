#!/usr/bin/env python3
"""
Database initialization script for secure admin users
"""

import mysql.connector
import hashlib

# Database connection
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Tashini258258",  # Update with your MySQL password
        database="AttendanceDB"  # Fixed database name
    )
    cursor = db.cursor()
    print("✅ Connected to AttendanceDB database successfully")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    exit(1)

def create_admin_table():
    """Create admin users table for secure authentication"""
    try:
        # Drop existing table if it has issues and recreate
        print("🔧 Setting up admin_users table...")
        
        cursor.execute("DROP TABLE IF EXISTS admin_users")
        print("   Dropped existing admin_users table (if any)")
        
        cursor.execute("""
            CREATE TABLE `admin_users` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(64) NOT NULL,
                full_name VARCHAR(100),
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        print("✅ Admin users table created successfully")
        
        # Create default admin user with hashed password
        default_password = "printcare2025"
        hashed_password = hashlib.sha256(default_password.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO admin_users (username, password, full_name, email)
            VALUES (%s, %s, %s, %s)
        """, ('admin', hashed_password, 'System Administrator', 'admin@printcare.com'))
        
        print("✅ Default admin user created")
        print("📋 Default admin credentials:")
        print("   Username: admin")
        print("   Password: printcare2025")
        
        db.commit()
        
    except Exception as e:
        print(f"❌ Error creating admin table: {e}")
        db.rollback()

def show_admin_users():
    """Display current admin users"""
    try:
        cursor.execute("SELECT username, full_name, email, created_at FROM admin_users")
        users = cursor.fetchall()
        
        print("\n📋 Current Admin Users:")
        print("-" * 60)
        for user in users:
            print(f"Username: {user[0]}")
            print(f"Name: {user[1] or 'N/A'}")
            print(f"Email: {user[2] or 'N/A'}")
            print(f"Created: {user[3]}")
            print("-" * 60)
            
    except Exception as e:
        print(f"❌ Error displaying admin users: {e}")

def add_admin_user():
    """Add a new admin user"""
    print("\n➕ Add New Admin User")
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    full_name = input("Enter full name (optional): ").strip() or None
    email = input("Enter email (optional): ").strip() or None
    
    if not username or not password:
        print("❌ Username and password are required")
        return
    
    try:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("""
            INSERT INTO admin_users (username, password, full_name, email)
            VALUES (%s, %s, %s, %s)
        """, (username, hashed_password, full_name, email))
        
        db.commit()
        print(f"✅ Admin user '{username}' created successfully")
        
    except mysql.connector.IntegrityError:
        print(f"❌ Username '{username}' already exists")
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")

def main():
    print("🔧 Printcare Admin Database Setup")
    print("=" * 40)
    
    # Create admin table and default user
    create_admin_table()
    
    while True:
        print("\n📋 Options:")
        print("1. Show admin users")
        print("2. Add new admin user")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            show_admin_users()
        elif choice == '2':
            add_admin_user()
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")
    
    cursor.close()
    db.close()

if __name__ == "__main__":
    main()
