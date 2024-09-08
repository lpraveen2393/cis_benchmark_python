import inspect
import os
from dotenv import load_dotenv
import subprocess
from datetime import datetime
import socket
import psycopg2
import distro
from utils.pretty import pretty_print, pretty_underline
#to change from ensure_nodev_on_tmp
# Database connection settings

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def create_table(cursor):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS unused_filesystems (
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
    INSERT INTO unused_filesystems (hostname, os_footprint, date, section, section_name, scored, checklist, deviation)
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
    data = [(hostname, os_footprint, current_date, section, section_name, 
             "Scored" if is_scored else "Not Scored", 
             "Compliant" if is_compliant else "Not Compliant", 
             deviation)]

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

def ensure_cramfs_disabled():
    section = "1.1.1.1"
    section_name = "Ensure mounting of cramfs filesystems is disabled"
    is_scored = True
    is_compliant = False

    pretty_print(f"[{section}] {section_name} (Scored)")
    print()

    filesystem = 'cramfs'

    modprobe_command = f'modprobe -n -v {filesystem}'
    lsmod_command = f'lsmod | grep {filesystem}'

    results = {}

    # Run modprobe command
    print(f"Running command: {modprobe_command}")
    modprobe_result = subprocess.run(modprobe_command, shell=True, capture_output=True, text=True)
    results['modprobe_command'] = modprobe_command
    results['modprobe_output'] = modprobe_result.stdout.strip()
    results['modprobe_error'] = modprobe_result.stderr.strip()
    print(modprobe_result.stdout)
    if modprobe_result.stderr:
        print("Error:")
        print(modprobe_result.stderr.strip())
        pretty_underline(modprobe_result.stderr, "-")

    # Run lsmod command
    print(f"Running command: {lsmod_command}")
    lsmod_result = subprocess.run(lsmod_command, shell=True, capture_output=True, text=True)
    results['lsmod_command'] = lsmod_command
    results['lsmod_output'] = lsmod_result.stdout.strip()
    results['lsmod_error'] = lsmod_result.stderr.strip()
    print(lsmod_result.stdout)
    if lsmod_result.stderr:
        print("Error:")
        print(lsmod_result.stderr.strip())
        pretty_underline(lsmod_result.stderr, "-")

    expected_output_modprobe = "insmod /lib/modules/6.5.0-35-generic/kernel/fs/cramfs/cramfs.ko"
    
    modprobe_disabled = expected_output_modprobe in modprobe_result.stdout or not modprobe_result.stdout.strip()
    lsmod_disabled = not lsmod_result.stdout.strip()

    if modprobe_disabled and lsmod_disabled:
        print(f"{filesystem} filesystem mounting is disabled")
        is_compliant = True
    else:
        print(f"{filesystem} filesystem mounting is not properly disabled.")
    print()

    # Write results to database
    write_output_to_database(section, section_name, is_scored, is_compliant, results)



def ensure_freevxfs_disabled():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The freevxfs filesystem type is a free version of the Veritas type filesystem. This is the
    primary filesystem type for HP-UX operating systems.

    Rationale:
    ----------
    Removing support for unneeded filesystem types reduces the local attack surface of the
    system. If this filesystem type is not needed, disable it.
    """
    section = "1.1.1.2"
    section_name = "Ensure mounting of freevxfs filesystems is disabled"
    is_scored = True
    is_compliant = False

    pretty_print(f"[{section}] {section_name} (Scored)")
    print()

    filesystem = 'freevxfs'

    modprobe_command = f'modprobe -n -v {filesystem}'
    lsmod_command = f'lsmod | grep {filesystem}'

    results = {}

    # Run modprobe command
    print(f"Running command: {modprobe_command}")
    modprobe_result = subprocess.run(modprobe_command, shell=True, capture_output=True, text=True)
    results['modprobe_command'] = modprobe_command
    results['modprobe_output'] = modprobe_result.stdout.strip()
    results['modprobe_error'] = modprobe_result.stderr.strip()
    print(modprobe_result.stdout)
    if modprobe_result.stderr:
        print("Error:")
        print(modprobe_result.stderr.strip())
        pretty_underline(modprobe_result.stderr, "-")

    # Run lsmod command
    print(f"Running command: {lsmod_command}")
    lsmod_result = subprocess.run(lsmod_command, shell=True, capture_output=True, text=True)
    results['lsmod_command'] = lsmod_command
    results['lsmod_output'] = lsmod_result.stdout.strip()
    results['lsmod_error'] = lsmod_result.stderr.strip()
    print(lsmod_result.stdout)
    if lsmod_result.stderr:
        print("Error:")
        print(lsmod_result.stderr.strip())
        pretty_underline(lsmod_result.stderr, "-")
    else:
        pretty_underline(lsmod_result.stdout, "-")

    expected_output_modprobe = "insmod /lib/modules/6.5.0-35-generic/kernel/fs/freevxfs/freevxfs.ko"

    modprobe_disabled = expected_output_modprobe in modprobe_result.stdout or not modprobe_result.stdout.strip()
    lsmod_disabled = not lsmod_result.stdout.strip()

    if modprobe_disabled and lsmod_disabled:
        print(f"{filesystem} filesystem mounting is disabled")
        is_compliant = True
    else:
        print(f"{filesystem} filesystem mounting is not properly disabled.")
    print()

    # Write results to database
    write_output_to_database(section, section_name, is_scored, is_compliant, results)


def ensure_jffs2_disabled():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The jffs2 (journaling flash filesystem 2) filesystem type is a log-structured filesystem used
    in flash memory devices.

    Rationale:
    ----------
    Removing support for unneeded filesystem types reduces the local attack surface of the
    system. If this filesystem type is not needed, disable it.
    """
    section = "1.1.1.3"
    section_name = "Ensure mounting of jffs2 filesystems is disabled"
    is_scored = True
    is_compliant = False

    pretty_print(f"[{section}] {section_name} (Scored)")
    print()

    filesystem = 'jffs2'

    modprobe_command = f'modprobe -n -v {filesystem}'
    lsmod_command = f'lsmod | grep {filesystem}'

    results = {}

    # Run modprobe command
    print(f"Running command: {modprobe_command}")
    modprobe_result = subprocess.run(modprobe_command, shell=True, capture_output=True, text=True)
    results['modprobe_command'] = modprobe_command
    results['modprobe_output'] = modprobe_result.stdout.strip()
    results['modprobe_error'] = modprobe_result.stderr.strip()
    print(modprobe_result.stdout)
    if modprobe_result.stderr:
        print("Error:")
        print(modprobe_result.stderr.strip())
        pretty_underline(modprobe_result.stderr, "-")

    # Run lsmod command
    print(f"Running command: {lsmod_command}")
    lsmod_result = subprocess.run(lsmod_command, shell=True, capture_output=True, text=True)
    results['lsmod_command'] = lsmod_command
    results['lsmod_output'] = lsmod_result.stdout.strip()
    results['lsmod_error'] = lsmod_result.stderr.strip()
    print(lsmod_result.stdout)
    if lsmod_result.stderr:
        print("Error:")
        print(lsmod_result.stderr.strip())
        pretty_underline(lsmod_result.stderr, "-")
    else:
        pretty_underline(lsmod_result.stdout, "-")

    expected_output_modprobe = "insmod /lib/modules/6.5.0-35-generic/kernel/fs/jffs2/jffs2.ko"

    modprobe_disabled = expected_output_modprobe in modprobe_result.stdout or not modprobe_result.stdout.strip()
    lsmod_disabled = not lsmod_result.stdout.strip()

    if modprobe_disabled and lsmod_disabled:
        print(f"{filesystem} filesystem mounting is disabled")
        is_compliant = True
    else:
        print(f"{filesystem} filesystem mounting is not properly disabled.")
    print()

    # Write results to database
    write_output_to_database(section, section_name, is_scored, is_compliant, results)

def ensure_hfs_disabled():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The hfs filesystem type is a hierarchical filesystem that allows you to mount Mac OS
    filesystems.

    Rationale:
    ----------
    Removing support for unneeded filesystem types reduces the local attack surface of the
    system. If this filesystem type is not needed, disable it.
    """
    section = "1.1.1.4"
    section_name = "Ensure mounting of hfs filesystems is disabled"
    is_scored = True
    is_compliant = False

    pretty_print(f"[{section}] Ensure mounting of hfs filesystems is disabled (Scored)")
    print()

    filesystem = 'hfs'

    modprobe_command = f'modprobe -n -v {filesystem}'
    lsmod_command = f'lsmod | grep {filesystem}'

    results = {}

    # Run modprobe command
    print(f"Running command: {modprobe_command}")
    modprobe_result = subprocess.run(modprobe_command, shell=True, capture_output=True, text=True)
    results['modprobe_command'] = modprobe_command
    results['modprobe_output'] = modprobe_result.stdout.strip()
    results['modprobe_error'] = modprobe_result.stderr.strip()
    print(modprobe_result.stdout)
    if modprobe_result.stderr:
        print("Error:")
        print(modprobe_result.stderr.strip())
        pretty_underline(modprobe_result.stderr, "-")

    # Run lsmod command
    print(f"Running command: {lsmod_command}")
    lsmod_result = subprocess.run(lsmod_command, shell=True, capture_output=True, text=True)
    results['lsmod_command'] = lsmod_command
    results['lsmod_output'] = lsmod_result.stdout.strip()
    results['lsmod_error'] = lsmod_result.stderr.strip()
    print(lsmod_result.stdout)
    if lsmod_result.stderr:
        print("Error:")
        print(lsmod_result.stderr.strip())
        pretty_underline(lsmod_result.stderr, "-")
    else:
        pretty_underline(lsmod_result.stdout, "-")

    expected_output_modprobe = "insmod /lib/modules/6.5.0-35-generic/kernel/fs/hfs/hfs.ko"

    modprobe_disabled = expected_output_modprobe in modprobe_result.stdout or not modprobe_result.stdout.strip()
    lsmod_disabled = not lsmod_result.stdout.strip()

    if modprobe_disabled and lsmod_disabled:
        print(f"{filesystem} filesystem mounting is disabled")
        is_compliant = True
    else:
        print(f"{filesystem} filesystem mounting is not properly disabled.")
    print()

    # Write results to database
    write_output_to_database(section, section_name, is_scored, is_compliant, results)


def ensure_hfsplus_disabled():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The hfsplus filesystem type is a hierarchical filesystem designed to replace hfs that allows
    you to mount Mac OS filesystems.

    Rationale:
    ----------
    Removing support for unneeded filesystem types reduces the local attack surface of the
    system. If this filesystem type is not needed, disable it.
    """
    section = "1.1.1.5"
    section_name = "Ensure mounting of hfsplus filesystems is disabled"
    is_scored = True
    is_compliant = False

    pretty_print(f"[{section}] Ensure mounting of hfsplus filesystems is disabled (Scored)")
    print()
    
    filesystem = 'hfsplus'

    modprobe_command = f'modprobe -n -v {filesystem}'
    lsmod_command = f'lsmod | grep {filesystem}'

    results = {}

    # Run modprobe command
    print(f"Running command: {modprobe_command}")
    modprobe_result = subprocess.run(modprobe_command, shell=True, capture_output=True, text=True)
    results['modprobe_command'] = modprobe_command
    results['modprobe_output'] = modprobe_result.stdout.strip()
    results['modprobe_error'] = modprobe_result.stderr.strip()
    print(modprobe_result.stdout)
    if modprobe_result.stderr:
        print("Error:")
        print(modprobe_result.stderr.strip())
        pretty_underline(modprobe_result.stderr, "-")

    # Run lsmod command
    print(f"Running command: {lsmod_command}")
    lsmod_result = subprocess.run(lsmod_command, shell=True, capture_output=True, text=True)
    results['lsmod_command'] = lsmod_command
    results['lsmod_output'] = lsmod_result.stdout.strip()
    results['lsmod_error'] = lsmod_result.stderr.strip()
    print(lsmod_result.stdout)
    if lsmod_result.stderr:
        print("Error:")
        print(lsmod_result.stderr.strip())
        pretty_underline(lsmod_result.stderr, "-")
    else:
        pretty_underline(lsmod_result.stdout, "-")

    expected_output_modprobe = "insmod /lib/modules/6.5.0-35-generic/kernel/fs/hfsplus/hfsplus.ko"

    modprobe_disabled = expected_output_modprobe in modprobe_result.stdout or not modprobe_result.stdout.strip()
    lsmod_disabled = not lsmod_result.stdout.strip()

    if modprobe_disabled and lsmod_disabled:
        print(f"{filesystem} filesystem mounting is disabled")
        is_compliant = True
    else:
        print(f"{filesystem} filesystem mounting is not properly disabled.")
    print()

    # Write results to database
    write_output_to_database(section, section_name, is_scored, is_compliant, results)


def ensure_squashfs_disabled():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The squashfs filesystem type is a compressed read-only Linux filesystem embedded in
    small footprint systems (similar to cramfs). A squashfs image can be used without having
    to first decompress the image.

    Rationale:
    ----------
    Removing support for unneeded filesystem types reduces the local attack surface of the
    system. If this filesystem type is not needed, disable it.
    """
    section = "1.1.1.6"
    section_name = "Ensure mounting of squashfs filesystems is disabled"
    is_scored = True
    is_compliant = False

    pretty_print(f"[{section}] Ensure mounting of squashfs filesystems is disabled (Scored)")
    print()
    
    filesystem = 'squashfs'

    modprobe_command = f'modprobe -n -v {filesystem}'
    lsmod_command = f'lsmod | grep {filesystem}'

    results = {}

    # Run modprobe command
    print(f"Running command: {modprobe_command}")
    modprobe_result = subprocess.run(modprobe_command, shell=True, capture_output=True, text=True)
    results['modprobe_command'] = modprobe_command
    results['modprobe_output'] = modprobe_result.stdout.strip()
    results['modprobe_error'] = modprobe_result.stderr.strip()
    print(modprobe_result.stdout)
    if modprobe_result.stderr:
        print("Error:")
        print(modprobe_result.stderr.strip())
        pretty_underline(modprobe_result.stderr, "-")

    # Run lsmod command
    print(f"Running command: {lsmod_command}")
    lsmod_result = subprocess.run(lsmod_command, shell=True, capture_output=True, text=True)
    results['lsmod_command'] = lsmod_command
    results['lsmod_output'] = lsmod_result.stdout.strip()
    results['lsmod_error'] = lsmod_result.stderr.strip()
    print(lsmod_result.stdout)
    if lsmod_result.stderr:
        print("Error:")
        print(lsmod_result.stderr.strip())
        pretty_underline(lsmod_result.stderr, "-")
    else:
        pretty_underline(lsmod_result.stdout, "-")

    expected_output_modprobe = "insmod /lib/modules/6.5.0-35-generic/kernel/fs/squashfs/squashfs.ko"

    modprobe_disabled = expected_output_modprobe in modprobe_result.stdout or not modprobe_result.stdout.strip()
    lsmod_disabled = not lsmod_result.stdout.strip()

    if modprobe_disabled and lsmod_disabled:
        print(f"{filesystem} filesystem mounting is disabled")
        is_compliant = True
    else:
        print(f"{filesystem} filesystem mounting is not properly disabled.")
    print()

    # Write results to database
    write_output_to_database(section, section_name, is_scored, is_compliant, results)


def ensure_udf_disabled():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The udf filesystem type is the universal disk format used to implement ISO/IEC 13346 and
    ECMA-167 specifications. This is an open vendor filesystem type for data storage on a
    broad range of media. This filesystem type is necessary to support writing DVDs and newer
    optical disc formats.

    Rationale:
    ----------
    Removing support for unneeded filesystem types reduces the local attack surface of the
    system. If this filesystem type is not needed, disable it.
    """
    section = "1.1.1.7"
    section_name = "Ensure mounting of udf filesystems is disabled"
    is_scored = True
    is_compliant = False

    pretty_print(f"[{section}] Ensure mounting of udf filesystems is disabled (Scored)")
    print()
    
    filesystem = 'udf'

    modprobe_command = f'modprobe -n -v {filesystem}'
    lsmod_command = f'lsmod | grep {filesystem}'

    results = {}

    # Run modprobe command
    print(f"Running command: {modprobe_command}")
    modprobe_result = subprocess.run(modprobe_command, shell=True, capture_output=True, text=True)
    results['modprobe_command'] = modprobe_command
    results['modprobe_output'] = modprobe_result.stdout.strip()
    results['modprobe_error'] = modprobe_result.stderr.strip()
    print(modprobe_result.stdout)
    if modprobe_result.stderr:
        print("Error:")
        print(modprobe_result.stderr.strip())
        pretty_underline(modprobe_result.stderr, "-")

    # Run lsmod command
    print(f"Running command: {lsmod_command}")
    lsmod_result = subprocess.run(lsmod_command, shell=True, capture_output=True, text=True)
    results['lsmod_command'] = lsmod_command
    results['lsmod_output'] = lsmod_result.stdout.strip()
    results['lsmod_error'] = lsmod_result.stderr.strip()
    print(lsmod_result.stdout)
    if lsmod_result.stderr:
        print("Error:")
        print(lsmod_result.stderr.strip())
        pretty_underline(lsmod_result.stderr, "-")
    else:
        pretty_underline(lsmod_result.stdout, "-")

    expected_output_modprobe = "insmod /lib/modules/6.5.0-35-generic/kernel/fs/udf/udf.ko"

    modprobe_disabled = expected_output_modprobe in modprobe_result.stdout or not modprobe_result.stdout.strip()
    lsmod_disabled = not lsmod_result.stdout.strip()

    if modprobe_disabled and lsmod_disabled:
        print(f"{filesystem} filesystem mounting is disabled")
        is_compliant = True
    else:
        print(f"{filesystem} filesystem mounting is not properly disabled.")
    print()

    # Write results to database
    write_output_to_database(section, section_name, is_scored, is_compliant, results)


#TODO: Add check for UEFI
def ensure_vfat_disabled():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The FAT filesystem format is primarily used on older windows systems and portable USB
    drives or flash modules. It comes in three types FAT12, FAT16, and FAT32, all of which
    are supported by the vfat kernel module.

    Rationale:
    ----------
    Removing support for unneeded filesystem types reduces the local attack surface of the
    system. If this filesystem type is not needed, disable it.
    """
    section = "1.1.1.8"
    section_name = "Ensure mounting of vfat filesystems is disabled"
    is_scored = True
    is_compliant = False

    pretty_print(f"[{section}] Ensure mounting of vfat filesystems is disabled (Scored)")
    print()
    
    filesystem = 'vfat'

    modprobe_command = f'modprobe -n -v {filesystem}'
    lsmod_command = f'lsmod | grep {filesystem}'

    results = {}

    # Run modprobe command
    print(f"Running command: {modprobe_command}")
    modprobe_result = subprocess.run(modprobe_command, shell=True, capture_output=True, text=True)
    results['modprobe_command'] = modprobe_command
    results['modprobe_output'] = modprobe_result.stdout.strip()
    results['modprobe_error'] = modprobe_result.stderr.strip()
    print(modprobe_result.stdout)
    if modprobe_result.stderr:
        print("Error:")
        print(modprobe_result.stderr.strip())
        pretty_underline(modprobe_result.stderr, "-")

    # Run lsmod command
    print(f"Running command: {lsmod_command}")
    lsmod_result = subprocess.run(lsmod_command, shell=True, capture_output=True, text=True)
    results['lsmod_command'] = lsmod_command
    results['lsmod_output'] = lsmod_result.stdout.strip()
    results['lsmod_error'] = lsmod_result.stderr.strip()
    print(lsmod_result.stdout)
    if lsmod_result.stderr:
        print("Error:")
        print(lsmod_result.stderr.strip())
        pretty_underline(lsmod_result.stderr, "-")
    else:
        pretty_underline(lsmod_result.stdout, "-")

    expected_output_modprobe = "insmod /lib/modules/6.5.0-35-generic/kernel/fs/vfat/vfat.ko"

    modprobe_disabled = expected_output_modprobe in modprobe_result.stdout or not modprobe_result.stdout.strip()
    lsmod_disabled = not lsmod_result.stdout.strip()

    if modprobe_disabled and lsmod_disabled:
        print(f"{filesystem} filesystem mounting is disabled")
        is_compliant = True
    else:
        print(f"{filesystem} filesystem mounting is not properly disabled.")
    print()

    # Write results to database
    write_output_to_database(section, section_name, is_scored, is_compliant, results)

def ensure_tmp_configured():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The /tmp directory is a world-writable directory used for temporary storage by all users
    and some applications.

    Rationale:
    ----------
    Making /tmp its own file system allows an administrator to set the noexec option on the
    mount, making /tmp useless for an attacker to install executable code. It would also
    prevent an attacker from establishing a hardlink to a system setuid program and wait for it
    to be updated. Once the program was updated, the hardlink would be broken and the
    attacker would have his own copy of the program. If the program happened to have a
    security vulnerability, the attacker could continue to exploit the known flaw.
    This can be accomplished by either mounting tmpfs to /tmp, or creating a separate
    partition for /tmp.
    """
    section = "1.1.2"
    section_name = "Ensure /tmp is configured"
    is_scored = True
    is_compliant = False

    configured = False

    pretty_print(f"[{section}] Ensure /tmp is configured (Scored)")
    print()

    # Collect command outputs
    results = {}
    commands = [
        "mount | grep -E '\\s/tmp\\s'",
        "grep -E '\\s/tmp\\s' /etc/fstab | grep -E -v '^\\s*#'",
        "systemctl is-enabled tmp.mount"
    ]

    expected_outputs = [
        "tmpfs on /tmp type tmpfs",
        "tmpfs\t/tmp\ttmpfs",
        "enabled"
    ]
    
    for cmd in commands:
        print(f"Running command: {cmd}")
        output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        results[cmd] = {
            'output': output.stdout.strip(),
            'error': output.stderr.strip()
        }
        print(output.stdout)
        if output.stderr:
            print("Error:")
            print(output.stderr.strip())
            pretty_underline(output.stderr, "-")

    # Check configuration status
    for op in expected_outputs:
        configured = configured or any(op in result['output'] for result in results.values())
    
    if configured:
        is_compliant = True
        print("/tmp is configured.")
    else:
        print("/tmp is NOT configured")

    print()
    
    # Write results to database
    write_output_to_database(section, section_name, is_scored, is_compliant, results)


def ensure_nodev_on_tmp():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The `nodev` mount option specifies that the filesystem cannot contain special devices.

    Rationale:
    ----------
    Since the `/tmp` filesystem is not intended to support devices, set this option to ensure that
    users cannot attempt to create block or character special devices in `/tmp`.
    """
    section = "1.1.3"
    section_name = "Ensure nodev option set on /tmp partition"
    is_scored = True
    is_compliant = False

    pretty_print("[1.1.3] Ensure nodev option set on /tmp partition (Scored)")
    print()

    cmd = "mount | grep -E '\\s/tmp\\s' | grep -v nodev"

    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    print(f"Command Run: {cmd}")

    result = {
        'command': cmd,
        'output': output.stdout.strip(),
        'error': output.stderr.strip()
    }

    if not result['output']:
        print("nodev option is set on /tmp partition.")
        is_compliant = True
    else:
        print("nodev option is NOT set on /tmp partition.")

    print()

    # Output to database
    write_output_to_database(section, section_name, is_scored, is_compliant, result)

def ensure_nosuid_on_tmp():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The `nosuid` mount option specifies that the filesystem cannot contain `setuid` files.

    Rationale:
    ----------
    Since the `/tmp` filesystem is only intended for temporary file storage, set this option to
    ensure that users cannot create `setuid` files in `/tmp`.
    """
    section = "1.1.4"
    section_name = "Ensure nosuid option set on /tmp partition"
    is_scored = True
    is_compliant = False

    pretty_print("[1.1.4] Ensure nosuid option set on /tmp partition (Scored)")
    print()

    cmd = "mount | grep -E '\\s/tmp\\s' | grep -v nosuid"

    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    print(f"Command Run: {cmd}")

    result = {
        'command': cmd,
        'output': output.stdout.strip(),
        'error': output.stderr.strip()
    }

    if not result['output']:
        is_compliant = True
        print("nosuid option is set on /tmp partition.")
    else:
        print("nosuid option is NOT set on /tmp partition.")

    print()

    # Output to database
    write_output_to_database(section, section_name, is_scored, is_compliant, result)

def ensure_noexec_on_tmp():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The `noexec` mount option specifies that the filesystem cannot contain executable binaries.

    Rationale:
    ----------
    Since the `/tmp` filesystem is only intended for temporary file storage, set this option to
    ensure that users cannot run executable binaries from `/tmp`.
    """
    section = "1.1.5"
    section_name = "Ensure noexec option set on /tmp partition"
    is_scored = True
    is_compliant = False

    pretty_print("[1.1.5] Ensure noexec option set on /tmp partition (Scored)")
    print()

    cmd = "mount | grep -E '\\s/tmp\\s' | grep -v noexec"

    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    print(f"Command Run: {cmd}")

    result = {
        'command': cmd,
        'output': output.stdout.strip(),
        'error': output.stderr.strip()
    }

    if not result['output']:
        is_compliant = True
        print("noexec option is set on /tmp partition.")
    else:
        print("noexec option is NOT set on /tmp partition.")

    print()

    # Output to database
    write_output_to_database(section, section_name, is_scored, is_compliant, result)


def ensure_var_configured():
    """
    Profile Applicability:
    ----------------------
    - Level 2 - Server
    - Level 2 - Workstation

    Description:
    ------------
    The `/var` directory is used by daemons and other system services to temporarily store
    dynamic data. Some directories created by these processes may be world-writable.

    Rationale:
    ----------
    Since the `/var` directory may contain world-writable files and directories, there is a risk of
    resource exhaustion if it is not bound to a separate partition.
    """
    section = "1.1.6"
    section_name = "Ensure separate partition exists for /var"
    is_scored = True
    is_compliant = False

    pretty_print("[1.1.6] Ensure separate partition exists for /var (Scored)")
    print()

    cmd = "mount | grep -E '\\s/var\\s'"

    expected_output = "/dev/xvdg1 on /var type ext4"

    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    print(f"Command Run: {cmd}")

    result = {
        'command': cmd,
        'output': output.stdout.strip(),
        'error': output.stderr.strip()
    }

    if result['output'] == expected_output:
        is_compliant = True
        print("/var is configured.")
    else:
        print("/var is NOT configured.")

    print()

    # Output to database
    write_output_to_database(section, section_name, is_scored, is_compliant, result)


#TODO: Add 1.1.7 - 1.1.12
def ensure_home_configured():
    """
    Profile Applicability:
    ----------------------
    - Level 2 - Server
    - Level 2 - Workstation

    Description:
    ------------
    The `/home` directory is used to support disk storage needs of local users.

    Rationale:
    ----------
    If the system is intended to support local users, create a separate partition for the `/home`
    directory to protect against resource exhaustion and restrict the type of files that can be
    stored under `/home`.
    """
    section = "1.1.13"
    section_name = "Ensure separate partition exists for /home"
    is_scored = True
    is_compliant = False

    pretty_print("[1.1.13] Ensure separate partition exists for /home (Scored)")
    print()

    cmd = "mount | grep /home"

    expected_output = "/dev/xvdf1 on /home type ext4"

    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    print(f"Command Run: {cmd}")

    result = {
        'command': cmd,
        'output': output.stdout.strip(),
        'error': output.stderr.strip()
    }

    if result['output'] == expected_output:
        is_compliant = True
        print("/home is configured.")
    else:
        print("/home is NOT configured.")

    print()

    # Output to database
    write_output_to_database(section, section_name, is_scored, is_compliant, result)

def ensure_nodev_on_home():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The `nodev` mount option specifies that the filesystem cannot contain special devices.

    Rationale:
    ----------
    Since the user partitions are not intended to support devices, set this option to ensure that
    users cannot attempt to create block or character special devices.
    """
    section = "1.1.14"
    section_name = "Ensure nodev option set on /home partition"
    is_scored = True
    is_compliant = False

    pretty_print("[1.1.14] Ensure nodev option set on /home partition (Scored)")
    print()

    cmd = "mount | grep -E '\\s/home\\s' | grep -v nodev"

    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    print(f"Command Run: {cmd}")

    result = {
        'command': cmd,
        'output': output.stdout.strip(),
        'error': output.stderr.strip()
    }

    if not result['output']:
        is_compliant = True
        print("nodev option is set on /home partition.")
    else:
        print("nodev option is NOT set on /home partition.")

    print()

    # Output to database
    write_output_to_database(section, section_name, is_scored, is_compliant, result)


def ensure_nodev_on_dev_shm():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The `nodev` mount option specifies that the filesystem cannot contain special devices.

    Rationale:
    ----------
    Since the `/dev/shm` filesystem is not intended to support devices, set this option to ensure
    that users cannot attempt to create special devices in `/dev/shm` partitions.
    """
    section = "1.1.15"
    section_name = "Ensure nodev option set on /dev/shm partition"
    is_scored = True
    is_compliant = False

    pretty_print("[1.1.15] Ensure nodev option set on /dev/shm partition (Scored)")
    print()

    cmd = "mount | grep -E '\\s/dev/shm\\s' | grep -v nodev"

    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    print(f"Command Run: {cmd}")

    result = {
        'command': cmd,
        'output': output.stdout.strip(),
        'error': output.stderr.strip()
    }

    if not result['output']:
        is_compliant = True
        print("nodev option is set on /dev/shm partition.")
    else:
        print("nodev option is NOT set on /dev/shm partition.")

    print()

    # Output to database
    write_output_to_database(section, section_name, is_scored, is_compliant, result)
def ensure_nosuid_on_dev_shm():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The `nosuid` mount option specifies that the filesystem cannot contain `setuid` files.

    Rationale:
    ----------
    Setting this option on a file system prevents users from introducing privileged programs
    onto the system and allowing non-root users to execute them.
    """
    section = "1.1.16"
    section_name = "Ensure nosuid option set on /dev/shm partition"
    is_scored = True
    is_compliant = False

    pretty_print("[1.1.16] Ensure nosuid option set on /dev/shm partition (Scored)")
    print()

    cmd = "mount | grep -E '\\s/dev/shm\\s' | grep -v nosuid"

    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    print(f"Command Run: {cmd}")

    result = {
        'command': cmd,
        'output': output.stdout.strip(),
        'error': output.stderr.strip()
    }

    if not result['output']:
        is_compliant = True
        print("nosuid option is set on /dev/shm partition.")
    else:
        print("nosuid option is NOT set on /dev/shm partition.")

    print()

    # Output to database
    write_output_to_database(section, section_name, is_scored, is_compliant, result)

def ensure_noexec_on_dev_shm():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The `noexec` mount option specifies that the filesystem cannot contain executable binaries.

    Rationale:
    ----------
    Setting this option on a file system prevents users from executing programs from shared
    memory. This deters users from introducing potentially malicious software on the system.
    """
    section = "1.1.17"
    section_name = "Ensure noexec option set on /dev/shm partition"
    is_scored = True
    is_compliant = False

    pretty_print("[1.1.17] Ensure noexec option set on /dev/shm partition (Scored)")
    print()

    cmd = "mount | grep -E '\\s/dev/shm\\s' | grep -v noexec"

    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    print(f"Command Run: {cmd}")

    result = {
        'command': cmd,
        'output': output.stdout.strip(),
        'error': output.stderr.strip()
    }

    if not result['output']:
        is_compliant = True
        print("noexec option is set on /dev/shm partition.")
    else:
        print("noexec option is NOT set on /dev/shm partition.")

    print()

    # Output to database
    write_output_to_database(section, section_name, is_scored, is_compliant, result)

def ensure_nodev_on_removable_media():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The `nodev` mount option specifies that the filesystem cannot contain special devices.

    Rationale:
    ----------
    Removable media containing character and block special devices could be used to
    circumvent security controls by allowing non-root users to access sensitive device files
    such as `/dev/kmem` or the raw disk partitions.
    """
    section = "1.1.18"
    section_name = "Ensure nodev option set on removable media partitions"
    is_scored = False
    is_compliant = False

    pretty_print("[1.1.18] Ensure nodev option set on removable media partitions (Not Scored)")
    print()

    cmd = "mount"

    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    result = {
        'command': cmd,
        'output': output.stdout.strip(),
        'error': output.stderr.strip()
    }

    print(f"Command Run: {cmd}")
    
    if result['error']:
        print(f"Error:\n{result['error']}")
    
    if result['output']:
        if any("nodev" not in line for line in result['output'].splitlines()):
            print("nodev option is NOT set on the removable medias.")
        else:
            is_compliant = True
            print("nodev option is set on the removable medias.")
    else:
        print("No output from mount command.")
    
    print()

    # Output to database
    write_output_to_database(section, section_name, is_scored, is_compliant, result)


def ensure_nosuid_on_removable_media():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The `nosuid` mount option specifies that the filesystem cannot contain `setuid` files.

    Rationale:
    ----------
    Run the following command and verify that the nosuid option is set on all removable media
    partitions.
    """
    section = "1.1.19"
    section_name = "Ensure nosuid option set on removable media partitions"
    is_scored = False
    is_compliant = False

    pretty_print("[1.1.19] Ensure nosuid option set on removable media partitions (Not Scored)")
    print()

    cmd = "mount"

    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    result = {
        'command': cmd,
        'output': output.stdout.strip(),
        'error': output.stderr.strip()
    }

    print(f"Command Run: {cmd}")

    if result['error']:
        print(f"Error:\n{result['error']}")
    
    if result['output']:
        if any("nosuid" not in line for line in result['output'].splitlines()):
            print("nosuid option is NOT set on the removable medias.")
        else:
            is_compliant = True
            print("nosuid option is set on the removable medias.")
    else:
        print("No output from mount command.")
    
    print()

    # Output to database
    write_output_to_database(section, section_name, is_scored, is_compliant, result)



def ensure_noexec_on_removable_media():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    The `noexec` mount option specifies that the filesystem cannot contain executable binaries.

    Rationale:
    ----------
    Run the following command and verify that the noexec option is set on all removable media
    partitions.
    """
    section = "1.1.20"
    section_name = "Ensure noexec option set on removable media partitions"
    is_scored = False
    is_compliant = False

    pretty_print("[1.1.20] Ensure noexec option set on removable media partitions (Not Scored)")
    print()

    cmd = "mount"

    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    result = {
        'command': cmd,
        'output': output.stdout.strip(),
        'error': output.stderr.strip()
    }

    print(f"Command Run: {cmd}")

    if result['error']:
        print(f"Error:\n{result['error']}")
    
    if result['output']:
        if any("noexec" not in line for line in result['output'].splitlines()):
            print("noexec option is NOT set on the removable medias.")
        else:
            is_compliant = True
            print("noexec option is set on the removable medias.")
    else:
        print("No output from mount command.")
    
    print()

    # Output to database
    write_output_to_database(section, section_name, is_scored, is_compliant, result)


def ensure_sticky_bit_on_world_writable_directories():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 1 - Workstation

    Description:
    ------------
    Setting the sticky bit on world writable directories prevents users from deleting or
    renaming files in that directory that are not owned by them.

    Rationale:
    ----------
    This feature prevents the ability to delete or rename files in world writable directories
    (such as `/tmp` ) that are owned by another user.
    """
    section = "1.1.21"
    section_name = "Ensure sticky bit is set on all world-writable directories"
    is_scored = True
    is_compliant = False

    pretty_print("[1.1.21] Ensure sticky bit is set on all world-writable directories (Scored)")
    print()

    cmd = "df --local -P | awk '{if (NR!=1) print $6}' | xargs -I '{}' find '{}' -xdev -type d \( -perm -0002 -a ! -perm -1000 \) 2>/dev/null"

    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    result = {
        'command': cmd,
        'output': output.stdout.strip(),
        'error': output.stderr.strip()
    }

    print(f"Command Run: {cmd}")

    if result['error']:
        print(f"Error:\n{result['error']}")
    
    if not result['output']:
        is_compliant = True
        print("Sticky bit is set on all world-writable directories.")
    else:
        print("Sticky bit is NOT set on all world-writable directories.")
    
    print()

    # Output to database
    write_output_to_database(section, section_name, is_scored, is_compliant, result)


def ensure_disabled_automounting():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 2 - Workstation

    Description:
    ------------
    `autofs` allows automatic mounting of devices, typically including CD/DVDs and USB drives.

    Rationale:
    ----------
    With automounting enabled anyone with physical access could attach a USB drive or disc
    and have its contents available in system even if they lacked permissions to mount it
    themselves.
    """
    section = "1.1.22"
    section_name = "Disable Automounting"
    is_scored = True
    is_compliant = False

    pretty_print("[1.1.22] Disable Automounting (Scored)")
    print()

    cmd = "systemctl is-enabled autofs"

    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    result = {
        'command': cmd,
        'output': output.stdout.strip(),
        'error': output.stderr.strip()
    }

    print(f"Command Run: {cmd}")

    if result['error']:
        print(f"Error:\n{result['error']}\n\nAutomounting is disabled as autofs is not in service.")
        pretty_underline(result['error'], "-")
        result['output'] = "Automounting is disabled as autofs is not in service."
    elif result['output'] == "disabled":
        is_compliant = True
        result['output'] = "Automounting is disabled."
        print("Automounting is disabled.")
    else:
        result['output'] = "Automounting is NOT disabled."
        print("Automounting is NOT disabled.")

    print()

    # Output to database
    write_output_to_database(section, section_name, is_scored, is_compliant, result)


def ensure_usb_storage_disabled():
    """
    Profile Applicability:
    ----------------------
    - Level 1 - Server
    - Level 2 - Workstation

    Description:
    ------------
    USB storage provides a means to transfer and store files ensuring persistence and
    availability of the files independent of network connection status. Its popularity and utility
    has led to USB-based malware being a simple and common means for network infiltration
    and a first step to establishing a persistent threat within a networked environment.

    Rationale:
    ----------
    Restricting USB access on the system will decrease the physical attack surface for a device
    and diminish the possible vectors to introduce malware.
    """
    section = "1.1.23"
    section_name = "Disabled USB Storage"
    is_scored = True
    is_compliant = False

    pretty_print("[1.1.23] Disable USB Storage (Scored)")
    print()
    
    filesystem = 'usb-storage'

    modprobe_command = f'modprobe -n -v {filesystem}'
    lsmod_command = f'lsmod | grep {filesystem}'

    print(f"Running command: {modprobe_command}")
    modprobe_result = subprocess.run(modprobe_command, shell=True, capture_output=True, text=True)
    print(modprobe_result.stdout)
    if modprobe_result.stderr:
        print("Error:")
        print(modprobe_result.stderr.strip())
        pretty_underline(modprobe_result.stderr, "-")

    print(f"Running command: {lsmod_command}")
    lsmod_result = subprocess.run(lsmod_command, shell=True, capture_output=True, text=True)
    print(lsmod_result.stdout)
    if lsmod_result.stderr:
        print("Error:")
        print(lsmod_result.stderr.strip())
        pretty_underline(lsmod_result.stderr, "-")
    else:
        pretty_underline(lsmod_result.stdout, "-")

    expected_output_modprobe = "insmod /lib/modules/6.5.0-35-generic/kernel/fs/storage/usb-storage.ko"

    modprobe_disabled = expected_output_modprobe in modprobe_result.stdout or not modprobe_result.stdout.strip()
    lsmod_disabled = not lsmod_result.stdout.strip()

    result = {
        'command_modprobe': modprobe_command,
        'output_modprobe': modprobe_result.stdout.strip(),
        'error_modprobe': modprobe_result.stderr.strip(),
        'command_lsmod': lsmod_command,
        'output_lsmod': lsmod_result.stdout.strip(),
        'error_lsmod': lsmod_result.stderr.strip(),
        'compliant_status': "Compliant" if modprobe_disabled and lsmod_disabled else "Not Compliant"
    }

    print(f"Command Run: {modprobe_command}")

    if modprobe_result.stderr:
        print(f"Error:\n{modprobe_result.stderr.strip()}")
    
    print(f"Command Run: {lsmod_command}")

    if lsmod_result.stderr:
        print(f"Error:\n{lsmod_result.stderr.strip()}")

    if modprobe_disabled and lsmod_disabled:
        is_compliant = True
        print(f"USB Access is restricted.")
    else:
        print(f"USB Access is NOT restricted.")
    
    print()

    # Output to database
    write_output_to_database(section, section_name, is_scored, is_compliant, result)

def run():
   
    pretty_print("[1.1] Filesystem Configuration", upper_underline=True)
    print()

    # Get the current module
    current_module = inspect.getmodule(inspect.currentframe())
    
    # Get all functions in the current module
    # functions = inspect.getmembers(current_module, inspect.isfunction)

    source_lines, _ = inspect.getsourcelines(current_module)

    functions = []
    for line in source_lines:
        if line.strip().startswith('def ensure'):
            func_name = line.split('(')[0].replace('def ', '').strip()
            functions.append(func_name)

    for func_name in functions:
        func = getattr(current_module, func_name)
        func()
run()
