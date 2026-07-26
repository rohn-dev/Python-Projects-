"""
dashboard.py
------------
Home dashboard: summary cards, a student-distribution pie chart (Matplotlib),
a recent-admissions table and quick action buttons.
"""

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import theme


class SummaryCard(ctk.CTkFrame):
    def __init__(self, master, title, value, icon, color, **kwargs):
        super().__init__(master, fg_color="white", corner_radius=theme.CORNER_RADIUS,
                          border_width=1, border_color="#E7EBF3", **kwargs)
        self.grid_columnconfigure(1, weight=1)

        icon_box = ctk.CTkFrame(self, fg_color=color, corner_radius=10, width=46, height=46)
        icon_box.grid(row=0, column=0, rowspan=2, padx=(16, 10), pady=16)
        icon_box.grid_propagate(False)
        ctk.CTkLabel(icon_box, text=icon, font=(theme.FONT_FAMILY, 20)).place(relx=0.5, rely=0.5, anchor="center")

        self.value_label = ctk.CTkLabel(self, text=str(value), font=theme.CARD_VALUE_FONT,
                                         text_color="#1A1D29", anchor="w")
        self.value_label.grid(row=0, column=1, sticky="w", pady=(16, 0))
        ctk.CTkLabel(self, text=title, font=theme.SMALL_FONT, text_color=theme.TEXT_MUTED,
                     anchor="w").grid(row=1, column=1, sticky="w", pady=(0, 16))

    def set_value(self, value):
        self.value_label.configure(text=str(value))


class DashboardFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, db, navigate_callback, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db
        self.navigate = navigate_callback

        self.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(self, text="Dashboard", font=theme.HEADING_FONT,
                     text_color="#1A1D29", anchor="w").grid(
            row=0, column=0, columnspan=3, sticky="w", padx=4, pady=(4, 16))

        self._build_cards()
        self._build_quick_actions()
        self._build_chart_and_recent()

    # ------------------------------------------------------------------ #
    def _build_cards(self):
        card_frame = ctk.CTkFrame(self, fg_color="transparent")
        card_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 20))
        for i in range(3):
            card_frame.grid_columnconfigure(i, weight=1)

        total = self.db.count_students()
        boys = self.db.count_by_gender("Male")
        girls = self.db.count_by_gender("Female")
        courses = len(self.db.get_courses())
        attendance = self.db.overall_attendance_percentage()
        fee = self.db.total_fee_collected()

        specs = [
            ("Total Students", total, "👥", theme.PRIMARY),
            ("Boys", boys, "🧑", "#3B7DD8"),
            ("Girls", girls, "👩", "#D8579E"),
            ("Courses", courses, "📚", theme.ACCENT),
            ("Attendance %", f"{attendance}%", "📅", theme.WARNING),
            ("Fee Collected", f"₹{fee:,.0f}", "💰", "#16A085"),
        ]
        self.cards = []
        for idx, (title, value, icon, color) in enumerate(specs):
            r, c = divmod(idx, 3)
            card = SummaryCard(card_frame, title, value, icon, color)
            card.grid(row=r, column=c, sticky="nsew", padx=8, pady=8)
            self.cards.append(card)

    def refresh_cards(self):
        total = self.db.count_students()
        boys = self.db.count_by_gender("Male")
        girls = self.db.count_by_gender("Female")
        courses = len(self.db.get_courses())
        attendance = self.db.overall_attendance_percentage()
        fee = self.db.total_fee_collected()
        values = [total, boys, girls, courses, f"{attendance}%", f"₹{fee:,.0f}"]
        for card, v in zip(self.cards, values):
            card.set_value(v)

    # ------------------------------------------------------------------ #
    def _build_quick_actions(self):
        frame = ctk.CTkFrame(self, fg_color="white", corner_radius=theme.CORNER_RADIUS,
                              border_width=1, border_color="#E7EBF3")
        frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 20))

        ctk.CTkLabel(frame, text="Quick Actions", font=theme.SUBHEADING_FONT,
                     text_color="#1A1D29").pack(anchor="w", padx=16, pady=(14, 6))

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        actions = [
            ("➕ Add Student", "Students"),
            ("✅ Mark Attendance", "Attendance"),
            ("💳 Collect Fee", "Fees"),
            ("📊 Reports", "Reports"),
        ]
        for text, target in actions:
            ctk.CTkButton(
                btn_row, text=text, height=38, corner_radius=theme.BUTTON_RADIUS,
                fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                command=lambda t=target: self.navigate(t),
            ).pack(side="left", padx=(0, 10))

    # ------------------------------------------------------------------ #
    def _build_chart_and_recent(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=3, column=0, columnspan=3, sticky="nsew")
        row.grid_columnconfigure(0, weight=1)
        row.grid_columnconfigure(1, weight=1)

        # --- Chart ---
        chart_card = ctk.CTkFrame(row, fg_color="white", corner_radius=theme.CORNER_RADIUS,
                                   border_width=1, border_color="#E7EBF3")
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(chart_card, text="Student Distribution by Course",
                     font=theme.SUBHEADING_FONT, text_color="#1A1D29").pack(
            anchor="w", padx=16, pady=(14, 6))

        data = self.db.students_per_course()
        labels = [row["course_name"] for row in data if row["cnt"] > 0]
        values = [row["cnt"] for row in data if row["cnt"] > 0]

        fig = Figure(figsize=(4.4, 3.2), dpi=100)
        ax = fig.add_subplot(111)
        if values:
            colors = ["#1E4FA3", "#3B7DD8", "#4CAF50", "#F5A623", "#D8579E", "#16A085"]
            ax.pie(values, labels=labels, autopct="%1.0f%%", colors=colors * 3,
                   textprops={"fontsize": 8})
        else:
            ax.text(0.5, 0.5, "No student data yet", ha="center", va="center", fontsize=10)
            ax.axis("off")
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_card)
        canvas.draw()
        canvas.get_tk_widget().pack(padx=10, pady=(0, 14), fill="both", expand=True)

        # --- Recent admissions ---
        recent_card = ctk.CTkFrame(row, fg_color="white", corner_radius=theme.CORNER_RADIUS,
                                    border_width=1, border_color="#E7EBF3")
        recent_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(recent_card, text="Recent Admissions", font=theme.SUBHEADING_FONT,
                     text_color="#1A1D29").pack(anchor="w", padx=16, pady=(14, 6))

        recents = self.db.recent_admissions(6)
        if not recents:
            ctk.CTkLabel(recent_card, text="No admissions yet.", text_color=theme.TEXT_MUTED,
                         font=theme.SMALL_FONT).pack(padx=16, pady=10)
        for r in recents:
            item = ctk.CTkFrame(recent_card, fg_color="#F7F9FC", corner_radius=8)
            item.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(item, text=f"{r['first_name']} {r['last_name']}",
                         font=theme.BODY_FONT, anchor="w").pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(item, text=r["course_name"] or "—", font=theme.SMALL_FONT,
                         text_color=theme.TEXT_MUTED).pack(side="right", padx=10)
        ctk.CTkLabel(recent_card, text="").pack(pady=4)  # bottom spacing
