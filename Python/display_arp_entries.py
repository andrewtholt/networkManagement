#!/usr/bin/env python3

import subprocess
import sys

def display_arp_entries():
    """
    Display all entries from the arp_table in the network_info database
    """
    try:
        # MySQL command to select all entries from arp_table
        cmd = [
            'mysql',
            '-u', 'andrewh',
            '-pletmein',
            '-e', 'USE network_info; SELECT * FROM arp_table ORDER BY id;'
        ]
        
        print("ARP Table Entries")
        print("=" * 95)
        
        # Execute the mysql command
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            # Parse and format the output
            lines = result.stdout.strip().split('\n')
            
            if len(lines) > 1:  # Check if we have data beyond header
                # Print formatted header
                print(f"{'ID':<4} {'IP Address':<15} {'HW Address':<18} {'Created At':<20} {'State':<8} {'Hostname':<15}")
                print("-" * 95)
                
                # Process each data line (skip the MySQL header)
                for line in lines[1:]:
                    if line.strip():  # Skip empty lines
                        columns = line.split('\t')
                        if len(columns) >= 6:
                            id_val = columns[0].strip()
                            ip_addr = columns[1].strip()
                            hw_addr = columns[2].strip()
                            created_at = columns[3].strip()
                            state = columns[4].strip()
                            hostname = columns[5].strip()
                            
                            print(f"{id_val:<4} {ip_addr:<15} {hw_addr:<18} {created_at:<20} {state:<8} {hostname:<15}")
                        elif len(columns) >= 5:  # Fallback for older data without hostname
                            id_val = columns[0].strip()
                            ip_addr = columns[1].strip()
                            hw_addr = columns[2].strip()
                            created_at = columns[3].strip()
                            state = columns[4].strip()
                            
                            print(f"{id_val:<4} {ip_addr:<15} {hw_addr:<18} {created_at:<20} {state:<8} {'unknown':<15}")
                
                print("-" * 95)
                print(f"Total entries: {len(lines) - 1}")
            else:
                print("No entries found in arp_table")
        else:
            print(f"Error connecting to MySQL: {result.stderr}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error displaying ARP entries: {e}")
        sys.exit(1)

def display_entries_by_state(state_filter=None):
    """
    Display entries filtered by state
    """
    try:
        if state_filter:
            query = f"USE network_info; SELECT * FROM arp_table WHERE state = '{state_filter}' ORDER BY id;"
            title = f"ARP Table Entries - State: {state_filter}"
        else:
            query = "USE network_info; SELECT * FROM arp_table ORDER BY id;"
            title = "ARP Table Entries - All States"
        
        cmd = [
            'mysql',
            '-u', 'andrewh',
            '-pletmein',
            '-e', query
        ]
        
        print(title)
        print("=" * 95)
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            
            if len(lines) > 1:
                print(f"{'ID':<4} {'IP Address':<15} {'HW Address':<18} {'Created At':<20} {'State':<8} {'Hostname':<15}")
                print("-" * 95)
                
                for line in lines[1:]:
                    if line.strip():
                        columns = line.split('\t')
                        if len(columns) >= 6:
                            print(f"{columns[0]:<4} {columns[1]:<15} {columns[2]:<18} {columns[3]:<20} {columns[4]:<8} {columns[5]:<15}")
                        elif len(columns) >= 5:  # Fallback for older data without hostname
                            print(f"{columns[0]:<4} {columns[1]:<15} {columns[2]:<18} {columns[3]:<20} {columns[4]:<8} {'unknown':<15}")
                
                print("-" * 95)
                print(f"Total entries: {len(lines) - 1}")
            else:
                print(f"No entries found with state '{state_filter}'" if state_filter else "No entries found")
        else:
            print(f"Error: {result.stderr}")
            
    except Exception as e:
        print(f"Error: {e}")

def show_summary():
    """
    Show summary statistics of the arp_table
    """
    try:
        cmd = [
            'mysql',
            '-u', 'andrewh',
            '-pletmein',
            '-e', 'USE network_info; SELECT state, COUNT(*) as count FROM arp_table GROUP BY state;'
        ]
        
        print("\nARP Table Summary")
        print("=" * 30)
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                print(f"{'State':<10} {'Count':<8}")
                print("-" * 20)
                
                for line in lines[1:]:
                    if line.strip():
                        columns = line.split('\t')
                        if len(columns) >= 2:
                            print(f"{columns[0]:<10} {columns[1]:<8}")
            else:
                print("No data available")
        
    except Exception as e:
        print(f"Error getting summary: {e}")

def main():
    """
    Main function with menu options
    """
    if len(sys.argv) > 1:
        if sys.argv[1] == "--state" and len(sys.argv) > 2:
            display_entries_by_state(sys.argv[2])
        elif sys.argv[1] == "--summary":
            show_summary()
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python3 display_arp_entries.py              # Show all entries")
            print("  python3 display_arp_entries.py --state UP   # Show entries with specific state")
            print("  python3 display_arp_entries.py --summary    # Show summary by state")
            print("  python3 display_arp_entries.py --help       # Show this help")
        else:
            print("Invalid option. Use --help for usage information.")
    else:
        # Default: show all entries
        display_arp_entries()
        show_summary()

if __name__ == "__main__":
    main()

