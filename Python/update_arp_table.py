#!/usr/bin/env python3

import subprocess
import sys
import re

def get_current_arp_entries():
    """
    Get current ARP entries from the system
    Returns a list of tuples (ip_address, hw_address)
    """
    try:
        # Get ARP table entries
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error getting ARP entries: {result.stderr}")
            return []
        
        arp_entries = []
        lines = result.stdout.strip().split('\n')
        
        for line in lines:
            if line.strip():
                # Parse ARP line format: name (ip) at hw_addr [ether] on interface
                # Extract IP and MAC address using regex
                ip_match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)', line)
                mac_match = re.search(r'at ([0-9a-fA-F:]{17})', line)
                
                if ip_match and mac_match:
                    ip_addr = ip_match.group(1)
                    hw_addr = mac_match.group(1).lower()  # Normalize to lowercase
                    arp_entries.append((ip_addr, hw_addr))
        
        return arp_entries
    
    except Exception as e:
        print(f"Error parsing ARP entries: {e}")
        return []

def get_existing_entries():
    """
    Get existing entries from the database
    Returns a set of tuples (ip_address, hw_address)
    """
    try:
        cmd = [
            'mysql',
            '-u', 'andrewh',
            '-pletmein',
            '-e', 'USE network_info; SELECT ip_address, hw_address FROM arp_table;'
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error reading existing entries: {result.stderr}")
            return set()
        
        existing_entries = set()
        lines = result.stdout.strip().split('\n')
        
        # Skip header line if present
        for line in lines[1:] if len(lines) > 1 else []:
            if line.strip():
                columns = line.split('\t')
                if len(columns) >= 2:
                    ip_addr = columns[0].strip()
                    hw_addr = columns[1].strip().lower()
                    existing_entries.add((ip_addr, hw_addr))
                else:
                    print(len(couumns))

        
        return existing_entries
    
    except Exception as e:
        print(f"Error getting existing entries: {e}")
        return set()

def insert_new_entries(new_entries):
    """
    Insert new ARP entries into the database
    """
    if not new_entries:
        print("No new entries to insert")
        return
    
    try:
        # Prepare SQL insert statements
        insert_statements = []
        for ip_addr, hw_addr in new_entries:
            insert_statements.append(f"INSERT INTO arp_table (ip_address, hw_address) VALUES ('{ip_addr}', '{hw_addr}');")
        
        # Combine all insert statements
        sql_commands = "USE network_info; " + " ".join(insert_statements)
        
        cmd = [
            'mysql',
            '-u', 'andrewh',
            '-pletmein',
            '-e', sql_commands
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            print(f"Successfully inserted {len(new_entries)} new entries")
        else:
            print(f"Error inserting entries: {result.stderr}")
    
    except Exception as e:
        print(f"Error inserting new entries: {e}")

def update_arp_database():
    """
    Main function to update the ARP database with current system entries
    """
    print("Updating ARP database...")
    print("=" * 50)
    
    # Get current ARP entries from system
    print("Getting current ARP entries from system...")
    current_entries = get_current_arp_entries()
    print(f"Found {len(current_entries)} current ARP entries")
    
    if not current_entries:
        print("No ARP entries found. Exiting.")
        return
    
    # Display current entries
    print("\nCurrent ARP entries:")
    for ip, mac in current_entries:
        print(f"  {ip} -> {mac}")
    
    # Get existing entries from database
    print("\nGetting existing entries from database...")
    existing_entries = get_existing_entries()
    print(f"Found {len(existing_entries)} existing database entries")
    
    # Find new entries
    current_set = set(current_entries)
    new_entries = current_set - existing_entries
    
    if new_entries:
        print(f"\nFound {len(new_entries)} new entries to add:")
        for ip, mac in new_entries:
            print(f"  {ip} -> {mac}")
        
        # Insert new entries
        print("\nInserting new entries into database...")
        insert_new_entries(list(new_entries))
    else:
        print("\nNo new entries found. Database is up to date.")
    
    print("\nUpdate complete!")

if __name__ == "__main__":
    update_arp_database()

