"""
results.py
----------
Result Management module: record subject-wise marks, auto-compute grade /
percentage / CGPA, and generate a printable PDF mark sheet.
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas

import theme


def compute_grade(percentage):
    if percentage >= 90:
        return "A+", 10.0
    if percentage >= 80:
        return "A", 9.0
    if percentage >= 70:
        return "B+", 8.0
    if percentage >= 60:
        return "B", 7.0
    if percentage >= 50:
        return "C", 6.0
    if percentage >= 40:
        return "D", 5.0
    return "F", 0.0


class MarksheetGenerator:
    @staticmethod
    def generate(path, student, results, overall_pct, overall_cgpa):
        c = pdf_canvas.Canvas(path, pagesize=A4)
        width, height = A4

        c.setFillColorRGB(0.118, 0.310, 0.639)
        c.rect(0, height - 35 * mm, width, 35 * mm, fill=True, stroke=False)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width / 2, height - 16 * mm, "Student Management System")
        c.setFont("Helvetica", 12)
        c.drawCentredString(width / 2, height - 25 * mm, "Official Mark Sheet")

        c.setFillColorRGB(0, 0, 0)
        y = height - 48 * mm
        c.setFont("Helvetica", 11)
        details = [
            f"Name: {student['first_name']} {student['last_name']}",
            f"Student ID: {student['student_id']}    Roll No: {student['roll_number'] or '-'}",
            f"Course: {student['course_name'] or '-'}    Semester: {student['semester'] or '-'}",
        ]
        for d in details:
            c.drawString(20 * mm, y, d)
            y -= 7 * mm

        y -= 6 * mm
        c.setFont("Helvetica-Bold", 10)
        headers = ["Subject", "Marks", "Max", "Grade", "Remarks"]
        col_x = [20, 90, 115, 140, 165]
        for h, x in zip(headers, col_x):
            c.drawString(x * mm, y, h)
        y -= 4 * mm
        c.line(20 * mm, y, width - 20 * mm, y)
        y -= 7 * mm

        c.setFont("Helvetica", 9)
        for r in results:
            c.drawString(20 * mm, y, r["subject"][:28])
            c.drawString(90 * mm, y, str(r["marks"]))
            c.drawString(115 * mm, y, str(r["max_marks"]))
            c.drawString(140 * mm, y, r["grade"] or "-")
            c.drawString(165 * mm, y, (r["remarks"] or "-")[:22])
            y -= 7 * mm

        y -= 6 * mm
        c.line(20 * mm, y, width - 20 * mm, y)
        y -= 9 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(20 * mm, y, f"Overall Percentage: {overall_pct:.2f}%")
        c.drawString(110 * mm, y, f"CGPA: {overall_cgpa:.2f}")

        y -= 20 * mm
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(20 * mm, y, "This is a system-generated mark sheet.")

        c.save()


class ResultForm(ctk.CTkToplevel):
    def __init__(self, master, db, student, on_saved):
        super().__init__(master)
        self.db = db
        self.student = student
        self.on_saved = on_saved

        self.title(f"Add Result - {student['first_name']} {student['last_name']}")
        self.geometry("380x460")
        self.grab_set()
        self.resizable(False, False)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Record Subject Result", font=theme.SUBHEADING_FONT).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(frame, text="Semester*", font=theme.SMALL_FONT, anchor="w").pack(fill="x")
        self.sem_entry = ctk.CTkEntry(frame, height=36)
        self.sem_entry.insert(0, str(student["semester"] or 1))
        self.sem_entry.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(frame, text="Subject*", font=theme.SMALL_FONT, anchor="w").pack(fill="x")
        self.subject_entry = ctk.CTkEntry(frame, height=36)
        self.subject_entry.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(frame, text="Marks Obtained*", font=theme.SMALL_FONT, anchor="w").pack(fill="x")
        self.marks_entry = ctk.CTkEntry(frame, height=36)
        self.marks_entry.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(frame, text="Max Marks*", font=theme.SMALL_FONT, anchor="w").pack(fill="x")
        self.max_entry = ctk.CTkEntry(frame, height=36)
        self.max_entry.insert(0, "100")
        self.max_entry.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(frame, text="Remarks", font=theme.SMALL_FONT, anchor="w").pack(fill="x")
        self.remarks_entry = ctk.CTkEntry(frame, height=36)
        self.remarks_entry.pack(fill="x", pady=(2, 10))

        self.error_label = ctk.CTkLabel(frame, text="", text_color=theme.DANGER, font=theme.SMALL_FONT)
        self.error_label.pack(anchor="w")

        ctk.CTkButton(frame, text="Save Result", height=40, corner_radius=theme.BUTTON_RADIUS,
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                      command=self._save).pack(fill="x", pady=(16, 0))

    def _save(self):
        sem = self.sem_entry.get().strip()
        subject = self.subject_entry.get().strip()
        marks = self.marks_entry.get().strip()
        max_marks = self.max_entry.get().strip()
        remarks = self.remarks_entry.get().strip()

        if not theme.not_empty(sem, subject, marks, max_marks):
            self.error_label.configure(text="Please fill all required fields.")
            return
        try:
            sem_val = int(sem)
            marks_val = float(marks)
            max_val = float(max_marks)
        except ValueError:
            self.error_label.configure(text="Semester/Marks/Max must be numeric.")
            return
        if max_val <= 0 or marks_val < 0 or marks_val > max_val:
            self.error_label.configure(text="Marks must be between 0 and Max Marks.")
            return

        pct = marks_val / max_val * 100
        grade, _ = compute_grade(pct)

        self.db.add_result(self.student["student_id"], subject, marks_val, max_val, grade, sem_val, remarks)
        self.on_saved()
        self.destroy()


class ResultsFrame(ctk.CTkFrame):
    def __init__(self, master, db, current_user="admin", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db
        self.current_user = current_user
        self.selected_student = None
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(header, text="Result Management", font=theme.HEADING_FONT,
                     text_color="#1A1D29").pack(side="left")

        toolbar = ctk.CTkFrame(self, fg_color="white", corner_radius=theme.CORNER_RADIUS,
                                border_width=1, border_color="#E7EBF3")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(toolbar, text="Select Student:", font=theme.SMALL_FONT).pack(side="left", padx=(14, 6), pady=10)
        self.student_map = {}
        self._refresh_student_map()
        self.student_var = ctk.StringVar(value="Select a student")
        self.student_dropdown = ctk.CTkOptionMenu(
            toolbar, values=list(self.student_map.keys()) or ["No students"],
            variable=self.student_var, width=260, command=self._on_student_selected)
        self.student_dropdown.pack(side="left", padx=6, pady=10)

        ctk.CTkButton(toolbar, text="➕ Add Result", width=130, height=32,
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                      command=self._add_result).pack(side="left", padx=10, pady=10)
        ctk.CTkButton(toolbar, text="🖨️ Mark Sheet", width=130, height=32,
                      fg_color=theme.SECONDARY, hover_color=theme.PRIMARY_HOVER,
                      command=self._generate_marksheet).pack(side="left", padx=6, pady=10)

        self.content = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=8)
        self.content.grid(row=2, column=0, sticky="nsew")

        self._render_placeholder()

    def _refresh_student_map(self):
        students = self.db.get_all_students()
        self.student_map = {
            f"{s['student_id']} - {s['first_name']} {s['last_name']}": s for s in students
        }

    def refresh(self):
        self._refresh_student_map()
        self.student_dropdown.configure(values=list(self.student_map.keys()) or ["No students"])

    def _render_placeholder(self):
        for w in self.content.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.content, text="Select a student above to view results.",
                     text_color=theme.TEXT_MUTED, font=theme.BODY_FONT).pack(pady=30)

    def _on_student_selected(self, choice):
        student = self.student_map.get(choice)
        if not student:
            return
        self.selected_student = student
        self._render_results()

    def _add_result(self):
        if not self.selected_student:
            messagebox.showwarning("No Student Selected", "Please select a student first.")
            return
        ResultForm(self, self.db, self.selected_student, on_saved=self._render_results)

    def _get_results_and_stats(self):
        results = self.db.get_results(self.selected_student["student_id"])
        if not results:
            return [], 0.0, 0.0
        total_marks = sum(r["marks"] for r in results)
        total_max = sum(r["max_marks"] for r in results)
        pct = (total_marks / total_max * 100) if total_max else 0.0
        cgpa_points = [compute_grade(r["marks"] / r["max_marks"] * 100)[1] for r in results]
        cgpa = sum(cgpa_points) / len(cgpa_points) if cgpa_points else 0.0
        return results, pct, cgpa

    def _render_results(self):
        for w in self.content.winfo_children():
            w.destroy()

        results, pct, cgpa = self._get_results_and_stats()

        summary_row = ctk.CTkFrame(self.content, fg_color="transparent")
        summary_row.pack(fill="x", padx=16, pady=16)
        for label, value, color in [
            ("Percentage", f"{pct:.2f}%", theme.PRIMARY),
            ("CGPA", f"{cgpa:.2f}", theme.ACCENT),
            ("Subjects", str(len(results)), theme.SECONDARY),
        ]:
            box = ctk.CTkFrame(summary_row, fg_color="#F7F9FC", corner_radius=10)
            box.pack(side="left", expand=True, fill="x", padx=6)
            ctk.CTkLabel(box, text=value, font=theme.CARD_VALUE_FONT, text_color=color).pack(pady=(12, 0))
            ctk.CTkLabel(box, text=label, font=theme.SMALL_FONT, text_color=theme.TEXT_MUTED).pack(pady=(0, 12))

        if not results:
            ctk.CTkLabel(self.content, text="No results recorded yet.", text_color=theme.TEXT_MUTED,
                         font=theme.SMALL_FONT).pack(anchor="w", padx=16, pady=10)
            return

        header_row = ctk.CTkFrame(self.content, fg_color=theme.PRIMARY)
        header_row.pack(fill="x", padx=16)
        for text, w in [("Sem", 50), ("Subject", 180), ("Marks", 90), ("Grade", 70), ("Remarks", 160), ("", 70)]:
            ctk.CTkLabel(header_row, text=text, font=theme.SMALL_FONT, text_color="white",
                         width=w, anchor="w").pack(side="left", padx=6, pady=8)

        for idx, r in enumerate(results):
            row = ctk.CTkFrame(self.content, fg_color="#F7F9FC" if idx % 2 else "white")
            row.pack(fill="x", padx=16, pady=1)
            for text, w in [(str(r["semester"]), 50), (r["subject"], 180),
                            (f"{r['marks']:.0f}/{r['max_marks']:.0f}", 90),
                            (r["grade"] or "-", 70), (r["remarks"] or "-", 160)]:
                ctk.CTkLabel(row, text=text, font=theme.SMALL_FONT, width=w, anchor="w").pack(
                    side="left", padx=6, pady=6)
            ctk.CTkButton(row, text="Delete", width=60, height=26, font=theme.SMALL_FONT,
                          fg_color=theme.DANGER, hover_color=theme.DANGER_HOVER,
                          command=lambda r=r: self._delete_result(r)).pack(side="left", padx=6, pady=4)

    def _delete_result(self, result_row):
        if messagebox.askyesno("Confirm", "Delete this result entry?"):
            self.db.delete_result(result_row["result_id"])
            self._render_results()

    def _generate_marksheet(self):
        if not self.selected_student:
            messagebox.showwarning("No Student Selected", "Please select a student first.")
            return
        results, pct, cgpa = self._get_results_and_stats()
        if not results:
            messagebox.showwarning("No Results", "This student has no results to print.")
            return
        default_name = f"marksheet_{self.selected_student['student_id']}.pdf"
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", initialfile=default_name,
            filetypes=[("PDF files", "*.pdf")], title="Save Mark Sheet As")
        if not path:
            return
        try:
            MarksheetGenerator.generate(path, self.selected_student, results, pct, cgpa)
            self.db.log_activity(self.current_user, f"Generated mark sheet for student {self.selected_student['student_id']}")
            messagebox.showinfo("Mark Sheet Generated", f"Mark sheet saved to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Error", f"Could not generate mark sheet:\n{exc}")
