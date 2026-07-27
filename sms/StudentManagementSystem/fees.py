"""
fees.py
-------
Fee Management module: record payments, view history/summary per student,
and generate a printable PDF receipt using ReportLab.
"""

import os
from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox, filedialog

from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas

import theme


class ReceiptGenerator:
    """Builds a simple, clean PDF fee receipt."""

    @staticmethod
    def generate(path, student, fee_record, receipt_no):
        c = pdf_canvas.Canvas(path, pagesize=A5)
        width, height = A5

        c.setFillColorRGB(0.118, 0.310, 0.639)
        c.rect(0, height - 30 * mm, width, 30 * mm, fill=True, stroke=False)
        c.setFillColorRGB(1, 1, 1)
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width / 2, height - 14 * mm, "Student Management System")
        c.setFont("Helvetica", 10)
        c.drawCentredString(width / 2, height - 21 * mm, "Official Fee Payment Receipt")

        c.setFillColorRGB(0, 0, 0)
        y = height - 42 * mm
        c.setFont("Helvetica-Bold", 11)
        c.drawString(15 * mm, y, f"Receipt No: {receipt_no}")
        c.drawRightString(width - 15 * mm, y, f"Date: {fee_record['payment_date']}")

        y -= 10 * mm
        c.setFont("Helvetica", 10)
        details = [
            ("Student Name", f"{student['first_name']} {student['last_name']}"),
            ("Student ID", str(student["student_id"])),
            ("Course", student["course_name"] or "-"),
            ("Roll Number", student["roll_number"] or "-"),
            ("Payment Mode", fee_record["payment_mode"] or "-"),
        ]
        for label, value in details:
            c.drawString(15 * mm, y, f"{label}:")
            c.drawString(60 * mm, y, str(value))
            y -= 7 * mm

        y -= 4 * mm
        c.line(15 * mm, y, width - 15 * mm, y)
        y -= 8 * mm
        c.setFont("Helvetica-Bold", 10)
        c.drawString(15 * mm, y, "Total Fee")
        c.drawRightString(width - 15 * mm, y, f"Rs. {fee_record['total_fee']:,.2f}")
        y -= 7 * mm
        c.drawString(15 * mm, y, "Amount Paid")
        c.drawRightString(width - 15 * mm, y, f"Rs. {fee_record['paid_amount']:,.2f}")
        y -= 7 * mm
        remaining = fee_record["total_fee"] - fee_record["paid_amount"]
        c.drawString(15 * mm, y, "Remaining Balance")
        c.drawRightString(width - 15 * mm, y, f"Rs. {remaining:,.2f}")

        y -= 20 * mm
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(width / 2, y, "This is a system-generated receipt.")

        c.save()


class FeeForm(ctk.CTkToplevel):
    def __init__(self, master, db, student, on_saved):
        super().__init__(master)
        self.db = db
        self.student = student
        self.on_saved = on_saved

        self.title(f"Add Payment - {student['first_name']} {student['last_name']}")
        self.geometry("380x420")
        self.grab_set()
        self.resizable(False, False)

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Record Fee Payment", font=theme.SUBHEADING_FONT).pack(anchor="w", pady=(0, 12))

        ctk.CTkLabel(frame, text="Total Fee*", font=theme.SMALL_FONT, anchor="w").pack(fill="x")
        self.total_entry = ctk.CTkEntry(frame, height=36)
        self.total_entry.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(frame, text="Paid Amount*", font=theme.SMALL_FONT, anchor="w").pack(fill="x")
        self.paid_entry = ctk.CTkEntry(frame, height=36)
        self.paid_entry.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(frame, text="Payment Date (YYYY-MM-DD)*", font=theme.SMALL_FONT, anchor="w").pack(fill="x")
        self.date_entry = ctk.CTkEntry(frame, height=36)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(fill="x", pady=(2, 10))

        ctk.CTkLabel(frame, text="Payment Mode*", font=theme.SMALL_FONT, anchor="w").pack(fill="x")
        self.mode_var = ctk.StringVar(value="Cash")
        ctk.CTkOptionMenu(frame, values=["Cash", "Card", "UPI", "Bank Transfer", "Cheque"],
                          variable=self.mode_var).pack(fill="x", pady=(2, 10))

        self.error_label = ctk.CTkLabel(frame, text="", text_color=theme.DANGER, font=theme.SMALL_FONT)
        self.error_label.pack(anchor="w")

        ctk.CTkButton(frame, text="Save Payment", height=40, corner_radius=theme.BUTTON_RADIUS,
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                      command=self._save).pack(fill="x", pady=(16, 0))

    def _save(self):
        total = self.total_entry.get().strip()
        paid = self.paid_entry.get().strip()
        date_str = self.date_entry.get().strip()
        mode = self.mode_var.get()

        if not theme.not_empty(total, paid, date_str):
            self.error_label.configure(text="Please fill all required fields.")
            return
        try:
            total_val = float(total)
            paid_val = float(paid)
        except ValueError:
            self.error_label.configure(text="Total Fee and Paid Amount must be numbers.")
            return
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self.error_label.configure(text="Date must be in YYYY-MM-DD format.")
            return

        self.db.add_fee_record(self.student["student_id"], total_val, paid_val, date_str, mode)
        self.on_saved()
        self.destroy()


