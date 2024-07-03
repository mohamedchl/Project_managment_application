import sqlite3

# Get the absolute path to the SQLite database file
db_file = r"c:\Users\Dell\OneDrive\Desktop\PFE_PROJECT\Project\db.sqlite3"

try:
    # Connect to the SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT nom_tache from Gestion_projet_tache where id_tache=11 ;")
    conn.commit()
except sqlite3.Error as e:
    print("Error connecting to the database:", e)
finally:
    # Close the connection
    conn.close()
