#!/usr/bin/env python3

import subprocess
import sys
import re

def get_device_by_ip(ip_address):
    """
    Get device information by IP address from the database
    Returns (id, ip_address, hw_address, state, hostname) or None if not found
    """
    try:
        cmd = [
            'mysql',
            '-u', 'andrewh',
            '-pletmein',
            '-e', f"USE network_info; SELECT id, ip_address, hw_address, state, hostname FROM arp_table WHERE ip_address = '{ip_address}';"
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error querying database: {result.stderr}")
            return None
        
        lines = result.stdout.strip().split('\n')
        
        # Check if we have data beyond header
        if len(lines) > 1:
            for line in lines[1:]:  # Skip header
                if line.strip():
                    columns = line.split('\t')
                    if len(columns) >= 5:
                        return {
                            'id': columns[0].strip(),
                            'ip_address': columns[1].strip(),
                            'hw_address': columns[2].strip(),
                            'state': columns[3].strip(),
                            'hostname': columns[4].strip()
                        }
        
        return None
    
    except Exception as e:
        print(f"Error getting device info: {e}")
        return None

def update_hostname(device_id, new_hostname):
    """
    Update the hostname for a device in the database
    """
    try:
        # Escape single quotes in hostname
        safe_hostname = new_hostname.replace("'", "''")
        
        cmd = [
            'mysql',
            '-u', 'andrewh',
            '-pletmein',
            '-e', f"USE network_info; UPDATE arp_table SET hostname = '{safe_hostname}' WHERE id = {device_id};"
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            return True
        else:
            print(f"Error updating hostname: {result.stderr}")
            return False
    
    except Exception as e:
        print(f"Error updating hostname: {e}")
        return False

def validate_ip_address(ip):
    """
    Validate if the given string is a valid IP address
    """
    pattern = r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return re.match(pattern, ip) is not None

def validate_hostname(hostname):
    """
    Validate hostname according to RFC standards
    """
    if not hostname or len(hostname) > 32:
        return False
    
    # Allow letters, numbers, hyphens, and dots
    # Cannot start or end with hyphen
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\.-]*[a-zA-Z0-9])?$'
    return re.match(pattern, hostname) is not None

