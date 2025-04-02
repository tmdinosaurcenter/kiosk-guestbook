import csv
import sqlite3

# Update the database file path if needed.
DATABASE = 'guestbook.db'
EXPORT_FILE = 'mailchimp_export.csv'

def export_guestbook_to_csv():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Select only entries that have an email address, if that's required.
    cursor.execute('''
        SELECT email, first_name, last_name, comment
        FROM guests
        WHERE email IS NOT NULL AND email <> ''
    ''')
    rows = cursor.fetchall()
    
    with open(EXPORT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Write headers matching Mailchimp's expected column names (and including comment)
        writer.writerow(['Email Address', 'First Name', 'Last Name', 'Comment'])
        for row in rows:
            writer.writerow(row)
    
    conn.close()
    print(f"Export completed: {EXPORT_FILE}")

if __name__ == '__main__':
    export_guestbook_to_csv()
