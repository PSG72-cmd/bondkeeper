import sqlite3

conn = sqlite3.connect("bondkeeper.db")

print("Contacts:", list(conn.execute("SELECT contact_id, name FROM contacts")))
print("Conversations sample:", list(conn.execute("SELECT conv_id, contact_id, substr(text,1,80) FROM conversations LIMIT 5")))

conn.close()
