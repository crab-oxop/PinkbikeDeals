"""
Dark and light theme stylesheets for PinkbikeDeals.

Color palette:
  - Accent: #E85D04 (Pinkbike orange)
  - Deal green: #2ECC71
  - Warning yellow: #F39C12
  - Danger red: #E74C3C
"""

# Score thresholds
SCORE_HOT = 80
SCORE_GOOD = 60
SCORE_FAIR = 40

# Colors
ACCENT = "#E85D04"
DEAL_GREEN = "#2ECC71"
DEAL_YELLOW = "#F39C12"
DEAL_RED = "#E74C3C"
DEAL_GRAY = "#95A5A6"


def score_color(score: float) -> str:
    """Return hex color for a deal score."""
    if score >= SCORE_HOT:
        return DEAL_GREEN
    elif score >= SCORE_GOOD:
        return DEAL_YELLOW
    elif score >= SCORE_FAIR:
        return DEAL_RED
    return DEAL_GRAY


DARK_STYLESHEET = """
/* ===== Global ===== */
QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    font-size: 13px;
}

/* ===== Main Window ===== */
QMainWindow {
    background-color: #1a1a2e;
}

QMainWindow::separator {
    background-color: #2d2d44;
    width: 1px;
    height: 1px;
}

/* ===== Menu Bar ===== */
QMenuBar {
    background-color: #16213e;
    color: #e0e0e0;
    border-bottom: 1px solid #2d2d44;
    padding: 2px 0;
}
QMenuBar::item:selected {
    background-color: #E85D04;
    color: white;
    border-radius: 4px;
}
QMenu {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #2d2d44;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item:selected {
    background-color: #E85D04;
    color: white;
    border-radius: 4px;
}
QMenu::separator {
    height: 1px;
    background-color: #2d2d44;
    margin: 4px 8px;
}

/* ===== Status Bar ===== */
QStatusBar {
    background-color: #16213e;
    color: #8899aa;
    border-top: 1px solid #2d2d44;
    font-size: 12px;
}
QStatusBar::item {
    border: none;
}

/* ===== Toolbar ===== */
QToolBar {
    background-color: #16213e;
    border-bottom: 1px solid #2d2d44;
    padding: 4px 8px;
    spacing: 8px;
}

/* ===== Push Buttons ===== */
QPushButton {
    background-color: #2d2d44;
    color: #e0e0e0;
    border: 1px solid #3d3d5c;
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: 500;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #3d3d5c;
    border-color: #E85D04;
}
QPushButton:pressed {
    background-color: #E85D04;
    color: white;
}
QPushButton:disabled {
    background-color: #1a1a2e;
    color: #555;
    border-color: #2d2d44;
}

/* Primary action buttons */
QPushButton#scanButton {
    background-color: #E85D04;
    color: white;
    border: none;
    font-weight: 600;
}
QPushButton#scanButton:hover {
    background-color: #FF6B1A;
}
QPushButton#scanButton:pressed {
    background-color: #CC4F00;
}
QPushButton#scanButton:disabled {
    background-color: #664422;
    color: #999;
}

/* ===== Table ===== */
QTableWidget, QTableView {
    background-color: #0f0f23;
    alternate-background-color: #141430;
    color: #e0e0e0;
    gridline-color: #1e1e3a;
    border: 1px solid #2d2d44;
    border-radius: 8px;
    selection-background-color: #E85D04;
    selection-color: white;
}
QTableWidget::item {
    padding: 4px 8px;
    border-bottom: 1px solid #1e1e3a;
}
QTableWidget::item:selected {
    background-color: rgba(232, 93, 4, 0.3);
    color: #ffffff;
}
QHeaderView::section {
    background-color: #16213e;
    color: #8899aa;
    border: none;
    border-bottom: 2px solid #2d2d44;
    border-right: 1px solid #1e1e3a;
    padding: 8px 12px;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
}
QHeaderView::section:hover {
    color: #E85D04;
}

/* ===== Scroll Bars ===== */
QScrollBar:vertical {
    background-color: #1a1a2e;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #3d3d5c;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #E85D04;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background-color: #1a1a2e;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background-color: #3d3d5c;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #E85D04;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ===== Combo Box ===== */
QComboBox {
    background-color: #2d2d44;
    color: #e0e0e0;
    border: 1px solid #3d3d5c;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 26px;
}
QComboBox:hover {
    border-color: #E85D04;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8899aa;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #2d2d44;
    selection-background-color: #E85D04;
    selection-color: white;
    border-radius: 6px;
}

/* ===== Line Edit / Spin Box ===== */
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #2d2d44;
    color: #e0e0e0;
    border: 1px solid #3d3d5c;
    border-radius: 6px;
    padding: 5px 10px;
    min-height: 26px;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #E85D04;
}

/* ===== Labels ===== */
QLabel#sectionTitle {
    color: #8899aa;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding-top: 8px;
}
QLabel#detailTitle {
    color: #ffffff;
    font-size: 18px;
    font-weight: 700;
}
QLabel#detailPrice {
    color: #2ECC71;
    font-size: 22px;
    font-weight: 700;
}
QLabel#detailScore {
    font-size: 28px;
    font-weight: 800;
}
QLabel#statValue {
    color: #E85D04;
    font-size: 16px;
    font-weight: 600;
}

/* ===== Splitter ===== */
QSplitter::handle {
    background-color: #2d2d44;
}
QSplitter::handle:horizontal {
    width: 2px;
}
QSplitter::handle:vertical {
    height: 2px;
}

/* ===== Group Box ===== */
QGroupBox {
    background-color: #16213e;
    border: 1px solid #2d2d44;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: 600;
}
QGroupBox::title {
    color: #8899aa;
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    font-size: 11px;
    text-transform: uppercase;
}

/* ===== Tab Widget ===== */
QTabWidget::pane {
    border: 1px solid #2d2d44;
    border-radius: 8px;
    background-color: #1a1a2e;
}
QTabBar::tab {
    background-color: #16213e;
    color: #8899aa;
    border: 1px solid #2d2d44;
    border-bottom: none;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 500;
}
QTabBar::tab:selected {
    background-color: #1a1a2e;
    color: #E85D04;
    border-bottom: 2px solid #E85D04;
}
QTabBar::tab:hover:!selected {
    color: #e0e0e0;
}

/* ===== Progress Bar ===== */
QProgressBar {
    background-color: #2d2d44;
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #E85D04;
    border-radius: 4px;
}

/* ===== Slider ===== */
QSlider::groove:horizontal {
    height: 4px;
    background: #2d2d44;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #E85D04;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}

/* ===== Check Box ===== */
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #3d3d5c;
    border-radius: 4px;
    background-color: #2d2d44;
}
QCheckBox::indicator:checked {
    background-color: #E85D04;
    border-color: #E85D04;
}

/* ===== Tool Tip ===== */
QToolTip {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #E85D04;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ===== Dialog ===== */
QDialog {
    background-color: #1a1a2e;
}
"""


