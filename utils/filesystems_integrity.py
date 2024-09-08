import subprocess
import socket
import os
from dotenv import load_dotenv
from datetime import datetime
import psycopg2
import distro
from utils.pretty import pretty_print, pretty_underline

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def create_table(cursor):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS filesystems_integrity (
        id SERIAL PRIMARY KEY,
        hostname VARCHAR(255),
        os_footprint VARCHAR(255),
        date DATE,
        section VARCHAR(50),
        section_name VARCHAR(255),
        scored VARCHAR(50),
        checklist VARCHAR(50),
        deviation VARCHAR(50),
        UNIQUE (hostname, date, section)
    )
    """
    cursor.execute(create_table_query)

def upsert_data(cursor, data):
    upsert_query = """
    INSERT INTO filesystems_integrity (hostname, os_footprint, date, section, section_name, scored, checklist, deviation)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (hostname, date, section) DO UPDATE
    SET os_footprint = EXCLUDED.os_footprint,
        section_name = EXCLUDED.section_name,
        scored = EXCLUDED.scored,
        checklist = EXCLUDED.checklist,
        deviation = EXCLUDED.deviation
    """
    cursor.executemany(upsert_query, data)

def get_os_footprint():
    os_type = distro.id()
    os_version = distro.version()
    os_codename = distro.codename()
    return f"{os_type} {os_version} {os_codename}"

def write_output_to_database(section, section_name, is_scored, is_compliant, results):
    # Get hostname
    hostname = socket.gethostname()

    # Get OS footprint
    os_footprint = get_os_footprint()

    # Get current date
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Determine deviation
    deviation = "Not Deviated" if is_compliant else "Deviated"

    # Prepare data for insertion
    data = []
    data.append((hostname, os_footprint, current_date, section, section_name, "Scored" if is_scored else "Not Scored", "Compliant" if is_compliant else "Not Compliant", deviation))

    # Connect to the database and insert data
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cursor = conn.cursor()

        # Create table if not exists
        create_table(cursor)

        # Upsert data
        upsert_data(cursor, data)

        # Commit the transaction
        conn.commit()
        pretty_print("Data inserted/updated successfully in the database.")
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error:", error)
    finally:
        if conn is not None:
            conn.close()

def ensure_aide_installed():
    section = "1.3.1"
    section_name = "Ensure AIDE is installed"
    is_scored = True
    is_compliant = False

    pretty_print(f"[{section}] {section_name} (Scored)")
    print()

    commands = {
        'rpm': 'rpm -q aide',
        'dpkg': 'dpkg -s aide'
    }

    results = {}
    for manager, command in commands.items():
        print(f"Running command: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        results[manager] = {
            'command': command,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip()
        }
        print(result.stdout)
        if result.stderr:
            print("Error:")
            print(result.stderr.strip())
            pretty_underline(result.stderr, "-")

    is_compliant = any('aide' in results[manager]['stdout'] for manager in results)
    compliance_message = "AIDE is installed." if is_compliant else "AIDE is not installed."
    print(compliance_message)
    print()

    write_output_to_database(section, section_name, is_scored, is_compliant, results)

def ensure_filesystem_integrity_checked():
    section = "1.3.2"
    section_name = "Ensure filesystem integrity is regularly checked"
    is_scored = True
    is_compliant = False

    pretty_print(f"[{section}] {section_name} (Scored)")
    print()

    systemd_commands = {
        'is-enabled aidcheck.service': 'systemctl is-enabled aidcheck.service',
        'status aidcheck.service': 'systemctl status aidcheck.service',
        'is-enabled aidcheck.timer': 'systemctl is-enabled aidcheck.timer',
        'status aidcheck.timer': 'systemctl status aidcheck.timer'
    }

    cron_commands = {
        'root crontab': 'crontab -u root -l | grep aide',
        'etc cron': 'grep -r aide /etc/cron.* /etc/crontab'
    }

    results = {}

    for desc, command in systemd_commands.items():
        print(f"Running command: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        results[desc] = {
            'command': command,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip()
        }
        print(result.stdout)
        if result.stderr:
            print("Error:")
            print(result.stderr.strip())
            pretty_underline(result.stderr, "-")

    for desc, command in cron_commands.items():
        print(f"Running command: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        results[desc] = {
            'command': command,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip()
        }
        print(result.stdout)
        if result.stderr:
            print("Error:")
            print(result.stderr.strip())
            pretty_underline(result.stderr, "-")

    is_compliant = any('enabled' in results[desc]['stdout'] or 'aide' in results[desc]['stdout'] for desc in results)
    compliance_message = "Filesystem integrity is regularly checked." if is_compliant else "Filesystem integrity is not regularly checked."
    print(compliance_message)
    print()

    write_output_to_database(section, section_name, is_scored, is_compliant, results)

def run():
    sections = [
        (ensure_aide_installed, "[1.3] Filesystem Integrity Checking"),
        (ensure_filesystem_integrity_checked, "[1.3] Filesystem Integrity Checking")
    ]

    for func, title in sections:
        pretty_print(title, upper_underline=True)
        print()
        func()

run()

