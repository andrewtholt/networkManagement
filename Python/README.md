# Network Info Database Utilities

A collection of Python utilities for managing and monitoring network device information using ARP table data stored in a MySQL database.

## Overview

This suite of tools helps you maintain a comprehensive database of network devices by:
- Automatically discovering devices through ARP table monitoring
- Tracking device states (UP/DOWN) with connectivity testing
- Managing human-readable hostnames for network devices
- Providing easy-to-use display and reporting capabilities

## Database Schema

The utilities work with a MySQL database (`network_info`) containing an `arp_table` with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Auto-increment primary key |
| `ip_address` | VARCHAR(15) | IPv4 address of the device |
| `hw_address` | VARCHAR(17) | MAC address of the device |
| `created_at` | TIMESTAMP | When the entry was first added |
| `state` | VARCHAR(8) | Current state: UP, DOWN, or UNKNOWN |
| `hostname` | VARCHAR(32) | Human-readable device name |

## Prerequisites

- **Operating System**: Linux (tested on Ubuntu)
- **Database**: MySQL server
- **Python**: Python 3.x
- **Network Tools**: `arp`, `ping` commands
- **Database Access**: MySQL user with permissions to the `network_info` database

### Database Setup

Use the provided setup script to automatically create the database, user, and table:

```bash
python3 setup_database.py
```

The setup script will:
- Check if MySQL service is running (and start it if needed)
- Test various connection methods to MySQL
- Create the `network_info` database
- Create the `andrewh` user with password `letmein`
- Create the `arp_table` with all required columns
- Verify the setup is working

**Manual Setup (if needed):**
If you prefer manual setup or need to customize the configuration:

```sql
CREATE DATABASE network_info;
CREATE USER 'andrewh'@'localhost' IDENTIFIED BY 'letmein';
GRANT ALL PRIVILEGES ON network_info.* TO 'andrewh'@'localhost';
FLUSH PRIVILEGES;

USE network_info;
CREATE TABLE arp_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip_address VARCHAR(15) NOT NULL,
    hw_address VARCHAR(17) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    state VARCHAR(8) DEFAULT 'DOWN',
    hostname VARCHAR(32) DEFAULT 'unknown'
);
```

## Utilities

### 0. setup_database.py

**Purpose**: Automated database setup and configuration.

#### Features
- Automatically detects and tests MySQL connection methods
- Creates the `network_info` database
- Creates the `andrewh` user with appropriate permissions
- Creates the `arp_table` with all required columns
- Verifies the setup is working correctly
- Handles various MySQL authentication scenarios

#### Usage

```bash
# Run the automated setup
python3 setup_database.py
```

The script will:
1. Check if MySQL service is running (and attempt to start it if not)
2. Test various connection methods (sudo, root, debian-sys-maint)
3. Create database, user, and table
4. Verify the setup
5. Display next steps

#### Example Output
```
Network Info Database Setup
========================================
This script will:
1. Check MySQL service status
2. Create the 'network_info' database
3. Create the 'andrewh' user with appropriate permissions
4. Create the 'arp_table' with all required columns
5. Verify the setup

Continue with setup? (y/N): y

Starting setup...

1. Checking MySQL service...
✓ MySQL service is running

2. Testing MySQL connection...
Testing MySQL connection methods...
✓ Connection successful using sudo mysql

3. Setting up database...

Creating database and user...
✓ Database and table created successfully

4. Verifying setup...

Verifying setup...
✓ Setup verification successful
✓ User 'andrewh' can access network_info database
✓ Table 'arp_table' exists with correct structure

============================================================
SETUP COMPLETE!
============================================================

Next steps:
1. Populate the database with current ARP entries:
   python3 update_network_info.py

2. View the entries:
   python3 display_arp_entries.py

3. Set hostnames for devices:
   python3 set_hostname.py 192.168.0.1 gateway
```

---

### 1. update_network_info.py

