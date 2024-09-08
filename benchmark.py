import psycopg2
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import distro
from utils import software_updates
from utils import filesystems_integrity
from utils import bootloader_settings
from utils import unused_filesystems

# Database connection details
DB_HOST = "localhost"
DB_NAME = "CIS_BENCHMARKING"
DB_USER = "postgres"
DB_PASSWORD = "praveen123"

# Define PDF filename
PDF_FILE = "cis_reports.pdf"

def create_connection():
    """Create a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
        )
        return conn
    except psycopg2.Error as e:
        print("Unable to connect to the database.")
        print(e)
        return None

def fetch_data_from_db(table_name):
    """Fetch data from the database."""
    conn = create_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {table_name}")
            rows = cur.fetchall()
            conn.close()
            return rows
        except psycopg2.Error as e:
            print(f"Error fetching data from {table_name}.")
            print(e)
            conn.close()
            return None

def generate_report():
    doc = SimpleDocTemplate(PDF_FILE, pagesize=letter)
    elements = []

    # Table headers
    table_data = [["Hostname", "OS Footprint", "Date", "Section", "Section Name", "Scored", "Checklist", "Deviation"]]

    # Fetch data from database and add to table
    for table_name in ["software_updates", "filesystems_integrity", "bootloader_settings"]:
        rows = fetch_data_from_db(table_name)
        if rows:
            for row in rows:
                table_data.append(row)

    # Create the table
    table = Table(table_data)

    # Add style to the table
    style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)])

    table.setStyle(style)
    elements.append(table)

    # Build PDF document
    doc.build(elements)
    print(f"Report generated: {PDF_FILE}")

def run_checks_and_generate_report():
    # Run all checks
    unused_filesystem.run()
    software_updates.run()
    filesystems_integrity.run()
    bootloader_settings.run()
    

    # Generate report
    generate_report()

if __name__ == "__main__":
    run_checks_and_generate_report()

