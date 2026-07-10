"""Main GUI application — 42 All-in-One.

All frames are constructed before mainloop() to avoid
the layer-by-layer rendering artefact on startup.
"""

from __future__ import annotations

import threading

import customtkinter as ctk

from .frames.dashboard import DashboardFrame
from .frames.norm_frame import NormFrame
from .frames.compiler_frame import CompilerFrame
from .frames.repo_frame import RepoFrame
from .frames.exams_frame import ExamsFrame
from .frames.predictor_frame import PredictorFrame
from .frames.git_frame import GitFrame
from .frames.exam_mode_frame import ExamModeFrame
from .frames.editor_frame import EditorFrame
from ..core.config import Config
from ..core.i18n import t, set_lang
from ..modules.updater.updater import check_for_update, do_update, get_current_version


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config = Config.load()
        self.exam_mode = False

        set_lang(self.config.language)

        self.title("42 All-in-One")
        self.geometry("1200x800")
        self.minsize(960, 640)

        # Build entire layout synchronously before showing anything
        self.withdraw()
        self._build_layout()
        self._show_frame("dashboard")
        self.deiconify()

        # Check for updates in background — no blocking
        threading.Thread(target=self._check_update_bg, daemon=True).start()

    # ---------------------------------------------------------------
    # Layout
    # ---------------------------------------------------------------

    def _build_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content()

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=190, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Logo
        ctk.CTkLabel(
            self.sidebar,
            text="42 AIO",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).grid(row=0, column=0, pady=(24, 2), padx=16, sticky="w")

        self.version_label = ctk.CTkLabel(
            self.sidebar,
            text=f"v{get_current_version()}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self.version_label.grid(row=1, column=0, pady=(0, 16), padx=18, sticky="w")

        # Navigation buttons
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("dashboard",  t("nav_dashboard")),
            ("editor",     "Editeur / Editor"),
            ("norm",       t("nav_norm")),
            ("compiler",   t("nav_compiler")),
            ("repo",       t("nav_repo")),
            ("git",        t("nav_git")),
            ("exams",      t("nav_exams")),
            ("predictor",  t("nav_predictor")),
            ("exam_mode",  t("nav_exam_mode")),
        ]

        for row_i, (key, label) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                anchor="w",
                height=38,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray75", "gray30"),
                command=lambda k=key: self._show_frame(k),
            )
            btn.grid(row=row_i, column=0, sticky="ew", padx=8, pady=2)
            self.nav_buttons[key] = btn

        # Update banner (hidden by default)
        self.update_banner = ctk.CTkButton(
            self.sidebar,
            text="Update available!",
            height=30,
            corner_radius=6,
            fg_color="#1a5c1a",
            hover_color="#236e23",
            command=self._show_update_dialog,
        )
        self.update_banner.grid(row=11, column=0, sticky="ew", padx=8, pady=4)
        self.update_banner.grid_remove()

        # Settings button
        ctk.CTkButton(
            self.sidebar,
            text=t("nav_settings"),
            anchor="w",
            height=34,
            corner_radius=8,
            fg_color="transparent",
            text_color="gray",
            hover_color=("gray75", "gray30"),
            command=self._open_settings,
        ).grid(row=12, column=0, sticky="ew", padx=8, pady=(0, 16))

    def _build_content(self):
        container = ctk.CTkFrame(self, corner_radius=10)
        container.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames: dict[str, ctk.CTkFrame] = {}
        frame_classes = {
            "dashboard":  DashboardFrame,
            "editor":     EditorFrame,
            "norm":       NormFrame,
            "compiler":   CompilerFrame,
            "repo":       RepoFrame,
            "git":        GitFrame,
            "exams":      ExamsFrame,
            "predictor":  PredictorFrame,
            "exam_mode":  ExamModeFrame,
        }

        for key, cls in frame_classes.items():
            frame = cls(container, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[key] = frame

    # ---------------------------------------------------------------
    # Navigation
    # ---------------------------------------------------------------

    def _show_frame(self, key: str):
        # Disable navigation buttons that are locked in exam mode
        locked = {"git", "repo", "predictor"} if self.exam_mode else set()

        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=("gray75", "gray25"))
            elif k in locked:
                btn.configure(fg_color="transparent", text_color="gray40",
                               state="disabled")
            else:
                btn.configure(fg_color="transparent",
                               text_color=("gray10", "gray90"), state="normal")

        self.frames[key].tkraise()

    # ---------------------------------------------------------------
    # Settings
    # ---------------------------------------------------------------

    def _open_settings(self):
        SettingsWindow(self)

    # ---------------------------------------------------------------
    # Update
    # ---------------------------------------------------------------

    def _check_update_bg(self):
        release = check_for_update()
        if release:
            self._pending_release = release
            self.after(0, self._show_update_banner)

    def _show_update_banner(self):
        release = getattr(self, "_pending_release", None)
        if release:
            self.update_banner.configure(text=f"Update v{release.tag} available!")
            self.update_banner.grid()

    def _show_update_dialog(self):
        release = getattr(self, "_pending_release", None)
        if not release:
            return
        UpdateDialog(self, release)


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent: App):
        super().__init__(parent)
        self.parent_app = parent
        self.title(t("settings_title"))
        self.geometry("480x380")
        self.grab_set()
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=t("settings_title"),
                     font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, pady=(20, 12))

        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, sticky="ew", padx=24)
        form.grid_columnconfigure(1, weight=1)

        fields = [
            ("settings_github", "github_username"),
            ("settings_login42", "intra_login"),
        ]
        self._entries: dict[str, ctk.CTkEntry] = {}

        for i, (label_key, attr) in enumerate(fields):
            ctk.CTkLabel(form, text=t(label_key)).grid(
                row=i, column=0, sticky="w", padx=10, pady=6)
            entry = ctk.CTkEntry(form)
            entry.grid(row=i, column=1, sticky="ew", padx=10, pady=6)
            entry.insert(0, getattr(parent.config, attr, ""))
            self._entries[attr] = entry

        # Language
        ctk.CTkLabel(form, text=t("settings_lang")).grid(
            row=2, column=0, sticky="w", padx=10, pady=6)
        self.lang_var = ctk.StringVar(value=parent.config.language)
        ctk.CTkOptionMenu(form, variable=self.lang_var,
                          values=["fr", "en"]).grid(
            row=2, column=1, sticky="ew", padx=10, pady=6)

        # Theme
        ctk.CTkLabel(form, text=t("settings_theme")).grid(
            row=3, column=0, sticky="w", padx=10, pady=6)
        self.theme_var = ctk.StringVar(value=parent.config.theme)
        ctk.CTkOptionMenu(form, variable=self.theme_var,
                          values=["dark", "light", "system"]).grid(
            row=3, column=1, sticky="ew", padx=10, pady=6)

        ctk.CTkButton(self, text=t("settings_save"),
                      command=self._save).grid(row=2, column=0, pady=20)

    def _save(self):
        for attr, entry in self._entries.items():
            setattr(self.parent_app.config, attr, entry.get())
        self.parent_app.config.language = self.lang_var.get()
        self.parent_app.config.theme = self.theme_var.get()
        self.parent_app.config.save()
        ctk.set_appearance_mode(self.theme_var.get())
        set_lang(self.lang_var.get())
        self.destroy()


