"""
init_db.py
Initializes bis_data.db using schema.sql and loads data from CSV files in data/.
"""

import os
import sqlite3
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(CURRENT_DIR, "bis_data.db")
SCHEMA_PATH = os.path.join(CURRENT_DIR, "schema.sql")
DATA_DIR = os.path.join(CURRENT_DIR, "data")


def get_table_columns(conn: sqlite3.Connection, table_name: str):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def initialize_database():
    print(f"Initializing SQLite database at: {DB_PATH}")

    # Remove old DB if starting fresh
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
        except Exception:
            pass

    conn = sqlite3.connect(DB_PATH)

    # 1. Execute schema.sql
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    print("Schema applied successfully.")

    # 2. Load standards CSV
    standards_csv = os.path.join(DATA_DIR, "standards_upload_ready.csv")
    if os.path.exists(standards_csv):
        df_std = pd.read_csv(standards_csv)
        valid_cols = get_table_columns(conn, "standards")
        cols_to_use = [c for c in df_std.columns if c in valid_cols]
        df_std[cols_to_use].to_sql("standards", conn, if_exists="append", index=False)
        print(f"Loaded {len(df_std)} records into 'standards' table.")

    # 3. Load crosswalk CSV
    crosswalk_csv = os.path.join(DATA_DIR, "crosswalk_upload_ready.csv")
    if os.path.exists(crosswalk_csv):
        df_cw = pd.read_csv(crosswalk_csv)
        valid_cols = get_table_columns(conn, "crosswalk")
        cols_to_use = [c for c in df_cw.columns if c in valid_cols]
        df_cw[cols_to_use].to_sql("crosswalk", conn, if_exists="append", index=False)
        print(f"Loaded {len(df_cw)} records into 'crosswalk' table.")

    # 4. Load HUID reference CSV
    huid_csv = os.path.join(DATA_DIR, "huid_reference_upload_ready.csv")
    if os.path.exists(huid_csv):
        df_huid = pd.read_csv(huid_csv)
        # Check if table is 'huid_reference' or 'huid_records'
        table_name = "huid_reference" if "huid_reference" in schema_sql else "huid_records"
        valid_cols = get_table_columns(conn, table_name)
        cols_to_use = [c for c in df_huid.columns if c in valid_cols]
        df_huid[cols_to_use].to_sql(table_name, conn, if_exists="append", index=False)
        print(f"Loaded {len(df_huid)} records into '{table_name}' table.")

    # 5. Check if ahc or labs CSVs exist and load them if present
    for extra_table in ["ahc", "labs"]:
        extra_csv = os.path.join(DATA_DIR, f"{extra_table}_upload_ready.csv")
        if os.path.exists(extra_csv):
            df_extra = pd.read_csv(extra_csv)
            valid_cols = get_table_columns(conn, extra_table)
            cols_to_use = [c for c in df_extra.columns if c in valid_cols]
            df_extra[cols_to_use].to_sql(extra_table, conn, if_exists="append", index=False)
            print(f"Loaded {len(df_extra)} records into '{extra_table}' table.")

    conn.commit()
    conn.close()
    print("Database initialization complete!")


if __name__ == "__main__":
    initialize_database()
