"""
reports.py
----------
Reports module: generate Student / Attendance / Fee / Result / Course
reports and export them to CSV, Excel (openpyxl) or PDF (reportlab).
"""

import csv

import customtkinter as ctk
from tkinter import messagebox, filedialog

import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas

import theme

REPORT_DEFINITIONS = {
    "Student Report": {
        "columns": ["student_id", "first_name", "last_name", "gender", "course_name",
                    "semester", "roll_number", "phone", "email"],
        "headers": ["ID", "First Name", "Last Name", "Gender", "Course", "Semester", "Roll No", "Phone", "Email"],
    },
    "Attendance Report": {
        "columns": ["student_id", "name", "roll_number", "attendance_pct"],
        "headers": ["ID", "Name", "Roll No", "Attendance %"],
    },
    "Fee Report": {
        "columns": ["student_id", "name", "total_fee", "paid_amount", "remaining"],
        "headers": ["ID", "Name", "Total Fee", "Paid", "Remaining"],
    },
    "Result Report": {
        "columns": ["student_id", "name", "subject", "marks", "max_marks", "grade", "semester"],
        "headers": ["ID", "Name", "Subject", "Marks", "Max", "Grade", "Semester"],
    },
    "Course Report": {
        "columns": ["course_id", "course_name", "duration_years", "course_fee", "faculty"],
        "headers": ["ID", "Course Name", "Duration (yrs)", "Fee", "Faculty"],
    },
}


