"""
settings.py
-----------
Settings module: dark/light mode toggle, database backup/restore,
change password, and basic user management (add/remove admin users).
"""

from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox, filedialog

import theme


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, db, current_user, on_logout, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db
        self.current_user = current_user
        self.on_logout = on_logout

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text="Settings", font=theme.HEADING_FONT, text_color="#1A1D29").pack(
            anchor="w", pady=(0, 16))

        self._build_appearance_section(scroll)
        self._build_backup_section(scroll)
        self._build_password_section(scroll)
        self._build_users_section(scroll)
        self._build_activity_log_section(scroll)

    # ------------------------------------------------------------------ #
    def _section(self, parent, title):
        card = ctk.CTkFrame(parent, fg_color="white", corner_radius=theme.CORNER_RADIUS,
                             border_width=1, border_color="#E7EBF3")
        card.pack(fill="x", pady=8)
        ctk.CTkLabel(card, text=title, font=theme.SUBHEADING_FONT, text_color="#1A1D29").pack(
            anchor="w", padx=18, pady=(14, 8))
        return card

    # ------------------------------------------------------------------ #
    def _build_appearance_section(self, parent):
        card = self._section(parent, "Appearance")
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 16))
        ctk.CTkLabel(row, text="Theme Mode", font=theme.BODY_FONT).pack(side="left")
        ctk.CTkSegmentedButton(row, values=["Light", "Dark"], command=self._toggle_theme).pack(side="right")

    def _toggle_theme(self, mode):
        ctk.set_appearance_mode(mode.lower())

    # ------------------------------------------------------------------ #
    def _build_backup_section(self, parent):
        card = self._section(parent, "Database Backup & Restore")
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 16))
        ctk.CTkButton(row, text="⬇ Backup Database", width=180, height=36,
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                      command=self._backup).pack(side="left", padx=(0, 10))
        ctk.CTkButton(row, text="⬆ Restore Database", width=180, height=36,
                      fg_color=theme.DANGER, hover_color=theme.DANGER_HOVER,
                      command=self._restore).pack(side="left")

    def _backup(self):
        default_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        path = filedialog.asksaveasfilename(defaultextension=".db", initialfile=default_name,
                                             filetypes=[("SQLite DB", "*.db")])
        if not path:
            return
        try:
            self.db.backup_database(path)
            self.db.log_activity(self.current_user, "Backed up database")
            messagebox.showinfo("Backup Complete", f"Database backed up to:\n{path}")
        except Exception as exc:
            messagebox.showerror("Backup Failed", str(exc))

    def _restore(self):
        path = filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db")])
        if not path:
            return
        if not messagebox.askyesno("Confirm Restore",
                                    "Restoring will overwrite the current database. Continue?"):
            return
        try:
            self.db.restore_database(path)
            self.db.log_activity(self.current_user, "Restored database from backup")
            messagebox.showinfo("Restore Complete", "Database restored successfully. "
                                                     "Please restart the application.")
        except Exception as exc:
            messagebox.showerror("Restore Failed", str(exc))

    # ------------------------------------------------------------------ #
    def _build_password_section(self, parent):
        card = self._section(parent, "Change Password")
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 16))

        self.old_pw = ctk.CTkEntry(row, placeholder_text="Current Password", show="•", width=200)
        self.old_pw.pack(side="left", padx=(0, 8))
        self.new_pw = ctk.CTkEntry(row, placeholder_text="New Password", show="•", width=200)
        self.new_pw.pack(side="left", padx=8)
        ctk.CTkButton(row, text="Update Password", width=160, height=32,
                      fg_color=theme.PRIMARY, hover_color=theme.PRIMARY_HOVER,
                      command=self._change_password).pack(side="left", padx=8)

    def _change_password(self):
        old = self.old_pw.get()
        new = self.new_pw.get()
        if not theme.not_empty(old, new):
            messagebox.showwarning("Missing Fields", "Please fill both password fields.")
            return
        if len(new) < 4:
            messagebox.showwarning("Weak Password", "New password should be at least 4 characters.")
            return
        if self.db.verify_user(self.current_user, old) is None:
            messagebox.showerror("Incorrect Password", "Your current password is incorrect.")
            return
        self.db.change_password(self.current_user, new)
        self.db.log_activity(self.current_user, "Changed password")
        self.old_pw.delete(0, "end")
        self.new_pw.delete(0, "end")
        messagebox.showinfo("Success", "Password updated successfully.")

    # ------------------------------------------------------------------ #
    def _build_users_section(self, parent):
        card = self._section(parent, "User Management")

        add_row = ctk.CTkFrame(card, fg_color="transparent")
        add_row.pack(fill="x", padx=18, pady=(0, 10))
        self.new_username = ctk.CTkEntry(add_row, placeholder_text="Username", width=160)
        self.new_username.pack(side="left", padx=(0, 8))
        self.new_user_pw = ctk.CTkEntry(add_row, placeholder_text="Password", show="•", width=160)
        self.new_user_pw.pack(side="left", padx=8)
        ctk.CTkButton(add_row, text="Add User", width=110, height=32,
                      fg_color=theme.ACCENT, hover_color="#3C9142",
                      command=self._add_user).pack(side="left", padx=8)

        self.users_list_frame = ctk.CTkFrame(card, fg_color="transparent")
        self.users_list_frame.pack(fill="x", padx=18, pady=(0, 16))
        self._refresh_users()

    def _add_user(self):
        username = self.new_username.get().strip()
        password = self.new_user_pw.get()
        if not theme.not_empty(username, password):
            messagebox.showwarning("Missing Fields", "Please provide a username and password.")
            return
        try:
            self.db.create_user(username, password, role="admin", full_name=username)
            self.db.log_activity(self.current_user, f"Created new user '{username}'")
            self.new_username.delete(0, "end")
            self.new_user_pw.delete(0, "end")
            self._refresh_users()
        except Exception as exc:
            messagebox.showerror("Error", f"Could not create user (duplicate name?):\n{exc}")

    def _refresh_users(self):
        for w in self.users_list_frame.winfo_children():
            w.destroy()
        for u in self.db.get_all_users():
            row = ctk.CTkFrame(self.users_list_frame, fg_color="#F7F9FC", corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=f"{u['username']}  ({u['role']})", font=theme.SMALL_FONT).pack(
                side="left", padx=10, pady=8)
            if u["username"] != self.current_user:
                ctk.CTkButton(row, text="Remove", width=70, height=26, font=theme.SMALL_FONT,
                              fg_color=theme.DANGER, hover_color=theme.DANGER_HOVER,
                              command=lambda u=u: self._remove_user(u)).pack(side="right", padx=8)

    def _remove_user(self, user_row):
        if messagebox.askyesno("Confirm", f"Remove user '{user_row['username']}'?"):
            self.db.delete_user(user_row["id"])
            self.db.log_activity(self.current_user, f"Removed user '{user_row['username']}'")
            self._refresh_users()

    # ------------------------------------------------------------------ #
    def _build_activity_log_section(self, parent):
        card = self._section(parent, "Recent Activity Log")
        log_frame = ctk.CTkFrame(card, fg_color="transparent")
        log_frame.pack(fill="x", padx=18, pady=(0, 16))

        logs = self.db.get_activity_log(15)
        if not logs:
            ctk.CTkLabel(log_frame, text="No activity recorded yet.", text_color=theme.TEXT_MUTED,
                         font=theme.SMALL_FONT).pack(anchor="w")
            return
        for log in logs:
            ts = log["timestamp"].split("T")[0] + " " + log["timestamp"].split("T")[1][:8]
            ctk.CTkLabel(log_frame, text=f"[{ts}] {log['username']}: {log['action']}",
                         font=theme.SMALL_FONT, text_color=theme.TEXT_MUTED, anchor="w").pack(
                anchor="w", pady=1)
