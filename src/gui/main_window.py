"""
Main application window for PinkbikeDeals.

Layout:
  - Toolbar: scan controls, refresh, scan status, listing count
  - Left: filter panel
  - Center: listing table (sortable)
  - Bottom: detail panel for selected listing
  - Menu bar: File, View, Scan, Help
  - Status bar: last scan info, DB stats
"""

import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QAction, QKeySequence, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QPushButton, QToolBar,
    QStatusBar, QComboBox, QSpinBox, QMessageBox,
    QFileDialog, QApplication, QProgressBar, QSizePolicy,
)

import sys
import os

from src.config import Config
from src.constants import CATEGORIES
from src.database.db import Database
from src.gui.listing_table import ListingTable
from src.gui.filter_panel import FilterPanel
from src.gui.detail_panel import DetailPanel
from src.gui.worker import ScrapeWorker, RescoreWorker
from src.gui.theme import DARK_STYLESHEET, LIGHT_STYLESHEET, ACCENT

logger = logging.getLogger(__name__)

# Build a lookup: display name -> key  (e.g. "Enduro Bikes" -> "enduro_bikes")
_CATEGORY_NAME_TO_KEY = {cat["name"]: key for key, cat in CATEGORIES.items()}
# Build a lookup: key -> display name  (e.g. "enduro_bikes" -> "Enduro Bikes")
_CATEGORY_KEY_TO_NAME = {key: cat["name"] for key, cat in CATEGORIES.items()}


