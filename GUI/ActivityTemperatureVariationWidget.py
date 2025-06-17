import math
import traceback

import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox,
                             QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
                             QLabel, QLineEdit, QMessageBox,
                             QProgressDialog, QPushButton, QSplitter, QTextEdit, QVBoxLayout, QWidget,
                             QGridLayout, QFrame, QSizePolicy)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from core import UnifiedExtrapolationModel as UEM
from utils.tool import export_data_to_file


class ActivityTemperatureVariationWidget(QWidget):
	"""用于显示活度和活度系数随温度变化的窗口"""
	
	# 替换您类中从 __init__ 到 create_action_buttons 的所有方法
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.parent_window = parent
		
		# 配置matplotlib以支持中文显示
		plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
		plt.rcParams['axes.unicode_minus'] = False
		
		# 初始化数据结构
		self.calculation_results = {"activity": {}, "activity_coefficient": {}}
		self.current_parameters = {}
		self.has_calculated = False
		
		# 初始化UI
		self.init_ui()
	
	def init_ui (self):
		"""初始化用户界面组件 (优化版)"""
		self.setFont(QFont("Microsoft YaHei", 10))
		main_layout = QHBoxLayout(self)  # 使用QHBoxLayout作为主布局
		main_layout.setSpacing(15)
		main_layout.setContentsMargins(15, 15, 15, 15)
		
		splitter = QSplitter(Qt.Horizontal)
		splitter.setHandleWidth(2)
		
		left_panel = self.create_left_panel()
		right_panel = self.create_right_panel()  # 假设您有此方法创建右侧面板
		
		splitter.addWidget(left_panel)
		splitter.addWidget(right_panel)
		splitter.setSizes([420, 780])
		
		main_layout.addWidget(splitter)
		self.update_element_dropdowns()
	
	def create_left_panel (self):
		"""创建左侧控制面板 (优化版)"""
		left_panel = QWidget()
		left_layout = QVBoxLayout(left_panel)
		left_layout.setSpacing(15)
		left_layout.setContentsMargins(10, 10, 10, 10)
		
		# 依次添加各个设置区域
		left_layout.addWidget(self.create_alloy_composition_group())
		left_layout.addWidget(self.create_temperature_range_group())
		left_layout.addWidget(self.create_calculation_params_group())
		left_layout.addWidget(self.create_model_selection_group())
		left_layout.addStretch(1)  # 弹性空间将按钮推到底部
		left_layout.addWidget(self.create_action_buttons())
		
		left_panel.setMinimumWidth(380)
		left_panel.setMaximumWidth(450)
		
		return left_panel
	
	def create_alloy_composition_group (self):
		"""创建合金组成区域 (优化版)"""
		group = QGroupBox("合金组成")
		group.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
		
		layout = QFormLayout(group)
		layout.setSpacing(10)
		layout.setContentsMargins(10, 20, 10, 10)
		layout.setLabelAlignment(Qt.AlignRight)
		
		# 合金组成输入行
		self.matrix_input = QLineEdit()
		self.matrix_input.setPlaceholderText("例如: Fe0.7Ni0.3")
		self.matrix_input.setMinimumHeight(32)  # 统一高度
		self.matrix_input.setFont(QFont("Microsoft YaHei", 10))
		
		update_btn = QPushButton("更新")
		update_btn.setFixedWidth(60)
		update_btn.setMinimumHeight(32)  # 统一高度
		update_btn.setFont(QFont("Microsoft YaHei", 10))
		update_btn.clicked.connect(self.update_element_dropdowns)
		
		input_row = QHBoxLayout()
		input_row.addWidget(self.matrix_input)
		input_row.addWidget(update_btn)
		
		layout.addRow(self.create_label("合金组成:"), input_row)
		
		# 溶剂和溶质选择
		self.solvent_combo = self.create_combo_box()
		self.solute_combo = self.create_combo_box()
		layout.addRow(self.create_label("溶剂元素:"), self.solvent_combo)
		layout.addRow(self.create_label("溶质元素:"), self.solute_combo)
		
		return group
	
	def create_temperature_range_group (self):
		"""创建温度范围设置区域 (优化版)"""
		group = QGroupBox("温度范围")
		group.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
		layout = QFormLayout(group)
		layout.setSpacing(10)
		layout.setContentsMargins(10, 20, 10, 10)
		
		self.min_temp = self.create_spin_box(300, 5000, 800, 50, " K")
		self.max_temp = self.create_spin_box(300, 5000, 1600, 50, " K")
		self.step_temp = self.create_spin_box(10, 500, 50, 10, " K")
		
		layout.addRow(self.create_label("最低温度:"), self.min_temp)
		layout.addRow(self.create_label("最高温度:"), self.max_temp)
		layout.addRow(self.create_label("温度步长:"), self.step_temp)
		
		return group
	
	def create_calculation_params_group (self):
		"""创建计算参数区域 (优化版)"""
		group = QGroupBox("计算参数")
		group.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
		layout = QFormLayout(group)
		layout.setSpacing(10)
		layout.setContentsMargins(10, 20, 10, 10)
		
		self.phase_combo = self.create_combo_box()
		self.phase_combo.addItems(["固态 (S)", "液态 (L)"])
		
		self.order_combo = self.create_combo_box()
		self.order_combo.addItems(["固溶体 (SS)", "非晶态 (AMP)", "金属间化合物 (IM)"])
		
		self.property_combo = self.create_combo_box()
		self.property_combo.addItems(["活度 (a)", "活度系数 (γ)"])
		self.property_combo.currentIndexChanged.connect(self.update_plot)
		
		layout.addRow(self.create_label("相态:"), self.phase_combo)
		layout.addRow(self.create_label("类型:"), self.order_combo)
		layout.addRow(self.create_label("绘图性质:"), self.property_combo)
		
		return group
	
	def create_model_selection_group (self):
		"""创建外推模型选择区域 (优化版)"""
		group = QGroupBox("外推模型选择")
		group.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
		layout = QGridLayout(group)
		layout.setSpacing(10)
		layout.setContentsMargins(10, 20, 10, 10)
		
		self.model_checkboxes = {}
		models = [("Kohler (K)", "K"), ("Muggianu (M)", "M"), ("Toop-Kohler (T-K)", "T-K"),
		          ("GSM/Chou", "GSM"), ("UEM1", "UEM1"), ("UEM2_N", "UEM2_N")]
		
		for index, (name, key) in enumerate(models):
			checkbox = QCheckBox(name)
			checkbox.setFont(QFont("Microsoft YaHei", 10))
			if key in ["UEM1", "GSM"]:
				checkbox.setChecked(True)
			self.model_checkboxes[key] = checkbox
			layout.addWidget(checkbox, index // 2, index % 2)
		
		return group
	
	def create_action_buttons (self):
		"""创建操作按钮区域 (优化版)"""
		container = QWidget()
		layout = QHBoxLayout(container)
		layout.setSpacing(15)
		layout.setContentsMargins(0, 0, 0, 0)
		
		calculate_button = QPushButton("计算")
		calculate_button.setMinimumHeight(40)  # 统一高度
		calculate_button.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
		calculate_button.clicked.connect(self.calculate_all_properties)
		
		export_button = QPushButton("导出数据")
		export_button.setMinimumHeight(40)  # 统一高度
		export_button.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
		export_button.clicked.connect(self.export_data)
		
		layout.addWidget(calculate_button, 1)
		layout.addWidget(export_button, 1)
		
		return container
	
	
	
	def create_right_panel (self):
		"""创建右侧面板（包括结果文本区域和图表）"""
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
		"""创建计算结果显示区域（使用富文本编辑框）"""
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
		title_label = QLabel("计算结果")
		title_font = QFont("Microsoft YaHei", 14, QFont.Bold)
		title_label.setFont(title_font)
		title_label.setAlignment(Qt.AlignCenter)
		title_label.setStyleSheet("color: #2C3E50; margin-bottom: 5px;")
		layout.addWidget(title_label)
		
		# 创建富文本编辑框用于显示结果
		self.results_text = QTextEdit()
		self.results_text.setReadOnly(True)
		self.results_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                background-color: white;
                font-size: 12pt;
                padding: 10px;
            }
        """)
		
		# 设置默认文本
		self.results_text.setHtml(
				"<div style='text-align: center; margin-top: 50px; color: #7F8C8D; font-size: 14pt;'>"
				"点击<b>计算</b>按钮开始计算，结果将显示在此处"
				"</div>"
		)
		
		# 添加到布局
		layout.addWidget(self.results_text)
		
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
		global activity_value, activity_coef_value
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
		
		# 检查选中的模型
		selected_models = [key for key, checkbox in self.model_checkboxes.items() if checkbox.isChecked()]
		if not selected_models:
			QMessageBox.warning(self, "模型选择", "请至少选择一个外推模型")
			return
		
		# 创建温度范围
		min_temp = self.min_temp.value()
		max_temp = self.max_temp.value()
		step_temp = self.step_temp.value()
		temp_range = np.arange(min_temp, max_temp + step_temp / 2, step_temp)
		
		# 存储当前参数
		self.current_parameters = {
			"base_matrix": matrix_input,
			"solute": solute,
			"solvent": solvent,
			"phase_state": phase_state,
			"order_degree": order_degree,
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
		progress.setWindowModality(Qt.WindowModal)
		progress.setMinimumDuration(0)
		progress.setValue(0)
		
		# 计算每个模型在不同温度下的热力学性质
		try:
			progress_count = 0
			
			# 开始使用HTML格式化以提高可读性
			results_text = """
	        <style>
	            table {width: 100%; border-collapse: collapse; margin-bottom: 10px;}
	            th {background-color: #3498DB; color: white; text-align: center; padding: 5px; border: 1px solid #BDC3C7;}
	            td {border: 1px solid #BDC3C7; padding: 5px; text-align: center;}
	            .temp-header {background-color: #ECF0F1; font-weight: bold;}
	            .model-name {font-weight: bold; text-align: left;}
	            .success {color: #2ECC71;}
	            .failure {color: #E74C3C;}
	        </style>
	        """
			
			from datetime import datetime
			timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			results_text += f"<h3>计算结果 - {timestamp}</h3>"
			
			# 添加计算参数
			results_text += f"""
	        <p><b>计算参数：</b> 合金: {matrix_input} | 溶质: {solute} | 溶剂: {solvent} |
	        相态: {'固态' if phase_state == 'S' else '液态'} | 类型: {order_degree}</p>
	        """
			
			# 按温度构建结果表格
			for temp in temp_range:
				results_text += f"""
	            <table>
	                <tr><th colspan="3">温度: {temp:.1f} K</th></tr>
	                <tr>
	                    <th width="30%">模型</th>
	                    <th width="35%">活度 (a<sub>{solute}</sub>)</th>
	                    <th width="35%">活度系数 (γ<sub>{solute}</sub>)</th>
	                </tr>
	            """
				
				# 为每个选中的模型执行计算
				for model_key in selected_models:
					if progress.wasCanceled():
						break
					
					model_func = model_functions.get(model_key)
					if not model_func:
						continue
					
					# 初始化该模型的数据结构（如果是第一个温度点）
					if model_key not in self.calculation_results["activity"]:
						for prop in ["activity", "activity_coefficient"]:
							self.calculation_results[prop][model_key] = {"temperatures": [], "values": []}
					
					# 计算活度
					try:
						progress.setLabelText(f"计算 {model_key} 模型在温度 {temp:.1f}K 下的活度...")
						activity_value = UEM.calculate_activity(
								base_matrix, solute, solvent, temp,
								phase_state, order_degree, model_func, model_key
						)
						activity_text = f'<span class="success">{activity_value:.6f}</span>'
					except Exception as e:
						activity_value = None
						activity_text = f'<span class="failure">计算失败</span>'
						print(f"计算温度 {temp}K 的活度时出错: {str(e)}")
					
					# 计算活度系数
					try:
						progress.setLabelText(f"计算 {model_key} 模型在温度 {temp:.1f}K 下的活度系数...")
						activity_coef_value = UEM.calculate_activity_coefficient(base_matrix, solute, solvent,
						                                                                  temp, phase_state,
						                                                                  order_degree, model_func,
						                                                                  model_key)
						activity_coef_value = math.exp(activity_coef_value)
						activity_coef_text = f'<span class="success">{activity_coef_value:.6f}</span>'
					except Exception as e:
						activity_coef_value = None
						activity_coef_text = f'<span class="failure">计算失败</span>'
						print(f"计算温度 {temp}K 的活度系数时出错: {str(e)}")
					
					# 添加该模型的结果行
					results_text += f"""
	                <tr>
	                    <td class="model-name">{self.model_checkboxes[model_key].text()}</td>
	                    <td>{activity_text}</td>
	                    <td>{activity_coef_text}</td>
	                </tr>
	                """
					
					# 只有当计算成功时才添加数据点
					if activity_value is not None or activity_coef_value is not None:
						# 存储温度数据
						if temp not in self.calculation_results["activity"][model_key]["temperatures"]:
							self.calculation_results["activity"][model_key]["temperatures"].append(temp)
							self.calculation_results["activity_coefficient"][model_key]["temperatures"].append(temp)
						
						# 存储活度和活度系数数据
						if activity_value is not None:
							self.calculation_results["activity"][model_key]["values"].append(activity_value)
						if activity_coef_value is not None:
							self.calculation_results["activity_coefficient"][model_key]["values"].append(
								activity_coef_value)
					
					progress_count += 2
					progress.setValue(progress_count)
				
				results_text += "</table>"
			
			# 确保每个模型的数据是numpy数组，用于绘图
			for prop in self.calculation_results:
				for model_key in self.calculation_results[prop]:
					if len(self.calculation_results[prop][model_key]["temperatures"]) > 0:
						self.calculation_results[prop][model_key]["temperatures"] = np.array(
								self.calculation_results[prop][model_key]["temperatures"])
						self.calculation_results[prop][model_key]["values"] = np.array(
								self.calculation_results[prop][model_key]["values"])
			
			# 获取之前的结果
			current_results = self.results_text.toHtml()
			
			# 合并新旧结果（保留之前的计算记录）
			if "点击<b>计算</b>按钮开始计算" in current_results:
				# 第一次计算，替换默认文本
				self.results_text.setHtml(results_text)
			else:
				# 新结果添加到顶部
				self.results_text.setHtml(results_text + "<hr>" + current_results)
			
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
			
			# 更新图表
			self.update_plot()
			
			# 显示成功消息
			QMessageBox.information(self, "计算完成", "计算完成，您可以查看图表结果。")
		
		except Exception as e:
			# 关闭进度对话框
			progress.close()
			
			# 显示错误消息
			QMessageBox.critical(self, "计算错误", f"计算过程中发生错误: {str(e)}")
			traceback.print_exc()
	
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
		
		# 创建子图
		ax = self.figure.add_subplot(111)
		
		# 设置颜色循环和标记
		colors = ['r', 'b', 'g', 'c', 'm', 'y', 'k']
		markers = ['o', 's', '^', 'D', 'v', '<', '>']
		plots = []
		labels = []
		
		# 获取温度范围，用于添加参考线
		min_temp = float('inf')
		max_temp = float('-inf')
		
		# 为每个模型绘制线条
		for i, (model_key, data) in enumerate(model_results.items()):
			if "temperatures" not in data or len(data["temperatures"]) == 0 or "values" not in data:
				continue
			
			temperatures = data["temperatures"]
			values = data["values"]
			
			# 更新温度范围
			if len(temperatures) > 0:
				min_temp = min(min_temp, np.min(temperatures))
				max_temp = max(max_temp, np.max(temperatures))
			
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
			                linewidth=2,
			                markersize=6,
			                label=self.model_checkboxes[model_key].text())
			
			plots.append(line)
			labels.append(self.model_checkboxes[model_key].text())
		
		# 如果有有效的温度范围，添加参考线
		if min_temp != float('inf') and max_temp != float('-inf'):
			temp_range = np.linspace(min_temp, max_temp, 100)
			
			if property_type == "activity":
				# 为活度添加摩尔分数线
				# 提取溶质的摩尔分数
				matrix_input = self.current_parameters["base_matrix"]
				solute = self.current_parameters["solute"]
				composition = self.parse_composition(matrix_input)
				
				if solute in composition:
					mole_fraction = composition[solute]
					# 绘制水平线表示摩尔分数
					ref_line, = ax.plot(temp_range, [mole_fraction] * len(temp_range),
					                    'k--', linewidth=1.5, alpha=0.7,
					                    label=f"摩尔分数 X{solute}={mole_fraction:.4f}")
					plots.append(ref_line)
					labels.append(f"摩尔分数 X{solute}={mole_fraction:.4f}")
					
					# 添加说明文本
					ax.text(max_temp - (max_temp - min_temp) * 0.2, mole_fraction * 1.1,
					        f"X{solute}={mole_fraction:.4f}",
					        fontsize=9, color='black', ha='right', va='bottom',
					        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=2))
			
			elif property_type == "activity_coefficient":
				# 为活度系数添加理想态线 (γ = 1)
				ref_line, = ax.plot(temp_range, [1.0] * len(temp_range),
				                    'k--', linewidth=1.5, alpha=0.7,
				                    label="理想态 (γ = 1)")
				plots.append(ref_line)
				labels.append("理想态 (γ = 1)")
				
				# 添加说明文本
				ax.text(max_temp - (max_temp - min_temp) * 0.2, 1.05,
				        "理想态 (γ = 1)",
				        fontsize=9, color='black', ha='right', va='bottom',
				        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=2))
		
		# 构建标题
		solute = self.current_parameters["solute"]
		
		matrix_input = self.current_parameters["base_matrix"]
		phase_dict = {"S": "Solid", "L": "Liquid"}
		phase_text = phase_dict.get(self.current_parameters["phase_state"], "Solid")
		order_text = self.current_parameters["order_degree"]
		solvent = self.current_parameters["solvent"]
		
		# 设置标题和标签
		if property_type == "activity":
			y_label = f"Activity ($a_{{{solute}}}$)"
			title_property = "Activity"
			# 调整Y轴范围，使参考线更加明显
			ax.set_ylim([0, max(ax.get_ylim()[1], 1.2)])  # 确保参考线可见
		else:  # activity_coefficient
			y_label = fr"Activity Coefficient ($\gamma_{{{solute}}}$)"
			title_property = "Activity Coefficient"
			# 确保理想态线可见
			ymin, ymax = ax.get_ylim()
			if ymin > 0.5:
				ymin = 0.5
			if ymax < 1.5:
				ymax = 1.5
			ax.set_ylim([ymin, ymax])
		
		# 设置坐标轴标签
		ax.set_xlabel("Temperature (K)", fontsize=12)
		ax.set_ylabel(y_label, fontsize=12)
		ymin, ymax = ax.get_ylim()
		data_min = float('inf')
		data_max = float('-inf')
		
		# 找出所有数据的最小值和最大值
		for _, data in model_results.items():
			if "values" in data and len(data["values"]) > 0:
				valid_values = data["values"][~np.isnan(data["values"])]
				if len(valid_values) > 0:
					data_min = min(data_min, np.min(valid_values))
					data_max = max(data_max, np.max(valid_values))
		
		# 确保y轴不会太贴近数据
		if data_min != float('inf') and data_max != float('-inf'):
			margin = (data_max - data_min) * 0.15  # 15%的边距
			
			if property_type == "activity":
				# 对于活度，确保0可见
				new_ymin = max(0, data_min - margin)
				new_ymax = data_max + margin
				
				# 确保摩尔分数参考线可见
				if "solute" in self.current_parameters:
					solute = self.current_parameters["solute"]
					composition = self.parse_composition(self.current_parameters["base_matrix"])
					if solute in composition:
						mole_fraction = composition[solute]
						new_ymax = max(new_ymax, mole_fraction * 1.2)
			
			else:  # activity_coefficient
				# 对于活度系数，确保理想态线(γ=1)可见
				new_ymin = min(data_min - margin, 0.7)  # 确保能看到γ=1以下的区域
				new_ymax = max(data_max + margin, 1.3)  # 确保能看到γ=1以上的区域
			
			# 保证一定的最小可视范围
			if new_ymax - new_ymin < 0.1:
				mean = (new_ymax + new_ymin) / 2
				new_ymin = mean - 0.05
				new_ymax = mean + 0.05
			
			# 应用新的y轴范围
			ax.set_ylim(new_ymin, new_ymax)
			
		title = f"{title_property} of {solute} vs Temperature\n" \
		        f"Alloy: {matrix_input} (Solvent: {solvent})\n" \
		        f"Phase: {phase_text}, Type: {order_text}"
		ax.set_title(title, fontsize=12, pad=10)
		
		# 添加网格
		ax.grid(True, linestyle='--', alpha=0.7)
		
		# 设置坐标轴刻度字体大小
		ax.tick_params(axis='both', which='major', labelsize=10)
		
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
			# 在图表下方创建图例
			legend = self.figure.legend(plots, labels, loc='upper center',
			                            bbox_to_anchor=(0.5, 0.98),
			                            ncol=min(3, len(plots)), fontsize=10)
			
			# 使图例可选择
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
			self.figure.text(0.5, 0.01, "点击图例项目可切换显示/隐藏对应模型的结果",
			                 ha='center', fontsize=9, style='italic')
		
		# 调整布局
		self.figure.tight_layout(rect=[0, 0, 1, 0.88])
		
		# 绘制画布
		self.canvas.draw()
	
	def export_data (self):
		"""
		准备数据并调用通用的导出函数。
		"""
		if not self.has_calculated:
			QMessageBox.warning(self, "导出错误", "请先计算数据再导出。")
			return
		
		# 1. 准备 parameters 字典
		params = self.current_parameters
		parameters = {
			'基体合金': params.get("base_matrix", ""),
			'添加元素': params.get("add_element", ""),
			'温度 (K)': params.get("temperature", 0),
			'相态': "固态 (S)" if params.get("phase_state") == "S" else "液态 (L)",
			'类型': params.get("order_degree", "")
		}
		
		# 2. 准备 header 和 data
		all_models = sorted(self.calculation_results["enthalpy"].keys())
		all_compositions = set()
		for prop_data in self.calculation_results.values():
			for model_data in prop_data.values():
				if "compositions" in model_data and model_data["compositions"].size > 0:
					all_compositions.update(model_data["compositions"])
		
		sorted_compositions = sorted(list(all_compositions))
		
		header = ['组成 (x)']
		for model in all_models:
			header.extend([f'{model}-混合焓(kJ/mol)', f'{model}-吉布斯能(kJ/mol)', f'{model}-混合熵(J/mol·K)'])
		
		data_rows = []
		for comp in sorted_compositions:
			row = [comp]
			for model in all_models:
				for prop in ["enthalpy", "gibbs", "entropy"]:
					data = self.calculation_results[prop].get(model, {})
					comps, vals = data.get("compositions", np.array([])), data.get("values", np.array([]))
					idx = np.where(comps == comp)[0]
					row.append(vals[idx[0]] if idx.size > 0 else None)
			data_rows.append(row)
		
		# 3. 调用通用导出函数
		export_data_to_file(
				parent=self,
				parameters=parameters,
				header=header,
				data=data_rows,
				default_filename=f'{parameters["基体合金"]}-{parameters["添加元素"]}_composition_variation'
		)
	

	