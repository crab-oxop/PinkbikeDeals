"""
PinkbikeDeals Desktop Application entry point.

This is the primary way to launch PinkbikeDeals as a desktop app.
No console window, no CLI arguments needed — just double-click and go.
"""

import sys
import os
import logging

# Ensure the project root is on sys.path so 'src' is importable
# Works whether running from source or from PyInstaller bundle
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(_here))  # src/gui -> src -> root
if _root not in sys.path:
    sys.path.insert(0, _root)

# Handle PyInstaller frozen mode
if getattr(sys, 'frozen', False):
    _bundle_dir = sys._MEIPASS
    _root = os.path.dirname(sys.executable)
    if _root not in sys.path:
        sys.path.insert(0, _root)


def _get_asset_path(filename: str) -> str:
    """Get path to an asset file, works in dev and PyInstaller."""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'assets', filename)
    return os.path.join(_root, 'assets', filename)


def setup_logging():
    """Set up logging — file-based when frozen (no console), console when dev."""
    if getattr(sys, 'frozen', False):
        # Frozen app: log to file in app data directory
        from src.config import Config
        cfg = Config()
        log_dir = os.path.dirname(cfg.database.path)
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, 'pinkbike_deals.log')
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            filename=log_file,
            filemode='a',
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("cloudscraper").setLevel(logging.WARNING)


def main():
    setup_logging()

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon

    from src.config import Config
    from src.gui.main_window import MainWindow

    config = Config()

    app = QApplication(sys.argv)
    app.setApplicationName("PinkbikeDeals")
    app.setApplicationDisplayName("PinkbikeDeals")
    app.setOrganizationName("PinkbikeDeals")
    app.setApplicationVersion(config.version)

    # High DPI support
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Set application icon
    icon_path = _get_asset_path('icon.png')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow(config)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