LIGHT_STYLESHEET = """
QWidget {
    background-color: #f5f5f5;
    color: #2c2c2c;
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    font-size: 13px;
}
QMainWindow {
    background-color: #f5f5f5;
}
QMenuBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e0e0e0;
}
QMenuBar::item:selected {
    background-color: #E85D04;
    color: white;
    border-radius: 4px;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
}
QMenu::item:selected {
    background-color: #E85D04;
    color: white;
}
QStatusBar {
    background-color: #ffffff;
    color: #666;
    border-top: 1px solid #e0e0e0;
}
QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e0e0e0;
}
QPushButton {
    background-color: #ffffff;
    color: #2c2c2c;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    padding: 6px 16px;
    min-height: 28px;
}
QPushButton:hover {
    border-color: #E85D04;
}
QPushButton#scanButton {
    background-color: #E85D04;
    color: white;
    border: none;
    font-weight: 600;
}
QTableWidget, QTableView {
    background-color: #ffffff;
    alternate-background-color: #fafafa;
    color: #2c2c2c;
    gridline-color: #eeeeee;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    selection-background-color: rgba(232, 93, 4, 0.2);
    selection-color: #2c2c2c;
}
QHeaderView::section {
    background-color: #f8f8f8;
    color: #666;
    border: none;
    border-bottom: 2px solid #e0e0e0;
    padding: 8px 12px;
    font-weight: 600;
    font-size: 12px;
}
QComboBox {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    padding: 5px 10px;
}
QComboBox:hover { border-color: #E85D04; }
QLineEdit, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #d0d0d0;
    border-radius: 6px;
    padding: 5px 10px;
}
QLineEdit:focus, QSpinBox:focus { border-color: #E85D04; }
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
}
QGroupBox::title {
    color: #888;
}
QSplitter::handle { background-color: #e0e0e0; }
QLabel#sectionTitle { color: #888; font-size: 11px; font-weight: 700; }
QLabel#detailTitle { color: #2c2c2c; font-size: 18px; font-weight: 700; }
QLabel#detailPrice { color: #2ECC71; font-size: 22px; font-weight: 700; }
QLabel#detailScore { font-size: 28px; font-weight: 800; }
QTabBar::tab {
    background-color: #f0f0f0;
    border: 1px solid #e0e0e0;
    padding: 8px 20px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    color: #E85D04;
    border-bottom: 2px solid #E85D04;
}
QScrollBar:vertical {
    background-color: #f0f0f0;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #c0c0c0;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover { background-color: #E85D04; }
QProgressBar {
    background-color: #e0e0e0;
    border: none;
    border-radius: 4px;
    height: 6px;
    color: transparent;
}
QProgressBar::chunk {
    background-color: #E85D04;
    border-radius: 4px;
}
"""
