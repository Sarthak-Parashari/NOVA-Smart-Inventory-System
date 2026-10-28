import math
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

import database
import mysql.connector
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter


COLORS = {
    "navy": "#14243A",
    "navy_light": "#203650",
    "blue": "#315E9E",
    "blue_light": "#EAF1FB",
    "teal": "#168C88",
    "green": "#25856A",
    "amber": "#D58A24",
    "red": "#C74B50",
    "ink": "#1E293B",
    "muted": "#68778A",
    "line": "#E2E8F0",
    "canvas": "#F3F6FA",
    "white": "#FFFFFF",
}


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            self,
            background=COLORS["canvas"],
            borderwidth=0,
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.body = tk.Frame(self.canvas, background=COLORS["canvas"])
        self.window_id = self.canvas.create_window(
            (0, 0),
            window=self.body,
            anchor="nw",
        )
        self.body.bind("<Configure>", self._update_scroll_region)
        self.canvas.bind("<Configure>", self._resize_body)
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _update_scroll_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_body(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _bind_mousewheel(self, _event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event=None):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), "units")


class InventoryApp:
    PRODUCT_COLUMNS = (
        "ID",
        "Product",
        "Category",
        "Purchase Price",
        "Selling Price",
        "Stock",
        "Reorder Level",
    )

    HISTORY_COLUMNS = (
        "Sale ID",
        "Date",
        "Customer",
        "Product",
        "Quantity",
        "Unit Price",
        "Revenue",
        "Est. Profit",
    )

    def __init__(self, root):
        self.root = root
        self.root.title("NOVA | Smart Inventory")
        self.root.configure(background=COLORS["canvas"])
        self.root.minsize(560, 480)
        self._center_window()
        self._configure_styles()

        self.current_page = "dashboard"
        self.nav_buttons = {}
        self.pages = {}
        self.page_bodies = {}
        self.analytics_figure = None
        self.analytics_axes = []
        self.analytics_canvas = None

        self._build_shell()
        self._build_dashboard_page()
        self._build_products_page()
        self._build_add_product_page()
        self._build_sale_page()
        self._build_history_page()
        self._build_report_page()
        self._build_analytics_page()
        self.show_page("dashboard")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _center_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = max(400, min(1440, screen_width - 48))
        height = max(420, min(940, screen_height - 72))
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.resizable(True, True)
        self.root.minsize(min(width, 760), min(height, 620))

    def _configure_styles(self):
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure(
            "TFrame",
            background=COLORS["canvas"],
        )
        style.configure(
            "TLabel",
            background=COLORS["canvas"],
            foreground=COLORS["ink"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "PageTitle.TLabel",
            font=("Segoe UI", 22, "bold"),
            foreground=COLORS["ink"],
        )
        style.configure(
            "PageSubtitle.TLabel",
            font=("Segoe UI", 10),
            foreground=COLORS["muted"],
        )
        style.configure(
            "Panel.TLabelframe",
            background=COLORS["white"],
            bordercolor=COLORS["line"],
            relief="solid",
        )
        style.configure(
            "Panel.TLabelframe.Label",
            background=COLORS["white"],
            foreground=COLORS["ink"],
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
        )
        style.configure(
            "Accent.TButton",
            background=COLORS["blue"],
            foreground=COLORS["white"],
            borderwidth=0,
        )
        style.map(
            "Accent.TButton",
            background=[("active", COLORS["navy_light"])],
            foreground=[("active", COLORS["white"])],
        )
        style.configure(
            "Danger.TButton",
            background=COLORS["red"],
            foreground=COLORS["white"],
            borderwidth=0,
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#A83B40")],
        )
        style.configure(
            "Treeview",
            background=COLORS["white"],
            fieldbackground=COLORS["white"],
            foreground=COLORS["ink"],
            rowheight=30,
            bordercolor=COLORS["line"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            background="#EAF0F6",
            foreground=COLORS["navy"],
            font=("Segoe UI", 9, "bold"),
            padding=(8, 9),
        )
        style.map(
            "Treeview",
            background=[("selected", COLORS["blue"])],
            foreground=[("selected", COLORS["white"])],
        )
        style.configure(
            "TEntry",
            padding=7,
            fieldbackground=COLORS["white"],
        )

    def _build_shell(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        sidebar = tk.Frame(self.root, background=COLORS["navy"], width=218)
        sidebar.grid(row=0, column=0, rowspan=2, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)

        brand = tk.Frame(sidebar, background=COLORS["navy"])
        brand.grid(row=0, column=0, sticky="ew", padx=20, pady=(25, 24))
        tk.Label(
            brand,
            text="NOVA",
            background=COLORS["navy"],
            foreground=COLORS["white"],
            font=("Segoe UI", 23, "bold"),
        ).pack(anchor="w")
        tk.Label(
            brand,
            text="SMART INVENTORY",
            background=COLORS["navy"],
            foreground="#AAB9CA",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", pady=(2, 0))

        navigation = (
            ("dashboard", "Dashboard"),
            ("products", "Products"),
            ("add_product", "Add Product"),
            ("sale", "Record Sale"),
            ("history", "Sales History"),
            ("report", "Revenue & Profit"),
            ("analytics", "Analytics"),
        )
        for index, (page, label) in enumerate(navigation, start=1):
            button = tk.Button(
                sidebar,
                text=f"  {label}",
                anchor="w",
                relief="flat",
                borderwidth=0,
                padx=15,
                pady=11,
                cursor="hand2",
                background=COLORS["navy"],
                foreground="#D4DDE8",
                activebackground=COLORS["navy_light"],
                activeforeground=COLORS["white"],
                font=("Segoe UI", 10, "bold"),
                command=lambda selected=page: self.show_page(selected),
            )
            button.grid(row=index, column=0, sticky="ew", padx=10, pady=2)
            button.bind(
                "<Enter>",
                lambda _event, selected=page: self._hover_nav(selected, True),
            )
            button.bind(
                "<Leave>",
                lambda _event, selected=page: self._hover_nav(selected, False),
            )
            self.nav_buttons[page] = button

        sidebar.grid_rowconfigure(9, weight=1)
        ttk.Separator(sidebar).grid(
            row=10,
            column=0,
            sticky="ew",
            padx=18,
            pady=(10, 12),
        )
        refresh_button = tk.Button(
            sidebar,
            text="  Refresh Data",
            anchor="w",
            relief="flat",
            borderwidth=0,
            padx=15,
            pady=11,
            cursor="hand2",
            background=COLORS["navy"],
            foreground="#D4DDE8",
            activebackground=COLORS["navy_light"],
            activeforeground=COLORS["white"],
            font=("Segoe UI", 10, "bold"),
            command=self.refresh_data,
        )
        refresh_button.grid(row=11, column=0, sticky="ew", padx=10, pady=2)
        refresh_button.bind(
            "<Enter>",
            lambda _event: refresh_button.configure(
                background=COLORS["navy_light"]
            ),
        )
        refresh_button.bind(
            "<Leave>",
            lambda _event: refresh_button.configure(
                background=COLORS["navy"]
            ),
        )

        exit_button = tk.Button(
            sidebar,
            text="  Exit Application",
            anchor="w",
            relief="flat",
            borderwidth=0,
            padx=15,
            pady=11,
            cursor="hand2",
            background=COLORS["navy"],
            foreground="#D4DDE8",
            activebackground=COLORS["navy_light"],
            activeforeground=COLORS["white"],
            font=("Segoe UI", 10, "bold"),
            command=self.close,
        )
        exit_button.grid(row=12, column=0, sticky="ew", padx=10, pady=(2, 20))

        header = tk.Frame(
            self.root,
            background=COLORS["white"],
            highlightbackground=COLORS["line"],
            highlightthickness=1,
        )
        header.grid(row=0, column=1, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        tk.Label(
            header,
            text="Inventory Intelligence",
            background=COLORS["white"],
            foreground=COLORS["navy"],
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(12, 0))
        tk.Label(
            header,
            text="Smart Inventory Management System",
            background=COLORS["white"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 12))
        self.date_label = tk.Label(
            header,
            text=date.today().strftime("%A, %d %B %Y"),
            background=COLORS["white"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 9, "bold"),
        )
        self.date_label.grid(row=0, column=1, rowspan=2, padx=24)

        self.pages_host = ttk.Frame(self.root)
        self.pages_host.grid(row=1, column=1, sticky="nsew")
        self.pages_host.grid_rowconfigure(0, weight=1)
        self.pages_host.grid_columnconfigure(0, weight=1)

        self.status_label = tk.Label(
            self.root,
            text="Ready",
            anchor="w",
            background=COLORS["canvas"],
            foreground=COLORS["muted"],
            font=("Segoe UI", 8),
        )
        self.status_label.grid(row=2, column=1, sticky="ew", padx=20, pady=4)

    def _hover_nav(self, page, hovering):
        button = self.nav_buttons[page]
        if page == self.current_page:
            button.configure(background=COLORS["blue"])
        else:
            button.configure(
                background=COLORS["navy_light"] if hovering else COLORS["navy"]
            )

    def _new_page(self, page, title, subtitle):
        scroll = ScrollableFrame(self.pages_host)
        scroll.grid(row=0, column=0, sticky="nsew")
        body = scroll.body
        body.configure(padx=24, pady=20)
        body.grid_columnconfigure(0, weight=1)
        ttk.Label(body, text=title, style="PageTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(body, text=subtitle, style="PageSubtitle.TLabel").grid(
            row=1, column=0, sticky="w", pady=(4, 18)
        )
        self.pages[page] = scroll
        self.page_bodies[page] = body
        return body

    def _panel(self, parent, title, **grid_options):
        panel = ttk.LabelFrame(
            parent,
            text=title,
            style="Panel.TLabelframe",
            padding=14,
        )
        panel.grid(**grid_options)
        return panel

    def _create_tree(self, parent, columns, headings, widths, height=10):
        wrapper = ttk.Frame(parent)
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(0, weight=1)
        tree = ttk.Treeview(
            wrapper,
            columns=columns,
            show="headings",
            height=height,
        )
        for column, heading, width in zip(columns, headings, widths):
            tree.heading(column, text=heading)
            tree.column(
                column,
                width=width,
                minwidth=65,
                anchor="w" if column in ("Product", "Customer", "Category") else "center",
                stretch=True,
            )
        tree.grid(row=0, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(
            wrapper,
            orient="vertical",
            command=tree.yview,
        )
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(
            wrapper,
            orient="horizontal",
            command=tree.xview,
        )
        horizontal.grid(row=1, column=0, sticky="ew")
        tree.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set,
        )
        tree.tag_configure("even", background=COLORS["white"])
        tree.tag_configure("odd", background="#F7F9FC")
        tree.tag_configure(
            "low_stock",
            background="#FFF1EE",
            foreground="#9F3338",
        )
        return wrapper, tree

    def _build_dashboard_page(self):
        body = self._new_page(
            "dashboard",
            "Dashboard",
            "A live overview of your inventory and sales performance.",
        )
        cards_frame = tk.Frame(body, background=COLORS["canvas"])
        cards_frame.grid(row=2, column=0, sticky="ew", pady=(0, 18))
        for column in range(3):
            cards_frame.grid_columnconfigure(column, weight=1, uniform="kpi")

        self.kpi_values = {}
        kpis = (
            ("Total Products", "products", COLORS["blue"]),
            ("Total Stock Units", "stock", COLORS["teal"]),
            ("Sales Transactions", "transactions", COLORS["amber"]),
            ("Total Revenue", "revenue", COLORS["green"]),
            ("Est. Gross Profit", "profit", COLORS["blue"]),
            ("Low-Stock Products", "low_stock", COLORS["red"]),
        )
        for index, (label, key, accent) in enumerate(kpis):
            card = tk.Frame(
                cards_frame,
                background=COLORS["white"],
                highlightbackground=COLORS["line"],
                highlightthickness=1,
                padx=16,
                pady=14,
            )
            card.grid(
                row=index // 3,
                column=index % 3,
                sticky="ew",
                padx=6,
                pady=6,
            )
            tk.Frame(card, background=accent, height=3).pack(
                fill="x",
                pady=(0, 11),
            )
            tk.Label(
                card,
                text=label.upper(),
                background=COLORS["white"],
                foreground=COLORS["muted"],
                font=("Segoe UI", 8, "bold"),
            ).pack(anchor="w")
            value = tk.Label(
                card,
                text="—",
                background=COLORS["white"],
                foreground=COLORS["ink"],
                font=("Segoe UI", 21, "bold"),
            )
            value.pack(anchor="w", pady=(5, 0))
            self.kpi_values[key] = value

        body.grid_columnconfigure(0, weight=1)
        for column in range(3):
            cards_frame.grid_columnconfigure(column, weight=1)

        lower = tk.Frame(body, background=COLORS["canvas"])
        lower.grid(row=3, column=0, sticky="nsew")
        lower.grid_columnconfigure(0, weight=2)
        lower.grid_columnconfigure(1, weight=1)

        low_panel = self._panel(
            lower,
            "Low-Stock Watchlist",
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 7),
        )
        low_panel.grid_columnconfigure(0, weight=1)
        low_panel.grid_rowconfigure(0, weight=1)
        wrapper, self.dashboard_low_tree = self._create_tree(
            low_panel,
            ("Product", "Category", "Stock", "Reorder"),
            ("Product", "Category", "In Stock", "Reorder At"),
            (220, 150, 90, 105),
            height=8,
        )
        wrapper.grid(row=0, column=0, sticky="nsew")
        self.dashboard_low_empty = ttk.Label(
            low_panel,
            text="No low-stock products.",
            foreground=COLORS["muted"],
        )
        self.dashboard_low_empty.grid(row=1, column=0, sticky="w", pady=(8, 0))

        summary_panel = self._panel(
            lower,
            "Sales Snapshot",
            row=0,
            column=1,
            sticky="nsew",
            padx=(7, 0),
        )
        summary_panel.grid_columnconfigure(0, weight=1)
        ttk.Label(
            summary_panel,
            text="Revenue is the total value of recorded sales. Estimated gross profit is calculated from the selling and purchase prices stored on each sale item.",
            wraplength=300,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 16))
        ttk.Button(
            summary_panel,
            text="Open Analytics",
            style="Accent.TButton",
            command=self.show_sales_analytics,
        ).grid(row=1, column=0, sticky="w")
        ttk.Button(
            summary_panel,
            text="Revenue & Profit Report",
            command=self.show_profit_report,
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))

    def _build_products_page(self):
        body = self._new_page(
            "products",
            "Product Management",
            "Search, review, select, update, and remove inventory products.",
        )
        toolbar = tk.Frame(body, background=COLORS["canvas"])
        toolbar.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        toolbar.grid_columnconfigure(1, weight=1)
        ttk.Label(toolbar, text="Search products").grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        search_entry.bind("<Return>", lambda _event: self.search_products())
        ttk.Button(
            toolbar,
            text="Search",
            style="Accent.TButton",
            command=self.search_products,
        ).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(
            toolbar,
            text="Show All",
            command=self.show_all_products,
        ).grid(row=0, column=3)

        table_panel = self._panel(
            body,
            "Inventory",
            row=3,
            column=0,
            sticky="nsew",
        )
        table_panel.grid_columnconfigure(0, weight=1)
        table_panel.grid_rowconfigure(0, weight=1)
        wrapper, self.product_tree = self._create_tree(
            table_panel,
            self.PRODUCT_COLUMNS,
            self.PRODUCT_COLUMNS,
            (65, 220, 140, 130, 130, 95, 125),
            height=10,
        )
        wrapper.grid(row=0, column=0, sticky="nsew")
        self.product_tree.bind(
            "<<TreeviewSelect>>",
            self._fill_edit_form,
        )
        self.product_empty = ttk.Label(
            table_panel,
            text="No products found. Add a product to begin.",
            foreground=COLORS["muted"],
        )
        self.product_empty.grid(row=1, column=0, sticky="w", pady=(8, 0))

        form_panel = self._panel(
            body,
            "Selected Product Details",
            row=4,
            column=0,
            sticky="ew",
            pady=(14, 0),
        )
        self.edit_entries = self._create_product_fields(form_panel)
        action_row = 3
        ttk.Button(
            form_panel,
            text="Save Changes",
            style="Accent.TButton",
            command=self.update_product,
        ).grid(row=action_row, column=0, sticky="w", pady=(12, 0))
        ttk.Button(
            form_panel,
            text="Delete Selected",
            style="Danger.TButton",
            command=self.delete_product,
        ).grid(row=action_row, column=1, sticky="w", padx=(10, 0), pady=(12, 0))
        ttk.Button(
            form_panel,
            text="Clear Form",
            command=self._clear_form(self.edit_entries),
        ).grid(row=action_row, column=2, sticky="w", padx=(10, 0), pady=(12, 0))

    def _create_product_fields(self, parent):
        labels = (
            "Product Name",
            "Category",
            "Purchase Price",
            "Selling Price",
            "Stock Quantity",
            "Reorder Level",
        )
        entries = {}
        for index, label in enumerate(labels):
            row = index // 3
            column = (index % 3) * 2
            ttk.Label(parent, text=label).grid(
                row=row,
                column=column,
                sticky="w",
                padx=(0, 8),
                pady=6,
            )
            entry = ttk.Entry(parent)
            entry.grid(
                row=row,
                column=column + 1,
                sticky="ew",
                padx=(0, 14),
                pady=6,
            )
            entries[label] = entry
            parent.grid_columnconfigure(column + 1, weight=1)
        return entries

    def _build_add_product_page(self):
        body = self._new_page(
            "add_product",
            "Add Product",
            "Create a product record using the existing inventory fields.",
        )
        panel = self._panel(
            body,
            "Product Information",
            row=2,
            column=0,
            sticky="ew",
        )
        self.add_entries = self._create_product_fields(panel)
        ttk.Label(
            panel,
            text="Enter prices and quantities as numbers. Reorder level defaults to 10 when left blank.",
            style="PageSubtitle.TLabel",
        ).grid(row=2, column=0, columnspan=6, sticky="w", pady=(12, 4))
        ttk.Button(
            panel,
            text="Add Product",
            style="Accent.TButton",
            command=self.add_product,
        ).grid(row=3, column=0, sticky="w", pady=(10, 0))
        ttk.Button(
            panel,
            text="Clear Form",
            command=self._clear_form(self.add_entries),
        ).grid(row=3, column=1, sticky="w", padx=(10, 0), pady=(10, 0))
        ttk.Button(
            panel,
            text="View Products",
            command=lambda: self.show_page("products"),
        ).grid(row=3, column=2, sticky="w", padx=(10, 0), pady=(10, 0))

    def _build_sale_page(self):
        body = self._new_page(
            "sale",
            "Record a Sale",
            "Record a sale and deduct stock within one database transaction.",
        )
        panel = self._panel(
            body,
            "Sale Details",
            row=2,
            column=0,
            sticky="ew",
        )
        panel.grid_columnconfigure(1, weight=1)
        fields = (
            ("Product ID", "sale_product_id"),
            ("Customer Name", "sale_customer"),
            ("Quantity", "sale_quantity"),
        )
        self.sale_entries = {}
        for row, (label, key) in enumerate(fields):
            ttk.Label(panel, text=label).grid(
                row=row,
                column=0,
                sticky="w",
                padx=(0, 18),
                pady=8,
            )
            entry = ttk.Entry(panel)
            entry.grid(row=row, column=1, sticky="ew", pady=8)
            self.sale_entries[key] = entry
        ttk.Label(
            panel,
            text="Product ID must refer to an existing product. Quantity must be a positive whole number and cannot exceed current stock. Leave customer blank for a walk-in sale.",
            style="PageSubtitle.TLabel",
            wraplength=650,
            justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 14))
        ttk.Button(
            panel,
            text="Record Sale",
            style="Accent.TButton",
            command=self.record_sale,
        ).grid(row=4, column=0, sticky="w")

    def _build_history_page(self):
        body = self._new_page(
            "history",
            "Sales History",
            "Recorded sales with unit prices, revenue, and estimated gross profit.",
        )
        panel = self._panel(
            body,
            "Sales Line Items",
            row=2,
            column=0,
            sticky="nsew",
        )
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=1)
        wrapper, self.history_tree = self._create_tree(
            panel,
            self.HISTORY_COLUMNS,
            self.HISTORY_COLUMNS,
            (80, 150, 160, 210, 90, 125, 135, 135),
            height=16,
        )
        wrapper.grid(row=0, column=0, sticky="nsew")
        self.history_empty = ttk.Label(
            panel,
            text="No sales records found.",
            foreground=COLORS["muted"],
        )
        self.history_empty.grid(row=1, column=0, sticky="w", pady=(8, 0))

    def _build_report_page(self):
        body = self._new_page(
            "report",
            "Revenue & Profit",
            "Revenue and estimated gross profit are shown as separate measures.",
        )
        cards = tk.Frame(body, background=COLORS["canvas"])
        cards.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        for column in range(3):
            cards.grid_columnconfigure(column, weight=1, uniform="report")
        self.report_values = {}
        for index, (key, label, accent) in enumerate(
            (
                ("transactions", "TOTAL TRANSACTIONS", COLORS["blue"]),
                ("revenue", "TOTAL REVENUE", COLORS["green"]),
                ("profit", "ESTIMATED GROSS PROFIT", COLORS["teal"]),
            )
        ):
            card = tk.Frame(
                cards,
                background=COLORS["white"],
                highlightbackground=COLORS["line"],
                highlightthickness=1,
                padx=16,
                pady=14,
            )
            card.grid(row=0, column=index, sticky="ew", padx=6)
            tk.Label(
                card,
                text=label,
                background=COLORS["white"],
                foreground=COLORS["muted"],
                font=("Segoe UI", 8, "bold"),
            ).pack(anchor="w")
            value = tk.Label(
                card,
                text="—",
                background=COLORS["white"],
                foreground=accent,
                font=("Segoe UI", 20, "bold"),
            )
            value.pack(anchor="w", pady=(6, 0))
            self.report_values[key] = value

        panel = self._panel(
            body,
            "Monthly Summary",
            row=3,
            column=0,
            sticky="nsew",
        )
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=1)
        wrapper, self.report_tree = self._create_tree(
            panel,
            ("Month", "Revenue", "Estimated Profit"),
            ("Month", "Revenue", "Estimated Gross Profit"),
            (180, 220, 250),
            height=12,
        )
        wrapper.grid(row=0, column=0, sticky="nsew")
        self.report_empty = ttk.Label(
            panel,
            text="No sales records to report.",
            foreground=COLORS["muted"],
        )
        self.report_empty.grid(row=1, column=0, sticky="w", pady=(8, 0))

    def _build_analytics_page(self):
        body = self._new_page(
            "analytics",
            "Analytics Dashboard",
            "All charts are calculated from current MySQL inventory and sales records.",
        )
        panel = self._panel(
            body,
            "Inventory & Sales Analytics",
            row=2,
            column=0,
            sticky="nsew",
        )
        panel.grid_columnconfigure(0, weight=1)

        self.analytics_figure = Figure(
            figsize=(5.5, 8.5),
            dpi=100,
            facecolor=COLORS["white"],
        )
        self.analytics_axes = [
            self.analytics_figure.add_subplot(3, 2, index)
            for index in range(1, 7)
        ]
        self.analytics_canvas = FigureCanvasTkAgg(
            self.analytics_figure,
            master=panel,
        )
        chart_widget = self.analytics_canvas.get_tk_widget()
        chart_widget.grid(row=0, column=0, sticky="ew")
        chart_widget.bind("<Configure>", self._resize_analytics_figure)
        panel.grid_rowconfigure(0, weight=1)

    def _resize_analytics_figure(self, event):
        if not self.analytics_figure or event.width < 100:
            return
        width_inches = max(5.0, event.width / self.analytics_figure.dpi)
        height_inches = max(8.5, width_inches * 0.86)
        self.analytics_figure.set_size_inches(
            width_inches,
            height_inches,
            forward=False,
        )
        self.analytics_canvas.draw_idle()

    def _format_currency(self, value):
        return f"₹{float(value or 0):,.2f}"

    def _set_status(self, text):
        self.status_label.configure(text=text)

    def _handle_database_error(self, error):
        self._set_status("Database unavailable")
        messagebox.showerror(
            "Database Error",
            f"{error}",
            parent=self.root,
        )

    def show_page(self, page):
        if page not in self.pages:
            return
        self.current_page = page
        self.pages[page].tkraise()
        for name, button in self.nav_buttons.items():
            active = name == page
            button.configure(
                background=COLORS["blue"] if active else COLORS["navy"],
                foreground=COLORS["white"] if active else "#D4DDE8",
            )
        self._set_status(f"{page.replace('_', ' ').title()} · Ready")

        if page == "dashboard":
            self.load_dashboard()
        elif page == "products":
            self.load_products()
        elif page == "history":
            self.load_sales_history()
        elif page == "report":
            self.load_profit_report()
        elif page == "analytics":
            self.load_analytics()

    def refresh_data(self):
        self.load_dashboard()
        if self.current_page == "products":
            self.load_products()
        elif self.current_page == "history":
            self.load_sales_history()
        elif self.current_page == "report":
            self.load_profit_report()
        elif self.current_page == "analytics":
            self.load_analytics()
        self._set_status("Data refreshed")

    def load_dashboard(self):
        try:
            data = database.get_dashboard_data()
            metrics = data["metrics"]
            low_stock_rows = data["low_stock_products"]
            values = {
                "products": f"{int(metrics['total_products']):,}",
                "stock": f"{int(metrics['total_stock_units']):,}",
                "transactions": f"{int(metrics['total_sales_transactions']):,}",
                "revenue": self._format_currency(metrics["total_revenue"]),
                "profit": self._format_currency(
                    metrics["estimated_gross_profit"]
                ),
                "low_stock": f"{int(metrics['low_stock_product_count']):,}",
            }
            for key, value in values.items():
                self.kpi_values[key].configure(text=value)

            self._populate_tree(self.dashboard_low_tree, low_stock_rows, True)
            if low_stock_rows:
                self.dashboard_low_empty.grid_remove()
            else:
                self.dashboard_low_empty.grid()
            self._set_status("Dashboard updated from MySQL")

        except (
            mysql.connector.Error,
            RuntimeError,
            database.DatabaseOperationError,
        ) as error:
            self._handle_database_error(error)

    def _populate_tree(self, tree, rows, low_stock=False):
        tree.delete(*tree.get_children())
        for index, row in enumerate(rows):
            values = tuple("" if value is None else value for value in row)
            tags = ["even" if index % 2 == 0 else "odd"]
            if low_stock:
                tags.append("low_stock")
            tree.insert("", tk.END, values=values, tags=tuple(tags))

    def _product_query(self, keyword=""):
        return (
            database.search_products(keyword)
            if keyword
            else database.get_all_products()
        )

    def load_products(self, keyword=None):
        if keyword is None:
            keyword = self.search_var.get().strip()
        try:
            rows = self._product_query(keyword)
            self._populate_tree(self.product_tree, rows)
            if rows:
                self.product_empty.grid_remove()
            else:
                self.product_empty.grid()
            self._set_status(f"{len(rows):,} product(s) loaded")
        except (
            mysql.connector.Error,
            RuntimeError,
            database.DatabaseOperationError,
        ) as error:
            self._handle_database_error(error)

    def search_products(self):
        self.load_products(self.search_var.get().strip())

    def show_all_products(self):
        self.search_var.set("")
        self.load_products("")

    def _read_product_form(self, entries):
        name = entries["Product Name"].get().strip()
        category = entries["Category"].get().strip()
        purchase_text = entries["Purchase Price"].get().strip()
        selling_text = entries["Selling Price"].get().strip()
        quantity_text = entries["Stock Quantity"].get().strip()
        reorder_text = entries["Reorder Level"].get().strip()
        if not name or not purchase_text or not selling_text or not quantity_text:
            raise ValueError(
                "Product name, purchase price, selling price, and stock quantity are required."
            )

        purchase_price = float(purchase_text)
        selling_price = float(selling_text)
        quantity = int(quantity_text)
        reorder = int(reorder_text) if reorder_text else 10

        if not math.isfinite(purchase_price) or not math.isfinite(selling_price):
            raise ValueError("Prices must be finite numbers.")
        if purchase_price < 0 or selling_price < 0:
            raise ValueError("Prices cannot be negative.")
        if quantity < 0 or reorder < 0:
            raise ValueError("Stock quantity and reorder level cannot be negative.")
        return name, category or None, purchase_price, selling_price, quantity, reorder

    def _clear_form(self, entries):
        def clear():
            for entry in entries.values():
                entry.delete(0, tk.END)
        return clear

    def add_product(self):
        try:
            product = self._read_product_form(self.add_entries)
        except ValueError as error:
            messagebox.showerror("Invalid Product", str(error), parent=self.root)
            return

        try:
            database.add_product(*product)
            self._clear_form(self.add_entries)()
            messagebox.showinfo(
                "Product Added",
                f"'{product[0]}' was added successfully.",
                parent=self.root,
            )
            self.load_dashboard()
            self.load_products("")
        except ValueError as error:
            messagebox.showerror("Invalid Product", str(error), parent=self.root)
        except (mysql.connector.Error, RuntimeError) as error:
            self._handle_database_error(error)

    def _fill_edit_form(self, _event=None):
        selected = self.product_tree.selection()
        if not selected:
            return
        values = self.product_tree.item(selected[0], "values")
        fields = (
            "Product Name",
            "Category",
            "Purchase Price",
            "Selling Price",
            "Stock Quantity",
            "Reorder Level",
        )
        for field, value in zip(fields, values[1:]):
            entry = self.edit_entries[field]
            entry.delete(0, tk.END)
            entry.insert(0, str(value))

    def update_product(self):
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showwarning(
                "Select Product",
                "Select a product from the inventory table first.",
                parent=self.root,
            )
            return
        product_id = self.product_tree.item(selected[0], "values")[0]
        try:
            product = self._read_product_form(self.edit_entries)
        except ValueError as error:
            messagebox.showerror("Invalid Product", str(error), parent=self.root)
            return

        try:
            database.update_product(product_id, *product)
            messagebox.showinfo(
                "Product Updated",
                "Product details were updated.",
                parent=self.root,
            )
            self.load_products("")
            self.load_dashboard()
        except (ValueError, database.DatabaseOperationError) as error:
            messagebox.showerror("Product Update Failed", str(error), parent=self.root)
        except (mysql.connector.Error, RuntimeError) as error:
            self._handle_database_error(error)

    def delete_product(self):
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showwarning(
                "Select Product",
                "Select a product from the inventory table first.",
                parent=self.root,
            )
            return
        values = self.product_tree.item(selected[0], "values")
        product_id, product_name = values[0], values[1]
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete '{product_name}'?",
            parent=self.root,
        ):
            return

        try:
            database.delete_product(product_id)
            self.load_products("")
            self.load_dashboard()
            messagebox.showinfo(
                "Product Deleted",
                "Product was deleted successfully.",
                parent=self.root,
            )
        except database.DatabaseOperationError as error:
            messagebox.showerror(
                "Product Not Found",
                str(error),
                parent=self.root,
            )
        except (mysql.connector.Error, RuntimeError) as error:
            messagebox.showerror(
                "Cannot Delete Product",
                "The product may be referenced by existing sales or purchases.\n\n"
                f"{error}",
                parent=self.root,
            )

    def record_sale(self):
        product_id_text = self.sale_entries["sale_product_id"].get().strip()
        customer_name = (
            self.sale_entries["sale_customer"].get().strip()
            or "Walk-in Customer"
        )
        quantity_text = self.sale_entries["sale_quantity"].get().strip()

        try:
            if not product_id_text or not quantity_text:
                raise ValueError("Product ID and quantity are required.")
            product_id = int(product_id_text)
            quantity = int(quantity_text)
            if product_id <= 0 or quantity <= 0:
                raise ValueError("Product ID and quantity must be positive integers.")
        except ValueError as error:
            messagebox.showerror("Invalid Sale", str(error), parent=self.root)
            return

        try:
            result = database.record_sale(product_id, quantity, customer_name)
            messagebox.showinfo(
                "Sale Successful",
                f"Sale ID: {result['sale_id']}\n"
                f"Product: {result['product_name']}\n"
                f"Quantity: {result['quantity']}\n"
                f"Total Revenue: {self._format_currency(result['total_amount'])}\n"
                f"Estimated Gross Profit: "
                f"{self._format_currency(result['estimated_gross_profit'])}",
                parent=self.root,
            )
            for entry in self.sale_entries.values():
                entry.delete(0, tk.END)
            self.load_dashboard()
            self.load_products("")
            if self.current_page == "history":
                self.load_sales_history()
        except database.ProductNotFoundError as error:
            messagebox.showerror(
                "Product Not Found",
                str(error),
                parent=self.root,
            )
        except database.InsufficientStockError as error:
            messagebox.showwarning(
                "Insufficient Stock",
                str(error),
                parent=self.root,
            )
        except ValueError as error:
            messagebox.showerror("Invalid Sale", str(error), parent=self.root)
        except (mysql.connector.Error, RuntimeError) as error:
            self._handle_database_error(error)

    def load_sales_history(self):
        try:
            records = database.get_sales_history()
            formatted = [
                (
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    self._format_currency(row[5]),
                    self._format_currency(row[6]),
                    self._format_currency(row[7]),
                )
                for row in records
            ]
            self._populate_tree(self.history_tree, formatted)
            if records:
                self.history_empty.grid_remove()
            else:
                self.history_empty.grid()
            self._set_status(f"{len(records):,} sales line item(s) loaded")
        except (mysql.connector.Error, RuntimeError) as error:
            self._handle_database_error(error)

    def show_sales_history(self):
        self.show_page("history")

    def load_profit_report(self):
        try:
            report = database.get_revenue_report()
            summary = report["summary"]
            self.report_values["transactions"].configure(
                text=f"{int(summary['total_sales_transactions']):,}"
            )
            self.report_values["revenue"].configure(
                text=self._format_currency(summary["total_revenue"])
            )
            self.report_values["profit"].configure(
                text=self._format_currency(
                    summary["estimated_gross_profit"]
                )
            )

            monthly_rows = report["monthly_totals"]
            monthly_rows = list(reversed(monthly_rows))
            formatted = [
                (
                    row[0],
                    self._format_currency(row[1]),
                    self._format_currency(row[2]),
                )
                for row in monthly_rows
            ]
            self._populate_tree(self.report_tree, formatted)
            if monthly_rows:
                self.report_empty.grid_remove()
            else:
                self.report_empty.grid()
            self._set_status("Revenue and estimated profit report updated")
        except (mysql.connector.Error, RuntimeError) as error:
            self._handle_database_error(error)

    def show_profit_report(self):
        self.show_page("report")

    def _fetch_analytics_data(self):
        data = database.get_analytics_data()
        return (
            data["monthly"],
            data["best_sellers"],
            data["category_stock"],
            data["low_stock"],
        )

    def _style_axis(self, axis, title):
        axis.set_title(title, loc="left", fontsize=11, fontweight="bold", pad=12)
        axis.set_facecolor(COLORS["white"])
        axis.grid(axis="y", color=COLORS["line"], linewidth=0.8)
        axis.set_axisbelow(True)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_color(COLORS["line"])
        axis.spines["bottom"].set_color(COLORS["line"])
        axis.tick_params(colors=COLORS["muted"], labelsize=8)

    def _empty_chart(self, axis, message):
        axis.text(
            0.5,
            0.5,
            message,
            ha="center",
            va="center",
            transform=axis.transAxes,
            color=COLORS["muted"],
            fontsize=10,
        )
        axis.set_xticks([])
        axis.set_yticks([])

    def _render_analytics(self, data):
        monthly, best_sellers, category_stock, low_stock = data
        for axis in self.analytics_axes:
            axis.clear()
            axis.set_facecolor(COLORS["white"])

        revenue_axis, profit_axis, products_axis, category_axis, low_axis, comparison_axis = (
            self.analytics_axes
        )
        self._style_axis(revenue_axis, "Monthly Revenue Trend")
        self._style_axis(profit_axis, "Monthly Estimated Profit Trend")
        self._style_axis(products_axis, "Best-Selling Products · Units Sold")
        self._style_axis(category_axis, "Stock Distribution by Category")
        self._style_axis(low_axis, "Low-Stock Products · Reorder Alert")
        self._style_axis(comparison_axis, "Monthly Revenue vs Estimated Profit")

        months = [str(row[0]) for row in monthly]
        revenues = [float(row[1] or 0) for row in monthly]
        profits = [float(row[2] or 0) for row in monthly]
        currency = FuncFormatter(lambda value, _position: f"₹{value:,.0f}")

        if months:
            revenue_axis.plot(
                months,
                revenues,
                color=COLORS["blue"],
                marker="o",
                linewidth=2.5,
                markersize=5,
            )
            revenue_axis.set_ylabel("Revenue (₹)")
            revenue_axis.yaxis.set_major_formatter(currency)
            revenue_axis.tick_params(axis="x", rotation=35)

            profit_axis.plot(
                months,
                profits,
                color=COLORS["teal"],
                marker="o",
                linewidth=2.5,
                markersize=5,
            )
            profit_axis.set_ylabel("Estimated profit (₹)")
            profit_axis.yaxis.set_major_formatter(currency)
            profit_axis.tick_params(axis="x", rotation=35)
        else:
            self._empty_chart(revenue_axis, "No sales data available yet.")
            self._empty_chart(profit_axis, "No sales data available yet.")

        if best_sellers:
            names = [str(row[0]) for row in reversed(best_sellers)]
            units = [int(row[1] or 0) for row in reversed(best_sellers)]
            products_axis.barh(names, units, color=COLORS["blue"])
            products_axis.set_xlabel("Units sold")
            products_axis.tick_params(axis="y", labelsize=8)
        else:
            self._empty_chart(products_axis, "No product sales recorded.")

        if category_stock:
            categories = [str(row[0]) for row in category_stock]
            stock_values = [int(row[1] or 0) for row in category_stock]
            category_axis.bar(
                categories,
                stock_values,
                color=COLORS["teal"],
            )
            category_axis.set_ylabel("Stock units")
            category_axis.tick_params(axis="x", rotation=30)
        else:
            self._empty_chart(category_axis, "No inventory categories available.")

        if low_stock:
            low_names = [str(row[0]) for row in reversed(low_stock)]
            quantities = [int(row[1] or 0) for row in reversed(low_stock)]
            thresholds = [int(row[2] or 0) for row in reversed(low_stock)]
            positions = list(range(len(low_names)))
            low_axis.barh(
                positions,
                thresholds,
                color="#FBE3DF",
                label="Reorder level",
            )
            low_axis.barh(
                positions,
                quantities,
                color=COLORS["red"],
                label="Current stock",
            )
            low_axis.set_yticks(positions)
            low_axis.set_yticklabels(low_names)
            low_axis.set_xlabel("Stock units")
            low_axis.legend(frameon=False, fontsize=8, loc="lower right")
        else:
            self._empty_chart(low_axis, "No low-stock products. Inventory is above reorder levels.")

        if months:
            positions = list(range(len(months)))
            bar_width = 0.38
            comparison_axis.bar(
                [position - bar_width / 2 for position in positions],
                revenues,
                width=bar_width,
                color=COLORS["blue"],
                label="Revenue",
            )
            comparison_axis.bar(
                [position + bar_width / 2 for position in positions],
                profits,
                width=bar_width,
                color=COLORS["teal"],
                label="Estimated gross profit",
            )
            comparison_axis.set_xticks(positions)
            comparison_axis.set_xticklabels(months, rotation=35, ha="right")
            comparison_axis.yaxis.set_major_formatter(currency)
            comparison_axis.set_ylabel("Amount (₹)")
            comparison_axis.legend(frameon=False, fontsize=8)
        else:
            self._empty_chart(comparison_axis, "No sales data available yet.")

        self.analytics_figure.tight_layout(pad=2.0, h_pad=2.4, w_pad=2.0)
        self.analytics_canvas.draw_idle()

    def load_analytics(self):
        try:
            self._render_analytics(self._fetch_analytics_data())
            self._set_status("Analytics updated from MySQL")
        except (mysql.connector.Error, RuntimeError) as error:
            self._handle_database_error(error)

    def show_sales_analytics(self):
        self.show_page("analytics")

    def close(self):
        if self.analytics_figure is not None:
            self.analytics_figure.clear()
            self.analytics_figure = None
        self.root.destroy()


if __name__ == "__main__":
    application_root = tk.Tk()
    app = InventoryApp(application_root)
    application_root.mainloop()
