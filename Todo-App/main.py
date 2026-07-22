"""
main.py
-------
Application entry point. Wires up the working directory so the
package-style imports (database.*, models.*, services.*, ui.*, utils.*)
resolve correctly regardless of where the script is launched from, then
boots the TodoApp window.
"""

from __future__ import annotations

import sys
import traceback
from pathlib import Path
from tkinter import messagebox

# Ensure the project root is on sys.path so absolute imports work
# whether this is run as `python main.py` from any directory.
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    from ui.home import TodoApp
    from database.database import DatabaseError
    from services.task_manager import TaskManagerError

    try:
        app = TodoApp()
        app.mainloop()
    except (DatabaseError, TaskManagerError) as exc:
        # A known, recoverable-in-spirit error (e.g. locked/corrupt DB file).
        try:
            messagebox.showerror(
                "TaskFlow — Startup Error",
                f"The application could not start due to a data error:\n\n{exc}",
            )
        except Exception:
            print(f"Startup error: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001 - last line of defense
        traceback.print_exc()
        try:
            messagebox.showerror(
                "TaskFlow — Unexpected Error",
                f"An unexpected error occurred and the application must close:\n\n{exc}",
            )
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
