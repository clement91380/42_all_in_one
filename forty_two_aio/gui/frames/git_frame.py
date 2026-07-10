"""Git frame — git add/commit/push with GitHub account integration."""

from __future__ import annotations

import threading
from tkinter import filedialog

import customtkinter as ctk

from ...modules.git_tools.git_manager import (
    get_github_user,
    get_status,
    git_add_commit_push,
    git_add,
    git_commit,
    git_push,
    git_init,
    is_gh_authenticated,
    gh_auth_login,
    create_github_repo,
    clone_repo,
)


class GitFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.project_path = ""
        self.github_user = ""

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._build_header()
        self._build_github_bar()
        self._build_project_bar()
        self._build_status_panel()
        self._build_actions()
        self._build_log()

        self._refresh_auth()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 5))
        ctk.CTkLabel(hdr, text="Git Automation",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")

    def _build_github_bar(self):
        bar = ctk.CTkFrame(self, corner_radius=8)
        bar.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bar, text="GitHub:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=10, pady=8, sticky="w")

        self.gh_status_label = ctk.CTkLabel(bar, text="Checking...", text_color="gray")
        self.gh_status_label.grid(row=0, column=1, padx=5, pady=8, sticky="w")

        self.gh_login_btn = ctk.CTkButton(
            bar, text="Connect", width=100, height=28,
            command=self._gh_login
        )
        self.gh_login_btn.grid(row=0, column=2, padx=10, pady=8)

    def _build_project_bar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(bar, text="Project:").grid(row=0, column=0, padx=(0, 8))

        self.path_label = ctk.CTkLabel(bar, text="No folder selected", text_color="gray")
        self.path_label.grid(row=0, column=1, sticky="w")

        ctk.CTkButton(bar, text="Open Folder", width=110, height=28,
                      command=self._select_folder).grid(row=0, column=2, padx=5)

        ctk.CTkButton(bar, text="Clone Repo", width=110, height=28,
                      fg_color="gray30", command=self._clone_dialog).grid(row=0, column=3, padx=5)

    def _build_status_panel(self):
        panel = ctk.CTkFrame(self)
        panel.grid(row=3, column=0, sticky="nsew", padx=20, pady=5)
        panel.grid_columnconfigure((0, 1), weight=1)
        panel.grid_rowconfigure(1, weight=1)

        # Left: status info
        left = ctk.CTkFrame(panel, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.branch_label = ctk.CTkLabel(left, text="Branch: —", text_color="gray")
        self.branch_label.pack(anchor="w")
        self.remote_label = ctk.CTkLabel(left, text="Remote: —", text_color="gray", wraplength=280)
        self.remote_label.pack(anchor="w")
        self.sync_label = ctk.CTkLabel(left, text="", text_color="orange")
        self.sync_label.pack(anchor="w")

        # Right: commit message
        right = ctk.CTkFrame(panel, fg_color="transparent")
        right.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Commit message:").pack(anchor="w")
        self.commit_entry = ctk.CTkEntry(right, placeholder_text="describe your changes...")
        self.commit_entry.pack(fill="x", pady=(4, 8))

        ctk.CTkLabel(right, text="Files to add (empty = all):").pack(anchor="w")
        self.files_entry = ctk.CTkEntry(right, placeholder_text="file1.c file2.c  (or leave empty)")
        self.files_entry.pack(fill="x")

    def _build_actions(self):
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=4, column=0, sticky="ew", padx=20, pady=8)

        self.push_all_btn = ctk.CTkButton(
            actions, text="Add + Commit + Push", width=180, height=36,
            font=ctk.CTkFont(weight="bold"),
            command=self._push_all
        )
        self.push_all_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(actions, text="Add only", width=100, height=36,
                      fg_color="gray30", command=self._add_only).pack(side="left", padx=4)

        ctk.CTkButton(actions, text="Commit only", width=110, height=36,
                      fg_color="gray30", command=self._commit_only).pack(side="left", padx=4)

        ctk.CTkButton(actions, text="Push only", width=100, height=36,
                      fg_color="gray30", command=self._push_only).pack(side="left", padx=4)

        ctk.CTkButton(actions, text="Refresh", width=90, height=36,
                      fg_color="transparent", border_width=1,
                      command=self._refresh_status).pack(side="right")

        ctk.CTkButton(actions, text="New GitHub Repo", width=140, height=36,
                      fg_color="gray25", command=self._new_repo_dialog).pack(side="right", padx=8)

    def _build_log(self):
        self.log = ctk.CTkTextbox(self, height=150, font=ctk.CTkFont(family="monospace", size=12))
        self.log.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 16))

    # ------------------------------------------------------------------

    def _refresh_auth(self):
        def _check():
            ok = is_gh_authenticated()
            user = get_github_user() if ok else ""
            self.github_user = user
            if ok and user:
                self.gh_status_label.configure(text=f"Connected as: {user}", text_color="green")
                self.gh_login_btn.configure(text="Reconnect", fg_color="gray30")
            else:
                self.gh_status_label.configure(text="Not connected", text_color="red")
                self.gh_login_btn.configure(text="Connect", fg_color=("#3B8ED0", "#1F6AA5"))
        threading.Thread(target=_check, daemon=True).start()

    def _gh_login(self):
        self._log("Opening GitHub login in browser...\n")
        def _do():
            r = gh_auth_login()
            if r.success:
                self._log("GitHub connected.\n")
            else:
                self._log(f"Auth failed: {r.stderr}\n")
            self._refresh_auth()
        threading.Thread(target=_do, daemon=True).start()

    def _select_folder(self):
        path = filedialog.askdirectory(title="Select project folder")
        if path:
            self.project_path = path
            self.path_label.configure(text=path, text_color="white")
            self._refresh_status()

    def _refresh_status(self):
        if not self.project_path:
            return
        def _do():
            s = get_status(self.project_path)
            branch = s.branch or "—"
            remote = s.remote or "no remote"
            self.branch_label.after(0, lambda: self.branch_label.configure(
                text=f"Branch: {branch}"))
            self.remote_label.after(0, lambda: self.remote_label.configure(
                text=f"Remote: {remote}"))
            sync_txt = ""
            if s.ahead > 0:
                sync_txt += f"  {s.ahead} commit(s) to push"
            if s.behind > 0:
                sync_txt += f"  {s.behind} commit(s) to pull"
            self.sync_label.after(0, lambda: self.sync_label.configure(text=sync_txt))
            if s.staged or s.unstaged or s.untracked:
                total = len(set(s.staged + s.unstaged + s.untracked))
                self._log(f"Status: {total} file(s) changed"
                          f" (staged:{len(s.staged)} unstaged:{len(s.unstaged)}"
                          f" untracked:{len(s.untracked)})\n")
        threading.Thread(target=_do, daemon=True).start()

    def _get_files(self) -> list[str] | None:
        raw = self.files_entry.get().strip()
        if not raw:
            return None
        return raw.split()

    def _push_all(self):
        if not self.project_path:
            self._log("Select a project folder first.\n")
            return
        msg = self.commit_entry.get().strip()
        if not msg:
            self._log("Enter a commit message.\n")
            return
        files = self._get_files()
        self.push_all_btn.configure(state="disabled")
        threading.Thread(target=self._run_push_all, args=(msg, files), daemon=True).start()

    def _run_push_all(self, msg: str, files: list[str] | None):
        login = self.github_user or self.app.config.github_username
        results = git_add_commit_push(self.project_path, msg, login, files)
        labels = ["git add", "git commit", "git push"]
        for i, r in enumerate(results):
            label = labels[i] if i < len(labels) else r.command
            if r.success:
                out = r.stdout.splitlines()[0] if r.stdout else "OK"
                self._log(f"[OK]   {label}: {out}\n")
            else:
                self._log(f"[FAIL] {label}: {r.stderr or r.stdout}\n")
        self.push_all_btn.after(0, lambda: self.push_all_btn.configure(state="normal"))
        self._refresh_status()

    def _add_only(self):
        if not self.project_path:
            return
        threading.Thread(target=lambda: self._log(
            "[OK]   git add\n" if git_add(self.project_path, self._get_files()).success
            else f"[FAIL] git add\n"
        ), daemon=True).start()

    def _commit_only(self):
        if not self.project_path:
            return
        msg = self.commit_entry.get().strip()
        if not msg:
            self._log("Enter a commit message.\n")
            return
        login = self.github_user or self.app.config.github_username
        threading.Thread(target=lambda: self._log(
            f"[OK]   git commit: {login}: {msg}\n"
            if git_commit(self.project_path, msg, login).success
            else "[FAIL] git commit\n"
        ), daemon=True).start()

    def _push_only(self):
        if not self.project_path:
            return
        def _do():
            r = git_push(self.project_path)
            if r.success:
                self._log(f"[OK]   git push\n")
            else:
                self._log(f"[FAIL] git push: {r.stderr}\n")
            self._refresh_status()
        threading.Thread(target=_do, daemon=True).start()

    def _new_repo_dialog(self):
        if not self.project_path:
            self._log("Select a project folder first.\n")
            return
        win = ctk.CTkToplevel(self)
        win.title("Create GitHub Repo")
        win.geometry("400x250")
        win.grab_set()

        ctk.CTkLabel(win, text="Repository name:").pack(pady=(20, 4), padx=20, anchor="w")
        name_entry = ctk.CTkEntry(win, placeholder_text="my-42-project")
        name_entry.pack(fill="x", padx=20)

        ctk.CTkLabel(win, text="Description (optional):").pack(pady=(12, 4), padx=20, anchor="w")
        desc_entry = ctk.CTkEntry(win, placeholder_text="42 project")
        desc_entry.pack(fill="x", padx=20)

        private_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(win, text="Private repo", variable=private_var).pack(pady=12, padx=20, anchor="w")

        def _create():
            name = name_entry.get().strip()
            if not name:
                return
            desc = desc_entry.get().strip()
            win.destroy()
            self._log(f"Creating GitHub repo: {name}...\n")
            def _do():
                r = create_github_repo(name, private_var.get(), desc)
                if r.success:
                    self._log(f"[OK]   Repo created and pushed\n")
                else:
                    self._log(f"[FAIL] {r.stderr}\n")
                self._refresh_status()
            threading.Thread(target=_do, daemon=True).start()

        ctk.CTkButton(win, text="Create", command=_create).pack(pady=10)

    def _clone_dialog(self):
        win = ctk.CTkToplevel(self)
        win.title("Clone Repository")
        win.geometry("450x160")
        win.grab_set()

        ctk.CTkLabel(win, text="Repository URL:").pack(pady=(20, 4), padx=20, anchor="w")
        url_entry = ctk.CTkEntry(win, placeholder_text="https://github.com/user/repo.git")
        url_entry.pack(fill="x", padx=20)

        def _clone():
            url = url_entry.get().strip()
            if not url:
                return
            win.destroy()
            dest = filedialog.askdirectory(title="Clone into which folder?")
            if not dest:
                return
            self._log(f"Cloning {url}...\n")
            def _do():
                r = clone_repo(url, dest)
                if r.success:
                    self.project_path = dest
                    self.path_label.after(0, lambda: self.path_label.configure(
                        text=dest, text_color="white"))
                    self._log(f"[OK]   Cloned to {dest}\n")
                    self._refresh_status()
                else:
                    self._log(f"[FAIL] {r.stderr}\n")
            threading.Thread(target=_do, daemon=True).start()

        ctk.CTkButton(win, text="Clone", command=_clone).pack(pady=16)

    def _log(self, text: str):
        self.log.after(0, lambda: self.log.insert("end", text))
