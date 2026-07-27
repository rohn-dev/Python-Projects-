"""
student.py
----------
Student Management module: a scrollable searchable/filterable table plus
an Add/Edit dialog with full validation and optional photo upload.
"""

import os
import shutil
from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image

import theme

PHOTO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "images")


class StudentForm(ctk.CTkToplevel):
    """Modal dialog used for both Add and Edit."""

    def __init__(self, master, db, on_saved, student_row=None):
        super().__init__(master)
        self.db = db
        self.on_saved = on_saved
        self.student_row = student_row
        self.photo_path = student_row["photo_path"] if student_row else None

        self.title("Edit Student" if student_row else "Add Student")
        self.geometry("560x680")
        self.grab_set()
        self.resizable(False, True)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(scroll, text=self.title(), font=theme.SUBHEADING_FONT).pack(anchor="w", pady=(0, 12))

        # Photo
        photo_row = ctk.CTkFrame(scroll, fg_color="transparent")
        photo_row.pack(fill="x", pady=(0, 12))
        self.photo_preview = ctk.CTkLabel(photo_row, text="No Photo", width=80, height=80,
                                           fg_color="#EEF2F8", corner_radius=8)
        self.photo_preview.pack(side="left")
        ctk.CTkButton(photo_row, text="Upload Photo", width=140,
                      command=self._upload_photo).pack(side="left", padx=12)
        self._refresh_photo_preview()

        self.fields = {}
        self._add_entry(scroll, "First Name*", "first_name")
        self._add_entry(scroll, "Last Name*", "last_name")
        self._add_dropdown(scroll, "Gender*", "gender", ["Male", "Female", "Other"])
        self._add_entry(scroll, "Date of Birth (YYYY-MM-DD)", "dob")
        self._add_entry(scroll, "Email*", "email")
        self._add_entry(scroll, "Phone Number*", "phone")
        self._add_entry(scroll, "Address", "address")

        courses = self.db.get_courses()
        self.course_map = {c["course_name"]: c["course_id"] for c in courses}
        course_names = list(self.course_map.keys()) or ["(No courses - add one first)"]
        self._add_dropdown(scroll, "Course*", "course", course_names)

        self._add_entry(scroll, "Semester*", "semester")
        self._add_entry(scroll, "Section", "section")
        self._add_entry(scroll, "Roll Number*", "roll_number")
        self._add_entry(scroll, "Admission Date (YYYY-MM-DD)", "admission_date",
                         default=datetime.now().strftime("%Y-%m-%d"))
        self._add_entry(scroll, "Guardian Name", "guardian_name")
        self._add_entry(scroll, "Guardian Phone", "guardian_phone")

        if student_row:
            self._prefill()

        self.error_label = ctk.CTkLabel(scroll, text="", text_color=theme.DANGER, font=theme.SMALL_FONT,
                                         wraplength=480, justify="left")
        self.error_label.pack(anchor="w", pady=(6, 0))

        ctk.CTkButton(scroll, text="Save Student", height=42, corner_radius=theme.BUTTON_RADIUS,
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                      command=self._save).pack(fill="x", pady=(16, 4))

    # ------------------------------------------------------------------ #
    def _add_entry(self, parent, label, key, default=""):
        ctk.CTkLabel(parent, text=label, font=theme.SMALL_FONT, anchor="w").pack(fill="x")
        entry = ctk.CTkEntry(parent, height=36)
        entry.pack(fill="x", pady=(2, 10))
        if default:
            entry.insert(0, default)
        self.fields[key] = entry

    def _add_dropdown(self, parent, label, key, options):
        ctk.CTkLabel(parent, text=label, font=theme.SMALL_FONT, anchor="w").pack(fill="x")
        var = ctk.StringVar(value=options[0] if options else "")
        dropdown = ctk.CTkOptionMenu(parent, values=options, variable=var)
        dropdown.pack(fill="x", pady=(2, 10))
        self.fields[key] = var

    def _prefill(self):
        s = self.student_row
        self.fields["first_name"].insert(0, s["first_name"] or "")
        self.fields["last_name"].insert(0, s["last_name"] or "")
        self.fields["gender"].set(s["gender"] or "Male")
        self.fields["dob"].insert(0, s["dob"] or "")
        self.fields["email"].insert(0, s["email"] or "")
        self.fields["phone"].insert(0, s["phone"] or "")
        self.fields["address"].insert(0, s["address"] or "")
        if s["course_name"]:
            self.fields["course"].set(s["course_name"])
        self.fields["semester"].insert(0, str(s["semester"] or ""))
        self.fields["section"].insert(0, s["section"] or "")
        self.fields["roll_number"].insert(0, s["roll_number"] or "")
        self.fields["admission_date"].delete(0, "end")
        self.fields["admission_date"].insert(0, s["admission_date"] or "")
        self.fields["guardian_name"].insert(0, s["guardian_name"] or "")
        self.fields["guardian_phone"].insert(0, s["guardian_phone"] or "")

    def _refresh_photo_preview(self):
        if self.photo_path and os.path.exists(self.photo_path):
            try:
                img = Image.open(self.photo_path)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(80, 80))
                self.photo_preview.configure(image=ctk_img, text="")
            except Exception:
                self.photo_preview.configure(text="No Photo", image=None)

    def _upload_photo(self):
        path = filedialog.askopenfilename(
            title="Select Student Photo",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif")]
        )
        if not path:
            return
        os.makedirs(PHOTO_DIR, exist_ok=True)
        dest = os.path.join(PHOTO_DIR, f"student_{datetime.now().timestamp():.0f}_{os.path.basename(path)}")
        shutil.copy2(path, dest)
        self.photo_path = dest
        self._refresh_photo_preview()

    # ------------------------------------------------------------------ #
    def _save(self):
        first_name = self.fields["first_name"].get().strip()
        last_name = self.fields["last_name"].get().strip()
        gender = self.fields["gender"].get()
        dob = self.fields["dob"].get().strip()
        email = self.fields["email"].get().strip()
        phone = self.fields["phone"].get().strip()
        address = self.fields["address"].get().strip()
        course_name = self.fields["course"].get()
        semester_raw = self.fields["semester"].get().strip()
        section = self.fields["section"].get().strip()
        roll_number = self.fields["roll_number"].get().strip()
        admission_date = self.fields["admission_date"].get().strip()
        guardian_name = self.fields["guardian_name"].get().strip()
        guardian_phone = self.fields["guardian_phone"].get().strip()

        # --- Validation ---
        if not theme.not_empty(first_name, last_name, email, phone, roll_number):
            self.error_label.configure(text="Please fill all required (*) fields.")
            return
        if not theme.is_valid_email(email):
            self.error_label.configure(text="Please enter a valid email address.")
            return
        if not theme.is_valid_phone(phone):
            self.error_label.configure(text="Please enter a valid phone number (7-15 digits).")
            return
        if course_name not in self.course_map:
            self.error_label.configure(text="Please add a course first, then select it here.")
            return
        try:
            semester = int(semester_raw)
        except ValueError:
            self.error_label.configure(text="Semester must be a number.")
            return

        exclude_id = self.student_row["student_id"] if self.student_row else None
        if self.db.email_exists(email, exclude_id):
            self.error_label.configure(text="A student with this email already exists.")
            return

        data = {
            "first_name": first_name,
            "last_name": last_name,
            "gender": gender,
            "dob": dob,
            "email": email,
            "phone": phone,
            "address": address,
            "course_id": self.course_map[course_name],
            "semester": semester,
            "section": section,
            "roll_number": roll_number,
            "admission_date": admission_date,
            "guardian_name": guardian_name,
            "guardian_phone": guardian_phone,
            "photo_path": self.photo_path,
        }

        try:
            if self.student_row:
                self.db.update_student(self.student_row["student_id"], data)
            else:
                self.db.add_student(data)
        except Exception as exc:
            self.error_label.configure(text=f"Database error: {exc}")
            return

        self.on_saved()
        self.destroy()


