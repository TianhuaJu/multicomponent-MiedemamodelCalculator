# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 收集所有必要的模块
hiddenimports = [
    # PyQt5相关
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.sip',

    # matplotlib相关
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_qt5',
    'matplotlib.figure',
    'matplotlib.style',
    'matplotlib.font_manager',
    'matplotlib._path',
    'matplotlib.ft2font',

    # numpy和科学计算
    'numpy',
    'numpy.core',
    'numpy.core._methods',
    'numpy.lib.format',

    # 您的自定义模块
    'core',
    'core.UnifiedExtrapolationModel',
    'utils',
    'utils.tool',
    'GUI',
    'GUI.SingleCalculationWidget',
    'GUI.CompositionVariationWidget',
    'GUI.TemperatureVariationWidget',
    'GUI.ActivityCoefficientWidget',
    'GUI.ActivityCompositionVariationWidget',
    'GUI.ActivityTemperatureVariationWidget',
]

# 收集matplotlib的数据文件
matplotlib_datas = collect_data_files('matplotlib', include_py_files=False)

# 收集字体文件
font_datas = []
try:
    import matplotlib
    mpl_data_dir = matplotlib.get_data_path()
    font_datas.append((os.path.join(mpl_data_dir, 'fonts'), 'matplotlib/mpl-data/fonts'))
except:
    pass

# 定义数据文件
datas = [
('core/BinaryData', 'core/BinaryData'),
    # 图标文件
    ('app_icon.ico', '.'),
    # matplotlib数据文件
    *matplotlib_datas,
    # 字体文件
    *font_datas,
]

# 如果有其他数据文件夹，请添加
# 例如：('data', 'data'), ('config', 'config')

# 定义要排除的模块（减小文件大小）
excludes = [
    'tkinter',
    'unittest',
    'email',
    'http',
    'urllib',
    'xml',
    'pydoc',
    'doctest',
    # 注意：不要排除这些，因为可能被您的程序使用
    # 'argparse',
    # 'subprocess',
    # 'csv',
    # 'json',
    # 'pickle',
    'multiprocessing',
    'concurrent',
    'sqlite3',
    'lzma',
    'bz2',
    'zipfile',
    'tarfile',
    'IPython',
    'jupyter',
    'notebook',
    'qtconsole',
    'PIL',
    'tornado',
    'zmq',
]

# 分析阶段
a = Analysis(
    ['MiedemaModelApp_Pro.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 移除重复项
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# 创建可执行文件
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MiedemaModelCalculator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 建议设置为False，UPX可能导致兼容性问题
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为False隐藏控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app_icon.ico' if os.path.exists('app_icon.ico') else None,  # 条件性设置图标
)

# 如果需要生成文件夹版本而不是单文件，请使用以下配置：
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='MiedemaModelCalculator'
# )