class UpdateDialog(ctk.CTkToplevel):
    def __init__(self, parent: App, release):
        super().__init__(parent)
        self.parent_app = parent
        self.release = release
        self.title("Update available")
        self.geometry("500x360")
        self.grab_set()
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text=f"Version {release.tag} available",
                     font=ctk.CTkFont(size=18, weight="bold")).grid(
            row=0, column=0, pady=(20, 8))

        notes_box = ctk.CTkTextbox(self, font=ctk.CTkFont(size=12))
        notes_box.grid(row=2, column=0, sticky="nsew", padx=20, pady=8)
        notes_box.insert("1.0", release.body or "No release notes.")
        notes_box.configure(state="disabled")

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, pady=(8, 20))

        self.update_btn = ctk.CTkButton(
            btn_frame, text="Update now", width=140,
            fg_color="#2d7a2d", command=self._do_update
        )
        self.update_btn.pack(side="left", padx=8)

        ctk.CTkButton(btn_frame, text="Later", width=80,
                      fg_color="gray30", command=self.destroy).pack(side="left")

        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.grid(row=4, column=0, pady=(0, 12))

    def _do_update(self):
        self.update_btn.configure(state="disabled", text="Updating...")
        threading.Thread(target=self._run_update, daemon=True).start()

    def _run_update(self):
        success, msg = do_update()
        def _finish():
            if success:
                self.status_label.configure(
                    text=f"Updated! Restart the app to apply changes.", text_color="green"
                )
                self.parent_app.update_banner.grid_remove()
            else:
                self.status_label.configure(text=f"Failed: {msg}", text_color="red")
                self.update_btn.configure(state="normal", text="Retry")
        self.after(0, _finish)


def run():
    app = App()
    app.mainloop()
