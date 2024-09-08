import subprocess
from datetime import datetime
import os
from dotenv import load_dotenv
import socket
import psycopg2
import distro
from utils.pretty import pretty_print, pretty_underline

# Database connection settings
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def create_table(cursor):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS bootloader_settings (
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
    INSERT INTO bootloader_settings (hostname, os_footprint, date, section, section_name, scored, checklist, deviation)
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

def ensure_bootloader_permissions_configured():
    section = "1.4.1"
    section_name = "Ensure permissions on bootloader config are configured"
    is_scored = True
    is_compliant = False

    pretty_print(f"[{section}] {section_name} (Scored)")
    print()

    commands = {
        '/boot/grub2/grub.cfg': 'stat /boot/grub2/grub.cfg',
        '/boot/grub/grub.cfg': 'stat /boot/grub/grub.cfg'
    }

    results = {}
    for path, command in commands.items():
        print(f"Running command: {command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        results[path] = {
            'command': command,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip()
        }
        print(result.stdout)
        if result.stderr:
            print("Error:")
            print(result.stderr.strip())
            pretty_underline(result.stderr, "-")

    is_compliant = any('Access: (' in results[path]['stdout'] for path in results)
    compliance_message = "Bootloader permissions are configured." if is_compliant else "Bootloader permissions are not configured."
    print(compliance_message)
    print()

    write_output_to_database(section, section_name, is_scored, is_compliant, results)

def ensure_bootloader_password_set():
    section = "1.4.2"
    section_name = "Ensure bootloader password is set"
    is_scored = True
    is_compliant = False

    pretty_print(f"[{section}] {section_name} (Scored)")
    print()

    commands = {
        'grub': 'grep "^\\s*password" /boot/grub/menu.lst',
        'grub2_user_cfg': 'grep "^\\s*GRUB2_PASSWORD" /boot/grub2/user.cfg',
        'grub2_superusers': 'grep "^\\s*set superusers" /boot/grub/grub.cfg',
        'grub2_password': 'grep "^\\s*password" /boot/grub/grub.cfg'
    }

    results = {}
    for desc, command in commands.items():
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

    is_compliant = any(results[desc]['stdout'] for desc in results)
    compliance_message = "Bootloader password is set." if is_compliant else "Bootloader password is not set."
    print(compliance_message)
    print()

    write_output_to_database(section, section_name, is_scored, is_compliant, results)

def ensure_single_user_mode_authentication():
    section = "1.4.3"
    section_name = "Ensure authentication required for single user mode"
    is_scored = True
    is_compliant = False

    pretty_print(f"[{section}] {section_name} (Scored)")
    print()

    command = 'grep ^root:[*\!]: /etc/shadow'
    print(f"Running command: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    results = {
        'command': command,
        'stdout': result.stdout.strip(),
        'stderr': result.stderr.strip()
    }
    print(result.stdout)
    if result.stderr:
        print("Error:")
        print(result.stderr.strip())
        pretty_underline(result.stderr, "-")

    is_compliant = 'root' in results['stdout']
    compliance_message = "Authentication is required for single user mode." if is_compliant else "Authentication is not required for single user mode."
    print(compliance_message)
    print()

    write_output_to_database(section, section_name, is_scored, is_compliant, {'single_user_mode': results})

def run():
    sections = [
        (ensure_bootloader_permissions_configured, "[1.4] Boot Settings"),
        (ensure_bootloader_password_set, "[1.4] Boot Settings"),
        (ensure_single_user_mode_authentication, "[1.4] Boot Settings")
    ]

    for func, title in sections:
        pretty_print(title, upper_underline=True)
        print()
        func()

run()

   