**Purpose**: Updates the database with current ARP table entries and device states.

#### Features
- Scans the system ARP table for current network devices
- Adds new devices to the database automatically
- Updates device states based on ping connectivity tests
- Supports both connectivity checking and ARP-only modes
- Provides detailed progress reporting

#### Usage

```bash
# Full update with connectivity checking (default)
python3 update_network_info.py

# Update without ping tests (faster, less accurate)
python3 update_network_info.py --no-ping

# Quiet mode with less verbose output
python3 update_network_info.py --quiet

# Show help
python3 update_network_info.py --help
```

#### Device State Logic
- **UP**: Device is in ARP table AND responds to ping
- **DOWN**: Device is not in ARP table OR doesn't respond to ping
- **UNKNOWN**: When ping checking is disabled (`--no-ping`)

#### Example Output
```
Updating Network Info Database
==================================================
Connectivity checking: Enabled

Getting current ARP entries from system...
Found 4 current ARP entries

Current ARP entries:
  192.168.0.1 -> 40:0d:10:8f:32:48
  192.168.0.18 -> 08:84:9d:ad:31:e9
  192.168.0.20 -> ec:c1:ab:0d:bc:02
  192.168.0.50 -> 02:0f:b5:43:fa:e4

No new entries found.

Updating states for 3 existing entries...
  192.168.0.1 -> 40:0d:10:8f:32:48: DOWN -> UP
  192.168.0.18 -> 08:84:9d:ad:31:e9: DOWN -> UP
  192.168.0.20 -> ec:c1:ab:0d:bc:02: DOWN -> UP
Successfully updated 3 entries

==================================================
Final Database Summary:
  UP: 3 entries
  DOWN: 1 entries
  Total: 4 entries
```

---

### 2. display_arp_entries.py

**Purpose**: Displays and filters database entries in a formatted table.

#### Features
- Shows all database entries in a clean, formatted table
- Filters entries by device state (UP, DOWN, UNKNOWN)
- Provides summary statistics by state
- Supports multiple display modes

#### Usage

```bash
# Display all entries with summary
python3 display_arp_entries.py

# Show only devices that are UP
python3 display_arp_entries.py --state UP

# Show only devices that are DOWN
python3 display_arp_entries.py --state DOWN

# Show only summary statistics
python3 display_arp_entries.py --summary

# Show help
python3 display_arp_entries.py --help
```

#### Example Output
```
ARP Table Entries
===============================================================================================
ID   IP Address      HW Address         Created At           State    Hostname       
-----------------------------------------------------------------------------------------------
11   192.168.0.1     40:0d:10:8f:32:48  2025-06-15 12:21:59  UP       gateway        
10   192.168.0.18    08:84:9d:ad:31:e9  2025-06-15 12:21:59  UP       laptop         
9    192.168.0.20    ec:c1:ab:0d:bc:02  2025-06-15 12:21:59  UP       printer        
12   192.168.0.15    f8:8b:37:c9:b8:f9  2025-06-15 12:21:59  DOWN     unknown        
-----------------------------------------------------------------------------------------------
Total entries: 4

ARP Table Summary
==============================
State      Count   
--------------------
UP         3       
DOWN       1       
```

---

### 3. set_hostname.py

**Purpose**: Sets human-readable hostnames for network devices.

#### Features
- Two operation modes: Interactive and Direct
- Input validation for IP addresses and hostnames
- Device lookup and verification
- RFC-compliant hostname validation
- Database update with confirmation

#### Usage

##### Interactive Mode
Prompts for hostname input with confirmation:
```bash
python3 set_hostname.py 192.168.0.1
```

##### Direct Mode
Sets hostname directly from command line:
```bash
python3 set_hostname.py 192.168.0.1 gateway
python3 set_hostname.py 192.168.0.20 printer
python3 set_hostname.py 192.168.0.50 file-server
```

