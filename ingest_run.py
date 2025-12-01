# ingest_run.py
# Simple helper to initialize the BondKeeper DB and ingest sample_messages.csv
# Save this file as ingest_run.py in your BondKeeper folder and run:
#    python ingest_run.py

import os
import sys

try:
    from simple_ingest import init_db, ingest
except Exception as e:
    print("Error: cannot import simple_ingest.py. Make sure file exists in the same folder.")
    print("Exception:", e)
    sys.exit(1)

CSV_FILE = "sample_messages.csv"
CONTACT_NAME = "Ravi"

def main():
    # check CSV exists
    if not os.path.isfile(CSV_FILE):
        print(f"Error: {CSV_FILE} not found in the current folder ({os.getcwd()}).")
        print("Make sure you saved sample_messages.csv in the BondKeeper folder.")
        return

    try:
        print("Initializing database...")
        init_db()
        print("Ingesting sample messages...")
        ingest(CSV_FILE, CONTACT_NAME)
        print("Done. You can now run: python simple_prompt_call.py")
    except Exception as e:
        print("An error occurred during ingestion:")
        print(e)

if __name__ == "__main__":
    main()
