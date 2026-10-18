"""
Left sidebar filter panel.

Provides dropdown and range filters for: category, brand, price range,
frame size, wheel size, condition, year range, location, and minimum score.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QPushButton, QScrollArea,
    QCheckBox, QLineEdit, QFrame,
)

from src.constants import CATEGORIES


class FilterPanel(QWidget):
    """
    Sidebar filter panel that emits filter_changed when any filter updates.

    Signal:
        filter_changed(dict) — dict of current filter values
    """
    filter_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(220)
        self.setMaximumWidth(280)
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        self._layout = QVBoxLayout(container)
        self._layout.setContentsMargins(12, 8, 12, 8)
        self._layout.setSpacing(6)

        # --- Title ---
        title = QLabel("FILTERS")
        title.setObjectName("sectionTitle")
        self._layout.addWidget(title)

        self._add_separator()

        # --- Category (display names, populated dynamically) ---
        self._add_label("Category")
        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", "")
        self.category_combo.currentIndexChanged.connect(self._emit_filters)
        self._layout.addWidget(self.category_combo)

        # --- Brand ---
        self._add_label("Brand")
        self.brand_combo = QComboBox()
        self.brand_combo.addItem("All Brands", "")
        self.brand_combo.setEditable(True)
        self.brand_combo.lineEdit().setPlaceholderText("Type to filter...")
        self.brand_combo.currentIndexChanged.connect(self._emit_filters)
        self._layout.addWidget(self.brand_combo)

        # --- Price Range ---
        self._add_label("Price Range (CAD)")
        price_row = QHBoxLayout()
        price_row.setSpacing(6)

        self.price_min = QSpinBox()
        self.price_min.setRange(0, 50000)
        self.price_min.setSingleStep(100)
        self.price_min.setPrefix("$")
        self.price_min.setValue(0)
        self.price_min.setSpecialValueText("Min")
        self.price_min.valueChanged.connect(self._emit_filters)

        dash = QLabel("—")
        dash.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash.setFixedWidth(16)

        self.price_max = QSpinBox()
        self.price_max.setRange(0, 50000)
        self.price_max.setSingleStep(100)
        self.price_max.setPrefix("$")
        self.price_max.setValue(50000)
        self.price_max.setSpecialValueText("Max")
        self.price_max.valueChanged.connect(self._emit_filters)

        price_row.addWidget(self.price_min)
        price_row.addWidget(dash)
        price_row.addWidget(self.price_max)
        self._layout.addLayout(price_row)

        self._add_separator()

        # --- Frame Size ---
        self._add_label("Frame Size")
        self.frame_size_combo = QComboBox()
        self.frame_size_combo.addItems(["Any", "XS", "S", "M", "M/L", "L", "XL", "XXL"])
        self.frame_size_combo.currentIndexChanged.connect(self._emit_filters)
        self._layout.addWidget(self.frame_size_combo)

        # --- Wheel Size ---
        self._add_label("Wheel Size")
        self.wheel_size_combo = QComboBox()
        self.wheel_size_combo.addItems(["Any", "26\"", "27.5\"", "29\"", "Mixed/Mullet"])
        self.wheel_size_combo.currentIndexChanged.connect(self._emit_filters)
        self._layout.addWidget(self.wheel_size_combo)

        # --- Material ---
        self._add_label("Frame Material")
        self.material_combo = QComboBox()
        self.material_combo.addItems(["Any", "Carbon", "Aluminum", "Steel", "Titanium"])
        self.material_combo.currentIndexChanged.connect(self._emit_filters)
        self._layout.addWidget(self.material_combo)

        self._add_separator()

        # --- Condition ---
        self._add_label("Condition")
        self.condition_combo = QComboBox()
        self.condition_combo.addItems(["Any", "New", "Excellent", "Good", "Fair", "Poor"])
        self.condition_combo.currentIndexChanged.connect(self._emit_filters)
        self._layout.addWidget(self.condition_combo)

        # --- Year Range ---
        self._add_label("Year")
        year_row = QHBoxLayout()
        year_row.setSpacing(6)

        self.year_min = QSpinBox()
        self.year_min.setRange(2000, 2030)
        self.year_min.setValue(2000)
        self.year_min.setSpecialValueText("Min")
        self.year_min.valueChanged.connect(self._emit_filters)

        dash2 = QLabel("—")
        dash2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dash2.setFixedWidth(16)

        self.year_max = QSpinBox()
        self.year_max.setRange(2000, 2030)
        self.year_max.setValue(2030)
        self.year_max.setSpecialValueText("Max")
        self.year_max.valueChanged.connect(self._emit_filters)

        year_row.addWidget(self.year_min)
        year_row.addWidget(dash2)
        year_row.addWidget(self.year_max)
        self._layout.addLayout(year_row)

        self._add_separator()

        # --- Min Score ---
        self._add_label("Minimum Deal Score")
        self.min_score = QSpinBox()
        self.min_score.setRange(0, 100)
        self.min_score.setValue(0)
        self.min_score.setSuffix(" / 100")
        self.min_score.valueChanged.connect(self._emit_filters)
        self._layout.addWidget(self.min_score)

        # --- Location search ---
        self._add_label("Location")
        self.location_search = QLineEdit()
        self.location_search.setPlaceholderText("Search location...")
        self.location_search.textChanged.connect(self._emit_filters)
        self._layout.addWidget(self.location_search)

        self._add_separator()

        # --- Checkboxes ---
        self.hide_sold = QCheckBox("Hide sold listings")
        self.hide_sold.setChecked(True)
        self.hide_sold.stateChanged.connect(self._emit_filters)
        self._layout.addWidget(self.hide_sold)

        self.hide_boosted = QCheckBox("Hide boosted / ads")
        self.hide_boosted.setChecked(False)
        self.hide_boosted.stateChanged.connect(self._emit_filters)
        self._layout.addWidget(self.hide_boosted)

        self._layout.addSpacing(12)

        # --- Reset button ---
        reset_btn = QPushButton("Reset Filters")
        reset_btn.clicked.connect(self.reset_filters)
        self._layout.addWidget(reset_btn)

        self._layout.addStretch()

        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _add_label(self, text: str):
        lbl = QLabel(text)
        lbl.setObjectName("sectionTitle")
        self._layout.addWidget(lbl)

    def _add_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #2d2d44; max-height: 1px;")
        self._layout.addWidget(sep)

    def get_filters(self) -> dict:
        """Return current filter values as a dict."""
        # Category: send the display name (matches what's stored in DB)
        cat_text = self.category_combo.currentText().strip()
        if self.category_combo.currentIndex() == 0:
            cat_text = ""

        # Brand
        brand_text = ""
        if self.brand_combo.currentIndex() > 0:
            brand_text = self.brand_combo.currentText().strip()

        return {
            "category": cat_text,
            "brand": brand_text,
            "price_min": self.price_min.value(),
            "price_max": self.price_max.value() if self.price_max.value() < 50000 else None,
            "frame_size": self.frame_size_combo.currentText() if self.frame_size_combo.currentIndex() > 0 else "",
            "wheel_size": self.wheel_size_combo.currentText() if self.wheel_size_combo.currentIndex() > 0 else "",
            "material": self.material_combo.currentText() if self.material_combo.currentIndex() > 0 else "",
            "condition": self.condition_combo.currentText() if self.condition_combo.currentIndex() > 0 else "",
            "year_min": self.year_min.value(),
            "year_max": self.year_max.value(),
            "min_score": self.min_score.value(),
            "location": self.location_search.text().strip(),
            "hide_sold": self.hide_sold.isChecked(),
            "hide_boosted": self.hide_boosted.isChecked(),
        }

    def _emit_filters(self, *args):
        self.filter_changed.emit(self.get_filters())

    def reset_filters(self):
        """Reset all filters to defaults."""
        self.category_combo.setCurrentIndex(0)
        self.brand_combo.setCurrentIndex(0)
        self.price_min.setValue(0)
        self.price_max.setValue(50000)
        self.frame_size_combo.setCurrentIndex(0)
        self.wheel_size_combo.setCurrentIndex(0)
        self.material_combo.setCurrentIndex(0)
        self.condition_combo.setCurrentIndex(0)
        self.year_min.setValue(2000)
        self.year_max.setValue(2030)
        self.min_score.setValue(0)
        self.location_search.clear()
        self.hide_sold.setChecked(True)
        self.hide_boosted.setChecked(False)
        self._emit_filters()

    def populate_brands(self, brands: list[str]):
        """Populate the brand dropdown with actual brands from the database."""
        current = self.brand_combo.currentText()
        self.brand_combo.blockSignals(True)
        self.brand_combo.clear()
        self.brand_combo.addItem("All Brands", "")
        for brand in sorted(brands):
            if brand:
                self.brand_combo.addItem(brand, brand)
        idx = self.brand_combo.findText(current)
        if idx >= 0:
            self.brand_combo.setCurrentIndex(idx)
        self.brand_combo.blockSignals(False)

    def populate_categories(self, categories: list[str]):
        """Populate the category dropdown with actual categories from the database."""
        current = self.category_combo.currentText().strip()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("All Categories", "")
        for cat_name in sorted(categories):
            if cat_name:
                self.category_combo.addItem(cat_name, cat_name)
        # Restore selection if possible
        idx = self.category_combo.findText(current)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        self.category_combo.blockSignals(False)
