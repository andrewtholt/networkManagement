#!/usr/bin/env python3

import subprocess
import sys

def read_arp_table():
    """
    Connect to MySQL database and read the arp_table contents using mysql command
    """
    try:
        # Use mysql command line client to query the database
        cmd = [
            'mysql',
            '-u', 'andrewh',
            '-pletmein',
            '-e', 'USE network_info; SELECT * FROM arp_table;'
        ]
        
        print("Connecting to MySQL database and reading arp_table...")
        print("-" * 60)
        
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
            if len(lines) > 1:  # Skip the header line
                print(f"{'ID':<4} {'IP Address':<15} {'HW Address':<18} {'Created At':<20}")
                print("-" * 60)
                
                for line in lines[1:]:  # Skip header
                    if line.strip():  # Skip empty lines
                        columns = line.split('\t')
                        if len(columns) >= 4:
                            print(f"{columns[0]:<4} {columns[1]:<15} {columns[2]:<18} {columns[3]}")
                        else:
                            print(len(columns))
                
                print(f"\nTotal records: {len(lines) - 1}")
            else:
                print("No records found in arp_table")
        else:
            print(f"Error connecting to MySQL: {result.stderr}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error executing MySQL query: {e}")
        sys.exit(1)

if __name__ == "__main__":
    read_arp_table()

