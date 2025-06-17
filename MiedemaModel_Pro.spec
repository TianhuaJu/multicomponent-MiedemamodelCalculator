# MiedemamodelApp_Pro.spec
import os

block_cipher = None

# --- Analysis Section ---
# PyInstaller 在这里分析你的代码，寻找依赖
a = Analysis(
    ['MiedemamodelApp_Pro.py'],
    pathex=[os.getcwd()],  # 确保PyInstaller能找到当前目录下的模块，比如GUI文件夹
    binaries=[],
    datas=[
        ('app_icon.ico', '.'), # 将图标文件打包到根目录
        # 如果您还有之前提到的数据库文件夹，也在这里添加
        # ('core/BinaryData', 'core/BinaryData')
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'numpy',
        'scipy',
        'matplotlib.backends.backend_qt5agg' # Matplotlib的PyQt5后端，非常重要
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# --- PYZ Section ---
# 将所有Python模块打包成一个 .pyz 压缩文件
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# --- EXE Section ---
# 创建最终的可执行文件
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=False, # 确保为False，以包含所有二进制文件
    name='MiedemaModel_Pro',  # 您可以自定义最终生成的文件名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True, # 使用UPX压缩（如果已安装），可减小文件体积
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 关键：设置为False以隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico'  # 关键：设置exe文件在Windows中的显示图标
)