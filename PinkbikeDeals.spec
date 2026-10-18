# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PinkbikeDeals.

Build with:
    pyinstaller PinkbikeDeals.spec

Or use the provided build.bat script.
"""

import sys
from pathlib import Path

block_cipher = None
ROOT = Path(SPECPATH)

a = Analysis(
    [str(ROOT / 'run.pyw')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Include assets (icon, etc.)
        (str(ROOT / 'assets'), 'assets'),
    ],
    hiddenimports=[
        # SQLAlchemy dialects
        'sqlalchemy.dialects.sqlite',
        # cloudscraper internals
        'cloudscraper',
        'cloudscraper.interpreters',
        'cloudscraper.interpreters.native',
        'cloudscraper.user_agent',
        # thefuzz
        'thefuzz',
        'thefuzz.fuzz',
        'thefuzz.process',
        'Levenshtein',
        # Our modules
        'src',
        'src.config',
        'src.constants',
        'src.database',
        'src.database.models',
        'src.database.db',
        'src.scraper',
        'src.scraper.client',
        'src.scraper.parser',
        'src.scraper.categories',
        'src.scraper.scheduler',
        'src.scoring',
        'src.scoring.deal_scorer',
        'src.scoring.component_extractor',
        'src.scoring.build_valuator',
        'src.scoring.component_values',
        'src.utils',
        'src.utils.title_parser',
        'src.gui',
        'src.gui.app',
        'src.gui.main_window',
        'src.gui.listing_table',
        'src.gui.filter_panel',
        'src.gui.detail_panel',
        'src.gui.worker',
        'src.gui.theme',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'pytest',
    ],
    noarchive=False,
    optimize=1,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PinkbikeDeals',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # <-- No console window!
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'assets' / 'icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PinkbikeDeals',
)
