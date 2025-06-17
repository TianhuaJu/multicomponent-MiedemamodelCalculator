# MiedemaModel.spec (Corrected for single-file build)
import os

block_cipher = None

a = Analysis(
    ['MiedemamodelApp.py'],
    # 确保 PyInstaller 能找到您的 GUI, core, utils 等自定义模块
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
    # exclude_binaries=True, # <--- 关键：删除或注释掉此行以创建单文件
    # 对于单文件构建，必须将二进制文件包含在exe内部，因此不能排除它们。
    # `False` 是默认值，删除此行即可。
    name='MiedemaModel',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,        # 正确：用于隐藏GUI程序的控制台窗口
    icon='app_icon.ico',  # 正确：用于设置exe文件的图标
)