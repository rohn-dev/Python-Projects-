# Student Management System

A modern, professional desktop ERP-style Student Management System built with
**Python**, **CustomTkinter**, and **SQLite**.

## Features

- **Login System** — username/password auth, salted password hashing, Remember Me, logout
- **Dashboard** — summary cards (students, boys, girls, courses, attendance %, fee collected),
  student-distribution pie chart, recent admissions, quick action buttons
- **Student Management** — add / edit / delete / view / search / filter by course & semester,
  photo upload
- **Attendance** — mark Present/Absent per date, bulk mark all, per-student attendance %
- **Fee Management** — record payments, view history & summary, generate PDF receipts
- **Course Management** — add / edit / delete courses with duration, fee, faculty
- **Result Management** — subject-wise marks with auto grade/percentage/CGPA, printable
  PDF mark sheets
- **Reports** — Student / Attendance / Fee / Result / Course reports, exportable to
  CSV, Excel (.xlsx), and PDF
- **Search** — by name, student ID, roll number, course, phone
- **Settings** — light/dark mode, database backup & restore, change password,
  user management, activity log

## Project Structure

```
StudentManagementSystem/
├── main.py           # Entry point, sidebar navigation & app shell
├── database.py        # All SQL / schema / CRUD (single source of DB truth)
├── theme.py            # Shared colors, fonts, validation helpers
├── login.py            # Login window
├── dashboard.py         # Dashboard cards, chart, recent admissions
├── student.py            # Student CRUD + search/filter + photo upload
├── attendance.py           # Attendance marking & history
├── fees.py                  # Fee payments + PDF receipt generator
├── courses.py                 # Course CRUD
├── results.py                   # Results + PDF mark sheet generator
├── reports.py                     # Reports + CSV/Excel/PDF export
├── settings.py                      # Theme, backup/restore, users, password
├── requirements.txt
├── database/
│   └── students.db      # created automatically on first run
└── assets/
    └── images/            # uploaded student photos are copied here
```

## Setup

```bash
pip install -r requirements.txt
python main.py
```

> **Note:** CustomTkinter uses Tkinter, which ships with most Python installers.
> On Linux, if you see `ModuleNotFoundError: No module named 'tkinter'`,
> install it via your package manager, e.g. `sudo apt install python3-tk`.

## Default Login

```
Username: admin
Password: admin123
```

You can change this password from **Settings → Change Password** after logging in,
and add more admin users from **Settings → User Management**.

## Database

SQLite database is created automatically at `database/students.db` on first run,
with normalized tables and foreign keys:

- `users` — login accounts (salted SHA-256 password hashes)
- `courses` — course catalog
- `students` — student records (FK → courses)
- `attendance` — one row per student per date (FK → students)
- `fees` — payment records (FK → students)
- `results` — subject-wise marks (FK → students)
- `activity_log` — audit trail of user actions

## Notes on Scope

This build focuses on a fully working core system: all 10 requested feature
areas are implemented end-to-end and have been tested (form validation, CRUD,
PDF/Excel/CSV export, and full navigation through every module). A few of the
"bonus" items from the original spec (webcam capture, QR codes, ID card
generation, email notifications) were left out to keep the codebase focused
and maintainable — the modular architecture (one class/module per feature,
all SQL isolated in `database.py`) makes them straightforward to add later
if you'd like help with any of them.
