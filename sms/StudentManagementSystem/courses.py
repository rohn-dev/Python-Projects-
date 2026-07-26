"""
courses.py
----------
Course Management module: add / edit / delete courses (name, duration,
fee, assigned faculty) with a simple card-list layout.
"""

import customtkinter as ctk
from tkinter import messagebox

import theme


class CourseForm(ctk.CTkToplevel):
    def __init__(self, master, db, on_saved, course_row=None):
        super().__init__(master)
        self.db = db
        self.on_saved = on_saved
        self.course_row = course_row

        self.title("Edit Course" if course_row else "Add Course")
        self.geometry("380x420")
        self.grab_set()
        self.resizable(False, False)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text=self.title(), font=theme.SUBHEADING_FONT).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(frame, text="Course Name*", font=theme.SMALL_FONT, anchor="w").pack(fill="x")
        self.name_entry = ctk.CTkEntry(frame, height=36)
        self.name_entry.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(frame, text="Duration (years)*", font=theme.SMALL_FONT, anchor="w").pack(fill="x")
        self.duration_entry = ctk.CTkEntry(frame, height=36)
        self.duration_entry.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(frame, text="Course Fee*", font=theme.SMALL_FONT, anchor="w").pack(fill="x")
        self.fee_entry = ctk.CTkEntry(frame, height=36)
        self.fee_entry.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(frame, text="Faculty Assigned", font=theme.SMALL_FONT, anchor="w").pack(fill="x")
        self.faculty_entry = ctk.CTkEntry(frame, height=36)
        self.faculty_entry.pack(fill="x", pady=(2, 10))

        if course_row:
            self.name_entry.insert(0, course_row["course_name"])
            self.duration_entry.insert(0, str(course_row["duration_years"]))
            self.fee_entry.insert(0, str(course_row["course_fee"]))
            self.faculty_entry.insert(0, course_row["faculty"] or "")

        self.error_label = ctk.CTkLabel(frame, text="", text_color=theme.DANGER, font=theme.SMALL_FONT,
                                         wraplength=330, justify="left")
        self.error_label.pack(anchor="w", pady=(4, 0))

        ctk.CTkButton(frame, text="Save Course", height=40, corner_radius=theme.BUTTON_RADIUS,
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                      command=self._save).pack(fill="x", pady=(16, 0))

    def _save(self):
        name = self.name_entry.get().strip()
        duration = self.duration_entry.get().strip()
        fee = self.fee_entry.get().strip()
        faculty = self.faculty_entry.get().strip()

        if not theme.not_empty(name, duration, fee):
            self.error_label.configure(text="Please fill all required (*) fields.")
            return
        try:
            duration_val = float(duration)
            fee_val = float(fee)
        except ValueError:
            self.error_label.configure(text="Duration and Fee must be numbers.")
            return

        try:
            if self.course_row:
                self.db.update_course(self.course_row["course_id"], name, duration_val, fee_val, faculty)
            else:
                self.db.add_course(name, duration_val, fee_val, faculty)
        except Exception as exc:
            self.error_label.configure(text=f"Database error (duplicate name?): {exc}")
            return

        self.on_saved()
        self.destroy()


class CourseFrame(ctk.CTkFrame):
    def __init__(self, master, db, current_user="admin", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db
        self.current_user = current_user
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Course Management", font=theme.HEADING_FONT,
                     text_color="#1A1D29").grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="➕ Add Course", height=38, corner_radius=theme.BUTTON_RADIUS,
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                      command=self._add_course).grid(row=0, column=1, sticky="e")

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.grid(row=1, column=0, sticky="nsew")
        self.list_frame.grid_columnconfigure((0, 1), weight=1)

        self.refresh()

    def refresh(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        courses = self.db.get_courses()
        if not courses:
            ctk.CTkLabel(self.list_frame, text="No courses added yet.", text_color=theme.TEXT_MUTED,
                         font=theme.BODY_FONT).grid(row=0, column=0, columnspan=2, pady=30)
            return

        for idx, c in enumerate(courses):
            r, col = divmod(idx, 2)
            card = ctk.CTkFrame(self.list_frame, fg_color="white", corner_radius=theme.CORNER_RADIUS,
                                 border_width=1, border_color="#E7EBF3")
            card.grid(row=r, column=col, sticky="nsew", padx=8, pady=8)

            ctk.CTkLabel(card, text=c["course_name"], font=theme.SUBHEADING_FONT,
                         text_color=theme.PRIMARY).pack(anchor="w", padx=16, pady=(14, 4))
            ctk.CTkLabel(card, text=f"Duration: {c['duration_years']} years", font=theme.SMALL_FONT,
                         text_color=theme.TEXT_MUTED).pack(anchor="w", padx=16)
            ctk.CTkLabel(card, text=f"Fee: ₹{c['course_fee']:,.0f}", font=theme.SMALL_FONT,
                         text_color=theme.TEXT_MUTED).pack(anchor="w", padx=16)
            ctk.CTkLabel(card, text=f"Faculty: {c['faculty'] or '—'}", font=theme.SMALL_FONT,
                         text_color=theme.TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 10))

            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=16, pady=(0, 14))
            ctk.CTkButton(btn_row, text="Edit", width=70, height=28, font=theme.SMALL_FONT,
                          fg_color=theme.SECONDARY, hover_color=theme.PRIMARY_HOVER,
                          command=lambda c=c: self._edit_course(c)).pack(side="left", padx=(0, 6))
            ctk.CTkButton(btn_row, text="Delete", width=70, height=28, font=theme.SMALL_FONT,
                          fg_color=theme.DANGER, hover_color=theme.DANGER_HOVER,
                          command=lambda c=c: self._delete_course(c)).pack(side="left")

    def _add_course(self):
        CourseForm(self, self.db, on_saved=self._after_change)

    def _edit_course(self, course_row):
        CourseForm(self, self.db, on_saved=self._after_change, course_row=course_row)

    def _after_change(self):
        self.db.log_activity(self.current_user, "Modified a course")
        self.refresh()

    def _delete_course(self, course_row):
        if messagebox.askyesno("Confirm Deletion",
                                f"Delete course '{course_row['course_name']}'?\n"
                                "Students in this course will remain but lose the course link."):
            self.db.delete_course(course_row["course_id"])
            self.db.log_activity(self.current_user, f"Deleted course {course_row['course_name']}")
            self.refresh()
