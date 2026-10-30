import sys
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, date, timedelta
from pathlib import Path
from PIL import Image, ImageTk

import library_management as lm

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

BG_IMAGE_PATH = BASE_DIR / "background.png"

COLOR_BG_BASE = "#12141d"
COLOR_CARD = "#1c202e"
COLOR_CARD_BORDER = "#2f364d"
COLOR_CARD_HEADER = "#252b3e"
COLOR_TEXT = "#f8fafc"
COLOR_TEXT_MUTED = "#94a3b8"
COLOR_PRIMARY = "#4f46e5"
COLOR_PRIMARY_HOVER = "#4338ca"
COLOR_SUCCESS = "#10b981"
COLOR_SUCCESS_HOVER = "#059669"
COLOR_DANGER = "#ef4444"
COLOR_DANGER_HOVER = "#dc2626"
COLOR_ACCENT = "#38bdf8"
COLOR_INPUT_BG = "#131622"
COLOR_INPUT_BORDER = "#3b4259"


class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert") or (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#0f111a",
            foreground="#e2e8f0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Segoe UI", 8),
            padx=6,
            pady=3,
        )
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class LibraryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BookShelf")
        
        window_width = 1100
        window_height = 720
        self.minsize(980, 640)
        self.configure(bg=COLOR_BG_BASE)

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        pos_x = max(0, (screen_width - window_width) // 2)
        pos_y = max(0, (screen_height - window_height) // 2)
        self.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

        self.raw_bg_image = None
        self.bg_photo = None
        self.bg_canvas = None
        self._resize_job = None

        lm.init_storage()

        if BG_IMAGE_PATH.exists():
            try:
                self.raw_bg_image = Image.open(BG_IMAGE_PATH).convert("RGBA")
            except Exception:
                pass

        self.setup_styles()

        self.bg_canvas = tk.Canvas(self, highlightthickness=0, bg=COLOR_BG_BASE)
        self.bg_canvas.pack(fill=tk.BOTH, expand=True)
        self.bg_canvas.bind("<Configure>", self.on_window_resize)

        self.main_container = tk.Frame(self.bg_canvas, bg=COLOR_BG_BASE)
        self.canvas_window_id = self.bg_canvas.create_window(
            (0, 0), window=self.main_container, anchor="nw"
        )

        self.build_top_bar()
        self.build_navigation()
        self.build_content_views()
        self.build_status_bar()

        self.show_view("books")
        self.update_clock()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=COLOR_CARD,
            foreground=COLOR_TEXT,
            fieldbackground=COLOR_CARD,
            rowheight=32,
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", COLOR_PRIMARY)],
            foreground=[("selected", "#ffffff")],
        )
        style.configure(
            "Treeview.Heading",
            background=COLOR_CARD_HEADER,
            foreground=COLOR_TEXT,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padding=6,
        )
        style.map(
            "Treeview.Heading",
            background=[("active", COLOR_CARD_BORDER)],
        )
        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background=COLOR_CARD_BORDER,
            troughcolor=COLOR_CARD,
            borderwidth=0,
            arrowsize=12,
        )

    def on_window_resize(self, event):
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(50, self._render_background, event.width, event.height)

    def _render_background(self, width, height):
        if width <= 10 or height <= 10:
            return

        self.bg_canvas.itemconfig(self.canvas_window_id, width=width, height=height)

        if not self.raw_bg_image:
            return

        try:
            resized = self.raw_bg_image.resize((width, height), Image.Resampling.LANCZOS)
            overlay = Image.new("RGBA", (width, height), (18, 20, 29, int(255 * 0.65)))
            blended = Image.alpha_composite(resized, overlay)
            self.bg_photo = ImageTk.PhotoImage(blended)
            self.bg_canvas.delete("bg_img")
            self.bg_canvas.create_image(0, 0, image=self.bg_photo, anchor="nw", tags="bg_img")
            self.bg_canvas.tag_lower("bg_img")
        except Exception:
            pass

    def build_top_bar(self):
        top_bar = tk.Frame(self.main_container, bg="#161824", height=60, padx=20, pady=10)
        top_bar.pack(fill=tk.X, side=tk.TOP)

        title_box = tk.Frame(top_bar, bg="#161824")
        title_box.pack(side=tk.LEFT)

        title_icon = tk.Label(title_box, text="📚", font=("Segoe UI Emoji", 16), bg="#161824", fg="#ffffff")
        title_icon.pack(side=tk.LEFT, padx=(0, 8))

        title_lbl = tk.Label(
            title_box,
            text="BOOKSHELF",
            font=("Segoe UI", 13, "bold"),
            bg="#161824",
            fg=COLOR_TEXT,
        )
        title_lbl.pack(side=tk.LEFT)

        right_box = tk.Frame(top_bar, bg="#161824")
        right_box.pack(side=tk.RIGHT)

        self.clock_lbl = tk.Label(
            right_box,
            text="",
            font=("Consolas", 10, "bold"),
            bg="#212536",
            fg=COLOR_ACCENT,
            padx=12,
            pady=4,
            relief=tk.FLAT,
        )
        self.clock_lbl.pack(side=tk.LEFT, padx=(0, 15))

        btn_refresh = tk.Button(
            right_box,
            text="🔄",
            font=("Segoe UI Emoji", 12),
            bg="#252a3c",
            fg="#ffffff",
            activebackground=COLOR_PRIMARY,
            activeforeground="#ffffff",
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self.refresh_all_data,
        )
        btn_refresh.pack(side=tk.LEFT)
        Tooltip(btn_refresh, "Refresh All Data")
        self.add_hover_effect(btn_refresh, "#252a3c", COLOR_PRIMARY)

    def update_clock(self):
        now = datetime.now()
        formatted = now.strftime("📅 %Y-%m-%d  ⏰ %H:%M:%S")
        self.clock_lbl.config(text=formatted)
        self.after(1000, self.update_clock)

    def build_navigation(self):
        nav_frame = tk.Frame(self.main_container, bg="#1a1d2b", height=48, padx=20)
        nav_frame.pack(fill=tk.X, side=tk.TOP)

        self.nav_buttons = {}
        tabs = [
            ("books", "📚 Books Catalog"),
            ("students", "🎓 Students Directory"),
            ("issue_return", "🔄 Issue & Return Desk"),
            ("records", "📋 Records & History"),
        ]

        for key, label in tabs:
            btn = tk.Button(
                nav_frame,
                text=label,
                font=("Segoe UI", 10, "bold"),
                bg="#1a1d2b",
                fg=COLOR_TEXT_MUTED,
                activebackground=COLOR_CARD,
                activeforeground=COLOR_TEXT,
                bd=0,
                padx=18,
                pady=10,
                cursor="hand2",
                command=lambda k=key: self.show_view(k),
            )
            btn.pack(side=tk.LEFT, padx=(0, 4))
            self.nav_buttons[key] = btn

    def show_view(self, key):
        for tab_key, btn in self.nav_buttons.items():
            if tab_key == key:
                btn.config(bg=COLOR_CARD, fg=COLOR_TEXT)
            else:
                btn.config(bg="#1a1d2b", fg=COLOR_TEXT_MUTED)

        for frame_key, frame in self.views.items():
            if frame_key == key:
                if key == "records":
                    frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
                else:
                    frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
            else:
                frame.pack_forget()

        if key == "books":
            self.refresh_books_table()
        elif key == "students":
            self.refresh_students_table()
        elif key == "issue_return":
            self.refresh_issue_desk()
        elif key == "records":
            self.refresh_records_table()

    def build_content_views(self):
        self.content_holder = tk.Frame(self.main_container, bg=COLOR_BG_BASE)
        self.content_holder.pack(fill=tk.BOTH, expand=True)

        self.views = {
            "books": self.create_books_view(self.content_holder),
            "students": self.create_students_view(self.content_holder),
            "issue_return": self.create_issue_return_view(self.content_holder),
            "records": self.create_records_view(self.content_holder),
        }

    def create_books_view(self, parent):
        view = tk.Frame(parent, bg=COLOR_BG_BASE)

        card = tk.LabelFrame(
            view,
            text=" Manage Books ",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_CARD,
            fg=COLOR_TEXT,
            bd=1,
            relief=tk.SOLID,
            padx=16,
            pady=12,
        )
        card.pack(fill=tk.X, pady=(0, 12))

        tk.Label(card, text="Book ID (opt):", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.book_id_entry = self.create_entry(card, width=10)
        self.book_id_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(card, text="Book Title:", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT).grid(row=0, column=2, sticky="w", padx=(10, 5), pady=5)
        self.book_title_entry = self.create_entry(card, width=22)
        self.book_title_entry.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(card, text="Quantity:", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT).grid(row=0, column=4, sticky="w", padx=(10, 5), pady=5)
        self.book_qty_entry = self.create_entry(card, width=6)
        self.book_qty_entry.grid(row=0, column=5, padx=5, pady=5)

        btn_add_book = self.create_btn(card, "+ Add / Update Book", COLOR_PRIMARY, COLOR_PRIMARY_HOVER, self.action_add_book)
        btn_add_book.grid(row=0, column=6, padx=(10, 5), pady=5)

        btn_del_book = self.create_btn(card, "🗑️ Delete Book", COLOR_DANGER, COLOR_DANGER_HOVER, self.action_delete_book)
        btn_del_book.grid(row=0, column=7, padx=5, pady=5)

        btn_clear_input = self.create_symbol_btn(card, "✕", "Clear Inputs", self.clear_book_inputs)
        btn_clear_input.grid(row=0, column=8, padx=5, pady=5)

        tk.Label(card, text="Search ID/Title:", font=("Segoe UI", 9), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).grid(row=1, column=0, sticky="w", padx=5, pady=(10, 5))
        self.book_search_entry = self.create_entry(card, width=24)
        self.book_search_entry.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=(10, 5))
        self.book_search_entry.bind("<KeyRelease>", lambda e: self.filter_books())

        btn_search_book = self.create_btn(card, "🔍 Search", "#334155", "#475569", self.filter_books)
        btn_search_book.grid(row=1, column=3, sticky="w", padx=5, pady=(10, 5))

        btn_clear_search = self.create_symbol_btn(card, "✕", "Clear Search", self.clear_book_search)
        btn_clear_search.grid(row=1, column=4, sticky="w", padx=5, pady=(10, 5))

        table_card = tk.Frame(view, bg=COLOR_CARD, bd=1, relief=tk.SOLID)
        table_card.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "name", "quantity", "status")
        self.books_tree = ttk.Treeview(table_card, columns=cols, show="headings", selectmode="browse")
        self.books_tree.heading("id", text="Book ID")
        self.books_tree.heading("name", text="Book Title")
        self.books_tree.heading("quantity", text="Available Quantity")
        self.books_tree.heading("status", text="Stock Status")

        self.books_tree.column("id", width=120, anchor="center", stretch=False)
        self.books_tree.column("name", width=440, anchor="w", stretch=True)
        self.books_tree.column("quantity", width=150, anchor="center", stretch=False)
        self.books_tree.column("status", width=160, anchor="center", stretch=False)

        self.books_tree.tag_configure("in_stock", foreground="#10b981")
        self.books_tree.tag_configure("out_of_stock", foreground="#ef4444")

        scroll = ttk.Scrollbar(table_card, orient=tk.VERTICAL, command=self.books_tree.yview)
        self.books_tree.configure(yscrollcommand=scroll.set)

        self.books_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(1, 0), pady=1)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=1)

        self.books_tree.bind("<<TreeviewSelect>>", self.on_book_select)
        return view

    def action_add_book(self):
        b_id = self.book_id_entry.get().strip()
        name = self.book_title_entry.get().strip()
        qty_str = self.book_qty_entry.get().strip()

        if not name:
            messagebox.showwarning("Input Required", "Please enter a book title.")
            return

        try:
            qty = int(qty_str)
            if qty <= 0:
                messagebox.showwarning("Invalid Input", "Quantity must be greater than 0.")
                return
        except ValueError:
            messagebox.showwarning("Invalid Input", "Quantity must be a valid integer.")
            return

        success, msg = lm.add_book(name, qty, b_id if b_id else None)
        if success:
            self.clear_book_inputs()
            self.refresh_books_table()
            self.status_msg.config(text=f"Success: {msg}", fg=COLOR_SUCCESS)
        else:
            messagebox.showerror("Error", msg)

    def action_delete_book(self):
        ident = self.book_id_entry.get().strip() or self.book_title_entry.get().strip()
        if not ident:
            selected = self.books_tree.selection()
            if selected:
                ident = self.books_tree.item(selected[0], "values")[0]

        if not ident:
            messagebox.showwarning("Select Book", "Please enter or select a Book ID or title to delete.")
            return

        success, msg = lm.delete_book(ident)
        if success:
            self.clear_book_inputs()
            self.refresh_books_table()
            self.status_msg.config(text=f"Success: {msg}", fg=COLOR_SUCCESS)
        else:
            messagebox.showerror("Cannot Delete", msg)

    def on_book_select(self, event):
        selected = self.books_tree.selection()
        if selected:
            values = self.books_tree.item(selected[0], "values")
            self.book_id_entry.delete(0, tk.END)
            self.book_id_entry.insert(0, values[0])
            self.book_title_entry.delete(0, tk.END)
            self.book_title_entry.insert(0, values[1])
            self.book_qty_entry.delete(0, tk.END)
            self.book_qty_entry.insert(0, values[2])

    def refresh_books_table(self):
        self.books_tree.delete(*self.books_tree.get_children())
        books = lm.get_all_books()
        for b in books:
            if b["quantity"] > 0:
                status_text = "● In Stock"
                tag = "in_stock"
            else:
                status_text = "● Out of Stock"
                tag = "out_of_stock"
            self.books_tree.insert("", tk.END, values=(b["id"], b["name"], b["quantity"], status_text), tags=(tag,))

    def filter_books(self):
        query = self.book_search_entry.get().strip().lower()
        self.books_tree.delete(*self.books_tree.get_children())
        books = lm.get_all_books()
        for b in books:
            if query in b["name"].lower() or query in b["id"].lower():
                if b["quantity"] > 0:
                    status_text = "● In Stock"
                    tag = "in_stock"
                else:
                    status_text = "● Out of Stock"
                    tag = "out_of_stock"
                self.books_tree.insert("", tk.END, values=(b["id"], b["name"], b["quantity"], status_text), tags=(tag,))

    def clear_book_inputs(self):
        self.book_id_entry.delete(0, tk.END)
        self.book_title_entry.delete(0, tk.END)
        self.book_qty_entry.delete(0, tk.END)

    def clear_book_search(self):
        self.book_search_entry.delete(0, tk.END)
        self.refresh_books_table()

    def create_students_view(self, parent):
        view = tk.Frame(parent, bg=COLOR_BG_BASE)

        card = tk.LabelFrame(
            view,
            text=" Manage Students ",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_CARD,
            fg=COLOR_TEXT,
            bd=1,
            relief=tk.SOLID,
            padx=16,
            pady=12,
        )
        card.pack(fill=tk.X, pady=(0, 12))

        tk.Label(card, text="Roll Number:", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.student_roll_entry = self.create_entry(card, width=18)
        self.student_roll_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(card, text="Student Name:", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT).grid(row=0, column=2, sticky="w", padx=(15, 5), pady=5)
        self.student_name_entry = self.create_entry(card, width=24)
        self.student_name_entry.grid(row=0, column=3, padx=5, pady=5)

        btn_add_student = self.create_btn(card, "+ Register Student", COLOR_PRIMARY, COLOR_PRIMARY_HOVER, self.action_add_student)
        btn_add_student.grid(row=0, column=4, padx=10, pady=5)

        btn_del_student = self.create_btn(card, "🗑️ Delete Student", COLOR_DANGER, COLOR_DANGER_HOVER, self.action_delete_student)
        btn_del_student.grid(row=0, column=5, padx=5, pady=5)

        btn_clear_input = self.create_symbol_btn(card, "✕", "Clear Inputs", self.clear_student_inputs)
        btn_clear_input.grid(row=0, column=6, padx=5, pady=5)

        tk.Label(card, text="Search Student:", font=("Segoe UI", 9), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).grid(row=1, column=0, sticky="w", padx=5, pady=(10, 5))
        self.student_search_entry = self.create_entry(card, width=18)
        self.student_search_entry.grid(row=1, column=1, padx=5, pady=(10, 5))
        self.student_search_entry.bind("<KeyRelease>", lambda e: self.filter_students())

        btn_search_student = self.create_btn(card, "🔍 Search", "#334155", "#475569", self.filter_students)
        btn_search_student.grid(row=1, column=2, padx=5, pady=(10, 5))

        btn_clear_search = self.create_symbol_btn(card, "✕", "Clear Search", self.clear_student_search)
        btn_clear_search.grid(row=1, column=3, sticky="w", padx=5, pady=(10, 5))

        table_card = tk.Frame(view, bg=COLOR_CARD, bd=1, relief=tk.SOLID)
        table_card.pack(fill=tk.BOTH, expand=True)

        cols = ("roll", "name", "active_borrows")
        self.students_tree = ttk.Treeview(table_card, columns=cols, show="headings", selectmode="browse")
        self.students_tree.heading("roll", text="Roll Number")
        self.students_tree.heading("name", text="Student Name")
        self.students_tree.heading("active_borrows", text="Active Borrowed Books")

        self.students_tree.column("roll", width=220, anchor="center")
        self.students_tree.column("name", width=420, anchor="w", stretch=True)
        self.students_tree.column("active_borrows", width=200, anchor="center")

        scroll = ttk.Scrollbar(table_card, orient=tk.VERTICAL, command=self.students_tree.yview)
        self.students_tree.configure(yscrollcommand=scroll.set)

        self.students_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(1, 0), pady=1)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=1)

        self.students_tree.bind("<<TreeviewSelect>>", self.on_student_select)
        return view

    def action_add_student(self):
        roll = self.student_roll_entry.get().strip()
        name = self.student_name_entry.get().strip()

        if not roll or not name:
            messagebox.showwarning("Input Required", "Please enter both roll number and student name.")
            return

        success, msg = lm.add_student(roll, name)
        if success:
            self.clear_student_inputs()
            self.refresh_students_table()
            self.status_msg.config(text=f"Success: {msg}", fg=COLOR_SUCCESS)
        else:
            messagebox.showerror("Error", msg)

    def action_delete_student(self):
        roll = self.student_roll_entry.get().strip()
        if not roll:
            selected = self.students_tree.selection()
            if selected:
                roll = self.students_tree.item(selected[0], "values")[0]

        if not roll:
            messagebox.showwarning("Select Student", "Please enter or select a student roll number to delete.")
            return

        success, msg = lm.delete_student(roll)
        if success:
            self.clear_student_inputs()
            self.refresh_students_table()
            self.status_msg.config(text=f"Success: {msg}", fg=COLOR_SUCCESS)
        else:
            messagebox.showerror("Cannot Delete", msg)

    def on_student_select(self, event):
        selected = self.students_tree.selection()
        if selected:
            values = self.students_tree.item(selected[0], "values")
            self.student_roll_entry.delete(0, tk.END)
            self.student_roll_entry.insert(0, values[0])
            self.student_name_entry.delete(0, tk.END)
            self.student_name_entry.insert(0, values[1])

    def refresh_students_table(self):
        self.students_tree.delete(*self.students_tree.get_children())
        students = lm.get_all_students()
        for s in students:
            borrows = len(lm.get_active_issues_for_student(s["roll_number"]))
            self.students_tree.insert("", tk.END, values=(s["roll_number"], s["name"], borrows))

    def filter_students(self):
        query = self.student_search_entry.get().strip().lower()
        self.students_tree.delete(*self.students_tree.get_children())
        students = lm.get_all_students()
        for s in students:
            if query in s["roll_number"].lower() or query in s["name"].lower():
                borrows = len(lm.get_active_issues_for_student(s["roll_number"]))
                self.students_tree.insert("", tk.END, values=(s["roll_number"], s["name"], borrows))

    def clear_student_inputs(self):
        self.student_roll_entry.delete(0, tk.END)
        self.student_name_entry.delete(0, tk.END)

    def clear_student_search(self):
        self.student_search_entry.delete(0, tk.END)
        self.refresh_students_table()

    def create_issue_return_view(self, parent):
        view = tk.Frame(parent, bg=COLOR_BG_BASE)

        top_split = tk.Frame(view, bg=COLOR_BG_BASE)
        top_split.pack(fill=tk.X, pady=(0, 12))

        issue_card = tk.LabelFrame(
            top_split,
            text=" 📖 Issue Book ",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_CARD,
            fg=COLOR_TEXT,
            bd=1,
            relief=tk.SOLID,
            padx=14,
            pady=10,
        )
        issue_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        tk.Label(issue_card, text="Student Roll:", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT).grid(row=0, column=0, sticky="w", pady=4)
        self.issue_roll_entry = self.create_entry(issue_card, width=22)
        self.issue_roll_entry.grid(row=0, column=1, sticky="w", padx=5, pady=4)

        tk.Label(issue_card, text="Book ID / Title:", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT).grid(row=1, column=0, sticky="w", pady=4)
        self.issue_book_entry = self.create_entry(issue_card, width=22)
        self.issue_book_entry.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        tk.Label(issue_card, text="Return Date:", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT).grid(row=2, column=0, sticky="w", pady=4)
        due_frame = tk.Frame(issue_card, bg=COLOR_CARD)
        due_frame.grid(row=2, column=1, sticky="w", padx=5, pady=4)

        self.issue_due_entry = self.create_entry(due_frame, width=14)
        self.issue_due_entry.pack(side=tk.LEFT)
        self.set_default_due_date()

        btn_default_date = self.create_btn(due_frame, "📅 +14d", "#334155", "#475569", self.set_default_due_date)
        btn_default_date.pack(side=tk.LEFT, padx=(5, 0))
        Tooltip(btn_default_date, "Set Default Due Date (Today + 14 Days)")

        issue_btn_frame = tk.Frame(issue_card, bg=COLOR_CARD)
        issue_btn_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0), sticky="w")

        btn_issue = self.create_btn(issue_btn_frame, "📖 Issue Book", COLOR_PRIMARY, COLOR_PRIMARY_HOVER, self.action_issue_book)
        btn_issue.pack(side=tk.LEFT, padx=(0, 8))

        btn_clear_issue = self.create_symbol_btn(issue_btn_frame, "✕", "Clear Fields", self.clear_issue_fields)
        btn_clear_issue.pack(side=tk.LEFT)

        return_card = tk.LabelFrame(
            top_split,
            text=" ↩️ Return Book ",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_CARD,
            fg=COLOR_TEXT,
            bd=1,
            relief=tk.SOLID,
            padx=14,
            pady=10,
        )
        return_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))

        tk.Label(return_card, text="Student Roll:", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT).grid(row=0, column=0, sticky="w", pady=4)
        self.return_roll_entry = self.create_entry(return_card, width=22)
        self.return_roll_entry.grid(row=0, column=1, sticky="w", padx=5, pady=4)

        tk.Label(return_card, text="Book ID / Title:", font=("Segoe UI", 9, "bold"), bg=COLOR_CARD, fg=COLOR_TEXT).grid(row=1, column=0, sticky="w", pady=4)
        self.return_book_entry = self.create_entry(return_card, width=22)
        self.return_book_entry.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        tk.Label(return_card, text="Tip: Select an active loan below to autofill", font=("Segoe UI", 8), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).grid(row=2, column=0, columnspan=2, sticky="w", pady=4)

        return_btn_frame = tk.Frame(return_card, bg=COLOR_CARD)
        return_btn_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0), sticky="w")

        btn_return = self.create_btn(return_btn_frame, "↩️ Return Book", COLOR_SUCCESS, COLOR_SUCCESS_HOVER, self.action_return_book)
        btn_return.pack(side=tk.LEFT, padx=(0, 8))

        btn_clear_return = self.create_symbol_btn(return_btn_frame, "✕", "Clear Fields", self.clear_return_fields)
        btn_clear_return.pack(side=tk.LEFT)

        active_table_card = tk.LabelFrame(
            view,
            text=" Active Borrowed Books (Click to Autofill Return) ",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_CARD,
            fg=COLOR_TEXT,
            bd=1,
            relief=tk.SOLID,
            padx=8,
            pady=8,
        )
        active_table_card.pack(fill=tk.BOTH, expand=True)

        cols = ("roll", "student_name", "book_id", "book_name", "issue_date", "return_date")
        self.active_issues_tree = ttk.Treeview(active_table_card, columns=cols, show="headings", selectmode="browse")
        self.active_issues_tree.heading("roll", text="Roll Number")
        self.active_issues_tree.heading("student_name", text="Student Name")
        self.active_issues_tree.heading("book_id", text="Book ID")
        self.active_issues_tree.heading("book_name", text="Book Title")
        self.active_issues_tree.heading("issue_date", text="Issue Date")
        self.active_issues_tree.heading("return_date", text="Due Date")

        self.active_issues_tree.column("roll", width=140, anchor="center", stretch=False)
        self.active_issues_tree.column("student_name", width=200, anchor="w", stretch=True)
        self.active_issues_tree.column("book_id", width=110, anchor="center", stretch=False)
        self.active_issues_tree.column("book_name", width=280, anchor="w", stretch=True)
        self.active_issues_tree.column("issue_date", width=120, anchor="center", stretch=False)
        self.active_issues_tree.column("return_date", width=120, anchor="center", stretch=False)

        scroll = ttk.Scrollbar(active_table_card, orient=tk.VERTICAL, command=self.active_issues_tree.yview)
        self.active_issues_tree.configure(yscrollcommand=scroll.set)

        self.active_issues_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(1, 0), pady=1)
        scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=1)

        self.active_issues_tree.bind("<<TreeviewSelect>>", self.on_active_issue_select)
        return view

    def set_default_due_date(self):
        due = lm.calculate_default_return_date(14)
        self.issue_due_entry.delete(0, tk.END)
        self.issue_due_entry.insert(0, due)

    def action_issue_book(self):
        roll = self.issue_roll_entry.get().strip()
        book = self.issue_book_entry.get().strip()
        due = self.issue_due_entry.get().strip()

        if not roll or not book:
            messagebox.showwarning("Input Required", "Please provide both student roll number and book ID or title.")
            return

        success, msg = lm.issue_book(roll, book, due)
        if success:
            self.clear_issue_fields()
            self.refresh_issue_desk()
            self.status_msg.config(text=f"Success: {msg}", fg=COLOR_SUCCESS)
        else:
            messagebox.showerror("Issue Failed", msg)

    def action_return_book(self):
        roll = self.return_roll_entry.get().strip()
        book = self.return_book_entry.get().strip()

        if not roll or not book:
            messagebox.showwarning("Input Required", "Please provide both student roll number and book ID or title to return.")
            return

        success, msg = lm.return_book(roll, book)
        if success:
            self.clear_return_fields()
            self.refresh_issue_desk()
            self.status_msg.config(text=f"Success: {msg}", fg=COLOR_SUCCESS)
        else:
            messagebox.showerror("Return Failed", msg)

    def on_active_issue_select(self, event):
        selected = self.active_issues_tree.selection()
        if selected:
            values = self.active_issues_tree.item(selected[0], "values")
            self.return_roll_entry.delete(0, tk.END)
            self.return_roll_entry.insert(0, values[0])
            self.return_book_entry.delete(0, tk.END)
            self.return_book_entry.insert(0, values[2])

    def refresh_issue_desk(self):
        self.active_issues_tree.delete(*self.active_issues_tree.get_children())
        active_loans = lm.get_all_issues(status_filter="ACTIVE")
        for loan in active_loans:
            student = lm.find_student(loan["roll_number"])
            student_name = student["name"] if student else "Unknown"
            self.active_issues_tree.insert(
                "",
                tk.END,
                values=(
                    loan["roll_number"],
                    student_name,
                    loan.get("book_id", "B101"),
                    loan["book_name"],
                    loan["issue_date"],
                    loan["return_date"],
                ),
            )

    def clear_issue_fields(self):
        self.issue_roll_entry.delete(0, tk.END)
        self.issue_book_entry.delete(0, tk.END)
        self.set_default_due_date()

    def clear_return_fields(self):
        self.return_roll_entry.delete(0, tk.END)
        self.return_book_entry.delete(0, tk.END)

    def create_records_view(self, parent):
        view = tk.Frame(parent, bg=COLOR_BG_BASE)

        card = tk.Frame(view, bg=COLOR_CARD, padx=16, pady=10)
        card.pack(fill=tk.X, side=tk.TOP)

        self.records_filter_var = tk.StringVar(value="ALL")

        filter_btn_frame = tk.Frame(card, bg=COLOR_CARD)
        filter_btn_frame.pack(side=tk.LEFT)

        filters = [("All Records", "ALL"), ("Active Only", "ACTIVE"), ("Returned Only", "RETURNED")]
        for text, val in filters:
            b = tk.Radiobutton(
                filter_btn_frame,
                text=text,
                value=val,
                variable=self.records_filter_var,
                font=("Segoe UI", 9, "bold"),
                bg=COLOR_CARD,
                fg=COLOR_TEXT,
                selectcolor=COLOR_PRIMARY,
                activebackground=COLOR_CARD,
                activeforeground=COLOR_TEXT,
                indicatoron=False,
                padx=14,
                pady=5,
                bd=0,
                cursor="hand2",
                command=self.refresh_records_table,
            )
            b.pack(side=tk.LEFT, padx=(0, 6))

        search_frame = tk.Frame(card, bg=COLOR_CARD)
        search_frame.pack(side=tk.RIGHT)

        tk.Label(search_frame, text="Filter:", font=("Segoe UI", 9), bg=COLOR_CARD, fg=COLOR_TEXT_MUTED).pack(side=tk.LEFT, padx=(0, 5))
        self.records_search_entry = self.create_entry(search_frame, width=20)
        self.records_search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.records_search_entry.bind("<KeyRelease>", lambda e: self.filter_records())

        btn_clear_rec_search = self.create_symbol_btn(search_frame, "✕", "Clear Filter", self.clear_records_search)
        btn_clear_rec_search.pack(side=tk.LEFT, padx=(0, 8))

        btn_refresh_table = self.create_symbol_btn(search_frame, "🔄", "Refresh Table", self.refresh_records_table)
        btn_refresh_table.pack(side=tk.LEFT)

        table_card = tk.Frame(view, bg=COLOR_CARD)
        table_card.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        cols = ("roll", "student_name", "book_id", "book_name", "issue_date", "return_date", "status")
        self.records_tree = ttk.Treeview(table_card, columns=cols, show="headings", selectmode="browse")
        self.records_tree.heading("roll", text="Roll Number")
        self.records_tree.heading("student_name", text="Student Name")
        self.records_tree.heading("book_id", text="Book ID")
        self.records_tree.heading("book_name", text="Book Title")
        self.records_tree.heading("issue_date", text="Issue Date")
        self.records_tree.heading("return_date", text="Due Date")
        self.records_tree.heading("status", text="Status")

        self.records_tree.column("roll", width=130, anchor="center", stretch=False)
        self.records_tree.column("student_name", width=200, anchor="w", stretch=True)
        self.records_tree.column("book_id", width=110, anchor="center", stretch=False)
        self.records_tree.column("book_name", width=260, anchor="w", stretch=True)
        self.records_tree.column("issue_date", width=110, anchor="center", stretch=False)
        self.records_tree.column("return_date", width=110, anchor="center", stretch=False)
        self.records_tree.column("status", width=120, anchor="center", stretch=False)

        self.records_tree.tag_configure("returned", foreground="#10b981")
        self.records_tree.tag_configure("active", foreground="#f59e0b")

        scroll = ttk.Scrollbar(table_card, orient=tk.VERTICAL, command=self.records_tree.yview)
        self.records_tree.configure(yscrollcommand=scroll.set)

        self.records_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        return view

    def refresh_records_table(self):
        self.records_tree.delete(*self.records_tree.get_children())
        filter_status = self.records_filter_var.get()
        records = lm.get_all_issues(status_filter=filter_status)
        query = self.records_search_entry.get().strip().lower()

        for rec in records:
            student = lm.find_student(rec["roll_number"])
            student_name = student["name"] if student else "Unknown"
            book_id_val = rec.get("book_id", "B101")

            if query:
                match = (
                    query in rec["roll_number"].lower()
                    or query in student_name.lower()
                    or query in book_id_val.lower()
                    or query in rec["book_name"].lower()
                )
                if not match:
                    continue

            if rec["if_returned"] == "YES":
                status_display = "● Returned"
                tag = "returned"
            else:
                status_display = "● Active"
                tag = "active"

            self.records_tree.insert(
                "",
                tk.END,
                values=(
                    rec["roll_number"],
                    student_name,
                    book_id_val,
                    rec["book_name"],
                    rec["issue_date"],
                    rec["return_date"],
                    status_display,
                ),
                tags=(tag,),
            )

    def filter_records(self):
        self.refresh_records_table()

    def clear_records_search(self):
        self.records_search_entry.delete(0, tk.END)
        self.refresh_records_table()

    def build_status_bar(self):
        self.status_bar = tk.Frame(self.main_container, bg="#12141e", height=28, padx=15)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_msg = tk.Label(
            self.status_bar,
            text="Ready",
            font=("Segoe UI", 9),
            bg="#12141e",
            fg=COLOR_TEXT_MUTED,
        )
        self.status_msg.pack(side=tk.LEFT, pady=4)

    def refresh_all_data(self):
        self.refresh_books_table()
        self.refresh_students_table()
        self.refresh_issue_desk()
        self.refresh_records_table()
        self.status_msg.config(text=f"All tables refreshed at {datetime.now().strftime('%H:%M:%S')}")

    def create_entry(self, parent, width=20):
        entry = tk.Entry(
            parent,
            font=("Segoe UI", 10),
            bg=COLOR_INPUT_BG,
            fg=COLOR_TEXT,
            insertbackground="#ffffff",
            relief=tk.SOLID,
            bd=1,
            highlightthickness=1,
            highlightcolor=COLOR_PRIMARY,
            highlightbackground=COLOR_INPUT_BORDER,
            width=width,
        )
        return entry

    def create_btn(self, parent, text, bg, hover_bg, command):
        btn = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 9, "bold"),
            bg=bg,
            fg="#ffffff",
            activebackground=hover_bg,
            activeforeground="#ffffff",
            bd=0,
            padx=12,
            pady=4,
            cursor="hand2",
            command=command,
        )
        self.add_hover_effect(btn, bg, hover_bg)
        return btn

    def create_symbol_btn(self, parent, symbol, tooltip_text, command):
        btn = tk.Button(
            parent,
            text=symbol,
            font=("Segoe UI Emoji", 10, "bold"),
            bg="#293042",
            fg="#cbd5e1",
            activebackground=COLOR_PRIMARY,
            activeforeground="#ffffff",
            bd=0,
            padx=8,
            pady=3,
            cursor="hand2",
            command=command,
        )
        self.add_hover_effect(btn, "#293042", COLOR_PRIMARY)
        if tooltip_text:
            Tooltip(btn, tooltip_text)
        return btn

    def add_hover_effect(self, widget, normal_bg, hover_bg):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg))


if __name__ == "__main__":
    app = LibraryApp()
    app.mainloop()
