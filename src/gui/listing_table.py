"""
Sortable, filterable listing table widget.

Displays listings with color-coded deal scores, inline condition badges,
and supports sorting by any column.
"""

import webbrowser
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QSortFilterProxyModel
from PyQt6.QtGui import QColor, QBrush, QFont, QAction
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu,
    QAbstractItemView, QWidget, QVBoxLayout,
)

from src.gui.theme import score_color, ACCENT


# Column definitions: (header, field, width, alignment)
COLUMNS = [
    ("Score",     "deal_score",               65,  Qt.AlignmentFlag.AlignCenter),
    ("Title",     "title",                    320, Qt.AlignmentFlag.AlignLeft),
    ("Price",     "price",                    85,  Qt.AlignmentFlag.AlignRight),
    ("Recon",     "total_reconstructed_value", 85,  Qt.AlignmentFlag.AlignRight),
    ("Conf",      "ai_build_confidence",      62,  Qt.AlignmentFlag.AlignCenter),
    ("Condition",  "condition",               100, Qt.AlignmentFlag.AlignCenter),
    ("Year",      "year",                     62,  Qt.AlignmentFlag.AlignCenter),
    ("Brand",     "brand",                    100, Qt.AlignmentFlag.AlignLeft),
    ("Location",  "seller_location",          180, Qt.AlignmentFlag.AlignLeft),
    ("Category",  "category",                 110, Qt.AlignmentFlag.AlignLeft),
    ("Posted",    "date_posted",              100, Qt.AlignmentFlag.AlignLeft),
]


class NumericTableItem(QTableWidgetItem):
    """Table item that sorts numerically instead of alphabetically."""

    def __init__(self, display_text: str, sort_value: float):
        super().__init__(display_text)
        self._sort_value = sort_value

    def __lt__(self, other):
        if isinstance(other, NumericTableItem):
            return self._sort_value < other._sort_value
        return super().__lt__(other)


