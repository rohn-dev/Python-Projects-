# TaskFlow — Professional Desktop To-Do List Application

A modern, feature-rich desktop task manager built with **Python 3.12+** and **CustomTkinter**, following clean architecture (MVC-style layering), SOLID principles, and a fully typed, modular codebase. Built to be portfolio-worthy — not a beginner Tkinter script.

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-3B8ED0.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## ✨ Features

### Task Management
- Add, edit, delete, and duplicate tasks
- Mark complete / undo completion
- Bulk-select and bulk-delete
- Clear all completed tasks in one click
- **Undo delete** (Ctrl+Z) — deleted tasks can be restored

### Organization
- Built-in categories: Personal, Work, College, Shopping, Health, Coding
- Create unlimited **custom categories** with custom colors
- Four priority levels (Low, Medium, High, Critical) with distinct colors
- Pin important tasks to the top of any list
- Mark tasks as favorites

### Dates & Reminders
- Due date **and** due time per task
- Automatic overdue detection and highlighting
- "Today" and "This Week" smart views

### Search, Sort & Filter
- Live search-as-you-type across title, description, category, and priority
- Sort by due date, priority, alphabetical, date created, or completion status
- Filter by: All, Today, This Week, Completed, Pending, Overdue, High Priority, Favorites, Pinned

### Dashboard
- KPI cards: Total, Completed, Pending, Overdue, Completion %
- Animated circular progress ring
- Completion streak tracker
- Daily / weekly goal display
- Recently completed tasks feed

### Modern UI
- Dark mode / Light mode with persisted preference
- Configurable accent color
- Adjustable font scale
- Rounded corners, hover states, and a fully responsive layout
- Toast notifications for every action
- Status bar with live task counts

### Settings (persisted to disk)
- Theme, accent color, font scale
- Startup page
- Auto-save toggle
- Daily / weekly productivity goals
- Sound-on-complete toggle

### Data Management
- Export all tasks to CSV
- Import tasks from CSV
- One-click database backup and restore
- SQLite storage with automatic schema migration

### Keyboard Shortcuts
| Shortcut | Action |
|---|---|
| `Ctrl + N` | New task |
| `Ctrl + F` | Focus search |
| `Delete` | Remove task |
| `Ctrl + E` | Edit task |
| `Ctrl + D` | Duplicate task |
| `Ctrl + S` | Save settings |
| `Ctrl + Z` | Undo last delete |

### Robust Error Handling
Empty titles, invalid dates/times, database failures, missing files on import/restore, and missing tasks are all caught and surfaced as friendly toast/dialog messages — the app never crashes on bad input.

---

## 📸 Screenshots

> Add screenshots of the Dashboard, Task List, and Settings views here after your first run, e.g.:
>
> `assets/images/dashboard.png`, `assets/images/task-list.png`, `assets/images/settings.png`

---

## 🛠 Technologies

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| UI Toolkit | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Database | SQLite (via `sqlite3`, stdlib) |
| Images | Pillow |
| Dates | `datetime` (stdlib) |
| Paths | `pathlib` (stdlib) |

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/Todo-App.git
cd Todo-App
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

> **Linux users:** Tkinter is not bundled with all Python distributions. If you see `ModuleNotFoundError: No module named 'tkinter'`, install it via your package manager, e.g. `sudo apt install python3-tk`.

### 4. Run the application
```bash
python main.py
```

The SQLite database (`data/tasks.db`) and settings file (`data/settings.json`) are created automatically on first launch.

---

## 🚀 Usage

- Click **+ New Task** or press `Ctrl+N` to add a task.
- Use the sidebar to jump between **Dashboard**, **Today's Tasks**, **All Tasks**, **Categories**, **Completed**, **Settings**, and **About**.
- Use the search bar (`Ctrl+F`) and sort dropdown at the top of any list view.
- Click the filter dropdown above a task list to narrow by status, and the category dropdown to narrow by category.
- Hover over a task card for quick actions: favorite ⭐, pin 📌, edit ✎, duplicate ⧉, delete 🗑.
- Visit **Settings** to switch themes, set an accent color, configure goals, export/import CSV, and back up or restore your database.

---

## 📁 Folder Structure

```
Todo-App/
│
├── main.py                  # Application entry point
├── requirements.txt
├── README.md
│
├── database/
│   └── database.py          # SQLite access layer (schema, migrations, CRUD)
│
├── models/
│   └── task.py               # Task dataclass, validation, computed properties
│
├── services/
│   └── task_manager.py       # Business logic: filtering, sorting, search, undo, stats
│
├── ui/
│   ├── home.py                # Main window, view routing, wiring
│   ├── sidebar.py             # Navigation sidebar
│   ├── dialogs.py             # Add/Edit task, confirm, and category dialogs
│   └── widgets.py             # TaskCard, StatCard, ProgressRing, Toast
│
├── utils/
│   ├── constants.py           # Priorities, categories, colors, shortcuts, paths
│   ├── helpers.py             # Settings persistence, date/time validation
│   └── themes.py              # Appearance mode + color palette helpers
│
├── assets/
│   ├── icons/
│   └── images/
│
└── data/
    ├── tasks.db                # Created automatically on first run
    ├── settings.json           # Created automatically on first run
    └── backups/                # Created when you use "Backup Database"
```

---

## 🏗 Architecture

The codebase follows an MVC-inspired separation of concerns:

- **Model** (`models/task.py`) — a plain, typed `Task` dataclass with validation and computed properties (`is_overdue`, `display_due_date`, etc.). No UI or database code.
- **Database** (`database/database.py`) — the only module that touches SQLite. Owns schema creation, forward migrations, and raw CRUD.
- **Service / Controller** (`services/task_manager.py`) — the single entry point the UI calls into. Owns validation orchestration, filtering, searching, sorting, undo stacks, statistics, and CSV/backup import-export.
- **View** (`ui/*.py`) — CustomTkinter widgets and windows. Never talks to the database directly; every action goes through `TaskManager`.

This means the database engine or UI toolkit could be swapped without touching business logic, and the business logic can be unit-tested independently of any GUI.

---

## 🔮 Future Improvements

- Drag-and-drop task reordering
- Built-in calendar view
- PDF export
- Recurring tasks (daily/weekly/monthly)
- Tags (in addition to categories)
- System tray integration with desktop notifications
- Automatic scheduled backups
- Multiple independent task lists/workspaces
- Full keyboard navigation across task cards

---

## 📄 License

MIT License — free to use, modify, and distribute.
