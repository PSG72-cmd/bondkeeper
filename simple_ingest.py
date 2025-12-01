import pandas as pd
import sqlite3

DB = "bondkeeper.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS contacts(
        contact_id INTEGER PRIMARY KEY, 
        name TEXT, 
        notes TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS conversations(
        conv_id INTEGER PRIMARY KEY, 
        contact_id INTEGER,
        timestamp TEXT,
        direction TEXT,
        text TEXT
    )
    """)
    conn.commit()
    conn.close()

def ingest(csv_path, contact_name):
    df = pd.read_csv(csv_path)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("INSERT INTO contacts(name, notes) VALUES (?,?)", (contact_name, ""))
    cid = cur.lastrowid

    for _, r in df.iterrows():
        cur.execute("""INSERT INTO conversations(contact_id, timestamp, direction, text)
                       VALUES (?,?,?,?)""",
                    (cid, r['timestamp'], r['direction'], r['text']))
    conn.commit()
    conn.close()
    print(f"Imported {len(df)} messages for {contact_name} (ID={cid})")

if __name__ == "__main__":
    init_db()
    print("BondKeeper database initialized.")