class ListingTable(QWidget):
    """
    Main listing table with sorting, selection, and context menus.

    Signals:
        listing_selected(dict) — Emitted when a row is clicked, with listing data
    """
    listing_selected = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._listings = []      # Raw listing data (list of dicts)
        self._listing_map = {}   # row -> listing dict
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(len(COLUMNS))
        self.table.setHorizontalHeaderLabels([c[0] for c in COLUMNS])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Column widths
        header = self.table.horizontalHeader()
        for i, (_, _, width, _) in enumerate(COLUMNS):
            self.table.setColumnWidth(i, width)
        # Stretch Title column
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # Row height
        self.table.verticalHeader().setDefaultSectionSize(36)

        # Signals
        self.table.currentCellChanged.connect(self._on_selection_changed)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.doubleClicked.connect(self._on_double_click)

        layout.addWidget(self.table)

    def load_listings(self, listings: list[dict]):
        """
        Load listings into the table.

        Args:
            listings: list of dicts with keys matching COLUMNS field names
        """
        self._listings = listings
        self._listing_map.clear()

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(listings))

        for row, listing in enumerate(listings):
            self._listing_map[row] = listing
            self._populate_row(row, listing)

        self.table.setSortingEnabled(True)
        # Default sort by score descending
        self.table.sortItems(0, Qt.SortOrder.DescendingOrder)

    def _populate_row(self, row: int, data: dict):
        """Fill a single row with listing data."""
        for col, (header, field, width, alignment) in enumerate(COLUMNS):
            value = data.get(field)
            item = self._create_item(col, field, value, data, alignment)
            self.table.setItem(row, col, item)

    def _create_item(self, col: int, field: str, value, data: dict,
                     alignment) -> QTableWidgetItem:
        """Create a formatted table item."""

        if field == "deal_score":
            score = value or 0.0
            item = NumericTableItem(f"{score:.0f}", score)
            item.setForeground(QBrush(QColor(score_color(score))))
            font = item.font()
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            item.setFont(font)

        elif field == "price":
            price = value or 0
            item = NumericTableItem(f"${price:,.0f}", price)

        elif field == "total_reconstructed_value":
            recon = value or 0
            if recon > 0:
                item = NumericTableItem(f"${recon:,.0f}", recon)
                # Color code: green if recon > price (good deal)
                price = data.get("price", 0) or 0
                if price > 0 and recon > price * 1.3:
                    item.setForeground(QBrush(QColor("#2ECC71")))
                elif price > 0 and recon < price * 0.8:
                    item.setForeground(QBrush(QColor("#E74C3C")))
            else:
                item = NumericTableItem("—", 0)
                item.setForeground(QBrush(QColor("#555")))

        elif field == "ai_build_confidence":
            conf = value or 0
            if conf > 0:
                item = NumericTableItem(f"{conf:.0%}", conf)
                if conf >= 0.7:
                    item.setForeground(QBrush(QColor("#2ECC71")))
                elif conf >= 0.4:
                    item.setForeground(QBrush(QColor("#F39C12")))
                else:
                    item.setForeground(QBrush(QColor("#95A5A6")))
            else:
                item = NumericTableItem("—", 0)
                item.setForeground(QBrush(QColor("#555")))

        elif field == "year":
            year = value or 0
            item = NumericTableItem(str(year) if year else "?", year)

        elif field == "condition":
            cond = str(value or "?")
            item = QTableWidgetItem(cond)
            # Color code conditions
            cond_colors = {
                "New": "#2ECC71",
                "Excellent": "#27AE60",
                "Good": "#F39C12",
                "Fair": "#E67E22",
                "Poor": "#E74C3C",
            }
            color = cond_colors.get(cond, "#95A5A6")
            item.setForeground(QBrush(QColor(color)))

        elif field == "title":
            title = str(value or "")
            item = QTableWidgetItem(title)
            # Bold for boosted listings
            if data.get("is_boosted"):
                font = item.font()
                font.setBold(True)
                item.setFont(font)

        else:
            text = str(value) if value else ""
            item = QTableWidgetItem(text)

        item.setTextAlignment(alignment | Qt.AlignmentFlag.AlignVCenter)
        # Store the listing data in the item
        item.setData(Qt.ItemDataRole.UserRole, data)
        return item

    def _on_selection_changed(self, row: int, col: int, prev_row: int, prev_col: int):
        """Handle row selection change."""
        if row < 0:
            return
        item = self.table.item(row, 0)
        if item:
            data = item.data(Qt.ItemDataRole.UserRole)
            if data:
                self.listing_selected.emit(data)

    def _on_double_click(self, index):
        """Open listing URL on double-click."""
        row = index.row()
        item = self.table.item(row, 0)
        if item:
            data = item.data(Qt.ItemDataRole.UserRole)
            url = data.get("url", "")
            if url:
                webbrowser.open(url)

    def _show_context_menu(self, pos):
        """Show right-click context menu."""
        item = self.table.itemAt(pos)
        if not item:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return

        menu = QMenu(self)

        open_action = QAction("Open on Pinkbike", self)
        open_action.triggered.connect(
            lambda: webbrowser.open(data.get("url", ""))
        )
        menu.addAction(open_action)

        copy_action = QAction("Copy Link", self)
        copy_action.triggered.connect(
            lambda: self._copy_to_clipboard(data.get("url", ""))
        )
        menu.addAction(copy_action)

        menu.addSeparator()

        copy_title = QAction("Copy Title", self)
        copy_title.triggered.connect(
            lambda: self._copy_to_clipboard(data.get("title", ""))
        )
        menu.addAction(copy_title)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(text)

    def get_selected_listing(self) -> Optional[dict]:
        """Return the currently selected listing data."""
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def get_listing_count(self) -> int:
        """Return the number of listings in the table."""
        return self.table.rowCount()