def list_devices():
    """
    List all devices in the database for reference
    """
    try:
        cmd = [
            'mysql',
            '-u', 'andrewh',
            '-pletmein',
            '-e', 'USE network_info; SELECT ip_address, hw_address, state, hostname FROM arp_table ORDER BY INET_ATON(ip_address);'
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            
            if len(lines) > 1:
                print("\nCurrent devices in database:")
                print("=" * 70)
                print(f"{'IP Address':<15} {'HW Address':<18} {'State':<8} {'Hostname':<15}")
                print("-" * 70)
                
                for line in lines[1:]:
                    if line.strip():
                        columns = line.split('\t')
                        if len(columns) >= 4:
                            ip = columns[0].strip()
                            mac = columns[1].strip()
                            state = columns[2].strip()
                            hostname = columns[3].strip() if len(columns) > 3 else 'unknown'
                            print(f"{ip:<15} {mac:<18} {state:<8} {hostname:<15}")
                
                print("-" * 70)
                print(f"Total devices: {len(lines) - 1}")
            else:
                print("No devices found in database")
        else:
            print(f"Error listing devices: {result.stderr}")
    
    except Exception as e:
        print(f"Error listing devices: {e}")

def set_hostname_interactive(ip_address):
    """
    Interactive function to set hostname for a given IP address
    """
    # Validate IP address format
    if not validate_ip_address(ip_address):
        print(f"Error: '{ip_address}' is not a valid IP address")
        return False
    
    # Get device information
    print(f"Looking up device with IP address: {ip_address}")
    device = get_device_by_ip(ip_address)
    
    if not device:
        print(f"Error: No device found with IP address {ip_address}")
        print("\nHint: Use --list to see all available devices")
        return False
    
    # Display current device information
    print("\nDevice found:")
    print("=" * 50)
    print(f"ID:         {device['id']}")
    print(f"IP Address: {device['ip_address']}")
    print(f"HW Address: {device['hw_address']}")
    print(f"State:      {device['state']}")
    print(f"Hostname:   {device['hostname']}")
    print("=" * 50)
    
    # Prompt for new hostname
    while True:
        try:
            new_hostname = input(f"\nEnter new hostname for {ip_address} (or 'cancel' to abort): ").strip()
            
            if new_hostname.lower() == 'cancel':
                print("Operation cancelled.")
                return False
            
            if not new_hostname:
                print("Error: Hostname cannot be empty")
                continue
            
            if not validate_hostname(new_hostname):
                print("Error: Invalid hostname format")
                print("Hostname must:")
                print("  - Be 1-32 characters long")
                print("  - Contain only letters, numbers, hyphens, and dots")
                print("  - Not start or end with a hyphen")
                continue
            
            # Confirm the change
            confirm = input(f"\nConfirm: Set hostname '{new_hostname}' for {ip_address}? (y/N): ").strip().lower()
            
            if confirm in ['y', 'yes']:
                break
            elif confirm in ['n', 'no', '']:
                print("Operation cancelled.")
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no")
        
        except KeyboardInterrupt:
            print("\n\nOperation cancelled.")
            return False
        except EOFError:
            print("\n\nOperation cancelled.")
            return False
    
    # Update the hostname
    print(f"\nUpdating hostname...")
    
    if update_hostname(device['id'], new_hostname):
        print(f"Success: Hostname updated to '{new_hostname}' for {ip_address}")
        
        # Show updated device info
        updated_device = get_device_by_ip(ip_address)
        if updated_device:
            print("\nUpdated device information:")
            print("-" * 30)
            print(f"IP Address: {updated_device['ip_address']}")
            print(f"HW Address: {updated_device['hw_address']}")
            print(f"State:      {updated_device['state']}")
            print(f"Hostname:   {updated_device['hostname']}")
        
        return True
    else:
        print(f"Error: Failed to update hostname for {ip_address}")
        return False

def set_hostname_direct(ip_address, hostname):
    """
    Directly set hostname for a given IP address without prompting
    """
    # Validate IP address format
    if not validate_ip_address(ip_address):
        print(f"Error: '{ip_address}' is not a valid IP address")
        return False
    
    # Validate hostname format
    if not validate_hostname(hostname):
        print(f"Error: Invalid hostname '{hostname}'")
        print("Hostname must:")
        print("  - Be 1-32 characters long")
        print("  - Contain only letters, numbers, hyphens, and dots")
        print("  - Not start or end with a hyphen")
        return False
    
    # Get device information
    print(f"Looking up device with IP address: {ip_address}")
    device = get_device_by_ip(ip_address)
    
    if not device:
        print(f"Error: No device found with IP address {ip_address}")
        print("\nHint: Use --list to see all available devices")
        return False
    
    # Display current device information
    print("\nDevice found:")
    print("=" * 50)
    print(f"ID:         {device['id']}")
    print(f"IP Address: {device['ip_address']}")
    print(f"HW Address: {device['hw_address']}")
    print(f"State:      {device['state']}")
    print(f"Current Hostname: {device['hostname']}")
    print(f"New Hostname:     {hostname}")
    print("=" * 50)
    
    # Update the hostname
    print(f"\nUpdating hostname to '{hostname}'...")
    
    if update_hostname(device['id'], hostname):
        print(f"Success: Hostname updated to '{hostname}' for {ip_address}")
        
        # Show updated device info
        updated_device = get_device_by_ip(ip_address)
        if updated_device:
            print("\nUpdated device information:")
            print("-" * 30)
            print(f"IP Address: {updated_device['ip_address']}")
            print(f"HW Address: {updated_device['hw_address']}")
            print(f"State:      {updated_device['state']}")
            print(f"Hostname:   {updated_device['hostname']}")
        
        return True
    else:
        print(f"Error: Failed to update hostname for {ip_address}")
        return False

def main():
    """
    Main function with command line argument parsing
    """
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  python3 {sys.argv[0]} <ip_address> [hostname]     # Set hostname for specific IP")
        print(f"  python3 {sys.argv[0]} --list                      # List all devices")
        print(f"  python3 {sys.argv[0]} --help                      # Show this help")
        print("")
        print("Examples:")
        print(f"  python3 {sys.argv[0]} 192.168.0.1                 # Interactive mode")
        print(f"  python3 {sys.argv[0]} 192.168.0.1 gateway         # Direct mode")
        print(f"  python3 {sys.argv[0]} 192.168.0.50 printer        # Direct mode")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    if arg == '--help':
        print("Set Hostname Tool")
        print("=" * 20)
        print("This script allows you to set hostnames for devices in the network_info database.")
        print("")
        print("Usage:")
        print(f"  python3 {sys.argv[0]} <ip_address> [hostname]     # Set hostname for specific IP")
        print(f"  python3 {sys.argv[0]} --list                      # List all devices")
        print(f"  python3 {sys.argv[0]} --help                      # Show this help")
        print("")
        print("Modes:")
        print("  Interactive: Provide only IP address, script will prompt for hostname")
        print("  Direct:      Provide both IP address and hostname on command line")
        print("")
        print("The script will:")
        print("  1. Look up the device by IP address")
        print("  2. Display current device information")
        print("  3. Either prompt for hostname (interactive) or use provided hostname (direct)")
        print("  4. Validate the hostname format")
        print("  5. Update the database with the new hostname")
        print("")
        print("Hostname requirements:")
        print("  - 1-32 characters long")
        print("  - Letters, numbers, hyphens, and dots only")
        print("  - Cannot start or end with hyphen")
    
    elif arg == '--list':
        list_devices()
    
    else:
        # Treat as IP address
        ip_address = arg
        
        # Check if hostname was provided on command line
        if len(sys.argv) >= 3:
            # Direct mode - hostname provided
            hostname = sys.argv[2]
            success = set_hostname_direct(ip_address, hostname)
        else:
            # Interactive mode - prompt for hostname
            success = set_hostname_interactive(ip_address)
        
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

