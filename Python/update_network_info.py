#!/usr/bin/env python3

import subprocess
import sys
import re
import time

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
    Returns a dict with (ip_address, hw_address) as key and (id, state) as value
    """
    try:
        cmd = [
            'mysql',
            '-u', 'andrewh',
            '-pletmein',
            '-e', 'USE network_info; SELECT id, ip_address, hw_address, state FROM arp_table;'
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error reading existing entries: {result.stderr}")
            return {}
        
        existing_entries = {}
        lines = result.stdout.strip().split('\n')
        
        # Skip header line if present
        for line in lines[1:] if len(lines) > 1 else []:
            if line.strip():
                columns = line.split('\t')
                if len(columns) >= 4:
                    entry_id = columns[0].strip()
                    ip_addr = columns[1].strip()
                    hw_addr = columns[2].strip().lower()
                    state = columns[3].strip()
                    existing_entries[(ip_addr, hw_addr)] = (entry_id, state)
        
        return existing_entries
    
    except Exception as e:
        print(f"Error getting existing entries: {e}")
        return {}

def ping_host(ip_address, timeout=2):
    """
    Ping a host to check if it's reachable
    Returns True if host responds, False otherwise
    """
    try:
        # Use ping command with timeout
        result = subprocess.run(
            ['ping', '-c', '1', '-W', str(timeout), ip_address],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def determine_state(ip_address, check_connectivity=True):
    """
    Determine the state of a host based on connectivity
    Returns 'UP' if reachable, 'DOWN' if not, 'UNKNOWN' if check is disabled
    """
    if not check_connectivity:
        return 'UNKNOWN'
    
    if ping_host(ip_address):
        return 'UP'
    else:
        return 'DOWN'

def insert_new_entries(new_entries, check_connectivity=True):
    """
    Insert new ARP entries into the database with state determination
    """
    if not new_entries:
        print("No new entries to insert")
        return
    
    try:
        print(f"Inserting {len(new_entries)} new entries...")
        insert_statements = []
        
        for ip_addr, hw_addr in new_entries:
            # Determine state by pinging
            state = determine_state(ip_addr, check_connectivity)
            print(f"  {ip_addr} -> {hw_addr} (State: {state})")
            
            insert_statements.append(
                f"INSERT INTO arp_table (ip_address, hw_address, state) VALUES ('{ip_addr}', '{hw_addr}', '{state}');"
            )
        
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

def update_existing_states(existing_entries, current_arp_set, check_connectivity=True):
    """
    Update states of existing entries based on current ARP presence and connectivity
    """
    try:
        updates = []
        
        for (ip_addr, hw_addr), (entry_id, current_state) in existing_entries.items():
            new_state = None
            
            if (ip_addr, hw_addr) in current_arp_set:
                # Entry is in current ARP table
                if check_connectivity:
                    new_state = determine_state(ip_addr, True)
                else:
                    new_state = 'UP'  # Present in ARP = UP
            else:
                # Entry not in current ARP table
                new_state = 'DOWN'
            
            # Only update if state has changed
            if new_state != current_state:
                updates.append((entry_id, ip_addr, hw_addr, current_state, new_state))
        
        if updates:
            print(f"\nUpdating states for {len(updates)} existing entries...")
            update_statements = []
            
            for entry_id, ip_addr, hw_addr, old_state, new_state in updates:
                print(f"  {ip_addr} -> {hw_addr}: {old_state} -> {new_state}")
                update_statements.append(
                    f"UPDATE arp_table SET state = '{new_state}' WHERE id = {entry_id};"
                )
            
            # Execute updates
            sql_commands = "USE network_info; " + " ".join(update_statements)
            
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
                print(f"Successfully updated {len(updates)} entries")
            else:
                print(f"Error updating entries: {result.stderr}")
        else:
            print("\nNo state updates needed for existing entries")
    
    except Exception as e:
        print(f"Error updating existing states: {e}")

def update_network_database(check_connectivity=True, verbose=True):
    """
    Main function to update the network_info database with current ARP entries and states
    """
    print("Updating Network Info Database")
    print("=" * 50)
    print(f"Connectivity checking: {'Enabled' if check_connectivity else 'Disabled'}")
    print()
    
    # Get current ARP entries from system
    if verbose:
        print("Getting current ARP entries from system...")
    current_entries = get_current_arp_entries()
    print(f"Found {len(current_entries)} current ARP entries")
    
    if not current_entries:
        print("No ARP entries found. Exiting.")
        return
    
    # Display current entries
    if verbose:
        print("\nCurrent ARP entries:")
        for ip, mac in current_entries:
            print(f"  {ip} -> {mac}")
    
    # Get existing entries from database
    print("\nGetting existing entries from database...")
    existing_entries = get_existing_entries()
    print(f"Found {len(existing_entries)} existing database entries")
    
    # Find new entries
    current_set = set(current_entries)
    existing_set = set(existing_entries.keys())
    new_entries = current_set - existing_set
    
    # Insert new entries
    if new_entries:
        print(f"\nFound {len(new_entries)} new entries to add:")
        insert_new_entries(list(new_entries), check_connectivity)
    else:
        print("\nNo new entries found.")
    
    # Update existing entry states
    if existing_entries:
        update_existing_states(existing_entries, current_set, check_connectivity)
    
    print("\nUpdate complete!")
    
    # Show final summary
    print("\n" + "=" * 50)
    print("Final Database Summary:")
    show_summary()

def show_summary():
    """
    Show summary statistics of the arp_table
    """
    try:
        cmd = [
            'mysql',
            '-u', 'andrewh',
            '-pletmein',
            '-e', 'USE network_info; SELECT state, COUNT(*) as count FROM arp_table GROUP BY state ORDER BY state;'
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
                total = 0
                for line in lines[1:]:
                    if line.strip():
                        columns = line.split('\t')
                        if len(columns) >= 2:
                            state = columns[0].strip()
                            count = int(columns[1].strip())
                            total += count
                            print(f"  {state}: {count} entries")
                print(f"  Total: {total} entries")
            else:
                print("  No data available")
        
    except Exception as e:
        print(f"Error getting summary: {e}")

def main():
    """
    Main function with command line options
    """
    check_connectivity = True
    verbose = True
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if '--no-ping' in sys.argv:
            check_connectivity = False
        if '--quiet' in sys.argv:
            verbose = False
        if '--help' in sys.argv:
            print("Usage:")
            print("  python3 update_network_info.py              # Update with connectivity check")
            print("  python3 update_network_info.py --no-ping    # Update without pinging hosts")
            print("  python3 update_network_info.py --quiet      # Less verbose output")
            print("  python3 update_network_info.py --help       # Show this help")
            print("")
            print("This script:")
            print("  - Gets current ARP table entries")
            print("  - Adds new entries to the database")
            print("  - Updates states of existing entries")
            print("  - Uses ping to determine UP/DOWN states (unless --no-ping)")
            return
    
    update_network_database(check_connectivity, verbose)

if __name__ == "__main__":
    main()

