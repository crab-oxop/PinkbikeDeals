"""
Listing detail panel — shows full info for a selected listing.

Displays: title, price vs reconstructed value, deal score badge,
specs grid, condition, location, seller info, description preview,
and action buttons (open on Pinkbike, copy link).
"""

import webbrowser

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QTextEdit, QScrollArea, QSizePolicy,
)

from src.gui.theme import score_color, ACCENT


class ScoreBadge(QLabel):
    """Large colored score badge."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("detailScore")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(72, 72)
        self.setStyleSheet("""
            border-radius: 36px;
            font-size: 28px;
            font-weight: 800;
        """)

    def set_score(self, score: float):
        self.setText(f"{score:.0f}")
        color = score_color(score)
        self.setStyleSheet(f"""
            border-radius: 36px;
            font-size: 28px;
            font-weight: 800;
            color: white;
            background-color: {color};
        """)


class DetailPanel(QWidget):
    """
    Bottom panel showing full details of the selected listing.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self._current_url = ""
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)

        # --- Top Row: Score badge + Title + Price ---
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        self.score_badge = ScoreBadge()
        top_row.addWidget(self.score_badge)

        # Title + subtitle column
        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        self.title_label = QLabel("Select a listing to view details")
        self.title_label.setObjectName("detailTitle")
        self.title_label.setWordWrap(True)
        title_col.addWidget(self.title_label)

        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet("color: #8899aa; font-size: 12px;")
        title_col.addWidget(self.subtitle_label)

        top_row.addLayout(title_col, stretch=1)

        # Price column
        price_col = QVBoxLayout()
        price_col.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.price_label = QLabel("")
        self.price_label.setObjectName("detailPrice")
        self.price_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        price_col.addWidget(self.price_label)

        self.recon_label = QLabel("")
        self.recon_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.recon_label.setStyleSheet("color: #8899aa; font-size: 12px;")
        price_col.addWidget(self.recon_label)

        top_row.addLayout(price_col)

        main_layout.addLayout(top_row)

        # --- Divider ---
        self._add_divider(main_layout)

        # --- Specs Grid ---
        self.specs_grid = QGridLayout()
        self.specs_grid.setSpacing(8)
        self.specs_grid.setColumnStretch(1, 1)
        self.specs_grid.setColumnStretch(3, 1)
        self.specs_grid.setColumnStretch(5, 1)

        # Create spec labels (3 columns of key-value pairs)
        self._spec_labels = {}
        spec_fields = [
            # Row 0
            ("Condition", 0, 0), ("Year", 0, 2), ("Brand", 0, 4),
            # Row 1
            ("Frame Size", 1, 0), ("Wheel Size", 1, 2), ("Material", 1, 4),
            # Row 2
            ("Front Travel", 2, 0), ("Rear Travel", 2, 2), ("Category", 2, 4),
            # Row 3
            ("Location", 3, 0), ("Seller", 3, 2), ("Posted", 3, 4),
            # Row 4
            ("Views", 4, 0), ("Confidence", 4, 2), ("Status", 4, 4),
        ]

        for label, row, col in spec_fields:
            key_lbl = QLabel(label)
            key_lbl.setStyleSheet("color: #8899aa; font-size: 11px; font-weight: 600;")

            val_lbl = QLabel("—")
            val_lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
            val_lbl.setWordWrap(True)

            self.specs_grid.addWidget(key_lbl, row, col)
            self.specs_grid.addWidget(val_lbl, row, col + 1)
            self._spec_labels[label] = val_lbl

        main_layout.addLayout(self.specs_grid)

        # --- Score Breakdown ---
        self._add_divider(main_layout)
        breakdown_title = QLabel("SCORE BREAKDOWN")
        breakdown_title.setObjectName("sectionTitle")
        main_layout.addWidget(breakdown_title)

        self.breakdown_layout = QHBoxLayout()
        self.breakdown_layout.setSpacing(16)
        self._score_bars = {}

        # Weights come from the scorer so the labels never drift from the model
        from src.scoring.deal_scorer import DealScorer
        w = DealScorer.WEIGHTS
        score_components = [
            ("Price vs Value", "price_value_score", round(w["price_value"] * 100)),
            ("Components", "component_score", round(w["component"] * 100)),
            ("Condition", "condition_score", round(w["condition"] * 100)),
            ("Freshness", "freshness_score", round(w["freshness"] * 100)),
            ("Age", "age_score", round(w["age"] * 100)),
            ("Brand", "brand_score", round(w["brand"] * 100)),
            ("Seller", "seller_score", round(w["seller"] * 100)),
        ]

        for label, key, weight in score_components:
            bar_widget = self._create_score_bar(label, weight)
            self.breakdown_layout.addWidget(bar_widget)
            self._score_bars[key] = bar_widget

        self.breakdown_layout.addStretch()
        main_layout.addLayout(self.breakdown_layout)

        # --- Description ---
        self._add_divider(main_layout)
        desc_title = QLabel("DESCRIPTION")
        desc_title.setObjectName("sectionTitle")
        main_layout.addWidget(desc_title)

        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(120)
        self.description_text.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: 1px solid #2d2d44;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
                color: #cccccc;
            }
        """)
        main_layout.addWidget(self.description_text)

        # --- Action Buttons ---
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.open_btn = QPushButton("Open on Pinkbike")
        self.open_btn.setObjectName("scanButton")
        self.open_btn.clicked.connect(self._open_url)
        btn_row.addWidget(self.open_btn)

        self.copy_btn = QPushButton("Copy Link")
        self.copy_btn.clicked.connect(self._copy_link)
        btn_row.addWidget(self.copy_btn)

        btn_row.addStretch()
        main_layout.addLayout(btn_row)

        main_layout.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _add_divider(self, layout):
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet("background-color: #2d2d44; max-height: 1px;")
        layout.addWidget(div)

    def _create_score_bar(self, label: str, weight: int) -> QWidget:
        """Create a mini vertical score bar with label."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        value_label = QLabel("—")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet("font-size: 14px; font-weight: 700;")
        layout.addWidget(value_label)

        name_label = QLabel(f"{label}\n({weight}%)")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("color: #8899aa; font-size: 10px;")
        name_label.setWordWrap(True)
        name_label.setFixedWidth(80)
        layout.addWidget(name_label)

        widget._value_label = value_label
        return widget

    def update_listing(self, data: dict):
        """Update all fields with listing data."""
        if not data:
            return

        self._current_url = data.get("url", "")

        # Score badge
        score = data.get("deal_score", 0) or 0
        self.score_badge.set_score(score)

        # Title
        title = data.get("title", "Unknown Listing")
        self.title_label.setText(title)

        # Subtitle
        brand = data.get("brand", "")
        year = data.get("year", "")
        category = data.get("category", "")
        subtitle_parts = [str(p) for p in [year, brand, category] if p]
        self.subtitle_label.setText(" · ".join(subtitle_parts))

        # Price
        price = data.get("price", 0) or 0
        self.price_label.setText(f"${price:,.0f} CAD")

        # Reconstructed value
        recon = data.get("total_reconstructed_value", 0) or 0
        if recon > 0:
            ratio = price / recon if recon > 0 else 0
            color = "#2ECC71" if ratio < 0.7 else "#F39C12" if ratio < 1.0 else "#E74C3C"
            self.recon_label.setText(f"Est. value: ${recon:,.0f}")
            self.recon_label.setStyleSheet(f"color: {color}; font-size: 12px;")
        else:
            self.recon_label.setText("Est. value: —")
            self.recon_label.setStyleSheet("color: #8899aa; font-size: 12px;")

        # Specs
        self._set_spec("Condition", data.get("condition", "—"))
        self._set_spec("Year", str(data.get("year", "—")))
        self._set_spec("Brand", data.get("brand", "—"))
        self._set_spec("Frame Size", data.get("frame_size", "—"))
        self._set_spec("Wheel Size", data.get("wheel_size", "—"))
        self._set_spec("Material", data.get("material", "—"))
        self._set_spec("Front Travel", f"{data['front_travel']}mm" if data.get("front_travel") else "—")
        self._set_spec("Rear Travel", f"{data['rear_travel']}mm" if data.get("rear_travel") else "—")
        self._set_spec("Category", data.get("category", "—"))
        self._set_spec("Location", data.get("seller_location", "—"))
        self._set_spec("Seller", data.get("seller_username", "—"))
        self._set_spec("Posted", data.get("date_posted", "—"))
        self._set_spec("Views", str(data.get("views", "—")) if data.get("views") else "—")

        conf = data.get("ai_build_confidence", 0) or 0
        self._set_spec("Confidence", f"{conf:.0%}" if conf > 0 else "—")

        is_sold = data.get("is_sold", False)
        self._set_spec("Status", "SOLD" if is_sold else "Active")
        if is_sold:
            self._spec_labels["Status"].setStyleSheet(
                "font-size: 13px; font-weight: 700; color: #E74C3C;"
            )
        else:
            self._spec_labels["Status"].setStyleSheet(
                "font-size: 13px; font-weight: 500; color: #2ECC71;"
            )

        # Score breakdown. Sub-scores aren't stored in the database, so
        # recompute them from the listing when they're missing (fast, offline).
        if data.get("price_value_score") is None and data.get("title"):
            try:
                from src.scoring.deal_scorer import DealScorer
                r = DealScorer.score_listing(
                    description=data.get("description") or "",
                    title=data.get("title") or "",
                    price=data.get("price") or 0.0,
                    condition=data.get("condition") or "Good",
                    brand=data.get("brand") or "",
                    model=data.get("model") or "",
                    year=data.get("year"),
                    material=data.get("material") or "",
                    category=data.get("category") or "",
                    seller_username=data.get("seller_username") or "",
                    seller_rating=data.get("seller_rating"),
                    is_boosted=bool(data.get("is_boosted")),
                    date_posted=data.get("date_posted") or "",
                )
                data = {**data, **{k: v for k, v in r.items() if k.endswith("_score")},
                        "condition_sub_score": r["condition_score"]}
            except Exception:
                pass
        score_fields = {
            "price_value_score": data.get("price_value_score"),
            "component_score": data.get("component_score"),
            "condition_score": data.get("condition_sub_score"),
            "freshness_score": data.get("freshness_score"),
            "age_score": data.get("age_score"),
            "brand_score": data.get("brand_score"),
            "seller_score": data.get("seller_score"),
        }
        for key, val in score_fields.items():
            if key in self._score_bars:
                bar = self._score_bars[key]
                if val is not None:
                    bar._value_label.setText(f"{val:.0f}")
                    bar._value_label.setStyleSheet(
                        f"font-size: 14px; font-weight: 700; color: {score_color(val)};"
                    )
                else:
                    bar._value_label.setText("—")
                    bar._value_label.setStyleSheet(
                        "font-size: 14px; font-weight: 700; color: #555;"
                    )

        # Description
        desc = data.get("description", "")
        if desc:
            self.description_text.setPlainText(desc[:2000])
        else:
            self.description_text.setPlainText("No description available.")

    def _set_spec(self, label: str, value: str):
        if label in self._spec_labels:
            self._spec_labels[label].setText(value or "—")

    def _open_url(self):
        if self._current_url:
            webbrowser.open(self._current_url)

    def _copy_link(self):
        if self._current_url:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(self._current_url)