class ReportsFrame(ctk.CTkFrame):
    def __init__(self, master, db, current_user="admin", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db
        self.current_user = current_user
        self.current_rows = []
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(header, text="Reports", font=theme.HEADING_FONT, text_color="#1A1D29").pack(side="left")

        toolbar = ctk.CTkFrame(self, fg_color="white", corner_radius=theme.CORNER_RADIUS,
                                border_width=1, border_color="#E7EBF3")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        ctk.CTkLabel(toolbar, text="Report Type:", font=theme.SMALL_FONT).pack(side="left", padx=(14, 6), pady=10)
        self.report_var = ctk.StringVar(value="Student Report")
        ctk.CTkOptionMenu(toolbar, values=list(REPORT_DEFINITIONS.keys()), variable=self.report_var,
                          width=180, command=lambda _: self._generate()).pack(side="left", padx=6, pady=10)

        ctk.CTkButton(toolbar, text="Generate", width=100, height=32,
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                      command=self._generate).pack(side="left", padx=6, pady=10)

        ctk.CTkButton(toolbar, text="Export CSV", width=110, height=32,
                      fg_color=theme.SECONDARY, hover_color=theme.PRIMARY_HOVER,
                      command=self._export_csv).pack(side="left", padx=6, pady=10)
        ctk.CTkButton(toolbar, text="Export Excel", width=110, height=32,
                      fg_color=theme.ACCENT, hover_color="#3C9142",
                      command=self._export_excel).pack(side="left", padx=6, pady=10)
        ctk.CTkButton(toolbar, text="Export PDF", width=110, height=32,
                      fg_color=theme.WARNING, hover_color="#D68F12",
                      command=self._export_pdf).pack(side="left", padx=6, pady=10)

        self.table = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=8)
        self.table.grid(row=2, column=0, sticky="nsew")

        self._generate()

    # ------------------------------------------------------------------ #
    def _fetch_rows(self, report_name):
        if report_name == "Student Report":
            rows = self.db.get_all_students()
            return [dict(r) for r in rows]

        if report_name == "Attendance Report":
            rows = self.db.get_all_students()
            result = []
            for s in rows:
                result.append({
                    "student_id": s["student_id"],
                    "name": f"{s['first_name']} {s['last_name']}",
                    "roll_number": s["roll_number"],
                    "attendance_pct": self.db.attendance_percentage(s["student_id"]),
                })
            return result

        if report_name == "Fee Report":
            rows = self.db.get_all_students()
            result = []
            for s in rows:
                summary = self.db.get_fee_summary(s["student_id"])
                result.append({
                    "student_id": s["student_id"],
                    "name": f"{s['first_name']} {s['last_name']}",
                    "total_fee": summary["total"],
                    "paid_amount": summary["paid"],
                    "remaining": summary["total"] - summary["paid"],
                })
            return result

        if report_name == "Result Report":
            rows = self.db.get_all_students()
            result = []
            for s in rows:
                for r in self.db.get_results(s["student_id"]):
                    result.append({
                        "student_id": s["student_id"],
                        "name": f"{s['first_name']} {s['last_name']}",
                        "subject": r["subject"],
                        "marks": r["marks"],
                        "max_marks": r["max_marks"],
                        "grade": r["grade"],
                        "semester": r["semester"],
                    })
            return result

        if report_name == "Course Report":
            return [dict(c) for c in self.db.get_courses()]

        return []

    def _generate(self):
        for w in self.table.winfo_children():
            w.destroy()

        report_name = self.report_var.get()
        definition = REPORT_DEFINITIONS[report_name]
        self.current_rows = self._fetch_rows(report_name)
        self.current_columns = definition["columns"]
        self.current_headers = definition["headers"]

        if not self.current_rows:
            ctk.CTkLabel(self.table, text="No data available for this report.",
                         text_color=theme.TEXT_MUTED, font=theme.BODY_FONT).pack(pady=30)
            return

        header_row = ctk.CTkFrame(self.table, fg_color=theme.PRIMARY)
        header_row.pack(fill="x")
        for h in self.current_headers:
            ctk.CTkLabel(header_row, text=h, font=theme.SMALL_FONT, text_color="white",
                         width=130, anchor="w").pack(side="left", padx=6, pady=8)

        for idx, row in enumerate(self.current_rows):
            row_frame = ctk.CTkFrame(self.table, fg_color="#F7F9FC" if idx % 2 else "white")
            row_frame.pack(fill="x", pady=1)
            for col in self.current_columns:
                value = row.get(col, "—")
                ctk.CTkLabel(row_frame, text=str(value), font=theme.SMALL_FONT, width=130,
                             anchor="w").pack(side="left", padx=6, pady=6)

    # ------------------------------------------------------------------ #
    def _export_csv(self):
        if not self.current_rows:
            messagebox.showwarning("No Data", "Generate a report first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(self.current_headers)
                for row in self.current_rows:
                    writer.writerow([row.get(c, "") for c in self.current_columns])
            self.db.log_activity(self.current_user, f"Exported {self.report_var.get()} to CSV")
            messagebox.showinfo("Exported", f"Report saved to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Error", f"Export failed:\n{exc}")

    def _export_excel(self):
        if not self.current_rows:
            messagebox.showwarning("No Data", "Generate a report first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not path:
            return
        try:
            df = pd.DataFrame(self.current_rows)[self.current_columns]
            df.columns = self.current_headers
            df.to_excel(path, index=False)
            self.db.log_activity(self.current_user, f"Exported {self.report_var.get()} to Excel")
            messagebox.showinfo("Exported", f"Report saved to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Error", f"Export failed:\n{exc}")

    def _export_pdf(self):
        if not self.current_rows:
            messagebox.showwarning("No Data", "Generate a report first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not path:
            return
        try:
            c = pdf_canvas.Canvas(path, pagesize=landscape(A4))
            width, height = landscape(A4)

            c.setFillColorRGB(0.118, 0.310, 0.639)
            c.rect(0, height - 20 * mm, width, 20 * mm, fill=True, stroke=False)
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 14)
            c.drawString(15 * mm, height - 13 * mm, self.report_var.get())

            c.setFillColorRGB(0, 0, 0)
            col_width = (width - 30 * mm) / len(self.current_headers)
            y = height - 30 * mm

            c.setFont("Helvetica-Bold", 9)
            for i, h in enumerate(self.current_headers):
                c.drawString((15 + i * (col_width / mm)) * mm, y, h[:20])
            y -= 6 * mm
            c.line(15 * mm, y, width - 15 * mm, y)
            y -= 6 * mm

            c.setFont("Helvetica", 8)
            for row in self.current_rows:
                if y < 15 * mm:
                    c.showPage()
                    y = height - 20 * mm
                    c.setFont("Helvetica", 8)
                for i, col in enumerate(self.current_columns):
                    value = str(row.get(col, ""))[:22]
                    c.drawString((15 + i * (col_width / mm)) * mm, y, value)
                y -= 6 * mm

            c.save()
            self.db.log_activity(self.current_user, f"Exported {self.report_var.get()} to PDF")
            messagebox.showinfo("Exported", f"Report saved to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Error", f"Export failed:\n{exc}")
