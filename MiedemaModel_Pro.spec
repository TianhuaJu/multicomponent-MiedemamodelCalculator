# MiedemaModel.spec (Corrected)
import os

block_cipher = None

a = Analysis(
    ['MiedemaModelApp_Pro.py'],
    # 确保 PyInstaller 能找到您的 GUI, core, utils 等模块
    pathex=[os.getcwd()],
    binaries=[],
    # 修正数据文件的源路径和目标路径
    datas=[
        ('core/BinaryData', 'core/BinaryData'),
        ('app_icon.ico', '.')
    ],
    hiddenimports=['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
                   'numpy', 'scipy', 'sqlite3', 'matplotlib', 'PyQt5.sip'],
    hookspath=[],
    hooksconfig={},
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
    name='MiedemaModel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='app_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MiedemaModel',
)