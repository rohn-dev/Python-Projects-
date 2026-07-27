"""
login.py
--------
Standalone login window shown before the main application launches.
Handles username/password auth against the Users table, plus a
"Remember Me" option persisted to a small local text file.
"""

import os
import customtkinter as ctk
from tkinter import messagebox

import theme

REMEMBER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", ".remember")


class LoginWindow(ctk.CTk):
    """The login screen. On success, calls `on_success(username)` and closes."""

    def __init__(self, db, on_success):
        super().__init__()
        self.db = db
        self.on_success = on_success

        self.title("Student Management System - Login")
        self.geometry("980x600")
        self.minsize(860, 560)
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()
        self._load_remembered_user()

        self.bind("<Return>", lambda e: self._attempt_login())

    # ------------------------------------------------------------------ #
    def _build_left_panel(self):
        left = ctk.CTkFrame(self, fg_color=theme.PRIMARY, corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        inner = ctk.CTkFrame(left, fg_color="transparent")
        inner.grid(row=0, column=0)

        ctk.CTkLabel(
            inner, text="🎓", font=(theme.FONT_FAMILY, 64), text_color="white"
        ).pack(pady=(0, 10))
        ctk.CTkLabel(
            inner,
            text="Student Management\nSystem",
            font=(theme.FONT_FAMILY, 26, "bold"),
            text_color="white",
            justify="center",
        ).pack(pady=(0, 10))
        ctk.CTkLabel(
            inner,
            text="A modern ERP-style platform to manage\nstudents, attendance, fees & results.",
            font=theme.BODY_FONT,
            text_color="#D6E3FA",
            justify="center",
        ).pack()

    # ------------------------------------------------------------------ #
    def _build_right_panel(self):
        right = ctk.CTkFrame(self, fg_color=theme.BG_LIGHT, corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(right, fg_color="white", corner_radius=theme.CORNER_RADIUS,
                             width=360, border_width=1, border_color="#E1E6EF")
        card.grid(row=0, column=0)
        card.grid_propagate(False)
        card.configure(width=360, height=420)

        ctk.CTkLabel(card, text="Welcome Back", font=theme.HEADING_FONT,
                     text_color=theme.PRIMARY).pack(pady=(36, 4), padx=30)
        ctk.CTkLabel(card, text="Sign in to continue to the dashboard",
                     font=theme.SMALL_FONT, text_color=theme.TEXT_MUTED).pack(pady=(0, 20))

        self.username_entry = ctk.CTkEntry(card, placeholder_text="Username", width=280, height=40)
        self.username_entry.pack(pady=6)

        self.password_entry = ctk.CTkEntry(card, placeholder_text="Password", show="•",
                                            width=280, height=40)
        self.password_entry.pack(pady=6)

        self.remember_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(card, text="Remember Me", variable=self.remember_var,
                         font=theme.SMALL_FONT).pack(pady=(10, 4), anchor="w", padx=40)

        ctk.CTkButton(
            card, text="Login", width=280, height=40, corner_radius=theme.BUTTON_RADIUS,
            fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
            command=self._attempt_login,
        ).pack(pady=(14, 6))

        self.status_label = ctk.CTkLabel(card, text="", text_color=theme.DANGER, font=theme.SMALL_FONT)
        self.status_label.pack(pady=(2, 0))

        ctk.CTkLabel(card, text="Default admin: admin / admin123",
                     font=theme.SMALL_FONT, text_color=theme.TEXT_MUTED).pack(pady=(20, 0))

    # ------------------------------------------------------------------ #
    def _load_remembered_user(self):
        if os.path.exists(REMEMBER_FILE):
            try:
                with open(REMEMBER_FILE, "r") as f:
                    saved_user = f.read().strip()
                if saved_user:
                    self.username_entry.insert(0, saved_user)
                    self.remember_var.set(True)
                    self.password_entry.focus()
            except OSError:
                pass

    def _save_remember(self, username):
        try:
            os.makedirs(os.path.dirname(REMEMBER_FILE), exist_ok=True)
            if self.remember_var.get():
                with open(REMEMBER_FILE, "w") as f:
                    f.write(username)
            elif os.path.exists(REMEMBER_FILE):
                os.remove(REMEMBER_FILE)
        except OSError:
            pass

    # ------------------------------------------------------------------ #
    def _attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            self.status_label.configure(text="Please enter both username and password.")
            return

        try:
            user = self.db.verify_user(username, password)
        except Exception as exc:
            messagebox.showerror("Database Error", f"Could not verify credentials:\n{exc}")
            return

        if user is None:
            self.status_label.configure(text="Invalid username or password.")
            return

        self._save_remember(username)
        self.db.log_activity(username, "Logged in")
        self.destroy()
        self.on_success(username)
