"""
attendance.py
-------------
Attendance module: pick a date, mark each student Present/Absent, view the
day's attendance and see per-student attendance percentage / history.
"""

from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox

import theme


class AttendanceFrame(ctk.CTkFrame):
    def __init__(self, master, db, current_user="admin", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db
        self.current_user = current_user
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Attendance Management", font=theme.HEADING_FONT,
                     text_color="#1A1D29").grid(row=0, column=0, sticky="w")

        toolbar = ctk.CTkFrame(self, fg_color="white", corner_radius=theme.CORNER_RADIUS,
                                border_width=1, border_color="#E7EBF3")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(toolbar, text="Date (YYYY-MM-DD):", font=theme.SMALL_FONT).pack(
            side="left", padx=(14, 4), pady=10)
        self.date_entry = ctk.CTkEntry(toolbar, width=140, height=32)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(side="left", padx=4, pady=10)

        ctk.CTkButton(toolbar, text="Load", width=80, height=32,
                      fg_color=theme.SECONDARY, hover_color=theme.PRIMARY_HOVER,
                      command=self.refresh).pack(side="left", padx=6, pady=10)
        ctk.CTkButton(toolbar, text="Mark All Present", width=140, height=32,
                      fg_color=theme.ACCENT, hover_color="#3C9142",
                      command=lambda: self._mark_all("Present")).pack(side="left", padx=6, pady=10)
        ctk.CTkButton(toolbar, text="Mark All Absent", width=140, height=32,
                      fg_color=theme.DANGER, hover_color=theme.DANGER_HOVER,
                      command=lambda: self._mark_all("Absent")).pack(side="left", padx=6, pady=10)
        ctk.CTkButton(toolbar, text="Save Attendance", width=150, height=32,
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                      command=self._save_attendance).pack(side="right", padx=14, pady=10)

        self.table = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=8)
        self.table.grid(row=2, column=0, sticky="nsew")

        self.status_vars = {}
        self.refresh()

    # ------------------------------------------------------------------ #
    def refresh(self):
        for w in self.table.winfo_children():
            w.destroy()
        self.status_vars.clear()

        date_str = self.date_entry.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Please use the format YYYY-MM-DD.")
            return

        students = self.db.get_all_students()
        if not students:
            ctk.CTkLabel(self.table, text="No students to display.", text_color=theme.TEXT_MUTED,
                         font=theme.BODY_FONT).pack(pady=30)
            return

        existing = {a["student_id"]: a["status"] for a in self.db.get_attendance_for_date(date_str)}

        # header row
        header_row = ctk.CTkFrame(self.table, fg_color=theme.PRIMARY)
        header_row.pack(fill="x")
        for text, w in [("ID", 60), ("Name", 200), ("Roll No", 100), ("Course", 160),
                        ("Attendance %", 110), ("Status", 220)]:
            ctk.CTkLabel(header_row, text=text, font=theme.SMALL_FONT, text_color="white",
                         width=w, anchor="w").pack(side="left", padx=6, pady=8)

        for idx, s in enumerate(students):
            row = ctk.CTkFrame(self.table, fg_color="#F7F9FC" if idx % 2 else "white")
            row.pack(fill="x", pady=1)

            for text, w in [(str(s["student_id"]), 60), (f"{s['first_name']} {s['last_name']}", 200),
                            (s["roll_number"] or "—", 100), (s["course_name"] or "—", 160)]:
                ctk.CTkLabel(row, text=text, font=theme.SMALL_FONT, width=w, anchor="w").pack(
                    side="left", padx=6, pady=6)

            pct = self.db.attendance_percentage(s["student_id"])
            ctk.CTkLabel(row, text=f"{pct}%", font=theme.SMALL_FONT, width=110, anchor="w").pack(
                side="left", padx=6, pady=6)

            var = ctk.StringVar(value=existing.get(s["student_id"], "Present"))
            self.status_vars[s["student_id"]] = var
            seg = ctk.CTkSegmentedButton(row, values=["Present", "Absent"], variable=var, width=200)
            seg.pack(side="left", padx=6, pady=4)

    def _mark_all(self, status):
        for var in self.status_vars.values():
            var.set(status)

    def _save_attendance(self):
        date_str = self.date_entry.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Invalid Date", "Please use the format YYYY-MM-DD.")
            return

        for student_id, var in self.status_vars.items():
            self.db.mark_attendance(student_id, date_str, var.get())

        self.db.log_activity(self.current_user, f"Saved attendance for {date_str}")
        messagebox.showinfo("Saved", f"Attendance for {date_str} saved successfully.")
        self.refresh()