class FeesFrame(ctk.CTkFrame):
    def __init__(self, master, db, current_user="admin", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db
        self.current_user = current_user
        self.selected_student = None
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(header, text="Fee Management", font=theme.HEADING_FONT,
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

        ctk.CTkButton(toolbar, text="➕ Add Payment", width=140, height=32,
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                      command=self._add_payment).pack(side="left", padx=10, pady=10)

        self.content = ctk.CTkScrollableFrame(self, fg_color="white", corner_radius=8)
        self.content.grid(row=2, column=0, sticky="nsew")

        self._render_placeholder()

    # ------------------------------------------------------------------ #
    def _refresh_student_map(self):
        students = self.db.get_all_students()
        self.student_map = {
            f"{s['student_id']} - {s['first_name']} {s['last_name']}": s for s in students
        }

    def _render_placeholder(self):
        for w in self.content.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.content, text="Select a student above to view fee details.",
                     text_color=theme.TEXT_MUTED, font=theme.BODY_FONT).pack(pady=30)

    def _on_student_selected(self, choice):
        student = self.student_map.get(choice)
        if not student:
            return
        self.selected_student = student
        self._render_student_fees()

    def _add_payment(self):
        if not self.selected_student:
            messagebox.showwarning("No Student Selected", "Please select a student first.")
            return
        FeeForm(self, self.db, self.selected_student, on_saved=self._render_student_fees)

    def _render_student_fees(self):
        for w in self.content.winfo_children():
            w.destroy()

        student = self.selected_student
        summary = self.db.get_fee_summary(student["student_id"])
        total, paid = summary["total"], summary["paid"]
        remaining = total - paid

        summary_row = ctk.CTkFrame(self.content, fg_color="transparent")
        summary_row.pack(fill="x", padx=16, pady=16)
        for label, value, color in [
            ("Total Fee", f"₹{total:,.0f}", theme.PRIMARY),
            ("Paid Amount", f"₹{paid:,.0f}", theme.ACCENT),
            ("Remaining", f"₹{remaining:,.0f}", theme.DANGER if remaining > 0 else theme.ACCENT),
        ]:
            box = ctk.CTkFrame(summary_row, fg_color="#F7F9FC", corner_radius=10)
            box.pack(side="left", expand=True, fill="x", padx=6)
            ctk.CTkLabel(box, text=value, font=theme.CARD_VALUE_FONT, text_color=color).pack(pady=(12, 0))
            ctk.CTkLabel(box, text=label, font=theme.SMALL_FONT, text_color=theme.TEXT_MUTED).pack(pady=(0, 12))

        ctk.CTkLabel(self.content, text="Payment History", font=theme.SUBHEADING_FONT).pack(
            anchor="w", padx=16, pady=(6, 6))

        history = self.db.get_fee_history(student["student_id"])
        if not history:
            ctk.CTkLabel(self.content, text="No payments recorded yet.", text_color=theme.TEXT_MUTED,
                         font=theme.SMALL_FONT).pack(anchor="w", padx=16, pady=10)
            return

        header_row = ctk.CTkFrame(self.content, fg_color=theme.PRIMARY)
        header_row.pack(fill="x", padx=16)
        for text, w in [("Date", 100), ("Total", 100), ("Paid", 100), ("Mode", 120), ("Receipt", 100)]:
            ctk.CTkLabel(header_row, text=text, font=theme.SMALL_FONT, text_color="white",
                         width=w, anchor="w").pack(side="left", padx=6, pady=8)

        for idx, f in enumerate(history):
            row = ctk.CTkFrame(self.content, fg_color="#F7F9FC" if idx % 2 else "white")
            row.pack(fill="x", padx=16, pady=1)
            for text, w in [(f["payment_date"], 100), (f"₹{f['total_fee']:,.0f}", 100),
                            (f"₹{f['paid_amount']:,.0f}", 100), (f["payment_mode"] or "-", 120)]:
                ctk.CTkLabel(row, text=text, font=theme.SMALL_FONT, width=w, anchor="w").pack(
                    side="left", padx=6, pady=6)
            ctk.CTkButton(row, text="🧾 Receipt", width=90, height=26, font=theme.SMALL_FONT,
                          fg_color=theme.SECONDARY, hover_color=theme.PRIMARY_HOVER,
                          command=lambda f=f: self._generate_receipt(f)).pack(side="left", padx=6, pady=4)

    def _generate_receipt(self, fee_record):
        default_name = f"receipt_{self.selected_student['student_id']}_{fee_record['fee_id']}.pdf"
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf", initialfile=default_name,
            filetypes=[("PDF files", "*.pdf")], title="Save Receipt As")
        if not path:
            return
        try:
            ReceiptGenerator.generate(path, self.selected_student, fee_record,
                                       receipt_no=f"RCPT-{fee_record['fee_id']:05d}")
            self.db.log_activity(self.current_user, f"Generated receipt for student {self.selected_student['student_id']}")
            messagebox.showinfo("Receipt Generated", f"Receipt saved to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Error", f"Could not generate receipt:\n{exc}")

    def refresh(self):
        self._refresh_student_map()
        self.student_dropdown.configure(values=list(self.student_map.keys()) or ["No students"])