class MainWindow(QMainWindow):
    """PinkbikeDeals main application window."""

    def __init__(self, config: Config = None):
        super().__init__()
        self.config = config or Config()
        self.db = Database(self.config.database.path)
        self.db.init_db()

        self._dark_mode = True
        self._scan_worker = None
        self._rescore_worker = None
        self._all_listings = []   # Full unfiltered list

        self.setWindowTitle("PinkbikeDeals")
        self.setMinimumSize(1100, 700)
        self.resize(1440, 880)

        # Set window icon
        self._set_window_icon()

        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_status_bar()
        self._setup_shortcuts()

        # Apply theme
        self._apply_theme()

        # Load data, then check if first run
        QTimer.singleShot(100, self._initial_load)

    def _set_window_icon(self):
        """Set the window icon from assets."""
        try:
            if getattr(sys, 'frozen', False):
                icon_path = os.path.join(sys._MEIPASS, 'assets', 'icon.png')
            else:
                icon_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(
                        os.path.abspath(__file__)))),
                    'assets', 'icon.png'
                )
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_menu_bar(self):
        menubar = self.menuBar()

        # --- File ---
        file_menu = menubar.addMenu("&File")

        export_csv = QAction("Export to CSV...", self)
        export_csv.setShortcut(QKeySequence("Ctrl+Shift+E"))
        export_csv.triggered.connect(self._export_csv)
        file_menu.addAction(export_csv)

        export_json = QAction("Export to JSON...", self)
        export_json.triggered.connect(self._export_json)
        file_menu.addAction(export_json)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # --- View ---
        view_menu = menubar.addMenu("&View")

        toggle_theme = QAction("Toggle Dark/Light Mode", self)
        toggle_theme.setShortcut(QKeySequence("Ctrl+T"))
        toggle_theme.triggered.connect(self._toggle_theme)
        view_menu.addAction(toggle_theme)

        toggle_filters = QAction("Toggle Filter Panel", self)
        toggle_filters.setShortcut(QKeySequence("Ctrl+Shift+F"))
        toggle_filters.triggered.connect(self._toggle_filters)
        view_menu.addAction(toggle_filters)

        toggle_detail = QAction("Toggle Detail Panel", self)
        toggle_detail.setShortcut(QKeySequence("Ctrl+D"))
        toggle_detail.triggered.connect(self._toggle_detail)
        view_menu.addAction(toggle_detail)

        view_menu.addSeparator()

        refresh_action = QAction("Refresh Listings", self)
        refresh_action.setShortcut(QKeySequence("F5"))
        refresh_action.triggered.connect(self._refresh_data)
        view_menu.addAction(refresh_action)

        # --- Scan ---
        scan_menu = menubar.addMenu("&Scan")

        scan_now = QAction("Quick Scan", self)
        scan_now.setShortcut(QKeySequence("Ctrl+Return"))
        scan_now.triggered.connect(self._start_quick_scan)
        scan_menu.addAction(scan_now)

        harvest_action = QAction("Full Harvest...", self)
        harvest_action.setShortcut(QKeySequence("Ctrl+Shift+Return"))
        harvest_action.triggered.connect(self._start_harvest)
        scan_menu.addAction(harvest_action)

        scan_menu.addSeparator()

        rescore_action = QAction("Rescore All Listings", self)
        rescore_action.setShortcut(QKeySequence("F6"))
        rescore_action.triggered.connect(self._start_rescore)
        scan_menu.addAction(rescore_action)

        scan_menu.addSeparator()

        stop_scan = QAction("Stop Scan", self)
        stop_scan.setShortcut(QKeySequence("Escape"))
        stop_scan.triggered.connect(self._stop_scan)
        scan_menu.addAction(stop_scan)

        # --- Help ---
        help_menu = menubar.addMenu("&Help")
        about = QAction("About PinkbikeDeals", self)
        about.triggered.connect(self._show_about)
        help_menu.addAction(about)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        # Scan button (primary action)
        self.scan_btn = QPushButton("  Scan Now  ")
        self.scan_btn.setObjectName("scanButton")
        self.scan_btn.setToolTip("Scrape new listings from Pinkbike (Ctrl+Enter)")
        self.scan_btn.clicked.connect(self._start_quick_scan)
        toolbar.addWidget(self.scan_btn)

        # Refresh button (reload from DB)
        self.refresh_btn = QPushButton("  Refresh  ")
        self.refresh_btn.setToolTip("Reload listings from database (F5)")
        self.refresh_btn.clicked.connect(self._refresh_data)
        toolbar.addWidget(self.refresh_btn)

        toolbar.addSeparator()

        # Category selector for scanning
        cat_label = QLabel("  Scan: ")
        toolbar.addWidget(cat_label)

        self.scan_category = QComboBox()
        self.scan_category.addItem("All Categories", "")

        # Group categories by type
        self.scan_category.insertSeparator(self.scan_category.count())
        # Bikes
        bike_cats = [(k, c) for k, c in sorted(CATEGORIES.items(), key=lambda x: x[1]["name"])
                     if "bikes" in k.lower() or "ebike" in k.lower() or "road" in k.lower()]
        for key, cat in bike_cats:
            self.scan_category.addItem(f"  {cat['name']}", key)

        self.scan_category.insertSeparator(self.scan_category.count())
        # Frames
        frame_cats = [(k, c) for k, c in sorted(CATEGORIES.items(), key=lambda x: x[1]["name"])
                      if "frame" in k.lower()]
        for key, cat in frame_cats:
            self.scan_category.addItem(f"  {cat['name']}", key)

        self.scan_category.insertSeparator(self.scan_category.count())
        # Components
        comp_cats = [(k, c) for k, c in sorted(CATEGORIES.items(), key=lambda x: x[1]["name"])
                     if "bike" not in k.lower() and "frame" not in k.lower()
                     and "ebike" not in k.lower() and "road" not in k.lower()]
        for key, cat in comp_cats:
            self.scan_category.addItem(f"  {cat['name']}", key)

        self.scan_category.setMinimumWidth(200)
        toolbar.addWidget(self.scan_category)

        # Pages spinner
        pages_label = QLabel("  Pages: ")
        toolbar.addWidget(pages_label)

        self.scan_pages = QSpinBox()
        self.scan_pages.setRange(1, 50)
        self.scan_pages.setValue(3)
        self.scan_pages.setFixedWidth(60)
        self.scan_pages.setToolTip("Number of pages to scrape per category")
        toolbar.addWidget(self.scan_pages)

        toolbar.addSeparator()

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setMaximum(0)  # Indeterminate
        self.progress_bar.hide()
        toolbar.addWidget(self.progress_bar)

        # Scan status label
        self.scan_status_label = QLabel("  Ready")
        self.scan_status_label.setStyleSheet("color: #8899aa;")
        toolbar.addWidget(self.scan_status_label)

        # Spacer pushes count to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # Listing count
        self.count_label = QLabel("0 listings  ")
        self.count_label.setStyleSheet(f"color: {ACCENT}; font-weight: 600; font-size: 14px;")
        toolbar.addWidget(self.count_label)

    def _setup_central_widget(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main splitter: filters | table+detail
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Filter panel (left)
        self.filter_panel = FilterPanel()
        self.filter_panel.filter_changed.connect(self._apply_filters)
        self.main_splitter.addWidget(self.filter_panel)

        # Right side: table + detail (vertical splitter)
        self.right_splitter = QSplitter(Qt.Orientation.Vertical)

        # Listing table
        self.listing_table = ListingTable()
        self.listing_table.listing_selected.connect(self._on_listing_selected)
        self.right_splitter.addWidget(self.listing_table)

        # Detail panel
        self.detail_panel = DetailPanel()
        self.right_splitter.addWidget(self.detail_panel)

        # Set proportions: table gets 60%, detail 40%
        self.right_splitter.setSizes([520, 360])

        self.main_splitter.addWidget(self.right_splitter)

        # Set proportions: filters ~240px, table gets rest
        self.main_splitter.setSizes([240, 1200])

        layout.addWidget(self.main_splitter)

    def _setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.db_stats_label = QLabel("Loading...")
        self.status_bar.addPermanentWidget(self.db_stats_label)

        self.last_scan_label = QLabel("")
        self.status_bar.addWidget(self.last_scan_label)

    def _setup_shortcuts(self):
        """Additional keyboard shortcuts (menu shortcuts defined above)."""
        pass  # All shortcuts are now attached to menu actions

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _initial_load(self):
        """Load data on startup."""
        self._refresh_data()

    def _refresh_data(self):
        """Reload all listing data from the database and update the table."""
        try:
            # Visual feedback
            self.refresh_btn.setEnabled(False)
            self.refresh_btn.setText("  Refreshing...  ")
            QApplication.processEvents()

            # Load all listings as plain dicts (safe outside DB session)
            self._all_listings = self.db.get_all_listings_as_dicts()

            # Populate brand filter with actual brands from data
            brands = set(d.get("brand", "") for d in self._all_listings if d.get("brand"))
            self.filter_panel.populate_brands(list(brands))

            # Populate category filter with actual categories from data
            categories = set(d.get("category", "") for d in self._all_listings if d.get("category"))
            self.filter_panel.populate_categories(list(categories))

            # Apply current filters and reload table
            self._apply_filters(self.filter_panel.get_filters())

            # Update stats in status bar
            stats = self.db.get_stats()
            self.db_stats_label.setText(
                f"DB: {stats['total_listings']:,} total  |  "
                f"{stats['active_listings']:,} active  |  "
                f"Avg: ${stats['avg_price']:,.0f} CAD"
            )

            self.scan_status_label.setText(
                f"  Refreshed — {len(self._all_listings)} listings loaded"
            )

        except Exception as e:
            logger.exception("Error loading data")
            self.status_bar.showMessage(f"Error: {e}", 5000)
        finally:
            self.refresh_btn.setEnabled(True)
            self.refresh_btn.setText("  Refresh  ")

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def _apply_filters(self, filters: dict):
        """Filter the listings and reload the table."""
        filtered = [d for d in self._all_listings if self._matches_filter(d, filters)]
        self.listing_table.load_listings(filtered)
        total = len(self._all_listings)
        shown = len(filtered)
        if shown < total:
            self.count_label.setText(f"{shown} / {total} listings  ")
        else:
            self.count_label.setText(f"{total} listings  ")

    def _matches_filter(self, data: dict, f: dict) -> bool:
        """Check if a listing matches all active filters."""

        # --- Category: compare display names directly ---
        filter_cat = f.get("category", "")
        if filter_cat:
            listing_cat = (data.get("category") or "").strip()
            # Filter sends the display name (e.g. "Enduro Bikes")
            if listing_cat.lower() != filter_cat.lower():
                return False

        # --- Brand ---
        if f.get("brand"):
            listing_brand = (data.get("brand") or "").lower()
            if f["brand"].lower() not in listing_brand:
                return False

        # --- Price range ---
        price = data.get("price", 0) or 0
        if f.get("price_min") and price < f["price_min"]:
            return False
        if f.get("price_max") and price > f["price_max"]:
            return False

        # --- Frame size ---
        if f.get("frame_size"):
            listing_size = (data.get("frame_size") or "").upper()
            if not listing_size:
                return False
            filter_size = f["frame_size"].upper()
            if filter_size not in listing_size:
                return False

        # --- Wheel size ---
        if f.get("wheel_size"):
            listing_wheel = (data.get("wheel_size") or "").replace('"', '').replace("'", "")
            filter_wheel = f["wheel_size"].replace('"', '').replace("'", "")
            if filter_wheel not in listing_wheel:
                return False

        # --- Material ---
        if f.get("material"):
            listing_material = (data.get("material") or "").lower()
            if not listing_material or f["material"].lower() not in listing_material:
                return False

        # --- Condition ---
        if f.get("condition"):
            listing_cond = (data.get("condition") or "").lower()
            if listing_cond != f["condition"].lower():
                return False

        # --- Year range ---
        year = data.get("year") or 0
        if year > 0:
            if f.get("year_min") and year < f["year_min"]:
                return False
            if f.get("year_max") and year > f["year_max"]:
                return False

        # --- Min score ---
        if f.get("min_score"):
            score = data.get("deal_score", 0) or 0
            if score < f["min_score"]:
                return False

        # --- Location ---
        if f.get("location"):
            loc = (data.get("seller_location") or "").lower()
            if f["location"].lower() not in loc:
                return False

        # --- Hide sold ---
        if f.get("hide_sold") and data.get("is_sold"):
            return False

        # --- Hide boosted ---
        if f.get("hide_boosted") and data.get("is_boosted"):
            return False

        return True

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    def _on_listing_selected(self, data: dict):
        """Handle listing selection — update detail panel."""
        self.detail_panel.update_listing(data)

    # ------------------------------------------------------------------
    # Scanning
    # ------------------------------------------------------------------

    def _start_quick_scan(self):
        if self._scan_worker and self._scan_worker.isRunning():
            self.status_bar.showMessage("Scan already running...", 3000)
            return

        category = self.scan_category.currentData() or None
        categories = [category] if category else None
        pages = self.scan_pages.value()

        self._scan_worker = ScrapeWorker(self.config)
        self._scan_worker.configure(
            scan_type="hot_scan",
            categories=categories,
            max_pages=pages,
        )
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.scan_complete.connect(self._on_scan_complete)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.start()

        self.scan_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.scan_btn.setText("  Scanning...  ")
        self.progress_bar.show()
        self.scan_status_label.setText("  Scanning...")

    def _start_harvest(self):
        if self._scan_worker and self._scan_worker.isRunning():
            self.status_bar.showMessage("Scan already running...", 3000)
            return

        category = self.scan_category.currentData() or None
        categories = [category] if category else None

        reply = QMessageBox.question(
            self, "Full Harvest",
            "This will scan ALL pages of the selected categories.\n"
            "This may take several minutes. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._scan_worker = ScrapeWorker(self.config)
        self._scan_worker.configure(
            scan_type="harvest",
            categories=categories,
        )
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.scan_complete.connect(self._on_scan_complete)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.start()

        self.scan_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.scan_btn.setText("  Harvesting...  ")
        self.progress_bar.show()

    def _start_rescore(self):
        if self._rescore_worker and self._rescore_worker.isRunning():
            return

        self._rescore_worker = RescoreWorker(self.config)
        self._rescore_worker.progress.connect(self._on_scan_progress)
        self._rescore_worker.rescore_complete.connect(self._on_rescore_complete)
        self._rescore_worker.error.connect(self._on_scan_error)
        self._rescore_worker.start()

        self.progress_bar.show()
        self.scan_status_label.setText("  Rescoring...")

    def _stop_scan(self):
        if self._scan_worker and self._scan_worker.isRunning():
            self._scan_worker.stop_scan()
            self.scan_status_label.setText("  Stopping...")

    def _on_scan_progress(self, msg: str):
        self.scan_status_label.setText(f"  {msg}")

    def _on_scan_complete(self, result: dict):
        self.scan_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.scan_btn.setText("  Scan Now  ")
        self.progress_bar.hide()
        self.scan_status_label.setText(
            f"  {result.get('new', 0)} new, "
            f"{result.get('found', 0)} found, "
            f"{result.get('errors', 0)} errors"
        )
        self.last_scan_label.setText(
            f"Last scan: {datetime.now().strftime('%H:%M:%S')}"
        )
        # Refresh table
        self._refresh_data()

    def _on_rescore_complete(self, result: dict):
        self.progress_bar.hide()
        self.scan_status_label.setText(
            f"  Rescored {result.get('scored', 0)} listings"
        )
        self._refresh_data()

    def _on_scan_error(self, error: str):
        self.scan_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.scan_btn.setText("  Scan Now  ")
        self.progress_bar.hide()
        self.scan_status_label.setText(f"  Error: {error[:60]}")
        QMessageBox.warning(self, "Scan Error", f"An error occurred:\n{error}")

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _apply_theme(self):
        if self._dark_mode:
            QApplication.instance().setStyleSheet(DARK_STYLESHEET)
        else:
            QApplication.instance().setStyleSheet(LIGHT_STYLESHEET)

    def _toggle_theme(self):
        self._dark_mode = not self._dark_mode
        self._apply_theme()

    # ------------------------------------------------------------------
    # Toggle panels
    # ------------------------------------------------------------------

    def _toggle_filters(self):
        self.filter_panel.setVisible(not self.filter_panel.isVisible())

    def _toggle_detail(self):
        self.detail_panel.setVisible(not self.detail_panel.isVisible())

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "pinkbike_deals.csv",
            "CSV Files (*.csv)",
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Score", "Title", "Price (CAD)", "Recon Value", "Confidence",
                    "Condition", "Year", "Brand", "Model", "Location",
                    "Category", "URL", "Posted",
                ])
                for data in self._all_listings:
                    writer.writerow([
                        f"{data.get('deal_score', 0):.1f}",
                        data.get("title", ""),
                        f"{data.get('price', 0):.0f}",
                        f"{data.get('total_reconstructed_value', 0):.0f}",
                        f"{data.get('ai_build_confidence', 0):.2f}",
                        data.get("condition", ""),
                        data.get("year", ""),
                        data.get("brand", ""),
                        data.get("model", ""),
                        data.get("seller_location", ""),
                        data.get("category", ""),
                        data.get("url", ""),
                        data.get("date_posted", ""),
                    ])
            self.status_bar.showMessage(
                f"Exported {len(self._all_listings)} listings to {path}", 5000
            )
        except Exception as e:
            QMessageBox.warning(self, "Export Error", str(e))

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export JSON", "pinkbike_deals.json",
            "JSON Files (*.json)",
        )
        if not path:
            return

        try:
            export_data = []
            for data in self._all_listings:
                export_data.append({
                    k: v for k, v in data.items()
                    if k != "description"
                })
            with open(path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, default=str)
            self.status_bar.showMessage(
                f"Exported {len(export_data)} listings to {path}", 5000
            )
        except Exception as e:
            QMessageBox.warning(self, "Export Error", str(e))

    # ------------------------------------------------------------------
    # About
    # ------------------------------------------------------------------

    def _show_about(self):
        stats = self.db.get_stats()
        QMessageBox.about(
            self,
            "About PinkbikeDeals",
            "<h2>PinkbikeDeals</h2>"
            "<p>Used Bike Deal Finder</p>"
            "<p>Scrapes Pinkbike's BuySell marketplace, scores deals using "
            "component analysis and build valuation, and helps you find "
            "the best bikes at the best prices.</p>"
            "<hr>"
            f"<p><b>{stats['total_listings']:,}</b> listings in database<br>"
            f"<b>{stats['active_listings']:,}</b> active<br>"
            f"Avg price: <b>${stats['avg_price']:,.0f} CAD</b></p>"
        )
