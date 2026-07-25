"""
main.py
-------
Application entry point. Shows the login window first; on successful
login, launches the MainApp window which hosts the sidebar navigation
and swaps between the feature modules (Dashboard, Students, Attendance,
Fees, Courses, Results, Reports, Settings).
"""

import customtkinter as ctk

from database import Database
from login import LoginWindow
from dashboard import DashboardFrame
from student import StudentFrame
from attendance import AttendanceFrame
from fees import FeesFrame
from courses import CourseFrame
from results import ResultsFrame
from reports import ReportsFrame
from settings import SettingsFrame
import theme


NAV_ITEMS = [
    ("Dashboard", "🏠"),
    ("Students", "👥"),
    ("Attendance", "📅"),
    ("Fees", "💰"),
    ("Courses", "📚"),
    ("Results", "📝"),
    ("Reports", "📊"),
    ("Settings", "⚙️"),
]


class MainApp(ctk.CTk):
    def __init__(self, db, username):
        super().__init__()
        self.db = db
        self.username = username

        self.title("Student Management System")
        self.geometry("1280x800")
        self.minsize(1100, 700)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.nav_buttons = {}
        self.current_frame = None
        self.current_name = None

        self._build_sidebar()
        self._build_topbar()
        self._build_content_area()

        self.navigate("Dashboard")

    # ------------------------------------------------------------------ #
    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=theme.SIDEBAR_BG_LIGHT, corner_radius=0, width=230)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsw")
        sidebar.grid_propagate(False)

        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(24, 20), padx=20)
        ctk.CTkLabel(logo_frame, text="🎓 SMS", font=(theme.FONT_FAMILY, 20, "bold"),
                     text_color="white").pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="Student Management", font=theme.SMALL_FONT,
                     text_color="#9FB3D6").pack(anchor="w")

        for name, icon in NAV_ITEMS:
            btn = ctk.CTkButton(
                sidebar, text=f"  {icon}   {name}", anchor="w", height=44,
                corner_radius=8, font=theme.BODY_FONT,
                fg_color="transparent", hover_color="#1A3A6B",
                command=lambda n=name: self.navigate(n),
            )
            btn.pack(fill="x", padx=14, pady=3)
            self.nav_buttons[name] = btn

        ctk.CTkFrame(sidebar, fg_color="transparent").pack(expand=True, fill="both")

        ctk.CTkButton(
            sidebar, text="  🚪   Logout", anchor="w", height=44, corner_radius=8,
            font=theme.BODY_FONT, fg_color=theme.DANGER, hover_color=theme.DANGER_HOVER,
            command=self._logout,
        ).pack(fill="x", padx=14, pady=(0, 20))

    def _highlight_nav(self, active_name):
        for name, btn in self.nav_buttons.items():
            if name == active_name:
                btn.configure(fg_color=theme.PRIMARY)
            else:
                btn.configure(fg_color="transparent")

    # ------------------------------------------------------------------ #
    def _build_topbar(self):
        topbar = ctk.CTkFrame(self, fg_color="white", height=60, corner_radius=0,
                               border_width=0)
        topbar.grid(row=0, column=1, sticky="ew")
        topbar.grid_propagate(False)

        self.page_title_label = ctk.CTkLabel(topbar, text="Dashboard", font=theme.SUBHEADING_FONT,
                                              text_color="#1A1D29")
        self.page_title_label.pack(side="left", padx=24)

        user_frame = ctk.CTkFrame(topbar, fg_color="transparent")
        user_frame.pack(side="right", padx=24)
        ctk.CTkLabel(user_frame, text=f"👤 {self.username}", font=theme.BODY_FONT,
                     text_color="#1A1D29").pack(side="left")

    def _build_content_area(self):
        self.content_container = ctk.CTkFrame(self, fg_color=theme.BG_LIGHT, corner_radius=0)
        self.content_container.grid(row=1, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------ #
    def navigate(self, name):
        if self.current_frame is not None:
            self.current_frame.destroy()

        self._highlight_nav(name)
        self.page_title_label.configure(text=name)
        self.current_name = name

        wrapper = ctk.CTkFrame(self.content_container, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        wrapper.grid_rowconfigure(0, weight=1)
        wrapper.grid_columnconfigure(0, weight=1)

        if name == "Dashboard":
            frame = DashboardFrame(wrapper, self.db, navigate_callback=self.navigate)
        elif name == "Students":
            frame = StudentFrame(wrapper, self.db, current_user=self.username)
        elif name == "Attendance":
            frame = AttendanceFrame(wrapper, self.db, current_user=self.username)
        elif name == "Fees":
            frame = FeesFrame(wrapper, self.db, current_user=self.username)
        elif name == "Courses":
            frame = CourseFrame(wrapper, self.db, current_user=self.username)
        elif name == "Results":
            frame = ResultsFrame(wrapper, self.db, current_user=self.username)
        elif name == "Reports":
            frame = ReportsFrame(wrapper, self.db, current_user=self.username)
        elif name == "Settings":
            frame = SettingsFrame(wrapper, self.db, current_user=self.username, on_logout=self._logout)
        else:
            frame = ctk.CTkLabel(wrapper, text="Not found")

        frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame = wrapper

    # ------------------------------------------------------------------ #
    def _logout(self):
        self.db.log_activity(self.username, "Logged out")
        self.destroy()
        launch_login(self.db)


def launch_login(db):
    def on_success(username):
        app = MainApp(db, username)
        app.mainloop()

    login_win = LoginWindow(db, on_success)
    login_win.mainloop()


def main():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    db = Database()
    try:
        launch_login(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
