import os
import sys
import traceback
import datetime
from typing import Callable, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
                             QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
                             QLabel, QLineEdit, QMainWindow, QMessageBox,
                             QProgressDialog, QPushButton, QSplitter, QTableWidget,
                             QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
                             QGridLayout, QFrame, QSizePolicy, QSpacerItem,
                             QHeaderView, QTabWidget)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import BinarySys as BinaryModel
import UnifiedExtrapolationModel as UEM


class ActivityTemperatureVariationWidget(QWidget):
	"""用于显示活度和活度系数随温度变化的窗口"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.parent_window = parent
		
		# 配置matplotlib以支持中文显示
		plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
		plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
		
		# 存储计算结果的数据结构
		self.calculation_results = {
			"activity": {},  # 活度数据
			"activity_coefficient": {}  # 活度系数数据
		}
		
		# 跟踪当前的计算参数，用于导出
		self.current_parameters = {
			"base_matrix": "",
			"solute": "",
			"solvent": "",
			"phase_state": "",
			"order_degree": "",
			"temp_range": []
		}
		
		# 存储历史计算结果
		self.calculation_history = {}
		
		self.has_calculated = False  # 跟踪是否已经计算
		self.legend_cids = []  # 保存图例事件连接ID
		
		# 设置窗口标题和大小
		self.setWindowTitle("热力学性质随温度变化计算器")
		self.resize(1200, 800)
		
		# 设置调色板
		self.setup_palette()
		
		# 初始化UI
		self.init_ui()
	
	def setup_palette (self):
		"""设置应用程序调色板"""
		palette = QPalette()
		
		# 设置背景色为浅灰色
		palette.setColor(QPalette.Window, QColor(240, 240, 245))
		
		# 设置控件背景色为白色
		palette.setColor(QPalette.Base, QColor(255, 255, 255))
		
		# 设置文本颜色
		palette.setColor(QPalette.Text, QColor(30, 30, 30))
		palette.setColor(QPalette.WindowText, QColor(30, 30, 30))
		
		# 设置高亮颜色
		palette.setColor(QPalette.Highlight, QColor(70, 130, 230))
		palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
		
		# 应用调色板
		self.setPalette(palette)
	
	def init_ui (self):
		"""初始化用户界面组件"""
		# 设置整体字体
		app_font = QFont("Microsoft YaHei", 10)
		self.setFont(app_font)
		
		# 主布局
		main_layout = QVBoxLayout()
		main_layout.setSpacing(15)  # 增加布局元素之间的间距
		main_layout.setContentsMargins(15, 15, 15, 15)  # 增加主布局边距
		
		# 创建分割器
		splitter = QSplitter(Qt.Horizontal)
		splitter.setHandleWidth(2)  # 设置分割线宽度
		
		# 创建左侧控制面板
		left_panel = self.create_left_panel()
		
		# 创建右侧面板（包括结果表格和图表）
		right_panel = self.create_right_panel()
		
		# 添加面板到分割器
		splitter.addWidget(left_panel)
		splitter.addWidget(right_panel)
		
		# 设置分割比例
		splitter.setSizes([400, 800])
		
		# 添加分割器到主布局
		main_layout.addWidget(splitter)
		
		# 设置窗口布局
		self.setLayout(main_layout)
		
		# 更新元素下拉列表
		self.update_element_dropdowns()
	
	def create_left_panel (self):
		"""创建左侧控制面板"""
		left_panel = QWidget()
		left_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
		
		# 使用垂直布局
		left_layout = QVBoxLayout()
		left_layout.setSpacing(20)  # 增加各组件之间的间距
		left_layout.setContentsMargins(15, 15, 15, 15)
		
		# 添加标题
		title_label = QLabel("热力学计算参数")
		title_font = QFont("Microsoft YaHei", 15, QFont.Bold)  # 增大字体
		title_label.setFont(title_font)
		title_label.setAlignment(Qt.AlignCenter)
		title_label.setStyleSheet("color: #2C3E50; margin-bottom: 10px;")
		left_layout.addWidget(title_label)
		
		# 添加水平分隔线
		separator = QFrame()
		separator.setFrameShape(QFrame.HLine)
		separator.setFrameShadow(QFrame.Sunken)
		separator.setLineWidth(1)
		separator.setStyleSheet("background-color: #BDC3C7;")
		left_layout.addWidget(separator)
		
		# 1. 合金组成区域
		left_layout.addWidget(self.create_alloy_composition_group())
		
		# 2. 温度范围区域
		left_layout.addWidget(self.create_temperature_range_group())
		
		# 3. 计算参数区域
		left_layout.addWidget(self.create_calculation_params_group())
		
		# 4. 外推模型选择区域
		left_layout.addWidget(self.create_model_selection_group())
		
		# 添加弹性空间
		left_layout.addStretch(1)
		
		# 5. 操作按钮区域
		left_layout.addWidget(self.create_action_buttons())
		
		left_panel.setLayout(left_layout)
		
		# 设置最小宽度和固定最大宽度，以避免控制面板过宽
		left_panel.setMinimumWidth(380)
		left_panel.setMaximumWidth(450)
		
		return left_panel
	
	def create_alloy_composition_group (self):
		"""创建合金组成区域"""
		group = QGroupBox("合金组成")
		group_font = QFont("Microsoft YaHei", 13, QFont.Bold)  # 增大字体
		group.setFont(group_font)
		
		group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #2C3E50;
            }
        """)
		
		layout = QFormLayout()
		layout.setSpacing(15)
		layout.setContentsMargins(15, 20, 15, 15)
		layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
		
		# 合金组成输入行
		comp_input_row = QHBoxLayout()
		
		self.matrix_input = QLineEdit()
		self.matrix_input.setPlaceholderText("例如: Fe0.7Ni0.3")
		self.matrix_input.setMinimumHeight(36)  # 增加高度
		self.matrix_input.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		self.matrix_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                padding: 5px;
                background-color: #F8F9F9;
                font-size: 12pt;
            }
            QLineEdit:focus {
                border: 1px solid #3498DB;
                background-color: white;
            }
        """)
		
		update_btn = QPushButton("更新")
		update_btn.setFixedWidth(80)
		update_btn.setMinimumHeight(36)  # 增加高度
		update_btn.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		update_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #1F618D;
            }
        """)
		update_btn.clicked.connect(self.update_element_dropdowns)
		
		comp_input_row.addWidget(self.matrix_input)
		comp_input_row.addWidget(update_btn)
		
		label = self.create_label("合金组成:")
		label.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		layout.addRow(label, comp_input_row)
		
		# 元素选择区域
		element_layout = QGridLayout()
		element_layout.setSpacing(10)
		element_layout.setColumnStretch(0, 1)
		element_layout.setColumnStretch(1, 2)
		
		# 溶剂元素下拉框
		self.solvent_combo = self.create_combo_box()
		self.solvent_combo.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		
		# 溶质元素下拉框
		self.solute_combo = self.create_combo_box()
		self.solute_combo.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		
		# 添加到布局
		solvent_label = self.create_label("溶剂元素:")
		solvent_label.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		solute_label = self.create_label("溶质元素:")
		solute_label.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		
		element_layout.addWidget(solvent_label, 0, 0)
		element_layout.addWidget(self.solvent_combo, 0, 1)
		element_layout.addWidget(solute_label, 1, 0)
		element_layout.addWidget(self.solute_combo, 1, 1)
		
		# 使用QWidget包装网格布局
		element_widget = QWidget()
		element_widget.setLayout(element_layout)
		
		element_label = self.create_label("元素选择:")
		element_label.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		layout.addRow(element_label, element_widget)
		
		# 设置布局
		group.setLayout(layout)
		
		return group
	
	def create_temperature_range_group (self):
		"""创建温度范围设置区域"""
		group = QGroupBox("温度范围")
		group_font = QFont("Microsoft YaHei", 13, QFont.Bold)  # 增大字体
		group.setFont(group_font)
		
		group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #2C3E50;
            }
        """)
		
		layout = QGridLayout()
		layout.setSpacing(15)
		layout.setContentsMargins(15, 20, 15, 15)
		
		# 创建温度范围控件
		self.min_temp = self.create_spin_box(300, 3000, 800, 50, " K")
		self.min_temp.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		
		self.max_temp = self.create_spin_box(300, 3000, 1600, 50, " K")
		self.max_temp.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		
		self.step_temp = self.create_spin_box(10, 200, 50, 10, " K")
		self.step_temp.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		
		# 添加标签
		min_label = self.create_label("最小温度:")
		min_label.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		max_label = self.create_label("最大温度:")
		max_label.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		step_label = self.create_label("温度步长:")
		step_label.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		
		# 添加组件到网格布局
		layout.addWidget(min_label, 0, 0)
		layout.addWidget(self.min_temp, 0, 1)
		layout.addWidget(max_label, 1, 0)
		layout.addWidget(self.max_temp, 1, 1)
		layout.addWidget(step_label, 2, 0)
		layout.addWidget(self.step_temp, 2, 1)
		
		# 设置布局
		group.setLayout(layout)
		
		return group
	
	def create_calculation_params_group (self):
		"""创建计算参数区域"""
		group = QGroupBox("计算参数")
		group_font = QFont("Microsoft YaHei", 13, QFont.Bold)  # 增大字体
		group.setFont(group_font)
		
		group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #2C3E50;
            }
        """)
		
		layout = QFormLayout()
		layout.setSpacing(15)
		layout.setContentsMargins(15, 20, 15, 15)
		layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
		
		# 相态选择
		self.phase_combo = self.create_combo_box()
		self.phase_combo.addItems(["固态 (S)", "液态 (L)"])
		self.phase_combo.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		
		phase_label = self.create_label("相态:")
		phase_label.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		layout.addRow(phase_label, self.phase_combo)
		
		# 有序度选择
		self.order_combo = self.create_combo_box()
		self.order_combo.addItems(["固溶体 (SS)", "非晶态 (AMP)", "金属间化合物 (IM)"])
		self.order_combo.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		
		order_label = self.create_label("类型:")
		order_label.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		layout.addRow(order_label, self.order_combo)
		
		# 热力学性质选择
		self.property_combo = self.create_combo_box()
		self.property_combo.addItems([
			"活度 (a)",
			"活度系数 (lnγ)"
		])
		self.property_combo.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		self.property_combo.currentIndexChanged.connect(self.update_plot)
		
		property_label = self.create_label("热力学性质:")
		property_label.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		layout.addRow(property_label, self.property_combo)
		
		# 外推模型选择
		self.geo_model_combo = self.create_combo_box()
		self.geo_model_combo.addItems(["UEM1", "UEM2_N", "GSM", "T-K", "K", "M"])
		self.geo_model_combo.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		
		geo_model_label = self.create_label("外推模型:")
		geo_model_label.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
		layout.addRow(geo_model_label, self.geo_model_combo)
		
		# 设置布局
		group.setLayout(layout)
		
		return group
	
	def create_model_selection_group (self):
		"""创建外推模型选择区域"""
		group = QGroupBox("外推模型选择")
		group_font = QFont("Microsoft YaHei", 13, QFont.Bold)  # 增大字体
		group.setFont(group_font)
		
		group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #2C3E50;
            }
        """)
		
		layout = QGridLayout()
		layout.setSpacing(15)
		layout.setContentsMargins(15, 20, 15, 15)
		
		# 创建模型选择复选框
		self.model_checkboxes = {}
		models = [
			("Kohler (K)", "K"),
			("Muggianu (M)", "M"),
			("Toop-Kohler (T-K)", "T-K"),
			("GSM/Chou", "GSM"),
			("UEM1", "UEM1"),
			("UEM2_N", "UEM2_N")
		]
		
		# 美化复选框样式
		checkbox_style = """
            QCheckBox {
                spacing: 8px;
                font-size: 12pt;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #BDC3C7;
                background-color: white;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #3498DB;
                background-color: #3498DB;
                border-radius: 3px;
            }
        """
		
		for index, (name, key) in enumerate(models):
			checkbox = QCheckBox(name)
			checkbox.setMinimumHeight(30)  # 增加高度
			checkbox.setFont(QFont("Microsoft YaHei", 12))  # 增大字体
			checkbox.setStyleSheet(checkbox_style)
			
			if key in ["UEM1", "GSM"]:  # 默认选中一些模型
				checkbox.setChecked(True)
			
			self.model_checkboxes[key] = checkbox
			
			row = index // 2  # 每行两个控件
			col = index % 2
			layout.addWidget(checkbox, row, col)
		
		# 设置布局
		group.setLayout(layout)
		
		return group
	
	def create_action_buttons (self):
		"""创建操作按钮区域"""
		frame = QFrame()
		frame.setFrameShape(QFrame.StyledPanel)
		frame.setStyleSheet("""
            QFrame {
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                background-color: white;
            }
        """)
		
		layout = QHBoxLayout()
		layout.setSpacing(15)
		layout.setContentsMargins(15, 15, 15, 15)
		
		# 计算按钮
		calculate_button = QPushButton("计算")
		calculate_button.setMinimumHeight(45)  # 增加高度
		calculate_button.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))  # 增大字体
		calculate_button.setStyleSheet("""
            QPushButton {
                background-color: #2ECC71;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 13pt;
            }
            QPushButton:hover {
                background-color: #27AE60;
            }
            QPushButton:pressed {
                background-color: #1E8449;
            }
        """)
		calculate_button.clicked.connect(self.calculate_all_properties)
		
		# 导出按钮
		export_button = QPushButton("导出数据")
		export_button.setMinimumHeight(45)  # 增加高度
		export_button.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))  # 增大字体
		export_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 13pt;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #1F618D;
            }
        """)
		export_button.clicked.connect(self.export_data)
		
		# 添加按钮到布局
		layout.addWidget(calculate_button)
		layout.addWidget(export_button)
		
		frame.setLayout(layout)
		
		return frame
	
	def create_right_panel (self):
		"""创建右侧面板（包括结果表格和图表）"""
		right_panel = QWidget()
		right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		
		layout = QVBoxLayout()
		layout.setSpacing(10)
		layout.setContentsMargins(10, 10, 10, 10)
		
		# 创建上下分割器
		splitter = QSplitter(Qt.Vertical)
		splitter.setHandleWidth(2)
		
		# 创建结果显示区域（上部）
		results_panel = self.create_results_panel()
		
		# 创建图表区域（下部）
		chart_panel = self.create_chart_panel()
		
		# 添加面板到分割器
		splitter.addWidget(results_panel)
		splitter.addWidget(chart_panel)
		
		# 设置分割比例（上:下 = 1:2）
		splitter.setSizes([300, 600])
		
		# 添加分割器到布局
		layout.addWidget(splitter)
		
		# 设置布局
		right_panel.setLayout(layout)
		
		return right_panel
	
	def create_results_panel (self):
		"""创建结果显示区域"""
		results_frame = QFrame()
		results_frame.setFrameShape(QFrame.StyledPanel)
		results_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                background-color: white;
            }
        """)
		
		layout = QVBoxLayout()
		layout.setSpacing(10)
		layout.setContentsMargins(10, 10, 10, 10)
		
		# 创建标题
		title_label = QLabel("计算结果与历史数据")
		title_font = QFont("Microsoft YaHei", 14, QFont.Bold)
		title_label.setFont(title_font)
		title_label.setAlignment(Qt.AlignCenter)
		title_label.setStyleSheet("color: #2C3E50; margin-bottom: 5px;")
		layout.addWidget(title_label)
		
		# 创建结果表格
		self.results_table = QTableWidget()
		self.results_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 6px;
                font-weight: bold;
                border: 1px solid #E0E0E0;
                font-size: 12pt;
            }
            QTableWidget::item {
                padding: 4px;
                font-size: 11pt;
            }
        """)
		
		# 设置表格列
		self.results_table.setColumnCount(4)
		self.results_table.setHorizontalHeaderLabels(["温度(K)", "模型", "活度(a)", "活度系数(lnγ)"])
		
		# 调整列宽
		header = self.results_table.horizontalHeader()
		header.setSectionResizeMode(QHeaderView.Stretch)
		self.results_table.verticalHeader().setVisible(False)  # 隐藏行号
		
		# 创建历史记录控制区域
		history_frame = QFrame()
		history_frame.setFrameShape(QFrame.NoFrame)
		
		history_layout = QHBoxLayout()
		history_layout.setContentsMargins(0, 0, 0, 0)
		
		# 历史记录下拉菜单
		history_label = QLabel("历史记录:")
		history_label.setFont(QFont("Microsoft YaHei", 12))
		
		self.history_combo = QComboBox()
		self.history_combo.setMinimumHeight(32)
		self.history_combo.setMinimumWidth(200)
		self.history_combo.setFont(QFont("Microsoft YaHei", 11))
		self.history_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                padding: 5px;
                background-color: #F8F9F9;
            }
            QComboBox:hover {
                border: 1px solid #3498DB;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 24px;
                border-left: 1px solid #BDC3C7;
            }
        """)
		self.history_combo.currentIndexChanged.connect(self.load_history_item)
		
		# 保存当前结果按钮
		save_button = QPushButton("保存当前结果")
		save_button.setFont(QFont("Microsoft YaHei", 11))
		save_button.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #1F618D;
            }
        """)
		save_button.clicked.connect(self.save_current_result)
		
		# 清除历史按钮
		clear_button = QPushButton("清除历史")
		clear_button.setFont(QFont("Microsoft YaHei", 11))
		clear_button.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #C0392B;
            }
            QPushButton:pressed {
                background-color: #A93226;
            }
        """)
		clear_button.clicked.connect(self.clear_history)
		
		# 添加控件到布局
		history_layout.addWidget(history_label)
		history_layout.addWidget(self.history_combo)
		history_layout.addWidget(save_button)
		history_layout.addWidget(clear_button)
		
		history_frame.setLayout(history_layout)
		
		# 添加表格和历史控制到主布局
		layout.addWidget(self.results_table)
		layout.addWidget(history_frame)
		
		# 设置布局
		results_frame.setLayout(layout)
		
		return results_frame
	
	def create_chart_panel (self):
		"""创建图表显示区域"""
		chart_frame = QFrame()
		chart_frame.setFrameShape(QFrame.StyledPanel)
		chart_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #BDC3C7;
                border-radius: 6px;
                background-color: white;
            }
        """)
		
		layout = QVBoxLayout()
		layout.setSpacing(5)
		layout.setContentsMargins(10, 10, 10, 10)
		
		# 创建标题
		title_label = QLabel("温度变化图表")
		title_font = QFont("Microsoft YaHei", 14, QFont.Bold)
		title_label.setFont(title_font)
		title_label.setAlignment(Qt.AlignCenter)
		title_label.setStyleSheet("color: #2C3E50; margin-bottom: 5px;")
		layout.addWidget(title_label)
		
		# 创建图表
		self.figure = Figure(figsize=(8, 6), dpi=100)
		self.canvas = FigureCanvas(self.figure)
		self.canvas.setStyleSheet("background-color: white;")
		
		# 创建工具栏
		toolbar_frame = QFrame()
		toolbar_frame.setFrameShape(QFrame.NoFrame)
		toolbar_frame.setLineWidth(0)
		toolbar_frame.setContentsMargins(0, 0, 0, 0)
		
		toolbar_layout = QHBoxLayout()
		toolbar_layout.setContentsMargins(0, 0, 0, 0)
		toolbar_layout.setSpacing(0)
		
		self.toolbar = NavigationToolbar(self.canvas, self)
		self.toolbar.setStyleSheet("""
            QToolBar {
                border: 0px;
                background-color: #F8F9F9;
                spacing: 5px;
            }
            QToolButton {
                border: 1px solid #BDC3C7;
                border-radius: 3px;
                background-color: white;
                padding: 3px;
            }
            QToolButton:hover {
                background-color: #ECF0F1;
            }
            QToolButton:pressed {
                background-color: #D6DBDF;
            }
        """)
		
		toolbar_layout.addWidget(self.toolbar)
		toolbar_layout.addStretch(1)
		
		toolbar_frame.setLayout(toolbar_layout)
		
		# 添加到布局
		layout.addWidget(toolbar_frame)
		layout.addWidget(self.canvas)
		
		# 设置布局
		chart_frame.setLayout(layout)
		
		return chart_frame
	
	def create_label (self, text):
		"""创建标准化的标签"""
		label = QLabel(text)
		label.setStyleSheet("""
            QLabel {
                color: #2C3E50;
                font-weight: bold;
                font-size: 12pt;
            }
        """)
		return label
	
	def create_combo_box (self):
		"""创建标准化的下拉框"""
		combo = QComboBox()
		combo.setMinimumHeight(36)  # 增加高度
		combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                padding: 5px;
                background-color: #F8F9F9;
                font-size: 12pt;
            }
            QComboBox:hover {
                border: 1px solid #3498DB;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 24px;
                border-left: 1px solid #BDC3C7;
            }
        """)
		return combo
	
	def create_spin_box (self, min_val, max_val, default_val, step, suffix=""):
		"""创建标准化的数字输入框"""
		spin = QDoubleSpinBox()
		spin.setRange(min_val, max_val)
		spin.setValue(default_val)
		spin.setSingleStep(step)
		spin.setSuffix(suffix)
		spin.setMinimumHeight(36)  # 增加高度
		spin.setStyleSheet("""
            QDoubleSpinBox {
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                padding: 5px;
                background-color: #F8F9F9;
                font-size: 12pt;
            }
            QDoubleSpinBox:hover {
                border: 1px solid #3498DB;
            }
            QDoubleSpinBox:focus {
                border: 1px solid #3498DB;
                background-color: white;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 20px;
                border-left: 1px solid #BDC3C7;
                background-color: #ECF0F1;
            }
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #D6DBDF;
            }
        """)
		return spin
	
	def update_element_dropdowns (self):
		"""根据当前输入的合金组成更新元素下拉列表"""
		comp_input = self.matrix_input.text().strip()
		if not comp_input:
			return
		
		try:
			# 解析合金组成
			composition = self.parse_composition(comp_input)
			if not composition:
				return
			
			# 记住当前选中的值（如果有）
			current_solvent = self.solvent_combo.currentText()
			current_solute = self.solute_combo.currentText()
			
			# 获取合金中的元素列表
			elements = list(composition.keys())
			
			# 阻止信号触发，防止更新时引起不必要的事件
			self.solvent_combo.blockSignals(True)
			self.solute_combo.blockSignals(True)
			
			# 清空当前下拉列表内容
			self.solvent_combo.clear()
			self.solute_combo.clear()
			
			# 添加合金中的元素到下拉列表
			self.solvent_combo.addItems(elements)
			self.solute_combo.addItems(elements)
			
			# 尝试恢复之前的选择（如果元素仍然存在）
			solvent_index = self.solvent_combo.findText(current_solvent)
			if solvent_index >= 0:
				self.solvent_combo.setCurrentIndex(solvent_index)
			elif len(elements) >= 1:
				self.solvent_combo.setCurrentIndex(0)  # 默认选择第一个元素
			
			solute_index = self.solute_combo.findText(current_solute)
			if solute_index >= 0:
				self.solute_combo.setCurrentIndex(solute_index)
			elif len(elements) >= 2:
				self.solute_combo.setCurrentIndex(1)  # 默认选择第二个元素
			elif len(elements) >= 1 and elements[0] != self.solvent_combo.currentText():
				self.solute_combo.setCurrentIndex(0)  # 选择第一个元素(如果与溶剂不同)
			elif len(elements) >= 1:
				self.solute_combo.setCurrentIndex(0)  # 实在没有其他选择时选择第一个
			
			# 恢复信号连接
			self.solvent_combo.blockSignals(False)
			self.solute_combo.blockSignals(False)
		
		except Exception as e:
			print(f"更新元素下拉列表时出错: {str(e)}")
	
	def parse_composition (self, comp_input):
		"""解析合金组成输入字符串，例如Fe0.7Ni0.3"""
		import re
		composition = {}
		# 正则表达式匹配元素和其对应的比例
		pattern = r'([A-Z][a-z]*)(\d*\.?\d*)'
		
		matches = re.findall(pattern, comp_input)
		
		for element, ratio_str in matches:
			# 如果没有指定比例，默认为1
			ratio = float(ratio_str) if ratio_str else 1.0
			composition[element] = ratio
		
		# 归一化组成
		total = sum(composition.values())
		if total > 0:
			for element in composition:
				composition[element] /= total
		
		return composition
	
	def calculate_all_properties (self):
		"""计算所有热力学性质随温度变化"""
		# 获取基本参数
		matrix_input = self.matrix_input.text().strip()
		if not matrix_input:
			QMessageBox.warning(self, "输入错误", "请输入基体合金组成")
			return
		
		try:
			base_matrix = self.parse_composition(matrix_input)
			if not base_matrix:
				QMessageBox.warning(self, "解析错误", "无法解析基体合金组成，请使用格式如Fe0.7Ni0.3")
				return
		except Exception as e:
			QMessageBox.critical(self, "解析错误", f"解析基体合金组成时出错: {str(e)}")
			return
		
		# 获取溶剂和溶质元素
		solvent = self.solvent_combo.currentText().strip()
		solute = self.solute_combo.currentText().strip()
		
		if not solvent or not solute:
			QMessageBox.warning(self, "输入错误", "请选择溶剂元素和溶质元素")
			return
		
		if solvent == solute:
			QMessageBox.warning(self, "输入错误", "溶剂元素和溶质元素不能相同")
			return
		
		# 获取相态
		phase_state = "S" if self.phase_combo.currentText().startswith("固态") else "L"
		
		# 获取有序度
		order_text = self.order_combo.currentText()
		if order_text.startswith("固溶体"):
			order_degree = "SS"
		elif order_text.startswith("非晶态"):
			order_degree = "AMP"
		else:
			order_degree = "IM"
		
		# 获取外推模型
		geo_model = self.geo_model_combo.currentText()
		
		# 检查选中的模型
		selected_models = [key for key, checkbox in self.model_checkboxes.items() if checkbox.isChecked()]
		if not selected_models:
			QMessageBox.warning(self, "模型选择", "请至少选择一个外推模型")
			return
		
		# 创建温度范围
		min_temp = self.min_temp.value()
		max_temp = self.max_temp.value()
		step_temp = self.step_temp.value()
		
		if min_temp >= max_temp:
			QMessageBox.warning(self, "温度设置错误", "最小温度必须小于最大温度")
			return
		
		temp_range = np.arange(min_temp, max_temp + step_temp / 2, step_temp)
		
		# 存储当前参数
		self.current_parameters = {
			"base_matrix": matrix_input,
			"solute": solute,
			"solvent": solvent,
			"phase_state": phase_state,
			"order_degree": order_degree,
			"geo_model": geo_model,
			"temp_range": temp_range.tolist()
		}
		
		# 清空之前的计算结果
		self.calculation_results = {
			"activity": {},  # 活度数据
			"activity_coefficient": {}  # 活度系数数据
		}
		
		# 获取不同模型的函数映射
		model_functions = {
			"K": UEM.Kohler,
			"M": UEM.Muggianu,
			"T-K": UEM.Toop_Kohler,
			"GSM": UEM.GSM,
			"UEM1": UEM.UEM1,
			"UEM2_N": UEM.UEM2_N
		}
		
		# 显示进度对话框
		progress = QProgressDialog("计算中...", "取消", 0, len(selected_models) * len(temp_range) * 2, self)
		progress.setWindowTitle("计算进度")
		progress.setStyleSheet("""
            QProgressDialog {
                font-size: 12px;
                background-color: white;
            }
            QProgressBar {
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                text-align: center;
                background-color: #F8F9F9;
            }
            QProgressBar::chunk {
                background-color: #3498DB;
                width: 5px;
            }
        """)
		progress.setWindowModality(Qt.WindowModal)
		progress.setMinimumDuration(0)
		progress.setValue(0)
		
		# 计算每个模型在不同温度下的热力学性质
		try:
			progress_count = 0
			
			# 为每个选中的模型执行计算
			for model_key in selected_models:
				if progress.wasCanceled():
					break
				
				model_func = model_functions.get(model_key)
				if not model_func:
					continue
				
				# 初始化该模型的不同热力学性质的数据结构
				for prop in ["activity", "activity_coefficient"]:
					self.calculation_results[prop][model_key] = {"temperatures": [], "values": []}
				
				# 计算不同温度下的活度和活度系数
				valid_temperatures = []
				valid_activity_values = []
				valid_activity_coef_values = []
				
				for temp in temp_range:
					if progress.wasCanceled():
						break
					
					# 计算活度
					try:
						progress.setLabelText(f"计算 {model_key} 模型在温度 {temp:.1f}K 下的活度...")
						activity_value = UEM.activity_calc_numerical(
								base_matrix, solute, solvent, temp,
								phase_state, order_degree, model_func, geo_model
						)
					except Exception as e:
						print(f"计算温度 {temp}K 的活度时出错: {str(e)}")
						# 尝试使用数值方法
						try:
							# 这里可以添加数值方法的实现
							activity_value = None  # 暂时设为None
						except:
							activity_value = None
					
					# 计算活度系数
					try:
						progress.setLabelText(f"计算 {model_key} 模型在温度 {temp:.1f}K 下的活度系数...")
						activity_coef_value = UEM.activityCoefficient_calc_numerical(
								base_matrix, solute, solvent, temp,
								phase_state, order_degree, model_func, geo_model
						)
					except Exception as e:
						print(f"计算温度 {temp}K 的活度系数时出错: {str(e)}")
						# 尝试使用数值方法
						try:
							# 这里可以添加数值方法的实现
							activity_coef_value = None  # 暂时设为None
						except:
							activity_coef_value = None
					
					# 只有当计算成功时才添加数据点
					if activity_value is not None or activity_coef_value is not None:
						valid_temperatures.append(temp)
						valid_activity_values.append(activity_value)
						valid_activity_coef_values.append(activity_coef_value)
					
					progress_count += 2
					progress.setValue(progress_count)
				
				# 存储有效的计算结果
				if valid_temperatures:
					self.calculation_results["activity"][model_key]["temperatures"] = np.array(valid_temperatures)
					self.calculation_results["activity"][model_key]["values"] = np.array(valid_activity_values)
					self.calculation_results["activity_coefficient"][model_key]["temperatures"] = np.array(
							valid_temperatures)
					self.calculation_results["activity_coefficient"][model_key]["values"] = np.array(
							valid_activity_coef_values)
			
			# 关闭进度对话框
			progress.close()
			
			# 检查是否有有效数据
			has_valid_data = False
			for prop in self.calculation_results:
				for model_key in self.calculation_results[prop]:
					if len(self.calculation_results[prop][model_key]["temperatures"]) > 0:
						has_valid_data = True
						break
				if has_valid_data:
					break
			
			if not has_valid_data:
				QMessageBox.warning(self, "无有效数据",
				                    "在指定温度范围内未能获得有效计算结果。请尝试调整温度范围或参数。")
				return
			
			# 标记已计算
			self.has_calculated = True
			
			# 更新图表和结果表格
			self.update_plot()
			self.update_results_table()
			
			# 显示成功消息
			QMessageBox.information(self, "计算完成", "计算完成，您可以查看表格和图表结果。")
		
		except Exception as e:
			# 关闭进度对话框
			progress.close()
			
			# 显示错误消息
			QMessageBox.critical(self, "计算错误", f"计算过程中发生错误: {str(e)}")
			traceback.print_exc()
	
	def update_results_table (self):
		"""更新结果表格"""
		if not self.has_calculated:
			return
		
		# 获取当前选择的热力学性质
		property_index = self.property_combo.currentIndex()
		property_types = ["activity", "activity_coefficient"]
		if property_index >= len(property_types):
			return
		
		selected_property = property_types[property_index]
		
		# 获取该性质的计算结果
		model_results = self.calculation_results[selected_property]
		
		# 清空表格
		self.results_table.clearContents()
		self.results_table.setRowCount(0)
		
		# 收集所有温度点和模型
		all_temps = set()
		all_models = []
		
		for model_key, data in model_results.items():
			if "temperatures" in data and len(data["temperatures"]) > 0:
				all_temps.update(data["temperatures"])
				all_models.append(model_key)
		
		# 如果没有数据则返回
		if not all_temps:
			return
		
		# 排序温度点
		all_temps = sorted(all_temps)
		
		# 设置表格行数
		total_rows = len(all_temps) * len(all_models)
		self.results_table.setRowCount(total_rows)
		
		# 填充表格
		row_index = 0
		for temp in all_temps:
			for model_key in all_models:
				# 检查该模型是否有该温度点的数据
				if model_key not in model_results:
					continue
				
				data = model_results[model_key]
				if "temperatures" not in data or len(data["temperatures"]) == 0:
					continue
				
				# 查找温度点索引
				temp_idx = np.where(data["temperatures"] == temp)[0]
				if len(temp_idx) == 0:
					continue
				
				temp_idx = temp_idx[0]
				
				# 获取活度/活度系数值
				if selected_property == "activity":
					prop_value = data["values"][temp_idx]
					# 获取对应的活度系数值
					if model_key in self.calculation_results["activity_coefficient"]:
						act_coef_data = self.calculation_results["activity_coefficient"][model_key]
						if "temperatures" in act_coef_data and len(act_coef_data["temperatures"]) > 0:
							act_coef_idx = np.where(act_coef_data["temperatures"] == temp)[0]
							if len(act_coef_idx) > 0:
								act_coef_value = act_coef_data["values"][act_coef_idx[0]]
							else:
								act_coef_value = None
						else:
							act_coef_value = None
					else:
						act_coef_value = None
				else:  # activity_coefficient
					act_coef_value = data["values"][temp_idx]
					# 获取对应的活度值
					if model_key in self.calculation_results["activity"]:
						act_data = self.calculation_results["activity"][model_key]
						if "temperatures" in act_data and len(act_data["temperatures"]) > 0:
							act_idx = np.where(act_data["temperatures"] == temp)[0]
							if len(act_idx) > 0:
								prop_value = act_data["values"][act_idx[0]]
							else:
								prop_value = None
						else:
							prop_value = None
					else:
						prop_value = None
				
				# 填充表格
				# 温度
				temp_item = QTableWidgetItem(f"{temp:.1f}")
				temp_item.setTextAlignment(Qt.AlignCenter)
				self.results_table.setItem(row_index, 0, temp_item)
				
				# 模型
				model_item = QTableWidgetItem(model_key)
				model_item.setTextAlignment(Qt.AlignCenter)
				self.results_table.setItem(row_index, 1, model_item)
				
				# 活度
				if prop_value is not None and not np.isnan(prop_value):
					activity_item = QTableWidgetItem(f"{prop_value:.6e}")
					activity_item.setTextAlignment(Qt.AlignCenter)
					self.results_table.setItem(row_index, 2, activity_item)
				
				# 活度系数
				if act_coef_value is not None and not np.isnan(act_coef_value):
					activity_coef_item = QTableWidgetItem(f"{act_coef_value:.6e}")
					activity_coef_item.setTextAlignment(Qt.AlignCenter)
					self.results_table.setItem(row_index, 3, activity_coef_item)
				
				row_index += 1
		
		# 调整表格显示的实际行数
		self.results_table.setRowCount(row_index)
		
		# 调整行高
		for i in range(row_index):
			self.results_table.setRowHeight(i, 28)
	
	def update_plot (self):
		"""基于选择的热力学性质更新图表"""
		if not self.has_calculated:
			return
		
		# 获取当前选择的热力学性质
		property_index = self.property_combo.currentIndex()
		property_types = ["activity", "activity_coefficient"]
		if property_index >= len(property_types):
			return
		
		selected_property = property_types[property_index]
		
		# 获取该性质的计算结果
		model_results = self.calculation_results[selected_property]
		
		# 没有数据则返回
		if not model_results:
			return
		
		# 绘制图表
		self.plot_property_variation(model_results, selected_property)
	
	def plot_property_variation (self, model_results, property_type):
		"""绘制热力学性质随温度变化的图表"""
		from matplotlib import ticker
		
		self.figure.clear()
		
		# 设置图表风格
		plt.style.use('seaborn-v0_8-whitegrid')
		
		# 创建子图
		ax = self.figure.add_subplot(111)
		
		# 设置颜色循环和标记
		colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
		markers = ['o', 's', '^', 'D', 'v', '<', '>']
		plots = []
		labels = []
		
		# 为每个模型绘制线条
		for i, (model_key, data) in enumerate(model_results.items()):
			if "temperatures" not in data or len(data["temperatures"]) == 0 or "values" not in data:
				continue
			
			temperatures = data["temperatures"]
			values = data["values"]
			
			# 确保数据为numpy数组并且是数值类型
			if not isinstance(values, np.ndarray):
				values = np.array(values, dtype=np.float64)
			
			# 过滤非法值
			valid_indices = np.ones(len(values), dtype=bool)
			try:
				nan_indices = np.isnan(values)
				valid_indices = ~nan_indices
			except (TypeError, ValueError):
				# 如果无法检查NaN，尝试另一种方法过滤
				print(f"无法检查NaN值，数据类型: {type(values)}")
				valid_indices = np.array([i is not None and (not isinstance(i, (float, int)) or (
					not np.isnan(float(i)) if isinstance(i, (float, int)) else True)) for i in values])
			
			if not np.any(valid_indices):
				continue
			
			temperatures = temperatures[valid_indices]
			values = values[valid_indices]
			
			if len(temperatures) == 0:
				continue
			
			color_idx = i % len(colors)
			marker_idx = i % len(markers)
			
			# 减少数据点数量，提高清晰度
			if len(temperatures) > 20:
				skip = len(temperatures) // 20
				plot_temps = temperatures[::skip]
				plot_values = values[::skip]
			else:
				plot_temps = temperatures
				plot_values = values
			
			# 绘制曲线和数据点
			line, = ax.plot(temperatures, values,
			                color=colors[color_idx],
			                marker=markers[marker_idx],
			                linewidth=2.5,
			                markersize=7,
			                alpha=0.8,
			                label=self.model_checkboxes[model_key].text())
			
			plots.append(line)
			labels.append(self.model_checkboxes[model_key].text())
		
		# 构建标题
		solute = self.current_parameters["solute"]
		matrix_input = self.current_parameters["base_matrix"]
		phase_dict = {"S": "固态", "L": "液态"}
		phase_text = phase_dict.get(self.current_parameters["phase_state"], "固态")
		order_dict = {"SS": "固溶体", "AMP": "非晶态", "IM": "金属间化合物"}
		order_text = order_dict.get(self.current_parameters["order_degree"], "固溶体")
		geo_model = self.current_parameters["geo_model"]
		solvent = self.current_parameters["solvent"]
		
		# 设置标题和标签
		if property_type == "activity":
			y_label = f"{solute}的活度 ($a_{{{solute}}}$)"
			title_property = f"{solute}活度"
		else:  # activity_coefficient
			y_label = f"{solute}的活度系数 ($\\ln\\gamma_{{{solute}}}$)"
			title_property = f"{solute}活度系数"
		
		# 设置坐标轴标签
		ax.set_xlabel("温度 (K)", fontsize=12)
		ax.set_ylabel(y_label, fontsize=12)
		
		title = f"{title_property}随温度变化曲线\n" \
		        f"合金: {matrix_input}  (溶剂: {solvent})\n" \
		        f"相态: {phase_text}  |  类型: {order_text}  |  外推模型: {geo_model}"
		ax.set_title(title, fontsize=13, pad=10, fontweight='bold')
		
		# 美化坐标轴
		ax.tick_params(axis='both', which='major', labelsize=10)
		ax.spines['top'].set_visible(False)
		ax.spines['right'].set_visible(False)
		
		# 添加网格
		ax.grid(True, linestyle='--', alpha=0.7)
		
		# 设置科学计数法格式
		def scientific_formatter (x, pos):
			if x == 0:
				return '0'
			
			exponent = int(np.floor(np.log10(abs(x))))
			coefficient = x / 10 ** exponent
			
			# 如果系数非常接近1，仅显示10^n
			if abs(coefficient - 1.0) < 1e-5:
				return r'$10^{%d}$' % exponent
			else:
				# 保留两位小数
				if abs(exponent) > 2:  # 数值很大或很小时使用科学计数法
					return r'$%.2f \times 10^{%d}$' % (coefficient, exponent)
				else:  # 适中的数值使用普通数字显示
					return f'{x:.4g}'
		
		# 应用格式化到坐标轴 - 只在数值范围适合时才应用
		ymin, ymax = ax.get_ylim()
		if max(abs(ymin), abs(ymax)) < 0.01 or max(abs(ymin), abs(ymax)) > 1000:
			ax.yaxis.set_major_formatter(ticker.FuncFormatter(scientific_formatter))
		
		# 添加交互式图例
		if plots:
			# 创建图例
			legend = self.figure.legend(plots, labels,
			                            loc='upper center',
			                            bbox_to_anchor=(0.5, 0.98),
			                            ncol=min(3, len(plots)),
			                            fontsize=10,
			                            frameon=True,
			                            fancybox=True,
			                            framealpha=0.8,
			                            shadow=True)
			
			# 清除已有的图例事件连接
			if hasattr(self, 'legend_cids'):
				for cid in self.legend_cids:
					self.canvas.mpl_disconnect(cid)
			
			self.legend_cids = []
			
			# 添加图例点击事件处理
			def on_legend_click (event):
				# 检查点击是否在图例内
				if legend.contains(event)[0]:
					# 确定点击的是哪个图例项
					for i, legend_item in enumerate(legend.get_lines()):
						# 检查点击是否在该图例项上
						if legend_item.contains(event)[0] and i < len(plots):
							# 切换对应线的可见性
							line = plots[i]
							visible = not line.get_visible()
							line.set_visible(visible)
							
							# 更新图例项的透明度
							legend_item.set_alpha(1.0 if visible else 0.2)
							
							# 重绘图表
							self.canvas.draw()
							return
			
			# 连接点击事件
			cid = self.canvas.mpl_connect('button_press_event', on_legend_click)
			self.legend_cids.append(cid)
			
			# 添加提示标签
			self.figure.text(0.5, 0.01, "点击图例可切换显示/隐藏对应模型的结果",
			                 ha='center', fontsize=9, style='italic', color='#7F8C8D')
		
		# 调整布局
		self.figure.tight_layout(rect=[0, 0, 1, 0.95])
		
		# 绘制画布
		self.canvas.draw()
	
	def save_current_result (self):
		"""保存当前计算结果到历史记录"""
		if not self.has_calculated:
			QMessageBox.warning(self, "保存错误", "请先计算数据再保存")
			return
		
		# 创建时间戳
		timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		
		# 保存标题信息
		title = f"{self.current_parameters['solute']} in {self.current_parameters['base_matrix']} ({timestamp})"
		
		# 保存计算结果
		self.calculation_history[title] = {
			"parameters": self.current_parameters.copy(),
			"results": {
				"activity": {},
				"activity_coefficient": {}
			}
		}
		
		# 复制计算结果（深拷贝）
		for prop in ["activity", "activity_coefficient"]:
			for model_key, data in self.calculation_results[prop].items():
				self.calculation_history[title]["results"][prop][model_key] = {
					"temperatures": data["temperatures"].copy() if isinstance(data["temperatures"], np.ndarray) else
					data["temperatures"],
					"values": data["values"].copy() if isinstance(data["values"], np.ndarray) else data["values"]
				}
		
		# 更新历史下拉菜单
		self.update_history_dropdown()
		
		QMessageBox.information(self, "保存成功", "当前计算结果已保存到历史记录")
	
	def update_history_dropdown (self):
		"""更新历史记录下拉菜单"""
		# 暂时阻止信号触发
		self.history_combo.blockSignals(True)
		
		# 保存当前选中项
		current_text = self.history_combo.currentText()
		
		# 清空下拉菜单
		self.history_combo.clear()
		
		# 添加历史记录
		if not self.calculation_history:
			self.history_combo.addItem("无历史记录")
		else:
			self.history_combo.addItem("当前计算结果")
			
			# 按时间顺序添加历史记录（最新的在前面）
			for title in reversed(list(self.calculation_history.keys())):
				self.history_combo.addItem(title)
		
		# 恢复之前选中的项
		if current_text and self.history_combo.findText(current_text) >= 0:
			self.history_combo.setCurrentText(current_text)
		else:
			self.history_combo.setCurrentIndex(0)
		
		# 恢复信号连接
		self.history_combo.blockSignals(False)
	
	def load_history_item (self, index):
		"""加载历史记录项"""
		if index == 0 or not self.has_calculated:
			# 当前计算结果或无历史记录
			return
		
		# 获取选中的历史记录标题
		title = self.history_combo.currentText()
		
		if title not in self.calculation_history:
			return
		
		# 加载历史记录
		history_data = self.calculation_history[title]
		
		# 恢复参数
		self.current_parameters = history_data["parameters"].copy()
		
		# 恢复计算结果
		self.calculation_results = {
			"activity": {},
			"activity_coefficient": {}
		}
		
		for prop in ["activity", "activity_coefficient"]:
			for model_key, data in history_data["results"][prop].items():
				self.calculation_results[prop][model_key] = {
					"temperatures": data["temperatures"].copy() if isinstance(data["temperatures"], np.ndarray) else
					data["temperatures"],
					"values": data["values"].copy() if isinstance(data["values"], np.ndarray) else data["values"]
				}
		
		# 更新UI
		self.update_parameters_ui()
		self.update_plot()
		self.update_results_table()
	
	def update_parameters_ui (self):
		"""更新UI以显示当前参数"""
		# 更新合金组成输入
		self.matrix_input.setText(self.current_parameters["base_matrix"])
		
		# 更新下拉菜单
		self.update_element_dropdowns()
		
		# 设置溶质和溶剂元素
		solute_index = self.solute_combo.findText(self.current_parameters["solute"])
		if solute_index >= 0:
			self.solute_combo.setCurrentIndex(solute_index)
		
		solvent_index = self.solvent_combo.findText(self.current_parameters["solvent"])
		if solvent_index >= 0:
			self.solvent_combo.setCurrentIndex(solvent_index)
		
		# 设置相态
		phase_index = 0 if self.current_parameters["phase_state"] == "S" else 1
		self.phase_combo.setCurrentIndex(phase_index)
		
		# 设置有序度
		order_map = {"SS": 0, "AMP": 1, "IM": 2}
		order_index = order_map.get(self.current_parameters["order_degree"], 0)
		self.order_combo.setCurrentIndex(order_index)
		
		# 设置外推模型
		geo_index = self.geo_model_combo.findText(self.current_parameters["geo_model"])
		if geo_index >= 0:
			self.geo_model_combo.setCurrentIndex(geo_index)
	
	def clear_history (self):
		"""清除历史记录"""
		if not self.calculation_history:
			return
		
		reply = QMessageBox.question(self, "确认清除", "确定要清除所有历史记录吗？",
		                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
		
		if reply == QMessageBox.Yes:
			self.calculation_history.clear()
			self.update_history_dropdown()
			QMessageBox.information(self, "清除成功", "历史记录已清除")
	
	def export_data (self):
		"""导出计算数据到CSV或Excel文件"""
		if not self.has_calculated:
			QMessageBox.warning(self, "导出错误", "请先计算数据再导出")
			return
		
		# 获取保存文件路径
		file_path, _ = QFileDialog.getSaveFileName(
				self, "导出数据", "", "CSV文件 (*.csv);;Excel文件 (*.xlsx);;所有文件 (*.*)")
		
		if not file_path:
			return
		
		try:
			# 根据文件扩展名决定导出格式
			if file_path.lower().endswith('.xlsx'):
				self.export_to_excel(file_path)
			else:
				# 默认导出为CSV
				if not file_path.lower().endswith('.csv'):
					file_path += '.csv'
				self.export_to_csv(file_path)
			
			QMessageBox.information(self, "导出成功", f"数据已成功导出到: {file_path}")
		except Exception as e:
			QMessageBox.critical(self, "导出错误", f"导出数据时发生错误: {str(e)}")
			traceback.print_exc()
	
	def export_to_csv (self, file_path):
		"""导出数据到CSV格式"""
		import csv
		
		# 获取所有模型和所有温度点
		all_models = set()
		all_temperatures = set()
		
		for prop_data in self.calculation_results.values():
			for model_key, data in prop_data.items():
				all_models.add(model_key)
				if "temperatures" in data and len(data["temperatures"]) > 0:
					all_temperatures.update(data["temperatures"])
		
		# 排序温度点和模型名称
		all_temperatures = sorted(all_temperatures)
		all_models = sorted(all_models)
		
		# 写入CSV文件
		with open(file_path, 'w', newline='') as csvfile:
			writer = csv.writer(csvfile)
			
			# 写入标题行 - 参数信息
			writer.writerow(['计算参数'])
			writer.writerow(['基体合金', self.current_parameters["base_matrix"]])
			writer.writerow(['溶剂元素', self.current_parameters["solvent"]])
			writer.writerow(['溶质元素', self.current_parameters["solute"]])
			writer.writerow(['相态', "固态" if self.current_parameters["phase_state"] == "S" else "液态"])
			writer.writerow(['类型', self.current_parameters["order_degree"]])
			writer.writerow(['外推模型', self.current_parameters["geo_model"]])
			writer.writerow([])  # 空行
			
			# 写入标题行 - 数据部分
			header = ['温度 (K)']
			for model in all_models:
				header.extend([
					f'{model}-活度 (a_{self.current_parameters["solute"]})',
					f'{model}-活度系数 (lnγ_{self.current_parameters["solute"]})'
				])
			writer.writerow(header)
			
			# 写入数据行
			for temp in all_temperatures:
				row = [temp]
				for model in all_models:
					# 活度
					activity_value = ''
					if model in self.calculation_results["activity"]:
						data = self.calculation_results["activity"][model]
						if "temperatures" in data and len(data["temperatures"]) > 0:
							idx = np.where(data["temperatures"] == temp)[0]
							if idx.size > 0 and idx[0] < len(data["values"]) and not np.isnan(data["values"][idx[0]]):
								activity_value = f"{data['values'][idx[0]]:.6f}"
					row.append(activity_value)
					
					# 活度系数
					act_coef_value = ''
					if model in self.calculation_results["activity_coefficient"]:
						data = self.calculation_results["activity_coefficient"][model]
						if "temperatures" in data and len(data["temperatures"]) > 0:
							idx = np.where(data["temperatures"] == temp)[0]
							if idx.size > 0 and idx[0] < len(data["values"]) and not np.isnan(data["values"][idx[0]]):
								act_coef_value = f"{data['values'][idx[0]]:.6f}"
					row.append(act_coef_value)
				
				writer.writerow(row)
	
	def export_to_excel (self, file_path):
		"""导出数据到Excel格式"""
		try:
			import xlsxwriter
		except ImportError:
			QMessageBox.warning(self, "缺少依赖", "导出Excel需要安装xlsxwriter模块。将导出为CSV格式。")
			self.export_to_csv(file_path.replace('.xlsx', '.csv'))
			return
		
		# 创建工作簿和工作表
		workbook = xlsxwriter.Workbook(file_path)
		worksheet = workbook.add_worksheet('计算结果')
		
		# 设置格式
		title_format = workbook.add_format({
			'bold': True,
			'font_size': 14,
			'align': 'center',
			'valign': 'vcenter',
			'border': 0,
			'font_color': '#2C3E50'
		})
		
		header_format = workbook.add_format({
			'bold': True,
			'align': 'center',
			'valign': 'vcenter',
			'border': 1,
			'bg_color': '#ECF0F1',
			'font_color': '#2C3E50'
		})
		
		param_label_format = workbook.add_format({
			'bold': True,
			'align': 'right',
			'valign': 'vcenter',
			'font_color': '#2C3E50'
		})
		
		param_value_format = workbook.add_format({
			'align': 'left',
			'valign': 'vcenter',
			'font_color': '#2980B9'
		})
		
		data_format = workbook.add_format({
			'num_format': '0.000000',
			'align': 'center',
			'valign': 'vcenter',
			'border': 1
		})
		
		temp_format = workbook.add_format({
			'num_format': '0.0',
			'align': 'center',
			'valign': 'vcenter',
			'border': 1,
			'bg_color': '#F8F9F9'
		})
		
		# 获取所有模型和所有温度点
		all_models = set()
		all_temperatures = set()
		
		for prop_data in self.calculation_results.values():
			for model_key, data in prop_data.items():
				all_models.add(model_key)
				if "temperatures" in data and len(data["temperatures"]) > 0:
					all_temperatures.update(data["temperatures"])
		
		# 排序温度点和模型名称
		all_temperatures = sorted(all_temperatures)
		all_models = sorted(all_models)
		
		# 写入标题
		worksheet.merge_range('A1:F1', '热力学性质随温度变化计算结果', title_format)
		
		# 写入参数信息
		worksheet.write(2, 0, '计算参数', header_format)
		worksheet.write(3, 0, '基体合金:', param_label_format)
		worksheet.write(3, 1, self.current_parameters["base_matrix"], param_value_format)
		worksheet.write(4, 0, '溶剂元素:', param_label_format)
		worksheet.write(4, 1, self.current_parameters["solvent"], param_value_format)
		worksheet.write(5, 0, '溶质元素:', param_label_format)
		worksheet.write(5, 1, self.current_parameters["solute"], param_value_format)
		worksheet.write(6, 0, '相态:', param_label_format)
		worksheet.write(6, 1, "固态" if self.current_parameters["phase_state"] == "S" else "液态", param_value_format)
		worksheet.write(7, 0, '类型:', param_label_format)
		worksheet.write(7, 1, self.current_parameters["order_degree"], param_value_format)
		worksheet.write(8, 0, '外推模型:', param_label_format)
		worksheet.write(8, 1, self.current_parameters["geo_model"], param_value_format)
		
		# 写入标题行 - 数据部分
		row = 10
		worksheet.write(row, 0, '温度 (K)', header_format)
		col = 1
		for model in all_models:
			worksheet.write(row, col, f'{model}-活度 (a_{self.current_parameters["solute"]})',
			                header_format)
			worksheet.write(row, col + 1,
			                f'{model}-活度系数 (lnγ_{self.current_parameters["solute"]})',
			                header_format)
			col += 2
		
		# 写入数据行
		row += 1
		for temp in all_temperatures:
			worksheet.write(row, 0, temp, temp_format)
			col = 1
			for model in all_models:
				# 活度
				if model in self.calculation_results["activity"]:
					data = self.calculation_results["activity"][model]
					if "temperatures" in data and len(data["temperatures"]) > 0:
						idx = np.where(data["temperatures"] == temp)[0]
						if idx.size > 0 and idx[0] < len(data["values"]) and not np.isnan(data["values"][idx[0]]):
							worksheet.write(row, col, data['values'][idx[0]], data_format)
				col += 1
				
				# 活度系数
				if model in self.calculation_results["activity_coefficient"]:
					data = self.calculation_results["activity_coefficient"][model]
					if "temperatures" in data and len(data["temperatures"]) > 0:
						idx = np.where(data["temperatures"] == temp)[0]
						if idx.size > 0 and idx[0] < len(data["values"]) and not np.isnan(data["values"][idx[0]]):
							worksheet.write(row, col, data['values'][idx[0]], data_format)
				col += 1
			
			row += 1
		
		# 设置列宽
		worksheet.set_column(0, 0, 12)
		for i in range(1, 2 * len(all_models) + 1):
			worksheet.set_column(i, i, 18)
		
		# 保存并关闭工作簿
		workbook.close()