##### Utility Commands
```bash
# List all devices
python3 set_hostname.py --list

# Show help
python3 set_hostname.py --help
```

#### Hostname Requirements
- 1-32 characters long
- Letters, numbers, hyphens, and dots only
- Cannot start or end with a hyphen
- Must follow RFC naming standards

#### Example Output (Direct Mode)
```
Looking up device with IP address: 192.168.0.1

Device found:
==================================================
ID:         11
IP Address: 192.168.0.1
HW Address: 40:0d:10:8f:32:48
State:      UP
Current Hostname: unknown
New Hostname:     gateway
==================================================

Updating hostname to 'gateway'...
Success: Hostname updated to 'gateway' for 192.168.0.1

Updated device information:
------------------------------
IP Address: 192.168.0.1
HW Address: 40:0d:10:8f:32:48
State:      UP
Hostname:   gateway
```

## Typical Workflow

### 1. Database Setup
```bash
# Set up the MySQL database, user, and table
python3 setup_database.py
```

### 2. Initial Data Population
```bash
# Populate the database with current ARP entries
python3 update_network_info.py
```

### 3. View Current Network Status
```bash
# See all devices
python3 display_arp_entries.py

# Check which devices are currently UP
python3 display_arp_entries.py --state UP
```

### 4. Assign Meaningful Names
```bash
# Set hostnames for important devices
python3 set_hostname.py 192.168.0.1 gateway
python3 set_hostname.py 192.168.0.100 file-server
python3 set_hostname.py 192.168.0.200 wifi-printer
```

### 5. Regular Monitoring
```bash
# Update device states (run periodically via cron)
python3 update_network_info.py --quiet

# Check current status
python3 display_arp_entries.py --summary
```

## Automation Examples

### Cron Job for Regular Updates
Add to crontab for automatic network monitoring:
```bash
# Update network info every 5 minutes
*/5 * * * * /usr/bin/python3 /home/andrewh/update_network_info.py --quiet

# Daily summary report
0 9 * * * /usr/bin/python3 /home/andrewh/display_arp_entries.py --summary
```

### Batch Hostname Assignment
```bash
#!/bin/bash
# Bulk hostname assignment script
python3 set_hostname.py 192.168.0.1 gateway
python3 set_hostname.py 192.168.0.10 dns-server
python3 set_hostname.py 192.168.0.100 file-server
python3 set_hostname.py 192.168.0.200 printer-hp
python3 set_hostname.py 192.168.0.250 wifi-ap
```

## Error Handling

All utilities include comprehensive error handling:

- **Database connectivity issues**: Clear error messages with troubleshooting hints
- **Invalid IP addresses**: Format validation with helpful feedback
- **Invalid hostnames**: RFC compliance checking with requirement details
- **Missing devices**: Informative messages with suggestions
- **Permission issues**: Database access error reporting

## Security Considerations

- Database credentials are stored in plaintext within scripts
- Consider using MySQL configuration files or environment variables for production
- The ping functionality requires appropriate network permissions
- Scripts should be run with appropriate user privileges

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify MySQL server is running
   - Check username/password credentials
   - Ensure `network_info` database exists

2. **No ARP Entries Found**
   - Check if `arp` command is available
   - Verify network interface is active
   - Run as user with network access permissions

3. **Ping Tests Failing**
   - Use `--no-ping` option if ping is restricted
   - Check firewall settings
   - Verify ICMP is allowed on the network

### Debug Tips

- Use `--help` option on any utility for detailed usage
- Run `--list` to see current database contents
- Test with a single device before bulk operations
- Check MySQL logs for database-related issues

## File Permissions

Make scripts executable:
```bash
chmod +x update_network_info.py
chmod +x display_arp_entries.py
chmod +x set_hostname.py
```

## License

These utilities are provided as-is for network administration purposes. Modify and distribute as needed for your environment.

---

*Last updated: 2025-06-15*

