"""
NeuroScan AI - Database Operations
All CRUD operations
"""

import sqlite3
from database.db_setup import get_connection


# ── DOCTORS ────────────────────────────────────────────────────

def add_doctor(full_name, email, hashed_password, specialty, phone):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO doctors (full_name, email, password, specialty, phone) VALUES (?,?,?,?,?)",
            (full_name, email, hashed_password, specialty, phone)
        )
        conn.commit()
        return True, "Doctor registered successfully!"
    except sqlite3.IntegrityError:
        return False, "Email already registered!"
    finally:
        conn.close()


def get_doctor_by_email(email):
    conn = get_connection()
    row = conn.execute("SELECT * FROM doctors WHERE email=?", (email,)).fetchone()
    conn.close()
    return row


def get_doctor_by_id(doctor_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM doctors WHERE id=?", (doctor_id,)).fetchone()
    conn.close()
    return row


# ── PATIENTS ───────────────────────────────────────────────────

def add_patient(doctor_id, full_name, age, gender, phone, email, address, medical_history):
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO patients
           (doctor_id, full_name, age, gender, phone, email, address, medical_history)
           VALUES (?,?,?,?,?,?,?,?)""",
        (doctor_id, full_name, age, gender, phone, email, address, medical_history)
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def get_patients_by_doctor(doctor_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM patients WHERE doctor_id=? ORDER BY created_at DESC", (doctor_id,)
    ).fetchall()
    conn.close()
    return rows


def get_patient_by_id(patient_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
    conn.close()
    return row


def update_patient(patient_id, full_name, age, gender, phone, email, address, medical_history):
    conn = get_connection()
    conn.execute(
        """UPDATE patients SET full_name=?,age=?,gender=?,phone=?,email=?,
           address=?,medical_history=? WHERE id=?""",
        (full_name, age, gender, phone, email, address, medical_history, patient_id)
    )
    conn.commit()
    conn.close()


def delete_patient(patient_id):
    conn = get_connection()
    conn.execute("DELETE FROM mri_scans WHERE patient_id=?", (patient_id,))
    conn.execute("DELETE FROM tumor_progression WHERE patient_id=?", (patient_id,))
    conn.execute("DELETE FROM patients WHERE id=?", (patient_id,))
    conn.commit()
    conn.close()


def search_patients(doctor_id, query):
    conn = get_connection()
    q = f"%{query}%"
    rows = conn.execute(
        """SELECT * FROM patients WHERE doctor_id=?
           AND (full_name LIKE ? OR phone LIKE ? OR email LIKE ?)
           ORDER BY created_at DESC""",
        (doctor_id, q, q, q)
    ).fetchall()
    conn.close()
    return rows


# ── SCANS ──────────────────────────────────────────────────────

def add_scan(patient_id, doctor_id, predicted_class, confidence,
             tumor_area, tumor_percentage, tumor_size_category, image_path, notes=""):
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO mri_scans
           (patient_id, doctor_id, predicted_class, confidence,
            tumor_area, tumor_percentage, tumor_size_category, image_path, notes)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (patient_id, doctor_id, predicted_class, confidence,
         tumor_area, tumor_percentage, tumor_size_category, image_path, notes)
    )
    conn.commit()
    scan_id = cur.lastrowid
    conn.execute(
        """INSERT INTO tumor_progression
           (patient_id, scan_id, scan_date, tumor_area, tumor_percentage, predicted_class, confidence)
           VALUES (?,?,datetime('now'),?,?,?,?)""",
        (patient_id, scan_id, tumor_area, tumor_percentage, predicted_class, confidence)
    )
    conn.commit()
    conn.close()
    return scan_id


def update_scan_report(scan_id, report_path):
    conn = get_connection()
    conn.execute("UPDATE mri_scans SET report_path=? WHERE id=?", (report_path, scan_id))
    conn.commit()
    conn.close()


def get_scans_by_patient(patient_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM mri_scans WHERE patient_id=? ORDER BY scan_date DESC", (patient_id,)
    ).fetchall()
    conn.close()
    return rows


def get_scans_by_doctor(doctor_id, limit=100):
    conn = get_connection()
    rows = conn.execute(
        """SELECT ms.*, p.full_name as patient_name
           FROM mri_scans ms JOIN patients p ON ms.patient_id=p.id
           WHERE ms.doctor_id=? ORDER BY ms.scan_date DESC LIMIT ?""",
        (doctor_id, limit)
    ).fetchall()
    conn.close()
    return rows


def get_progression(patient_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tumor_progression WHERE patient_id=? ORDER BY scan_date ASC",
        (patient_id,)
    ).fetchall()
    conn.close()
    return rows


# ── ANALYTICS ──────────────────────────────────────────────────

def get_analytics(doctor_id):
    conn = get_connection()

    total_patients = conn.execute(
        "SELECT COUNT(*) FROM patients WHERE doctor_id=?", (doctor_id,)
    ).fetchone()[0]

    total_scans = conn.execute(
        "SELECT COUNT(*) FROM mri_scans WHERE doctor_id=?", (doctor_id,)
    ).fetchone()[0]

    tumor_dist = conn.execute(
        "SELECT predicted_class, COUNT(*) as count FROM mri_scans WHERE doctor_id=? GROUP BY predicted_class",
        (doctor_id,)
    ).fetchall()

    recent_scans = conn.execute(
        """SELECT ms.scan_date, ms.predicted_class, ms.confidence, p.full_name
           FROM mri_scans ms JOIN patients p ON ms.patient_id=p.id
           WHERE ms.doctor_id=? ORDER BY ms.scan_date DESC LIMIT 10""",
        (doctor_id,)
    ).fetchall()

    monthly_scans = conn.execute(
        """SELECT strftime('%Y-%m', scan_date) as month, COUNT(*) as count
           FROM mri_scans WHERE doctor_id=? GROUP BY month ORDER BY month DESC LIMIT 6""",
        (doctor_id,)
    ).fetchall()

    conn.close()
    return {
        "total_patients":    total_patients,
        "total_scans":       total_scans,
        "tumor_distribution": tumor_dist,
        "recent_scans":      recent_scans,
        "monthly_scans":     monthly_scans,
    }


# ── CHAT ───────────────────────────────────────────────────────

def save_chat_message(doctor_id, role, message):
    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_history (doctor_id, role, message) VALUES (?,?,?)",
        (doctor_id, role, message)
    )
    conn.commit()
    conn.close()


def get_chat_history(doctor_id, limit=50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, message FROM chat_history WHERE doctor_id=? ORDER BY timestamp ASC LIMIT ?",
        (doctor_id, limit)
    ).fetchall()
    conn.close()
    return rows


def clear_chat_history(doctor_id):
    conn = get_connection()
    conn.execute("DELETE FROM chat_history WHERE doctor_id=?", (doctor_id,))
    conn.commit()
    conn.close()
