# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run_cli.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('alembic', 'alembic'),
        ('alembic.ini', '.'),
    ],
    hiddenimports=[
        'uvicorn.lifespan',
        'uvicorn.loops',
        'uvicorn.protocols',
        'passlib.handlers.bcrypt',
        'openpyxl',
        'pdfplumber',
        'pdfminer',
        'pdfminer.pdfparser',
        'pdfminer.pdfdocument',
        'pdfminer.pdfpage',
        'pdfminer.pdfinterp',
        'pdfminer.converter',
        'pdfminer.layout',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='arthsaarthi-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, # We need the console for stdout/stderr to be captured by Electron
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='arthsaarthi-backend',
)
