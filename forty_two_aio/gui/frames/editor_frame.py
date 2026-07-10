"""Integrated code editor with C syntax highlighting, norm checks, and mass operations."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from tkinter import filedialog, font as tkfont
import tkinter as tk

import customtkinter as ctk

from ...core.syntax import apply_highlighting, configure_tags
from ...core.file_scanner import scan_directory, ScanResult, ScannedFile
from ...modules.norm import NorminetteFormatter
from ...modules.compiler.checker import check_compilation, check_main_commented_or_missing


class EditorFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.formatter = NorminetteFormatter()

        self.current_file: Path | None = None
        self.scan_result: ScanResult | None = None
        self._modified = False
        self._highlight_job = None
        self._last_content = ""

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_file_tree()
        self._build_editor_area()
        self._build_toolbar()

    # ---------------------------------------------------------------
    # File tree (left panel)
    # ---------------------------------------------------------------

    def _build_file_tree(self):
        tree_frame = ctk.CTkFrame(self, width=240, corner_radius=0)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_propagate(False)
        tree_frame.grid_rowconfigure(2, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Header
        hdr = ctk.CTkFrame(tree_frame, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=6, pady=(8, 4))

        ctk.CTkLabel(hdr, text="Files", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(hdr, text="+", width=24, height=24,
                      command=self._open_folder).pack(side="right")

        # Scan options
        opts = ctk.CTkFrame(tree_frame, fg_color="transparent")
        opts.grid(row=1, column=0, sticky="ew", padx=6, pady=2)
        opts.grid_columnconfigure(0, weight=1)

        self.pattern_entry = ctk.CTkEntry(opts, placeholder_text="pattern: ft_*.c", height=26)
        self.pattern_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkButton(opts, text="Scan", width=48, height=26,
                      command=self._rescan).grid(row=0, column=1)

        depth_row = ctk.CTkFrame(opts, fg_color="transparent")
        depth_row.grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        ctk.CTkLabel(depth_row, text="Depth:", font=ctk.CTkFont(size=11)).pack(side="left")
        self.depth_var = ctk.StringVar(value="∞")
        ctk.CTkOptionMenu(depth_row, variable=self.depth_var,
                          values=["∞", "1", "2", "3", "5"], width=60, height=24).pack(side="left", padx=4)

        # File list
        self.file_listbox = tk.Listbox(
            tree_frame,
            bg="#1e1e1e", fg="#cccccc",
            selectbackground="#264f78", selectforeground="white",
            borderwidth=0, highlightthickness=0,
            font=("monospace", 11),
            activestyle="none",
        )
        self.file_listbox.grid(row=2, column=0, sticky="nsew", padx=2, pady=2)
        scrollbar = ctk.CTkScrollbar(tree_frame, command=self.file_listbox.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        self.file_listbox.bind("<<ListboxSelect>>", self._on_file_select)
        self.file_listbox.bind("<Double-Button-1>", self._on_file_select)

        self._tree_files: list[ScannedFile] = []

        # Mass action buttons
        mass = ctk.CTkFrame(tree_frame, fg_color="transparent")
        mass.grid(row=3, column=0, columnspan=2, sticky="ew", padx=6, pady=6)

        ctk.CTkButton(mass, text="Check All", height=28,
                      command=self._mass_check).pack(fill="x", pady=2)
        ctk.CTkButton(mass, text="Fix All", height=28,
                      fg_color="#1a5c1a",
                      command=self._mass_fix).pack(fill="x", pady=2)
        ctk.CTkButton(mass, text="Compile All", height=28,
                      fg_color="gray30",
                      command=self._mass_compile).pack(fill="x", pady=2)

    # ---------------------------------------------------------------
    # Editor area (right panel)
    # ---------------------------------------------------------------

    def _build_editor_area(self):
        editor_container = ctk.CTkFrame(self)
        editor_container.grid(row=0, column=1, sticky="nsew")
        editor_container.grid_rowconfigure(1, weight=1)
        editor_container.grid_columnconfigure(0, weight=1)

        # Top bar
        top = ctk.CTkFrame(editor_container, height=36, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 0))

        self.file_title = ctk.CTkLabel(
            top, text="No file open", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.file_title.pack(side="left")

        self.modified_label = ctk.CTkLabel(top, text="", text_color="#ff6b6b")
        self.modified_label.pack(side="left", padx=8)

        ctk.CTkButton(top, text="Save", width=70, height=26,
                      command=self._save_file).pack(side="right", padx=4)
        ctk.CTkButton(top, text="Save As", width=80, height=26,
                      fg_color="gray30", command=self._save_as).pack(side="right", padx=4)
        ctk.CTkButton(top, text="Open File", width=80, height=26,
                      fg_color="gray30", command=self._open_file_dialog).pack(side="right", padx=4)

        # Editor with line numbers
        edit_frame = ctk.CTkFrame(editor_container, fg_color="#1e1e1e", corner_radius=6)
        edit_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=6)
        edit_frame.grid_rowconfigure(0, weight=1)
        edit_frame.grid_columnconfigure(1, weight=1)

        self.line_numbers = tk.Text(
            edit_frame,
            width=4, padx=4,
            state="disabled",
            bg="#252526", fg="#858585",
            font=("monospace", 13),
            borderwidth=0, highlightthickness=0,
            selectbackground="#252526",
        )
        self.line_numbers.grid(row=0, column=0, sticky="ns")

        self.editor = tk.Text(
            edit_frame,
            bg="#1e1e1e", fg="#d4d4d4",
            insertbackground="white",
            font=("monospace", 13),
            borderwidth=0, highlightthickness=0,
            undo=True, maxundo=100,
            selectbackground="#264f78",
            padx=8, pady=4,
            wrap="none",
            tabs=("4c",),
        )
        self.editor.grid(row=0, column=1, sticky="nsew")

        scroll_y = ctk.CTkScrollbar(edit_frame, command=self._scroll_both_y)
        scroll_y.grid(row=0, column=2, sticky="ns")
        scroll_x = ctk.CTkScrollbar(edit_frame, orientation="horizontal",
                                     command=self.editor.xview)
        scroll_x.grid(row=1, column=1, sticky="ew")

        self.editor.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.line_numbers.configure(yscrollcommand=scroll_y.set)

        # Configure syntax tags
        configure_tags(self.editor, "dark")

        # Bind events
        self.editor.bind("<KeyRelease>", self._on_key_release)
        self.editor.bind("<Control-s>", lambda e: self._save_file())
        self.editor.bind("<Control-z>", lambda e: self.editor.edit_undo())
        self.editor.bind("<Control-y>", lambda e: self.editor.edit_redo())
        self.editor.bind("<Control-a>", lambda e: self._select_all())
        self.editor.bind("<Control-f>", lambda e: self._open_find())
        self.editor.bind("<Control-g>", lambda e: self._goto_line())
        self.editor.bind("<Tab>", self._handle_tab)

    # ---------------------------------------------------------------
    # Toolbar (bottom)
    # ---------------------------------------------------------------

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self, height=28, fg_color="#252526", corner_radius=0)
        toolbar.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.status_label = ctk.CTkLabel(
            toolbar, text="Ready", font=ctk.CTkFont(size=11), text_color="gray"
        )
        self.status_label.pack(side="left", padx=10)

        self.pos_label = ctk.CTkLabel(
            toolbar, text="Ln 1, Col 1", font=ctk.CTkFont(size=11), text_color="gray"
        )
        self.pos_label.pack(side="right", padx=10)

        self.norm_status = ctk.CTkLabel(
            toolbar, text="", font=ctk.CTkFont(size=11)
        )
        self.norm_status.pack(side="right", padx=10)

        self.editor.bind("<ButtonRelease-1>", self._update_pos)
        self.editor.bind("<KeyRelease>", self._update_pos, add="+")

    # ---------------------------------------------------------------
    # File operations
    # ---------------------------------------------------------------

    def _open_folder(self):
        path = filedialog.askdirectory(title="Open project folder")
        if path:
            self._scan_and_populate(path)

    def _rescan(self):
        if self.scan_result:
            self._scan_and_populate(str(self.scan_result.root))

    def _scan_and_populate(self, path: str):
        pattern_raw = self.pattern_entry.get().strip()
        patterns = [p.strip() for p in pattern_raw.split(",") if p.strip()] or None
        depth_raw = self.depth_var.get()
        depth = None if depth_raw == "∞" else int(depth_raw)

        self._set_status(f"Scanning {path}...")
        threading.Thread(
            target=self._do_scan, args=(path, patterns, depth), daemon=True
        ).start()

    def _do_scan(self, path: str, patterns, depth):
        result = scan_directory(path, depth=depth, patterns=patterns)
        self.scan_result = result

        def _update():
            self.file_listbox.delete(0, "end")
            self._tree_files = result.files
            for f in result.files:
                self.file_listbox.insert("end", f.rel_path)
            self._set_status(
                f"{len(result.c_files)} .c  {len(result.h_files)} .h  "
                f"| {result.total_lines} lines  {result.total_size // 1024} KB"
            )
        self.after(0, _update)

    def _on_file_select(self, event=None):
        sel = self.file_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self._tree_files):
            f = self._tree_files[idx]
            self._load_file(f.path)

    def _open_file_dialog(self):
        path = filedialog.askopenfilename(
            title="Open file",
            filetypes=[("C/H files", "*.c *.h"), ("All", "*.*")],
        )
        if path:
            self._load_file(Path(path))

    def _load_file(self, path: Path):
        if self._modified:
            # Could add a "save changes?" dialog here
            pass
        try:
            content = path.read_text(errors="replace")
        except OSError as e:
            self._set_status(f"Error: {e}")
            return

        self.current_file = path
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", content)
        self._last_content = content
        self._modified = False
        self.modified_label.configure(text="")
        self.file_title.configure(text=path.name)
        self._update_line_numbers()
        self._schedule_highlight()
        self._run_norm_check_bg(content, str(path))
        self._set_status(f"Opened: {path}")

    def _save_file(self, event=None):
        if not self.current_file:
            self._save_as()
            return
        content = self.editor.get("1.0", "end-1c")
        try:
            self.current_file.write_text(content)
            self._modified = False
            self.modified_label.configure(text="")
            self._set_status(f"Saved: {self.current_file.name}")
            self._run_norm_check_bg(content, str(self.current_file))
        except OSError as e:
            self._set_status(f"Save failed: {e}")

    def _save_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".c",
            filetypes=[("C files", "*.c"), ("H files", "*.h"), ("All", "*.*")],
        )
        if path:
            self.current_file = Path(path)
            self._save_file()

    # ---------------------------------------------------------------
    # Editor helpers
    # ---------------------------------------------------------------

    def _handle_tab(self, event):
        self.editor.insert("insert", "\t")
        return "break"

    def _select_all(self):
        self.editor.tag_add("sel", "1.0", "end")
        return "break"

    def _on_key_release(self, event=None):
        content = self.editor.get("1.0", "end-1c")
        if content != self._last_content:
            self._modified = True
            self.modified_label.configure(text="●")
            self._last_content = content
            self._update_line_numbers()
            self._schedule_highlight()

    def _schedule_highlight(self):
        if self._highlight_job:
            self.after_cancel(self._highlight_job)
        self._highlight_job = self.after(400, self._do_highlight)

    def _do_highlight(self):
        content = self.editor.get("1.0", "end-1c")
        if self.current_file and self.current_file.suffix in (".c", ".h"):
            apply_highlighting(self.editor, content, "dark")

    def _update_line_numbers(self):
        content = self.editor.get("1.0", "end-1c")
        lines = content.count("\n") + 1
        nums = "\n".join(str(i) for i in range(1, lines + 1))
        self.line_numbers.configure(state="normal")
        self.line_numbers.delete("1.0", "end")
        self.line_numbers.insert("1.0", nums)
        self.line_numbers.configure(state="disabled")

    def _scroll_both_y(self, *args):
        self.editor.yview(*args)
        self.line_numbers.yview(*args)

    def _update_pos(self, event=None):
        pos = self.editor.index("insert")
        line, col = pos.split(".")
        self.pos_label.configure(text=f"Ln {line}, Col {int(col)+1}")

    def _open_find(self):
        FindDialog(self)

    def _goto_line(self):
        GotoDialog(self)

    # ---------------------------------------------------------------
    # Norm check on current file
    # ---------------------------------------------------------------

    def _run_norm_check_bg(self, content: str, file_path: str):
        threading.Thread(
            target=self._do_norm_check, args=(content, file_path), daemon=True
        ).start()

    def _do_norm_check(self, content: str, file_path: str):
        try:
            diags = self.formatter.diagnose_source(content, file_path)
            count = len(diags)
            if count == 0:
                self.norm_status.after(0, lambda: self.norm_status.configure(
                    text="Norm OK", text_color="green"))
            else:
                self.norm_status.after(0, lambda: self.norm_status.configure(
                    text=f"{count} norm error(s)", text_color="orange"))
        except RuntimeError:
            pass

    # ---------------------------------------------------------------
    # Mass operations
    # ---------------------------------------------------------------

    def _mass_check(self):
        if not self.scan_result or not self.scan_result.files:
            self._set_status("No files loaded — open a folder first.")
            return
        threading.Thread(target=self._do_mass_check, daemon=True).start()

    def _do_mass_check(self):
        files = self.scan_result.c_files + self.scan_result.h_files
        total_errors = 0
        results = []
        for i, f in enumerate(files):
            self.after(0, lambda i=i: self._set_status(
                f"Checking {i+1}/{len(files)}..."
            ))
            try:
                diags = self.formatter.diagnose_file(str(f.path))
                total_errors += len(diags)
                results.append((f.rel_path, len(diags), diags))
            except RuntimeError as e:
                results.append((f.rel_path, -1, []))

        def _show():
            MassResultWindow(self, "Norm Check Results", results)
            self._set_status(
                f"Check done: {total_errors} errors in {len(files)} files"
            )
        self.after(0, _show)

    def _mass_fix(self):
        if not self.scan_result or not self.scan_result.files:
            self._set_status("No files loaded — open a folder first.")
            return
        threading.Thread(target=self._do_mass_fix, daemon=True).start()

    def _do_mass_fix(self):
        files = self.scan_result.c_files + self.scan_result.h_files
        total_fixed = 0
        results = []
        for i, f in enumerate(files):
            self.after(0, lambda i=i: self._set_status(
                f"Fixing {i+1}/{len(files)}..."
            ))
            try:
                result = self.formatter.format_file(str(f.path))
                applied = len(result.applied)
                total_fixed += applied
                results.append((f.rel_path, applied, result.applied))
            except RuntimeError as e:
                results.append((f.rel_path, -1, []))

        # Reload current file if it was modified
        if self.current_file:
            try:
                new_content = self.current_file.read_text(errors="replace")
                if new_content != self._last_content:
                    self.after(0, lambda: self._load_file(self.current_file))
            except OSError:
                pass

        def _show():
            self._set_status(
                f"Fix done: {total_fixed} fixes applied in {len(files)} files"
            )
        self.after(0, _show)

    def _mass_compile(self):
        if not self.scan_result or not self.scan_result.c_files:
            self._set_status("No .c files loaded — open a folder first.")
            return
        threading.Thread(target=self._do_mass_compile, daemon=True).start()

    def _do_mass_compile(self):
        files = self.scan_result.c_files
        results = []
        passed = 0
        for i, f in enumerate(files):
            self.after(0, lambda i=i: self._set_status(
                f"Compiling {i+1}/{len(files)}..."
            ))
            source = f.path.read_text(errors="replace")
            main_check = check_main_commented_or_missing(source)
            comp = check_compilation(str(f.path))
            results.append({
                "file": f.rel_path,
                "ok": comp.success,
                "errors": comp.errors,
                "main_commented": main_check["main_commented"],
            })
            if comp.success:
                passed += 1

        def _show():
            CompileResultWindow(self, results)
            self._set_status(
                f"Compile done: {passed}/{len(files)} passed"
            )
        self.after(0, _show)

    # ---------------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------------

    def _set_status(self, text: str):
        self.status_label.after(0, lambda: self.status_label.configure(text=text))


# ---------------------------------------------------------------
# Find dialog
# ---------------------------------------------------------------

class FindDialog(ctk.CTkToplevel):
    def __init__(self, editor: EditorFrame):
        super().__init__(editor)
        self.editor = editor
        self.title("Find / Replace")
        self.geometry("420x180")
        self.resizable(False, False)
        self.grab_set()

        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Find:").grid(row=0, column=0, padx=12, pady=8, sticky="w")
        self.find_entry = ctk.CTkEntry(self)
        self.find_entry.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        self.find_entry.bind("<Return>", lambda e: self._find_next())

        ctk.CTkLabel(self, text="Replace:").grid(row=1, column=0, padx=12, pady=4, sticky="w")
        self.replace_entry = ctk.CTkEntry(self)
        self.replace_entry.grid(row=1, column=1, padx=8, pady=4, sticky="ew")

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=2, column=0, columnspan=2, pady=12)
        ctk.CTkButton(btns, text="Find Next", width=100, command=self._find_next).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Replace", width=100, command=self._replace_one).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Replace All", width=110, command=self._replace_all).pack(side="left", padx=4)

        self._last_pos = "1.0"
        self.find_entry.focus_set()

    def _find_next(self):
        query = self.find_entry.get()
        if not query:
            return
        text = self.editor.editor
        pos = text.search(query, self._last_pos, stopindex="end", nocase=True)
        if not pos:
            pos = text.search(query, "1.0", stopindex="end", nocase=True)
        if pos:
            end = f"{pos}+{len(query)}c"
            text.tag_remove("sel", "1.0", "end")
            text.tag_add("sel", pos, end)
            text.mark_set("insert", pos)
            text.see(pos)
            self._last_pos = end
        else:
            self.editor._set_status(f"'{query}' not found")

    def _replace_one(self):
        query = self.find_entry.get()
        replacement = self.replace_entry.get()
        text = self.editor.editor
        sel = text.tag_ranges("sel")
        if sel and text.get(*sel) == query:
            text.delete(*sel)
            text.insert(sel[0], replacement)
        self._find_next()

    def _replace_all(self):
        query = self.find_entry.get()
        replacement = self.replace_entry.get()
        if not query:
            return
        text = self.editor.editor
        content = text.get("1.0", "end-1c")
        new_content = content.replace(query, replacement)
        count = content.count(query)
        text.delete("1.0", "end")
        text.insert("1.0", new_content)
        self.editor._set_status(f"Replaced {count} occurrence(s)")


# ---------------------------------------------------------------
# Goto line dialog
# ---------------------------------------------------------------

class GotoDialog(ctk.CTkToplevel):
    def __init__(self, editor: EditorFrame):
        super().__init__(editor)
        self.editor = editor
        self.title("Go to Line")
        self.geometry("280x120")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(self, text="Line number:").pack(pady=(16, 4))
        self.entry = ctk.CTkEntry(self, width=120)
        self.entry.pack()
        self.entry.bind("<Return>", lambda e: self._go())
        ctk.CTkButton(self, text="Go", width=80, command=self._go).pack(pady=8)
        self.entry.focus_set()

    def _go(self):
        try:
            line = int(self.entry.get())
            self.editor.editor.mark_set("insert", f"{line}.0")
            self.editor.editor.see(f"{line}.0")
            self.destroy()
        except ValueError:
            pass


# ---------------------------------------------------------------
# Mass result windows
# ---------------------------------------------------------------

class MassResultWindow(ctk.CTkToplevel):
    def __init__(self, parent, title: str, results: list):
        super().__init__(parent)
        self.title(title)
        self.geometry("700x500")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="monospace", size=12))
        box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ok = sum(1 for _, n, _ in results if n == 0)
        box.insert("end", f"{'='*60}\n")
        box.insert("end", f"  {ok}/{len(results)} files OK\n")
        box.insert("end", f"{'='*60}\n\n")

        for fname, count, diags in results:
            if count == 0:
                box.insert("end", f"  OK  {fname}\n")
            elif count < 0:
                box.insert("end", f"  ERR {fname}: could not check\n")
            else:
                box.insert("end", f"  {count:3d} {fname}\n")
                for d in diags[:5]:
                    box.insert("end", f"       L{d.line}:{d.col} [{d.code}] {d.message}\n")
                if len(diags) > 5:
                    box.insert("end", f"       ... {len(diags)-5} more\n")

        ctk.CTkButton(self, text="Close", command=self.destroy).grid(
            row=1, column=0, pady=8)


class CompileResultWindow(ctk.CTkToplevel):
    def __init__(self, parent, results: list[dict]):
        super().__init__(parent)
        self.title("Compilation Results")
        self.geometry("700x500")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="monospace", size=12))
        box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ok = sum(1 for r in results if r["ok"])
        box.insert("end", f"{'='*60}\n  {ok}/{len(results)} compiled OK\n{'='*60}\n\n")

        for r in results:
            status = "OK  " if r["ok"] else "FAIL"
            warn = " [main commented!]" if r["main_commented"] else ""
            box.insert("end", f"  {status} {r['file']}{warn}\n")
            for e in r["errors"][:3]:
                box.insert("end", f"       {e}\n")

        ctk.CTkButton(self, text="Close", command=self.destroy).grid(
            row=1, column=0, pady=8)