class StudentFrame(ctk.CTkFrame):
    def __init__(self, master, db, current_user="admin", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db
        self.current_user = current_user
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_toolbar()
        self._build_table_header()
        self._build_table()

        self.refresh()

    # ------------------------------------------------------------------ #
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Student Management", font=theme.HEADING_FONT,
                     text_color="#1A1D29").grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="➕ Add Student", height=38, corner_radius=theme.BUTTON_RADIUS,
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                      command=self._add_student).grid(row=0, column=1, sticky="e")

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="white", corner_radius=theme.CORNER_RADIUS,
                                border_width=1, border_color="#E7EBF3")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        self.search_entry = ctk.CTkEntry(toolbar, placeholder_text="🔍 Search by name, ID, roll no, phone…",
                                          width=300, height=36)
        self.search_entry.pack(side="left", padx=10, pady=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh())

        courses = self.db.get_courses()
        self.course_filter_map = {"All Courses": None}
        self.course_filter_map.update({c["course_name"]: c["course_id"] for c in courses})
        self.course_var = ctk.StringVar(value="All Courses")
        ctk.CTkOptionMenu(toolbar, values=list(self.course_filter_map.keys()),
                          variable=self.course_var, command=lambda _: self.refresh(),
                          width=170).pack(side="left", padx=6, pady=10)

        self.semester_var = ctk.StringVar(value="All Semesters")
        sem_options = ["All Semesters"] + [str(i) for i in range(1, 9)]
        ctk.CTkOptionMenu(toolbar, values=sem_options, variable=self.semester_var,
                          command=lambda _: self.refresh(), width=140).pack(side="left", padx=6, pady=10)

        ctk.CTkButton(toolbar, text="Clear Filters", width=110, fg_color="#EEF2F8",
                      text_color="#1A1D29", hover_color="#DCE4F0",
                      command=self._clear_filters).pack(side="left", padx=6, pady=10)

    def _clear_filters(self):
        self.search_entry.delete(0, "end")
        self.course_var.set("All Courses")
        self.semester_var.set("All Semesters")
        self.refresh()

    def _build_table_header(self):
        header = ctk.CTkFrame(self, fg_color=theme.PRIMARY, corner_radius=8, height=38)
        header.grid(row=2, column=0, sticky="ew")
        header.grid_propagate(False)
        cols = [("ID", 60), ("Name", 170), ("Course", 150), ("Sem", 50),
                ("Roll No", 90), ("Phone", 120), ("Gender", 80), ("Actions", 220)]
        for i, (label, w) in enumerate(cols):
            header.grid_columnconfigure(i, minsize=w)
            ctk.CTkLabel(header, text=label, font=theme.SMALL_FONT, text_color="white").grid(
                row=0, column=i, sticky="w", padx=6)

    def _build_table(self):
        self.table = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=8)
        self.table.grid(row=3, column=0, sticky="nsew")

    # ------------------------------------------------------------------ #
    def refresh(self):
        for widget in self.table.winfo_children():
            widget.destroy()

        course_id = self.course_filter_map.get(self.course_var.get())
        semester = None if self.semester_var.get() == "All Semesters" else int(self.semester_var.get())
        search = self.search_entry.get().strip() or None

        rows = self.db.get_all_students(course_id=course_id, semester=semester, search=search)

        if not rows:
            ctk.CTkLabel(self.table, text="No students found.", text_color=theme.TEXT_MUTED,
                         font=theme.BODY_FONT).pack(pady=30)
            return

        cols_w = [60, 170, 150, 50, 90, 120, 80, 220]
        for r_idx, s in enumerate(rows):
            row_frame = ctk.CTkFrame(self.table, fg_color="#F7F9FC" if r_idx % 2 else "white")
            row_frame.pack(fill="x", pady=1)
            for i, w in enumerate(cols_w):
                row_frame.grid_columnconfigure(i, minsize=w)

            values = [
                str(s["student_id"]), f"{s['first_name']} {s['last_name']}",
                s["course_name"] or "—", str(s["semester"] or "—"),
                s["roll_number"] or "—", s["phone"] or "—", s["gender"] or "—",
            ]
            for i, v in enumerate(values):
                ctk.CTkLabel(row_frame, text=v, font=theme.SMALL_FONT, anchor="w").grid(
                    row=0, column=i, sticky="w", padx=6, pady=8)

            action_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            action_frame.grid(row=0, column=7, sticky="w", padx=4)
            ctk.CTkButton(action_frame, text="View", width=50, height=26, font=theme.SMALL_FONT,
                          fg_color="#EEF2F8", text_color="#1A1D29", hover_color="#DCE4F0",
                          command=lambda s=s: self._view_student(s)).pack(side="left", padx=2)
            ctk.CTkButton(action_frame, text="Edit", width=50, height=26, font=theme.SMALL_FONT,
                          fg_color=theme.SECONDARY, hover_color=theme.PRIMARY_HOVER,
                          command=lambda s=s: self._edit_student(s)).pack(side="left", padx=2)
            ctk.CTkButton(action_frame, text="Delete", width=55, height=26, font=theme.SMALL_FONT,
                          fg_color=theme.DANGER, hover_color=theme.DANGER_HOVER,
                          command=lambda s=s: self._delete_student(s)).pack(side="left", padx=2)

    # ------------------------------------------------------------------ #
    def _add_student(self):
        if not self.db.get_courses():
            messagebox.showwarning("No Courses", "Please add at least one course before adding students.")
            return
        StudentForm(self, self.db, on_saved=self._after_change)

    def _edit_student(self, student_row):
        StudentForm(self, self.db, on_saved=self._after_change, student_row=student_row)

    def _after_change(self):
        self.db.log_activity(self.current_user, "Modified a student record")
        self.refresh()

    def _delete_student(self, student_row):
        name = f"{student_row['first_name']} {student_row['last_name']}"
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {name}?\n"
                                                     "This will also remove their attendance, fees and results."):
            self.db.delete_student(student_row["student_id"])
            self.db.log_activity(self.current_user, f"Deleted student {name}")
            self.refresh()

    def _view_student(self, student_row):
        win = ctk.CTkToplevel(self)
        win.title("Student Details")
        win.geometry("420x560")
        win.grab_set()

        scroll = ctk.CTkScrollableFrame(win, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        if student_row["photo_path"] and os.path.exists(student_row["photo_path"]):
            try:
                img = Image.open(student_row["photo_path"])
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))
                ctk.CTkLabel(scroll, image=ctk_img, text="").pack(pady=(0, 10))
            except Exception:
                pass

        ctk.CTkLabel(scroll, text=f"{student_row['first_name']} {student_row['last_name']}",
                     font=theme.SUBHEADING_FONT).pack(anchor="w")

        fields = [
            ("Student ID", student_row["student_id"]),
            ("Gender", student_row["gender"]),
            ("Date of Birth", student_row["dob"]),
            ("Email", student_row["email"]),
            ("Phone", student_row["phone"]),
            ("Address", student_row["address"]),
            ("Course", student_row["course_name"]),
            ("Semester", student_row["semester"]),
            ("Section", student_row["section"]),
            ("Roll Number", student_row["roll_number"]),
            ("Admission Date", student_row["admission_date"]),
            ("Guardian Name", student_row["guardian_name"]),
            ("Guardian Phone", student_row["guardian_phone"]),
            ("Attendance %", f"{self.db.attendance_percentage(student_row['student_id'])}%"),
        ]
        for label, value in fields:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=label, font=theme.SMALL_FONT, text_color=theme.TEXT_MUTED,
                         width=130, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=str(value) if value not in (None, "") else "—",
                         font=theme.BODY_FONT, anchor="w").pack(side="left")
