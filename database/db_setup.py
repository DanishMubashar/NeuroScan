"""
NeuroScan AI - Database Setup
Creates all required SQLite tables on first run
"""

import sqlite3

DB_PATH = "neuroscan.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name   TEXT    NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            specialty   TEXT    DEFAULT 'Neurologist',
            phone       TEXT,
            gender      TEXT,
            age         INTEGER,
            address     TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # ── Migration: add new columns to an already-existing doctors table ──
    existing_cols = [row[1] for row in c.execute("PRAGMA table_info(doctors)").fetchall()]
    for col_name, col_def in [
        ("gender",  "TEXT"),
        ("age",     "INTEGER"),
        ("address", "TEXT"),
    ]:
        if col_name not in existing_cols:
            c.execute(f"ALTER TABLE doctors ADD COLUMN {col_name} {col_def}")

    c.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id       INTEGER NOT NULL,
            full_name       TEXT    NOT NULL,
            age             INTEGER,
            gender          TEXT,
            phone           TEXT,
            email           TEXT,
            address         TEXT,
            medical_history TEXT,
            created_at      TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS mri_scans (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id          INTEGER NOT NULL,
            doctor_id           INTEGER NOT NULL,
            scan_date           TEXT    DEFAULT (datetime('now')),
            predicted_class     TEXT,
            confidence          REAL,
            tumor_area          REAL,
            tumor_percentage    REAL,
            tumor_size_category TEXT,
            image_path          TEXT,
            report_path         TEXT,
            notes               TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id)  REFERENCES doctors(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tumor_progression (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id       INTEGER NOT NULL,
            scan_id          INTEGER NOT NULL,
            scan_date        TEXT,
            tumor_area       REAL,
            tumor_percentage REAL,
            predicted_class  TEXT,
            confidence       REAL,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (scan_id)    REFERENCES mri_scans(id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id   INTEGER NOT NULL,
            role        TEXT    NOT NULL,
            message     TEXT    NOT NULL,
            timestamp   TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    """)

    conn.commit()
    conn.close()


def seed_guest_data():
    """Ensure guest doctor (id=1) and guest patient (id=1) exist for no-auth mode."""
    conn = get_connection()
    c = conn.cursor()

    # Guest doctor
    exists = c.execute("SELECT id FROM doctors WHERE id=1").fetchone()
    if not exists:
        c.execute(
            "INSERT OR IGNORE INTO doctors (id, full_name, email, password, specialty) "
            "VALUES (1, 'Guest Doctor', 'guest@neuroscan.ai', 'no-auth', 'Radiology')"
        )

    # Guest patient (placeholder for no-auth scans)
    p_exists = c.execute("SELECT id FROM patients WHERE id=1").fetchone()
    if not p_exists:
        c.execute(
            "INSERT OR IGNORE INTO patients (id, doctor_id, full_name, age, gender) "
            "VALUES (1, 1, 'Anonymous Patient', 0, 'Unknown')"
        )

    conn.commit()
    conn.close()
