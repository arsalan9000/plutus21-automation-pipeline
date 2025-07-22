# setup_database.py
import sqlite3

# Connect to the database (this will create the file if it doesn't exist)
conn = sqlite3.connect('opportunities.db')
cursor = conn.cursor()

# Create the table
cursor.execute('''
CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    company_name TEXT,
    contact_email TEXT,
    company_website TEXT,
    description TEXT,
    status TEXT,
    ai_summary TEXT,
    alignment_score INTEGER
)
''')

print("Database 'opportunities.db' and table 'opportunities' created successfully.")

# Commit changes and close the connection
conn.commit()
conn.close()