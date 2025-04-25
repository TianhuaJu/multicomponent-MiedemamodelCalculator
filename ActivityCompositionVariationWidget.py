import os
import sys
import traceback
from typing import Callable, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
                             QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
                             QLabel, QLineEdit, QMainWindow, QMessageBox,
                             QProgressDialog, QPushButton, QSplitter, QTableWidget,
                             QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
                             QGridLayout)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import BinarySys as BinaryModel
import UnifiedExtrapolationModel as UEM


class ActivityCompositionVariationWidget(QWidget):
	"""用于显示活度和活度系数随组分浓度变化的窗口"""
	
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
			"target_element": "",
			"var_element": "",
			"temperature": 0,
			"phase_state": "",
			"order_degree": "",
			"comp_range": []
		}
		
		self.has_calculated = False  # 跟踪是否已经计算
		self.init_ui()
	
	def init_ui (self):
		"""初始化用户界面组件"""
		# 设置整体字体
		app_font = QFont()
		app_font.setPointSize(10)  # 增大基本字体
		self.setFont(app_font)
		
		# 主布局
		main_layout = QVBoxLayout()
		main_layout.setSpacing(15)  # 增加布局元素之间的间距
		
		# 控制面板布局 - 使用垂直布局以增加高度
		left_panel = QWidget()
		left_layout = QVBoxLayout()
		left_layout.setSpacing(15)
		left_layout.setContentsMargins(10, 10, 10, 10)
		
		# 基体合金输入
		matrix_group = QGroupBox("合金组成")
		matrix_layout = QFormLayout()
		matrix_layout.setSpacing(10)
		matrix_layout.setContentsMargins(10, 20, 10, 10)
		
		# 创建水平布局来放置输入框和按钮
		comp_input_row = QHBoxLayout()
		
		self.matrix_input = QLineEdit()
		self.matrix_input.setPlaceholderText("例如: Fe0.7Ni0.3")
		self.matrix_input.setMinimumHeight(30)
		
		update_btn = QPushButton("update")
		update_btn.setFixedWidth(80)
		update_btn.clicked.connect(self.update_element_dropdowns)
		
		# 添加到水平布局
		comp_input_row.addWidget(self.matrix_input)
		comp_input_row.addWidget(update_btn)
		
		matrix_layout.addRow("合金组成:", comp_input_row)
		
		# 目标元素和变化元素选择
		element_layout = QGridLayout()
		element_layout.setSpacing(10)
		
		self.target_element_combo = QComboBox()
		self.target_element_combo.setMinimumHeight(30)
		
		self.target_conc_spin = QDoubleSpinBox()
		self.target_conc_spin.setRange(0.01, 0.99)
		self.target_conc_spin.setValue(0.1)  # 默认值
		self.target_conc_spin.setSingleStep(0.05)
		self.target_conc_spin.setMinimumHeight(30)
		self.target_conc_spin.setSuffix(" (固定)")
		
		self.var_element_combo = QComboBox()
		self.var_element_combo.setMinimumHeight(30)
		
		# 溶剂元素下拉框
		self.solvent_combo = QComboBox()
		self.solvent_combo.setMinimumHeight(30)
		
		element_layout.addWidget(QLabel("溶剂元素:"), 0, 0)
		element_layout.addWidget(self.solvent_combo, 0, 1)
		element_layout.addWidget(QLabel("目标元素:"), 1, 0)
		element_layout.addWidget(self.target_element_combo, 1, 1)
		element_layout.addWidget(QLabel("变化元素:"), 2, 0)
		element_layout.addWidget(self.var_element_combo, 2, 1)
		
		matrix_layout.addRow("元素选择:", element_layout)
		
		# 组成范围 - 网格布局以增加清晰度
		range_widget = QWidget()
		range_layout = QGridLayout()
		range_layout.setContentsMargins(0, 0, 0, 0)
		range_layout.setSpacing(10)
		
		# 创建标签
		min_label = QLabel("min:")
		min_label.setMinimumWidth(40)
		max_label = QLabel("max:")
		max_label.setMinimumWidth(40)
		step_label = QLabel("step:")
		step_label.setMinimumWidth(40)
		
		# 创建浓度范围控件
		self.min_comp = QDoubleSpinBox()
		self.min_comp.setRange(0.0, 1.0)
		self.min_comp.setValue(0.0)
		self.min_comp.setSingleStep(0.05)
		self.min_comp.setMinimumHeight(30)
		self.min_comp.setMinimumWidth(80)
		
		self.max_comp = QDoubleSpinBox()
		self.max_comp.setRange(0.0, 1.0)
		self.max_comp.setValue(0.5)
		self.max_comp.setSingleStep(0.05)
		self.max_comp.setMinimumHeight(30)
		self.max_comp.setMinimumWidth(80)
		
		self.step_comp = QDoubleSpinBox()
		self.step_comp.setRange(0.01, 0.2)
		self.step_comp.setValue(0.05)
		self.step_comp.setSingleStep(0.01)
		self.step_comp.setMinimumHeight(30)
		self.step_comp.setMinimumWidth(80)
		
		# 添加组件到网格布局
		range_layout.addWidget(min_label, 0, 0)
		range_layout.addWidget(self.min_comp, 0, 1)
		range_layout.addWidget(max_label, 0, 2)
		range_layout.addWidget(self.max_comp, 0, 3)
		range_layout.addWidget(step_label, 1, 0)
		range_layout.addWidget(self.step_comp, 1, 1)
		
		range_widget.setLayout(range_layout)
		matrix_layout.addRow("浓度范围:", range_widget)
		
		matrix_group.setLayout(matrix_layout)
		left_layout.addWidget(matrix_group)
		
		# 计算参数区域
		params_group = QGroupBox("计算参数")
		params_layout = QFormLayout()
		params_layout.setSpacing(12)
		params_layout.setContentsMargins(10, 25, 10, 15)
		params_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
		
		# 添加温度输入
		self.temp_input = QDoubleSpinBox()
		self.temp_input.setRange(300, 5000)
		self.temp_input.setValue(1000)
		self.temp_input.setSingleStep(50)
		self.temp_input.setSuffix(" K")
		self.temp_input.setMinimumHeight(30)
		params_layout.addRow("温度:", self.temp_input)
		
		# 添加相态选择
		self.phase_combo = QComboBox()
		self.phase_combo.addItems(["固态 (S)", "液态 (L)"])
		self.phase_combo.setMinimumHeight(30)
		params_layout.addRow("相态:", self.phase_combo)
		
		# 添加有序度选择
		self.order_combo = QComboBox()
		self.order_combo.addItems(["固溶体 (SS)", "非晶态 (AMP)", "金属间化合物 (IM)"])
		self.order_combo.setMinimumHeight(30)
		params_layout.addRow("类型:", self.order_combo)
		
		# 热力学性质选择
		self.property_combo = QComboBox()
		self.property_combo.addItems([
			"活度 (a)",
			"活度系数 (γ)"
		])
		self.property_combo.setMinimumHeight(30)
		
		# 当热力学性质选择改变时更新图表
		self.property_combo.currentIndexChanged.connect(self.update_plot)
		
		params_layout.addRow("热力学性质:", self.property_combo)
		
		
		# 外推模型选择
		self.geo_model_combo = QComboBox()
		self.geo_model_combo.addItems(["UEM1", "UEM2_N", "GSM", "T-K", "K", "M"])
		self.geo_model_combo.setMinimumHeight(30)
		params_layout.addRow("外推模型:", self.geo_model_combo)
		
		params_group.setLayout(params_layout)
		left_layout.addWidget(params_group)
		
		# 外推模型选择
		models_group = QGroupBox("外推模型选择")
		models_layout = QVBoxLayout()
		models_layout.setSpacing(10)
		models_layout.setContentsMargins(15, 25, 15, 15)
		
		self.model_checkboxes = {}
		models = [
			("Kohler (K)", "K"),
			("Muggianu (M)", "M"),
			("Toop-Kohler (T-K)", "T-K"),
			("GSM/Chou", "GSM"),
			("UEM1", "UEM1"),
			("UEM2_N", "UEM2_N")
		]
		
		for name, key in models:
			checkbox = QCheckBox(name)
			checkbox.setMinimumHeight(25)
			if key in ["UEM1", "GSM"]:  # 默认选中一些模型
				checkbox.setChecked(True)
			self.model_checkboxes[key] = checkbox
			models_layout.addWidget(checkbox)
		
		models_group.setLayout(models_layout)
		left_layout.addWidget(models_group)
		
		# 按钮区域
		buttons_layout = QHBoxLayout()
		
		# 计算按钮
		calculate_button = QPushButton("计算")
		calculate_button.setMinimumHeight(40)
		calculate_button.setStyleSheet(
				"font-size: 12pt; font-weight: bold; background-color: #4A86E8; color: white; border: none; border-radius: 4px;"
		)
		calculate_button.clicked.connect(self.calculate_all_properties)
		buttons_layout.addWidget(calculate_button)
		
		# 导出按钮
		export_button = QPushButton("导出数据")
		export_button.setMinimumHeight(40)
		export_button.setStyleSheet(
				"font-size: 12pt; font-weight: bold; background-color: #28a745; color: white; border: none; border-radius: 4px;"
		)
		export_button.clicked.connect(self.export_data)
		buttons_layout.addWidget(export_button)
		
		left_layout.addLayout(buttons_layout)  # 添加按钮布局
		
		# 设置左侧面板
		left_panel.setLayout(left_layout)
		left_panel.setMinimumWidth(380)
		left_panel.setMaximumWidth(450)
		
		# 绘图区域
		right_panel = QWidget()
		right_layout = QVBoxLayout()
		
		# 创建图表
		self.figure = Figure(figsize=(8, 6), dpi=100)
		self.canvas = FigureCanvas(self.figure)
		self.toolbar = NavigationToolbar(self.canvas, self)
		
		right_layout.addWidget(self.toolbar)
		right_layout.addWidget(self.canvas)
		
		right_panel.setLayout(right_layout)
		
		# 使用分割器将左右面板分开
		splitter = QSplitter(Qt.Horizontal)
		splitter.addWidget(left_panel)
		splitter.addWidget(right_panel)
		splitter.setSizes([350, 850])  # 设置初始大小分配
		
		main_layout.addWidget(splitter)
		self.setLayout(main_layout)
		
		# 连接组成输入框的信号到更新元素下拉列表的槽
		self.matrix_input.textChanged.connect(self.update_element_dropdowns)
		
		# 应用样式表
		self.apply_stylesheet()
		
		# 初始化时更新一次元素下拉列表
		self.update_element_dropdowns()
	
	def apply_stylesheet (self):
		"""应用样式表以统一外观"""
		# 标签样式
		label_style = "QLabel { font-size: 11pt; padding: 2px; }"
		
		# 输入框和下拉框样式
		input_style = """
            QLineEdit, QComboBox, QDoubleSpinBox {
                font-size: 11pt;
                padding: 3px;
                min-height: 25px;
                background-color: white;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 25px;
                border-left: 1px solid #AAAAAA;
            }
        """
		
		# 分组框样式
		group_style = """
            QGroupBox {
                font-size: 12pt;
                font-weight: bold;
                border: 1px solid #AAAAAA;
                border-radius: 5px;
                margin-top: 15px;
                padding-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }
        """
		
		# 复选框样式
		checkbox_style = """
            QCheckBox {
                font-size: 11pt;
                spacing: 8px;
                min-height: 22px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """
		
		# 按钮样式
		button_style = """
            QPushButton {
                font-size: 12pt;
                padding: 8px;
                background-color: #4A86E8;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3A76D8;
            }
            QPushButton:pressed {
                background-color: #2A66C8;
            }
        """
		
		# 应用样式
		self.setStyleSheet(label_style + input_style + group_style + checkbox_style + button_style)
	
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
			current_target = self.target_element_combo.currentText()
			current_var = self.var_element_combo.currentText()
			current_solvent = self.solvent_combo.currentText()
			
			# 获取合金中的元素列表
			elements = list(composition.keys())
			
			# 阻止信号触发，防止更新时引起不必要的事件
			self.target_element_combo.blockSignals(True)
			self.var_element_combo.blockSignals(True)
			self.solvent_combo.blockSignals(True)
			
			# 清空当前下拉列表内容
			self.target_element_combo.clear()
			self.var_element_combo.clear()
			self.solvent_combo.clear()
			
			# 添加合金中的元素到下拉列表
			self.target_element_combo.addItems(elements)
			self.var_element_combo.addItems(elements)
			self.solvent_combo.addItems(elements)
			
			# 尝试恢复之前的选择（如果元素仍然存在）
			target_index = self.target_element_combo.findText(current_target)
			if target_index >= 0:
				self.target_element_combo.setCurrentIndex(target_index)
			elif len(elements) >= 2:
				self.target_element_combo.setCurrentIndex(1)  # 默认选择第二个元素
			
			var_index = self.var_element_combo.findText(current_var)
			if var_index >= 0:
				self.var_element_combo.setCurrentIndex(var_index)
			elif len(elements) >= 2:
				self.var_element_combo.setCurrentIndex(0)  # 默认选择第一个元素
			
			solvent_index = self.solvent_combo.findText(current_solvent)
			if solvent_index >= 0:
				self.solvent_combo.setCurrentIndex(solvent_index)
			elif len(elements) >= 3:
				self.solvent_combo.setCurrentIndex(3)  # 默认选择第三个元素
			elif len(elements) >= 1:
				self.solvent_combo.setCurrentIndex(0)  # 默认选择第一个元素
			
			# 恢复信号连接
			self.target_element_combo.blockSignals(False)
			self.var_element_combo.blockSignals(False)
			self.solvent_combo.blockSignals(False)
		
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
		"""计算所有热力学性质随组分变化"""
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
		
		# 获取目标元素和变化元素
		target_element = self.target_element_combo.currentText().strip()
		target_conc = self.target_conc_spin.value()
		var_element = self.var_element_combo.currentText().strip()
		solvent = self.solvent_combo.currentText().strip()
		
		if not target_element or not var_element or not solvent:
			QMessageBox.warning(self, "输入错误", "请选择目标元素和变化元素")
			return
		
		if target_element == var_element:
			QMessageBox.warning(self, "输入错误", "目标元素和变化元素不能相同")
			return
		
		# 获取温度
		temperature = self.temp_input.value()
		
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
		
		# 创建组成范围
		min_comp = self.min_comp.value()
		max_comp = self.max_comp.value()
		step_comp = self.step_comp.value()
		comp_range = np.arange(min_comp, max_comp + step_comp / 2, step_comp)
		
		# 存储当前参数
		self.current_parameters = {
			"base_matrix": matrix_input,
			"target_element": target_element,
			"var_element": var_element,
			"solvent": solvent,
			"temperature": temperature,
			"phase_state": phase_state,
			"order_degree": order_degree,
			"geo_model": geo_model,
			"comp_range": comp_range.tolist()
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
		progress = QProgressDialog("计算中...", "取消", 0, len(selected_models) * len(comp_range) * 2, self)
		progress.setWindowTitle("计算进度")
		progress.setWindowModality(Qt.WindowModal)
		progress.setMinimumDuration(0)
		progress.setValue(0)
		
		# 计算每个模型在不同组成下的热力学性质
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
					self.calculation_results[prop][model_key] = {"compositions": [], "values": []}
				
				# 计算不同组成下的活度和活度系数
				valid_compositions = []
				valid_activity_values = []
				valid_activity_coef_values = []
				
				for x in comp_range:
					if progress.wasCanceled():
						break
					
					# 创建新的组成字典
					new_comp = {}
					# 固定目标元素浓度
					new_comp[target_element] = target_conc
					new_comp[var_element] = x
					total_others = target_conc + x
					if total_others >= 1.0:
						# 处理无法计算的情况
						continue
					new_comp[solvent] = 1.0 - total_others
					
					# 归一化组成确保总和为1
					total = sum(new_comp.values())
					if abs(total - 1.0) > 1e-10:
						for element in new_comp:
							new_comp[element] /= total
					
					# 计算活度
					try:
						progress.setLabelText(f"计算 {model_key} 模型在组成 {var_element}={x:.3f} 下的活度...")
						activity_value = UEM.activity_calc_numerical(
								new_comp, target_element, solvent, temperature,
								phase_state, order_degree, model_func, geo_model
						)
					except Exception as e:
						print(f"计算组成 {new_comp} 的活度时出错: {str(e)}")
						# 尝试使用数值方法
						try:
							# 这里可以添加数值方法的实现
							activity_value = None  # 暂时设为None
						except:
							activity_value = None
					
					# 计算活度系数
					try:
						progress.setLabelText(f"计算 {model_key} 模型在组成 {var_element}={x:.3f} 下的活度系数...")
						activity_coef_value = UEM.activityCoefficient_calc_numerical(
								new_comp, target_element, solvent, temperature,
								phase_state, order_degree, model_func, geo_model
						)
					except Exception as e:
						print(f"计算组成 {new_comp} 的活度系数时出错: {str(e)}")
						# 尝试使用数值方法
						try:
							# 这里可以添加数值方法的实现
							activity_coef_value = None  # 暂时设为None
						except:
							activity_coef_value = None
					
					# 只有当计算成功时才添加数据点
					if activity_value is not None or activity_coef_value is not None:
						valid_compositions.append(x)
						valid_activity_values.append(activity_value)
						valid_activity_coef_values.append(activity_coef_value)
					
					progress_count += 2
					progress.setValue(progress_count)
				
				# 存储有效的计算结果
				if valid_compositions:
					self.calculation_results["activity"][model_key]["compositions"] = np.array(valid_compositions)
					self.calculation_results["activity"][model_key]["values"] = np.array(valid_activity_values)
					self.calculation_results["activity_coefficient"][model_key]["compositions"] = np.array(
							valid_compositions)
					self.calculation_results["activity_coefficient"][model_key]["values"] = np.array(
							valid_activity_coef_values)
			
			# 关闭进度对话框
			progress.close()
			
			# 检查是否有有效数据
			has_valid_data = False
			for prop in self.calculation_results:
				for model_key in self.calculation_results[prop]:
					if len(self.calculation_results[prop][model_key]["compositions"]) > 0:
						has_valid_data = True
						break
				if has_valid_data:
					break
			
			if not has_valid_data:
				QMessageBox.warning(self, "无有效数据",
				                    "在指定组成范围内未能获得有效计算结果。请尝试调整组成范围或参数。")
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
		"""绘制热力学性质随组分浓度变化的图表"""
		self.figure.clear()
		
		# 创建子图
		ax = self.figure.add_subplot(111)
		
		# 设置颜色循环和标记
		colors = ['r', 'b', 'g', 'c', 'm', 'y', 'k']
		markers = ['o', 's', '^', 'D', 'v', '<', '>']
		plots = []
		labels = []
		
		# 为每个模型绘制线条
		for i, (model_key, data) in enumerate(model_results.items()):
			if "compositions" not in data or len(data["compositions"]) == 0 or "values" not in data:
				continue
			
			# 确保数据有效
			valid_indices = ~np.isnan(data["values"])
			if not np.any(valid_indices):
				continue
			
			compositions = data["compositions"][valid_indices]
			values = data["values"][valid_indices]
			
			if len(compositions) == 0:
				continue
			
			color_idx = i % len(colors)
			marker_idx = i % len(markers)
			
			# 减少数据点数量，提高清晰度
			if len(compositions) > 20:
				skip = len(compositions) // 20
				plot_comp = compositions[::skip]
				plot_values = values[::skip]
			else:
				plot_comp = compositions
				plot_values = values
			
			# 绘制曲线和数据点
			line, = ax.plot(compositions, values,
			                color=colors[color_idx],
			                marker=markers[marker_idx],
			                linewidth=2,
			                markersize=6,
			                label=self.model_checkboxes[model_key].text())
			
			plots.append(line)
			labels.append(self.model_checkboxes[model_key].text())
		
		# 设置标题和标签
		if property_type == "activity":
			y_label = "Activity (a)"
			title_property = "Activity"
		else:  # activity_coefficient
			y_label = "Activity Coefficient (γ)"
			title_property = "Activity Coefficient"
		
		# 设置X轴标签
		var_element = self.current_parameters["var_element"]
		ax.set_xlabel(f"{var_element} Mole Fraction (x)", fontsize=12)
		ax.set_ylabel(y_label, fontsize=12)
		
		# 构建标题
		target_element = self.current_parameters["target_element"]
		matrix_input = self.current_parameters["base_matrix"]
		temperature = self.current_parameters["temperature"]
		phase_dict = {"S": "Solid", "L": "Liquid"}
		phase_text = phase_dict.get(self.current_parameters["phase_state"], "Solid")
		order_text = self.current_parameters["order_degree"]
		geo_model = self.current_parameters["geo_model"]
		solvent = self.current_parameters["solvent"]
		
		title = f"{title_property} of {target_element} in {matrix_input}\n" \
		        f"Variable: {var_element}, Solvent: {solvent}, T: {temperature}K\n" \
		        f"Phase: {phase_text}, Type: {order_text}, Geo: {geo_model}"
		ax.set_title(title, fontsize=12, pad=10)
		
		# 添加网格
		ax.grid(True, linestyle='--', alpha=0.7)
		
		# 设置坐标轴刻度字体大小
		ax.tick_params(axis='both', which='major', labelsize=10)
		
		# 添加图例，放在图表外部以避免遮挡数据
		if plots:
			self.figure.legend(plots, labels, loc='upper center', bbox_to_anchor=(0.5, 0.98),
			                   ncol=min(3, len(plots)), fontsize=10)
		
		# 调整布局
		self.figure.tight_layout(rect=[0, 0, 1, 0.9])
		
		# 绘制画布
		self.canvas.draw()
	
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
		
		# 获取所有模型和所有组成点
		all_models = set()
		all_compositions = set()
		
		for prop_data in self.calculation_results.values():
			for model_key, data in prop_data.items():
				all_models.add(model_key)
				if "compositions" in data and len(data["compositions"]) > 0:
					all_compositions.update(data["compositions"])
		
		# 排序组成点和模型名称
		all_compositions = sorted(all_compositions)
		all_models = sorted(all_models)
		
		# 写入CSV文件
		with open(file_path, 'w', newline='') as csvfile:
			writer = csv.writer(csvfile)
			
			# 写入标题行 - 参数信息
			writer.writerow(['计算参数'])
			writer.writerow(['基体合金', self.current_parameters["base_matrix"]])
			writer.writerow(['目标元素', self.current_parameters["target_element"]])
			writer.writerow(['变化元素', self.current_parameters["var_element"]])
			writer.writerow(['溶剂元素', self.current_parameters["solvent"]])
			writer.writerow(['温度', f"{self.current_parameters['temperature']} K"])
			writer.writerow(['相态', "固态" if self.current_parameters["phase_state"] == "S" else "液态"])
			writer.writerow(['类型', self.current_parameters["order_degree"]])
			writer.writerow(['外推模型', self.current_parameters["geo_model"]])
			writer.writerow([])  # 空行
			
			# 写入标题行 - 数据部分
			header = [f'{self.current_parameters["var_element"]} 浓度']
			for model in all_models:
				header.extend([
					f'{model}-活度 (a)',
					f'{model}-活度系数 (γ)'
				])
			writer.writerow(header)
			
			# 写入数据行
			for comp in all_compositions:
				row = [comp]
				for model in all_models:
					# 活度
					activity_value = ''
					if model in self.calculation_results["activity"]:
						data = self.calculation_results["activity"][model]
						if "compositions" in data and len(data["compositions"]) > 0:
							idx = np.where(data["compositions"] == comp)[0]
							if idx.size > 0 and idx[0] < len(data["values"]) and not np.isnan(data["values"][idx[0]]):
								activity_value = f"{data['values'][idx[0]]:.6f}"
					row.append(activity_value)
					
					# 活度系数
					act_coef_value = ''
					if model in self.calculation_results["activity_coefficient"]:
						data = self.calculation_results["activity_coefficient"][model]
						if "compositions" in data and len(data["compositions"]) > 0:
							idx = np.where(data["compositions"] == comp)[0]
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
		header_format = workbook.add_format({
			'bold': True,
			'align': 'center',
			'valign': 'vcenter',
			'border': 1
		})
		
		param_format = workbook.add_format({
			'align': 'center',
			'valign': 'vcenter'
		})
		
		data_format = workbook.add_format({
			'num_format': '0.000000',
			'align': 'center'
		})
		
		# 获取所有模型和所有组成点
		all_models = set()
		all_compositions = set()
		
		for prop_data in self.calculation_results.values():
			for model_key, data in prop_data.items():
				all_models.add(model_key)
				if "compositions" in data and len(data["compositions"]) > 0:
					all_compositions.update(data["compositions"])
		
		# 排序组成点和模型名称
		all_compositions = sorted(all_compositions)
		all_models = sorted(all_models)
		
		# 写入标题行 - 参数信息
		worksheet.write(0, 0, '计算参数', header_format)
		worksheet.write(1, 0, '基体合金', param_format)
		worksheet.write(1, 1, self.current_parameters["base_matrix"], param_format)
		worksheet.write(2, 0, '目标元素', param_format)
		worksheet.write(2, 1, self.current_parameters["target_element"], param_format)
		worksheet.write(3, 0, '变化元素', param_format)
		worksheet.write(3, 1, self.current_parameters["var_element"], param_format)
		worksheet.write(4, 0, '溶剂元素', param_format)
		worksheet.write(4, 1, self.current_parameters["solvent"], param_format)
		worksheet.write(5, 0, '温度', param_format)
		worksheet.write(5, 1, f"{self.current_parameters['temperature']} K", param_format)
		worksheet.write(6, 0, '相态', param_format)
		worksheet.write(6, 1, "固态" if self.current_parameters["phase_state"] == "S" else "液态", param_format)
		worksheet.write(7, 0, '类型', param_format)
		worksheet.write(7, 1, self.current_parameters["order_degree"], param_format)
		worksheet.write(8, 0, '外推模型', param_format)
		worksheet.write(8, 1, self.current_parameters["geo_model"], param_format)
		
		# 写入标题行 - 数据部分
		row = 10
		worksheet.write(row, 0, f'{self.current_parameters["var_element"]} 浓度', header_format)
		col = 1
		for model in all_models:
			worksheet.write(row, col, f'{model}-活度 (a)', header_format)
			worksheet.write(row, col + 1, f'{model}-活度系数 (γ)', header_format)
			col += 2
		
		# 写入数据行
		row += 1
		for comp in all_compositions:
			worksheet.write(row, 0, comp, data_format)
			col = 1
			for model in all_models:
				# 活度
				if model in self.calculation_results["activity"]:
					data = self.calculation_results["activity"][model]
					if "compositions" in data and len(data["compositions"]) > 0:
						idx = np.where(data["compositions"] == comp)[0]
						if idx.size > 0 and idx[0] < len(data["values"]) and not np.isnan(data["values"][idx[0]]):
							worksheet.write(row, col, data['values'][idx[0]], data_format)
				col += 1
				
				# 活度系数
				if model in self.calculation_results["activity_coefficient"]:
					data = self.calculation_results["activity_coefficient"][model]
					if "compositions" in data and len(data["compositions"]) > 0:
						idx = np.where(data["compositions"] == comp)[0]
						if idx.size > 0 and idx[0] < len(data["values"]) and not np.isnan(data["values"][idx[0]]):
							worksheet.write(row, col, data['values'][idx[0]], data_format)
				col += 1
			
			row += 1
		
		# 设置列宽
		worksheet.set_column(0, 0, 12)
		for i in range(1, 2 * len(all_models) + 1):
			worksheet.set_column(i, i, 20)
		
		# 保存并关闭工作簿
		workbook.close()