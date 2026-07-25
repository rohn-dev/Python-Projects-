"""
database.py
-----------
Central database access layer for the Student Management System.

Design notes:
    * All SQL lives here (and nowhere else) so GUI modules never touch
      SQLite directly - this keeps GUI and data logic cleanly separated.
    * Every query is parameterized to avoid SQL-injection.
    * Foreign keys are enforced (PRAGMA foreign_keys = ON).
    * Passwords are stored as salted SHA-256 hashes, never in plain text.
"""

import sqlite3
import hashlib
import os
import secrets
import shutil
from datetime import datetime

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
DB_PATH = os.path.join(DB_DIR, "students.db")


class Database:
    """Wraps a single SQLite connection and exposes typed helper methods
    for every table used by the application."""

    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(DB_DIR, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self._create_tables()
        self._seed_admin()

    # ------------------------------------------------------------------ #
    # Schema
    # ------------------------------------------------------------------ #
    def _create_tables(self):
        """Create all tables (idempotent) with proper foreign keys."""
        self.cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                username        TEXT UNIQUE NOT NULL,
                password_hash   TEXT NOT NULL,
                salt            TEXT NOT NULL,
                role            TEXT NOT NULL DEFAULT 'admin',
                full_name       TEXT,
                created_at      TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS courses (
                course_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name     TEXT UNIQUE NOT NULL,
                duration_years  REAL NOT NULL,
                course_fee      REAL NOT NULL,
                faculty         TEXT
            );

            CREATE TABLE IF NOT EXISTS students (
                student_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name      TEXT NOT NULL,
                last_name       TEXT NOT NULL,
                gender          TEXT NOT NULL,
                dob             TEXT,
                email           TEXT UNIQUE,
                phone           TEXT,
                address         TEXT,
                course_id       INTEGER,
                semester        INTEGER,
                section         TEXT,
                roll_number     TEXT,
                admission_date  TEXT,
                guardian_name   TEXT,
                guardian_phone  TEXT,
                photo_path      TEXT,
                created_at      TEXT NOT NULL,
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
                    ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS attendance (
                attendance_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id      INTEGER NOT NULL,
                date            TEXT NOT NULL,
                status          TEXT NOT NULL CHECK (status IN ('Present', 'Absent')),
                FOREIGN KEY (student_id) REFERENCES students(student_id)
                    ON DELETE CASCADE,
                UNIQUE(student_id, date)
            );

            CREATE TABLE IF NOT EXISTS fees (
                fee_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id      INTEGER NOT NULL,
                total_fee       REAL NOT NULL,
                paid_amount     REAL NOT NULL DEFAULT 0,
                payment_date    TEXT,
                payment_mode    TEXT,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS results (
                result_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id      INTEGER NOT NULL,
                subject         TEXT NOT NULL,
                marks           REAL NOT NULL,
                max_marks       REAL NOT NULL DEFAULT 100,
                grade           TEXT,
                semester        INTEGER,
                remarks         TEXT,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS activity_log (
                log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username        TEXT,
                action          TEXT NOT NULL,
                timestamp       TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def _seed_admin(self):
        """Create a default admin user (admin / admin123) on first run."""
        self.cursor.execute("SELECT COUNT(*) FROM users")
        if self.cursor.fetchone()[0] == 0:
            self.create_user("admin", "admin123", "admin", "Administrator")

    # ------------------------------------------------------------------ #
    # Password hashing helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

    # ------------------------------------------------------------------ #
    # Users
    # ------------------------------------------------------------------ #
    def create_user(self, username, password, role="admin", full_name=""):
        salt = secrets.token_hex(16)
        pw_hash = self._hash_password(password, salt)
        self.cursor.execute(
            "INSERT INTO users (username, password_hash, salt, role, full_name, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (username, pw_hash, salt, role, full_name, datetime.now().isoformat()),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def verify_user(self, username, password):
        """Return the user row if credentials are valid, else None."""
        self.cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = self.cursor.fetchone()
        if row is None:
            return None
        expected = self._hash_password(password, row["salt"])
        if secrets.compare_digest(expected, row["password_hash"]):
            return row
        return None

    def change_password(self, username, new_password):
        salt = secrets.token_hex(16)
        pw_hash = self._hash_password(new_password, salt)
        self.cursor.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE username = ?",
            (pw_hash, salt, username),
        )
        self.conn.commit()

    def get_all_users(self):
        self.cursor.execute("SELECT id, username, role, full_name, created_at FROM users")
        return self.cursor.fetchall()

    def delete_user(self, user_id):
        self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()

    # ------------------------------------------------------------------ #
    # Courses
    # ------------------------------------------------------------------ #
    def add_course(self, name, duration, fee, faculty):
        self.cursor.execute(
            "INSERT INTO courses (course_name, duration_years, course_fee, faculty) "
            "VALUES (?, ?, ?, ?)",
            (name, duration, fee, faculty),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def update_course(self, course_id, name, duration, fee, faculty):
        self.cursor.execute(
            "UPDATE courses SET course_name=?, duration_years=?, course_fee=?, faculty=? "
            "WHERE course_id=?",
            (name, duration, fee, faculty, course_id),
        )
        self.conn.commit()

    def delete_course(self, course_id):
        self.cursor.execute("DELETE FROM courses WHERE course_id=?", (course_id,))
        self.conn.commit()

    def get_courses(self):
        self.cursor.execute("SELECT * FROM courses ORDER BY course_name")
        return self.cursor.fetchall()

    def get_course_by_id(self, course_id):
        self.cursor.execute("SELECT * FROM courses WHERE course_id=?", (course_id,))
        return self.cursor.fetchone()

    # ------------------------------------------------------------------ #
    # Students
    # ------------------------------------------------------------------ #
    def add_student(self, data: dict):
        """data keys must match the students table columns (minus student_id)."""
        data = dict(data)
        data["created_at"] = datetime.now().isoformat()
        columns = ", ".join(data.keys())
        placeholders = ", ".join("?" for _ in data)
        self.cursor.execute(
            f"INSERT INTO students ({columns}) VALUES ({placeholders})",
            tuple(data.values()),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def update_student(self, student_id, data: dict):
        set_clause = ", ".join(f"{k}=?" for k in data.keys())
        self.cursor.execute(
            f"UPDATE students SET {set_clause} WHERE student_id=?",
            tuple(data.values()) + (student_id,),
        )
        self.conn.commit()

    def delete_student(self, student_id):
        self.cursor.execute("DELETE FROM students WHERE student_id=?", (student_id,))
        self.conn.commit()

    def get_student(self, student_id):
        self.cursor.execute("SELECT * FROM students WHERE student_id=?", (student_id,))
        return self.cursor.fetchone()

    def email_exists(self, email, exclude_id=None):
        if exclude_id:
            self.cursor.execute(
                "SELECT 1 FROM students WHERE email=? AND student_id<>?", (email, exclude_id)
            )
        else:
            self.cursor.execute("SELECT 1 FROM students WHERE email=?", (email,))
        return self.cursor.fetchone() is not None

    def get_all_students(self, course_id=None, semester=None, search=None):
        query = (
            "SELECT s.*, c.course_name FROM students s "
            "LEFT JOIN courses c ON s.course_id = c.course_id WHERE 1=1"
        )
        params = []
        if course_id:
            query += " AND s.course_id = ?"
            params.append(course_id)
        if semester:
            query += " AND s.semester = ?"
            params.append(semester)
        if search:
            query += (
                " AND (s.first_name LIKE ? OR s.last_name LIKE ? OR s.roll_number LIKE ? "
                "OR s.phone LIKE ? OR CAST(s.student_id AS TEXT) LIKE ?)"
            )
            like = f"%{search}%"
            params += [like, like, like, like, like]
        query += " ORDER BY s.student_id DESC"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def count_students(self):
        self.cursor.execute("SELECT COUNT(*) FROM students")
        return self.cursor.fetchone()[0]

    def count_by_gender(self, gender):
        self.cursor.execute("SELECT COUNT(*) FROM students WHERE gender=?", (gender,))
        return self.cursor.fetchone()[0]

    def recent_admissions(self, limit=5):
        self.cursor.execute(
            "SELECT s.*, c.course_name FROM students s "
            "LEFT JOIN courses c ON s.course_id = c.course_id "
            "ORDER BY s.created_at DESC LIMIT ?",
            (limit,),
        )
        return self.cursor.fetchall()

    def students_per_course(self):
        self.cursor.execute(
            "SELECT c.course_name, COUNT(s.student_id) as cnt FROM courses c "
            "LEFT JOIN students s ON s.course_id = c.course_id "
            "GROUP BY c.course_id ORDER BY cnt DESC"
        )
        return self.cursor.fetchall()

    # ------------------------------------------------------------------ #
    # Attendance
    # ------------------------------------------------------------------ #
    def mark_attendance(self, student_id, date, status):
        self.cursor.execute(
            "INSERT INTO attendance (student_id, date, status) VALUES (?, ?, ?) "
            "ON CONFLICT(student_id, date) DO UPDATE SET status=excluded.status",
            (student_id, date, status),
        )
        self.conn.commit()

    def get_attendance_for_date(self, date):
        self.cursor.execute(
            "SELECT a.*, s.first_name, s.last_name, s.roll_number FROM attendance a "
            "JOIN students s ON a.student_id = s.student_id WHERE a.date=?",
            (date,),
        )
        return self.cursor.fetchall()

    def get_attendance_history(self, student_id):
        self.cursor.execute(
            "SELECT * FROM attendance WHERE student_id=? ORDER BY date DESC", (student_id,)
        )
        return self.cursor.fetchall()

    def attendance_percentage(self, student_id):
        self.cursor.execute(
            "SELECT COUNT(*) FROM attendance WHERE student_id=?", (student_id,)
        )
        total = self.cursor.fetchone()[0]
        if total == 0:
            return 0.0
        self.cursor.execute(
            "SELECT COUNT(*) FROM attendance WHERE student_id=? AND status='Present'",
            (student_id,),
        )
        present = self.cursor.fetchone()[0]
        return round(present / total * 100, 1)

    def overall_attendance_percentage(self):
        self.cursor.execute("SELECT COUNT(*) FROM attendance")
        total = self.cursor.fetchone()[0]
        if total == 0:
            return 0.0
        self.cursor.execute("SELECT COUNT(*) FROM attendance WHERE status='Present'")
        present = self.cursor.fetchone()[0]
        return round(present / total * 100, 1)

    # ------------------------------------------------------------------ #
    # Fees
    # ------------------------------------------------------------------ #
    def add_fee_record(self, student_id, total_fee, paid_amount, payment_date, payment_mode):
        self.cursor.execute(
            "INSERT INTO fees (student_id, total_fee, paid_amount, payment_date, payment_mode) "
            "VALUES (?, ?, ?, ?, ?)",
            (student_id, total_fee, paid_amount, payment_date, payment_mode),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_fee_history(self, student_id):
        self.cursor.execute(
            "SELECT * FROM fees WHERE student_id=? ORDER BY payment_date DESC", (student_id,)
        )
        return self.cursor.fetchall()

    def get_fee_summary(self, student_id):
        self.cursor.execute(
            "SELECT COALESCE(SUM(total_fee),0) as total, COALESCE(SUM(paid_amount),0) as paid "
            "FROM fees WHERE student_id=?",
            (student_id,),
        )
        return self.cursor.fetchone()

    def total_fee_collected(self):
        self.cursor.execute("SELECT COALESCE(SUM(paid_amount),0) FROM fees")
        return self.cursor.fetchone()[0]

    def get_all_fees(self):
        self.cursor.execute(
            "SELECT f.*, s.first_name, s.last_name, s.roll_number FROM fees f "
            "JOIN students s ON f.student_id = s.student_id ORDER BY f.payment_date DESC"
        )
        return self.cursor.fetchall()

    # ------------------------------------------------------------------ #
    # Results
    # ------------------------------------------------------------------ #
    def add_result(self, student_id, subject, marks, max_marks, grade, semester, remarks):
        self.cursor.execute(
            "INSERT INTO results (student_id, subject, marks, max_marks, grade, semester, remarks) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (student_id, subject, marks, max_marks, grade, semester, remarks),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def delete_result(self, result_id):
        self.cursor.execute("DELETE FROM results WHERE result_id=?", (result_id,))
        self.conn.commit()

    def get_results(self, student_id, semester=None):
        if semester:
            self.cursor.execute(
                "SELECT * FROM results WHERE student_id=? AND semester=? ORDER BY subject",
                (student_id, semester),
            )
        else:
            self.cursor.execute(
                "SELECT * FROM results WHERE student_id=? ORDER BY semester, subject",
                (student_id,),
            )
        return self.cursor.fetchall()

    # ------------------------------------------------------------------ #
    # Activity log
    # ------------------------------------------------------------------ #
    def log_activity(self, username, action):
        self.cursor.execute(
            "INSERT INTO activity_log (username, action, timestamp) VALUES (?, ?, ?)",
            (username, action, datetime.now().isoformat()),
        )
        self.conn.commit()

    def get_activity_log(self, limit=100):
        self.cursor.execute(
            "SELECT * FROM activity_log ORDER BY log_id DESC LIMIT ?", (limit,)
        )
        return self.cursor.fetchall()

    # ------------------------------------------------------------------ #
    # Backup / Restore
    # ------------------------------------------------------------------ #
    def backup_database(self, backup_path):
        self.conn.commit()
        shutil.copy2(self.db_path, backup_path)
        return backup_path

    def restore_database(self, backup_path):
        self.conn.close()
        shutil.copy2(backup_path, self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()
