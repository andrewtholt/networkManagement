#!/usr/bin/env python3

import subprocess
import sys
import getpass
import time

def run_mysql_command(command, user="root", password=None, use_sudo=False):
    """
    Execute a MySQL command with proper authentication
    """
    try:
        if use_sudo:
            cmd = ['sudo', 'mysql', '-e', command]
        elif password:
            cmd = ['mysql', '-u', user, f'-p{password}', '-e', command]
        else:
            cmd = ['mysql', '-u', user, '-e', command]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return result.returncode == 0, result.stdout, result.stderr
    
    except Exception as e:
        return False, "", str(e)

def check_mysql_service():
    """
    Check if MySQL service is running
    """
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', 'mysql'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False

def start_mysql_service():
    """
    Attempt to start MySQL service
    """
    try:
        result = subprocess.run(
            ['sudo', 'systemctl', 'start', 'mysql'],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False

def test_mysql_connection():
    """
    Test different MySQL connection methods
    """
    print("Testing MySQL connection methods...")
    
    # Method 1: Try sudo mysql (common on Ubuntu)
    success, stdout, stderr = run_mysql_command("SELECT 1;", use_sudo=True)
    if success:
        print("✓ Connection successful using sudo mysql")
        return "sudo", None, None
    
    # Method 2: Try root without password
    success, stdout, stderr = run_mysql_command("SELECT 1;", user="root")
    if success:
        print("✓ Connection successful as root without password")
        return "root", "root", None
    
    # Method 3: Try root with password
    print("\nAttempting to connect as root with password...")
    try:
        password = getpass.getpass("Enter MySQL root password (or press Enter to skip): ")
        if password:
            success, stdout, stderr = run_mysql_command("SELECT 1;", user="root", password=password)
            if success:
                print("✓ Connection successful as root with password")
                return "password", "root", password
    except KeyboardInterrupt:
        print("\nSkipping password authentication...")
    
    # Method 4: Check debian-sys-maint
    try:
        result = subprocess.run(
            ['sudo', 'cat', '/etc/mysql/debian.cnf'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            user_line = next((line for line in lines if line.startswith('user')), None)
            pass_line = next((line for line in lines if line.startswith('password')), None)
            
            if user_line and pass_line:
                debian_user = user_line.split('=')[1].strip()
                debian_pass = pass_line.split('=')[1].strip()
                
                success, stdout, stderr = run_mysql_command("SELECT 1;", user=debian_user, password=debian_pass)
                if success:
                    print(f"✓ Connection successful using {debian_user}")
                    return "debian", debian_user, debian_pass
    except:
        pass
    
    print("✗ Unable to establish MySQL connection")
    return None, None, None

def create_database_and_user(method, user, password):
    """
    Create the network_info database and andrewh user
    """
    print("\nCreating database and user...")
    
    # SQL commands to execute
    commands = [
        "CREATE DATABASE IF NOT EXISTS network_info;",
        "CREATE USER IF NOT EXISTS 'andrewh'@'localhost' IDENTIFIED BY 'letmein';",
        "GRANT ALL PRIVILEGES ON network_info.* TO 'andrewh'@'localhost';",
        "FLUSH PRIVILEGES;",
        "USE network_info;",
        """
        CREATE TABLE IF NOT EXISTS arp_table (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ip_address VARCHAR(15) NOT NULL,
            hw_address VARCHAR(17) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            state VARCHAR(8) DEFAULT 'DOWN',
            hostname VARCHAR(32) DEFAULT 'unknown'
        );
        """
    ]
    
    # Combine all commands
    full_command = " ".join(commands)
    
    # Execute based on connection method
    if method == "sudo":
        success, stdout, stderr = run_mysql_command(full_command, use_sudo=True)
    elif method == "debian":
        success, stdout, stderr = run_mysql_command(full_command, user=user, password=password)
    else:
        success, stdout, stderr = run_mysql_command(full_command, user=user, password=password)
    
    if success:
        print("✓ Database and table created successfully")
        return True
    else:
        print(f"✗ Error creating database: {stderr}")
        return False

def verify_setup():
    """
    Verify the setup by testing the andrewh user connection
    """
    print("\nVerifying setup...")
    
    # Test andrewh user connection
    success, stdout, stderr = run_mysql_command(
        "USE network_info; DESCRIBE arp_table;",
        user="andrewh",
        password="letmein"
    )
    
    if success:
        print("✓ Setup verification successful")
        print("✓ User 'andrewh' can access network_info database")
        print("✓ Table 'arp_table' exists with correct structure")
        
        # Show table structure
        lines = stdout.strip().split('\n')
        if len(lines) > 1:
            print("\nTable structure:")
            for line in lines:
                if line.strip():
                    print(f"  {line}")
        
        return True
    else:
        print(f"✗ Verification failed: {stderr}")
        return False

def show_next_steps():
    """
    Display next steps for the user
    """
    print("\n" + "="*60)
    print("SETUP COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("1. Populate the database with current ARP entries:")
    print("   python3 update_network_info.py")
    print("\n2. View the entries:")
    print("   python3 display_arp_entries.py")
    print("\n3. Set hostnames for devices:")
    print("   python3 set_hostname.py 192.168.0.1 gateway")
    print("\n4. Set up automated monitoring (optional):")
    print("   # Add to crontab:")
    print("   */5 * * * * /usr/bin/python3 /home/andrewh/update_network_info.py --quiet")
    print("\nDatabase Details:")
    print("  Database: network_info")
    print("  Table: arp_table")
    print("  User: andrewh")
    print("  Password: letmein")
    print("\nFor more information, see README.md")

def main():
    """
    Main setup function
    """
    print("Network Info Database Setup")
    print("="*40)
    print("This script will:")
    print("1. Check MySQL service status")
    print("2. Create the 'network_info' database")
    print("3. Create the 'andrewh' user with appropriate permissions")
    print("4. Create the 'arp_table' with all required columns")
    print("5. Verify the setup")
    print()
    
    # Check if user wants to continue
    try:
        response = input("Continue with setup? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Setup cancelled.")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nSetup cancelled.")
        sys.exit(0)
    
    print("\nStarting setup...")
    
    # Step 1: Check MySQL service
    print("\n1. Checking MySQL service...")
    if not check_mysql_service():
        print("MySQL service is not running. Attempting to start...")
        if start_mysql_service():
            print("✓ MySQL service started")
            time.sleep(2)  # Give service time to start
        else:
            print("✗ Failed to start MySQL service")
            print("Please ensure MySQL is installed and start it manually:")
            print("  sudo systemctl start mysql")
            sys.exit(1)
    else:
        print("✓ MySQL service is running")
    
    # Step 2: Test connection
    print("\n2. Testing MySQL connection...")
    method, user, password = test_mysql_connection()
    
    if not method:
        print("\nUnable to connect to MySQL. Please check:")
        print("1. MySQL is properly installed")
        print("2. You have appropriate permissions")
        print("3. MySQL root password is correct")
        sys.exit(1)
    
    # Step 3: Create database and user
    print("\n3. Setting up database...")
    if not create_database_and_user(method, user, password):
        print("Database setup failed. Please check MySQL permissions.")
        sys.exit(1)
    
    # Step 4: Verify setup
    print("\n4. Verifying setup...")
    if not verify_setup():
        print("Setup verification failed. Please check the configuration.")
        sys.exit(1)
    
    # Step 5: Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()

