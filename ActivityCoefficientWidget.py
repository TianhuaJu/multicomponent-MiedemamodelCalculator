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
                             QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import BinarySys as BinaryModel
import UnifiedExtrapolationModel as UEM


class ActivityCoefficientWidget(QWidget):
	"""Widget for calculating and displaying activity and activity coefficients"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.parent_window = parent
		
		# Configure matplotlib for Chinese display
		plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
		plt.rcParams['axes.unicode_minus'] = False
		
		# Store calculation results
		self.calculation_results = {
			"activity": {},  # Activity data
			"activity_coefficient": {}  # Activity coefficient data
		}
		
		# Track current calculation parameters for export
		self.current_parameters = {
			"composition": {},
			"solute": "",
			"solvent": "",
			"temperature": 0,
			"phase_state": "",
			"order_degree": ""
		}
		
		self.has_calculated = False
		self.init_ui()
	
	def init_ui (self):
		"""Initialize user interface components"""
		# Set overall font
		app_font = QFont()
		app_font.setPointSize(10)
		self.setFont(app_font)
		
		# Main layout
		main_layout = QVBoxLayout()
		main_layout.setSpacing(15)
		
		# Control panel layout
		left_panel = QWidget()
		left_layout = QVBoxLayout()
		left_layout.setSpacing(15)
		left_layout.setContentsMargins(10, 10, 10, 10)
		
		# Alloy composition input
		comp_group = QGroupBox("合金组成")
		comp_layout = QVBoxLayout()
		comp_layout.setSpacing(10)
		comp_layout.setContentsMargins(10, 20, 10, 10)
		
		comp_input_row = QHBoxLayout()
		self.comp_input = QLineEdit()
		self.comp_input.setPlaceholderText("例如: Fe0.7Ni0.3")
		self.comp_input.setMinimumHeight(30)
		
		update_btn = QPushButton("更新元素")
		update_btn.setFixedWidth(80)
		update_btn.clicked.connect(self.update_element_dropdowns)
		
		comp_input_row.addWidget(self.comp_input)
		comp_input_row.addWidget(update_btn)
		
		comp_layout.addWidget(QLabel("合金组成:"))
		comp_layout.addLayout(comp_input_row)
		#comp_layout.addWidget(self.comp_input)
		
		# Solute and solvent selection
		solute_layout = QHBoxLayout()
		solute_layout.setSpacing(10)
		
		self.solute_combo = QComboBox()
		self.solute_combo.setMinimumHeight(30)
		self.solute_combo.setEditable(False)
		
		
		self.solvent_combo = QComboBox()
		self.solvent_combo.setMinimumHeight(30)
		self.solvent_combo.setEditable(False)
		
		
		solute_layout.addWidget(QLabel("溶剂元素:"))
		solute_layout.addWidget(self.solvent_combo)
		solute_layout.addWidget(QLabel("溶质元素:"))
		solute_layout.addWidget(self.solute_combo)
		
		comp_layout.addLayout(solute_layout)
		comp_group.setLayout(comp_layout)
		left_layout.addWidget(comp_group)
		
		# Calculation parameters
		params_group = QGroupBox("计算参数")
		params_layout = QFormLayout()
		params_layout.setSpacing(12)
		params_layout.setContentsMargins(10, 25, 10, 15)
		params_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
		
		# Temperature input
		self.temp_input = QDoubleSpinBox()
		self.temp_input.setRange(300, 5000)
		self.temp_input.setValue(1000)
		self.temp_input.setSingleStep(50)
		self.temp_input.setSuffix(" K")
		self.temp_input.setMinimumHeight(30)
		params_layout.addRow("温度:", self.temp_input)
		
		# Phase state selection
		self.phase_combo = QComboBox()
		self.phase_combo.addItems(["固态 (S)", "液态 (L)"])
		self.phase_combo.setMinimumHeight(30)
		self.phase_combo.setMinimumWidth(160)
		params_layout.addRow("相态:", self.phase_combo)
		
		# Order degree selection
		self.order_combo = QComboBox()
		self.order_combo.addItems(["固溶体 (SS)", "非晶态 (AMP)", "金属间化合物 (IM)"])
		self.order_combo.setMinimumHeight(30)
		params_layout.addRow("类型:", self.order_combo)
		
		# Thermodynamic property selection
		self.property_combo = QComboBox()
		self.property_combo.addItems([
			"活度 (a)",
			"活度系数 (γ)"
		])
		self.property_combo.setMinimumHeight(30)
		self.property_combo.currentIndexChanged.connect(self.update_plot)
		self.comp_input.textChanged.connect(self.update_element_dropdowns)
		
		params_layout.addRow("热力学性质:", self.property_combo)
		
		# Geometric model selection
		self.geo_model_combo = QComboBox()
		self.geo_model_combo.addItems(["UEM1", "UEM2_N", "GSM", "T-K", "K", "M"])
		self.geo_model_combo.setMinimumHeight(30)
		params_layout.addRow("几何模型:", self.geo_model_combo)
		
		params_group.setLayout(params_layout)
		left_layout.addWidget(params_group)
		
		# Extrapolation model selection
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
			if key in ["UEM1", "GSM"]:  # Default selected models
				checkbox.setChecked(True)
			self.model_checkboxes[key] = checkbox
			models_layout.addWidget(checkbox)
		
		models_group.setLayout(models_layout)
		left_layout.addWidget(models_group)
		
		# Results display
		results_group = QGroupBox("计算结果")
		results_layout = QVBoxLayout()
		
		self.results_text = QTextEdit()
		self.results_text.setReadOnly(True)
		self.results_text.setMinimumHeight(250)
		self.results_text.setFont(QFont("Consolas", 11))
		self.results_text.setStyleSheet("background-color: #FAFAFA;")
		results_layout.addWidget(self.results_text)
		
		results_group.setLayout(results_layout)
		left_layout.addWidget(results_group,3)
		
		# Button area
		buttons_layout = QHBoxLayout()
		
		# Calculate button
		calculate_button = QPushButton("计算")
		calculate_button.setMinimumHeight(40)
		calculate_button.setStyleSheet(
				"font-size: 12pt; font-weight: bold; background-color: #4A86E8; color: white; border: none; border-radius: 4px;"
		)
		calculate_button.clicked.connect(self.calculate_all_properties)
		buttons_layout.addWidget(calculate_button)
		
		# Export button
		export_button = QPushButton("导出数据")
		export_button.setMinimumHeight(40)
		export_button.setStyleSheet(
				"font-size: 12pt; font-weight: bold; background-color: #28a745; color: white; border: none; border-radius: 4px;"
		)
		export_button.clicked.connect(self.export_data)
		buttons_layout.addWidget(export_button)
		
		left_layout.addLayout(buttons_layout)
		
		# Set up left panel
		left_panel.setLayout(left_layout)
		left_panel.setMinimumWidth(480)
		left_panel.setMaximumWidth(500)
		
		# Plot area
		right_panel = QWidget()
		right_layout = QVBoxLayout()
		
		self.figure = Figure(figsize=(8, 6), dpi=100)
		self.canvas = FigureCanvas(self.figure)
		self.toolbar = NavigationToolbar(self.canvas, self)
		
		right_layout.addWidget(self.toolbar)
		right_layout.addWidget(self.canvas)
		
		right_panel.setLayout(right_layout)
		
		# Use splitter to separate left and right panels
		splitter = QSplitter(Qt.Horizontal)
		splitter.addWidget(left_panel)
		splitter.addWidget(right_panel)
		splitter.setSizes([350, 850])
		
		main_layout.addWidget(splitter)
		self.setLayout(main_layout)
		
		# Apply stylesheet
		self.apply_stylesheet()
	
	def apply_stylesheet (self):
		"""Apply stylesheet for consistent appearance"""
		# Label style
		label_style = "QLabel { font-size: 11pt; padding: 2px; }"
		
		# Input box and dropdown style
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
		
		# Group box style
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
		
		# Checkbox style
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
		
		# Button style
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
		
		# Apply styles
		self.setStyleSheet(label_style + input_style + group_style + checkbox_style + button_style)
	
	# 在 ActivityCoefficientWidget 类中添加方法来更新元素下拉列表
	def update_element_dropdowns (self):
		"""根据当前输入的合金组成更新溶质和溶剂元素下拉列表"""
		comp_input = self.comp_input.text().strip()
		if not comp_input:
			return
		
		try:
			# 解析合金组成
			composition = self.parse_composition(comp_input)
			if not composition:
				return
			
			# 获取合金中的元素列表
			elements = list(composition.keys())
			
			# 清空当前下拉列表内容
			self.solute_combo.clear()
			self.solvent_combo.clear()
			
			# 添加合金中的元素到下拉列表
			self.solute_combo.addItems(elements)
			self.solvent_combo.addItems(elements)
			
			# 如果有两个或更多元素，设置默认选择
			if len(elements) >= 2:
				self.solute_combo.setCurrentIndex(1)  # 默认选择第二个元素作为溶质
				self.solvent_combo.setCurrentIndex(0)  # 默认选择第一个元素作为溶剂
		
		except Exception as e:
			print(f"更新元素下拉列表时出错: {str(e)}")
	def parse_composition (self, comp_input):
		"""Parse alloy composition input string, such as Fe0.7Ni0.3"""
		import re
		composition = {}
		# Regular expression to match elements and their ratios
		pattern = r'([A-Z][a-z]*)(\d*\.?\d*)'
		
		matches = re.findall(pattern, comp_input)
		
		for element, ratio_str in matches:
			# Default to 1 if no ratio specified
			ratio = float(ratio_str) if ratio_str else 1.0
			composition[element] = ratio
		
		# Normalize composition
		total = sum(composition.values())
		if total > 0:
			for element in composition:
				composition[element] /= total
		
		return composition
	
	def calculate_all_properties (self):
		"""Calculate all thermodynamic properties"""
		# Get alloy composition
		comp_input = self.comp_input.text().strip()
		if not comp_input:
			QMessageBox.warning(self, "输入错误", "请输入合金组成")
			return
		
		try:
			composition = self.parse_composition(comp_input)
			if not composition:
				QMessageBox.warning(self, "解析错误", "无法解析合金组成，请使用格式如Fe0.7Ni0.3")
				return
		except Exception as e:
			QMessageBox.critical(self, "解析错误", f"解析合金组成时出错: {str(e)}")
			return
		
		# Get solute and solvent
		solute = self.solute_combo.currentText().strip()
		solvent = self.solvent_combo.currentText().strip()
		
		if not solute or not solvent:
			QMessageBox.warning(self, "输入错误", "请选择溶质元素和溶剂元素")
			return
		
		if solute not in composition or solvent not in composition:
			QMessageBox.warning(self, "元素错误", "溶质和溶剂元素必须存在于合金组成中")
			return
		
		# Get temperature
		temperature = self.temp_input.value()
		
		# Get phase state
		phase_state = "S" if self.phase_combo.currentText().startswith("固态") else "L"
		
		# Get order degree
		order_text = self.order_combo.currentText()
		if order_text.startswith("固溶体"):
			order_degree = "SS"
		elif order_text.startswith("非晶态"):
			order_degree = "AMP"
		else:
			order_degree = "IM"
		
		# Get geometric model
		geo_model = self.geo_model_combo.currentText()
		
		# Check selected models
		selected_models = [key for key, checkbox in self.model_checkboxes.items() if checkbox.isChecked()]
		if not selected_models:
			QMessageBox.warning(self, "模型选择", "请至少选择一个外推模型")
			return
		
		# Store current parameters
		self.current_parameters = {
			"composition": composition,
			"comp_input": comp_input,
			"solute": solute,
			"solvent": solvent,
			"temperature": temperature,
			"phase_state": phase_state,
			"order_degree": order_degree,
			"geo_model": geo_model
		}
		
		# Clear previous calculation results
		self.calculation_results = {
			"activity": {},  # Activity data
			"activity_coefficient": {}  # Activity coefficient data
		}
		
		# Get model function mapping
		model_functions = {
			"K": UEM.Kohler,
			"M": UEM.Muggianu,
			"T-K": UEM.Toop_Kohler,
			"GSM": UEM.GSM,
			"UEM1": UEM.UEM1,
			"UEM2_N": UEM.UEM2_N
		}
		
		# Show progress dialog
		progress = QProgressDialog("计算中...", "取消", 0, len(selected_models) * 2, self)
		progress.setWindowTitle("计算进度")
		progress.setWindowModality(Qt.WindowModal)
		progress.setMinimumDuration(0)
		progress.setValue(0)
		
		
		
		# Calculate for each model
		try:
			progress_count = 0
			current_results = self.results_text.toPlainText()
			results_text = "计算结果：\n"
			
			for model_key in selected_models:
				if progress.wasCanceled():
					break
				
				model_func = model_functions.get(model_key)
				if not model_func:
					continue
				
				# Initialize data structures for this model
				for prop in ["activity", "activity_coefficient"]:
					self.calculation_results[prop][model_key] = {"value": None}
				
				# Calculate activity
				progress.setLabelText(f"计算 {model_key} 模型的活度...")
				
				# 修改calculate_all_properties方法
				try:
					activity_value = UEM.activity_calc(
							composition, solute, solvent, temperature,
							phase_state, order_degree, model_func, geo_model
					)
					
					self.calculation_results["activity"][model_key]["value"] = activity_value
					results_text += f"{model_key} 模型活度: {activity_value:.6f}\n"
				
				except Exception as e:
					error_msg = str(e)
					print(f"计算活度时出错 ({model_key}): {error_msg}")
					
					# 尝试使用备选的数值方法
					try:
						print("尝试使用数值方法计算...")
						activity_value = UEM.activity_calc_numerical(
								composition, solute, solvent, temperature,
								phase_state, order_degree, model_func, geo_model
						)
						
						self.calculation_results["activity"][model_key]["value"] = activity_value
						results_text += f"{model_key} 模型活度: {activity_value:.6f} (数值方法)\n"
					except Exception as e2:
						print(f"数值方法也失败: {str(e2)}")
						results_text += f"{model_key} 模型活度: 计算失败\n"
				
				progress_count += 1
				progress.setValue(progress_count)
				
				# Calculate activity coefficient
				progress.setLabelText(f"计算 {model_key} 模型的活度系数...")
				
				try:
					act_coef_value = UEM.activityCoefficient_calc(
							composition, solute, solvent, temperature,
							phase_state, order_degree, model_func, geo_model
					)
					
					self.calculation_results["activity_coefficient"][model_key]["value"] = act_coef_value
					results_text += f"{model_key} 模型活度系数: {act_coef_value:.6f}\n"
				
				except Exception as e:
					print(f"计算活度系数时出错 ({model_key}): {str(e)}")
					results_text += f"{model_key} 模型活度系数: 计算失败\n"
					
					try:
						print("尝试使用数值方法计算...")
						activity_value = UEM.activityCoefficient_calc_numerical(
								composition, solute, solvent, temperature,
								phase_state, order_degree, model_func, geo_model
						)
						
						self.calculation_results["activity_coefficient"][model_key]["value"] = activity_value
						results_text += f"{model_key} 模型活度系数: {activity_value:.6f} (数值方法)\n"
					except Exception as e2:
						print(f"数值方法也失败: {str(e2)}")
						results_text += f"{model_key} 模型活度系数: 计算失败\n"
				
				results_text += "\n"
				
				progress_count += 1
				progress.setValue(progress_count)
			
			# Close progress dialog
			progress.close()
		
			# Check if we have valid data
			has_valid_data = False
			for prop in self.calculation_results:
				for model_key in self.calculation_results[prop]:
					if self.calculation_results[prop][model_key]["value"] is not None:
						has_valid_data = True
						break
				if has_valid_data:
					break
			
			if not has_valid_data:
				QMessageBox.warning(self, "无有效数据", "未能获得有效计算结果。请检查输入参数。")
				return
			
			# Mark as calculated
			self.has_calculated = True
			
			from datetime import datetime
			timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			results_text = f"--- {timestamp} ---\n" + results_text + "\n"
			combined_results = current_results + '\n' + results_text
			self.results_text.setText(combined_results)
			# Update results display
			self.results_text.setText(results_text)
			
			# Update plot
			self.update_plot()
			
			# Show success message
			QMessageBox.information(self, "计算完成", "活度和活度系数计算完成，可查看结果和图表。")
		
		except Exception as e:
			# Close progress dialog
			progress.close()
			
			# Show error message
			QMessageBox.critical(self, "计算错误", f"计算过程中发生错误: {str(e)}")
			traceback.print_exc()
	
	def update_plot (self):
		"""Update plot based on selected thermodynamic property"""
		if not self.has_calculated:
			return
		
		# Get current selected property
		property_index = self.property_combo.currentIndex()
		property_types = ["activity", "activity_coefficient"]
		if property_index >= len(property_types):
			return
		
		selected_property = property_types[property_index]
		
		# Get calculation results for the property
		model_results = self.calculation_results[selected_property]
		
		# No data, return
		if not model_results:
			return
		
		# Draw chart
		self.plot_model_comparison(model_results, selected_property)
	
	def plot_model_comparison (self, model_results, property_type):
		"""Plot comparison of different models"""
		self.figure.clear()
		
		# Create bar chart
		ax = self.figure.add_subplot(111)
		
		# Prepare data for bar chart
		models = []
		values = []
		
		for model_key, data in model_results.items():
			if data["value"] is not None:
				models.append(self.model_checkboxes[model_key].text())
				values.append(data["value"])
		
		if not models:
			return
		
		# Set colors for bars
		colors = ['#4A86E8', '#E8993A', '#6AA84F', '#CC0000', '#674EA7', '#999999']
		colors = colors[:len(models)]  # Limit to number of models
		
		# Create bar chart
		bars = ax.bar(models, values, color=colors, width=0.6)
		
		# Add value labels on top of bars
		for bar in bars:
			height = bar.get_height()
			ax.text(bar.get_x() + bar.get_width() / 2., height + 0.01 * max(values),
			        f'{height:.4f}', ha='center', va='bottom', fontsize=9)
		
		# Set title and labels
		if property_type == "activity":
			title_property = "Activity"
			y_label = "Activity (a)"
		else:  # activity_coefficient
			title_property = "Activity Coefficient"
			y_label = "Activity Coefficient (γ)"
		
		# Set axis labels
		ax.set_xlabel("Extrapolation Model", fontsize=12)
		ax.set_ylabel(y_label, fontsize=12)
		
		# Build title
		comp_input = self.current_parameters["comp_input"]
		solute = self.current_parameters["solute"]
		solvent = self.current_parameters["solvent"]
		temperature = self.current_parameters["temperature"]
		phase_dict = {"S": "Solid", "L": "Liquid"}
		phase_text = phase_dict.get(self.current_parameters["phase_state"], "Solid")
		order_text = self.current_parameters["order_degree"]
		geo_model = self.current_parameters["geo_model"]
		
		title = f"{title_property} of {solute} in {comp_input}\n" \
		        f"Solvent: {solvent}, T: {temperature}K, Phase: {phase_text}, Type: {order_text}, Geo: {geo_model}"
		ax.set_title(title, fontsize=12, pad=10)
		
		# Add grid
		ax.grid(True, linestyle='--', alpha=0.7, axis='y')
		
		# Set axis tick font size
		ax.tick_params(axis='both', which='major', labelsize=10)
		
		# Rotate x-axis labels for better readability
		plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
		
		# Adjust layout
		self.figure.tight_layout()
		
		# Draw canvas
		self.canvas.draw()
	
	def export_data (self):
		"""Export calculation data to CSV file"""
		if not self.has_calculated:
			QMessageBox.warning(self, "导出错误", "请先计算数据再导出")
			return
		
		# Get save file path
		file_path, _ = QFileDialog.getSaveFileName(
				self, "导出数据", "", "CSV文件 (*.csv);;Excel文件 (*.xlsx);;所有文件 (*.*)"
		)
		
		if not file_path:
			return
		
		try:
			# Determine export format based on file extension
			if file_path.lower().endswith('.xlsx'):
				self.export_to_excel(file_path)
			else:
				# Default to CSV
				if not file_path.lower().endswith('.csv'):
					file_path += '.csv'
				self.export_to_csv(file_path)
			
			QMessageBox.information(self, "导出成功", f"数据已成功导出到: {file_path}")
		except Exception as e:
			QMessageBox.critical(self, "导出错误", f"导出数据时发生错误: {str(e)}")
			traceback.print_exc()
	
	def export_to_csv (self, file_path):
		"""Export data to CSV format"""
		import csv
		
		# Get all models
		all_models = set()
		
		for prop_data in self.calculation_results.values():
			for model_key in prop_data:
				all_models.add(model_key)
		
		# Sort models
		all_models = sorted(all_models)
		
		# Prepare data
		with open(file_path, 'w', newline='') as csvfile:
			writer = csv.writer(csvfile)
			
			# Write header row - parameter info
			writer.writerow(['计算参数'])
			writer.writerow(['合金组成', self.current_parameters["comp_input"]])
			writer.writerow(['溶质元素', self.current_parameters["solute"]])
			writer.writerow(['溶剂元素', self.current_parameters["solvent"]])
			writer.writerow(['温度', f"{self.current_parameters['temperature']} K"])
			writer.writerow(['相态', "固态" if self.current_parameters["phase_state"] == "S" else "液态"])
			writer.writerow(['类型', self.current_parameters["order_degree"]])
			writer.writerow(['几何模型', self.current_parameters["geo_model"]])
			writer.writerow([])  # Empty row
			
			# Write header row - data section
			writer.writerow(['外推模型', '活度 (a)', '活度系数 (γ)'])
			
			# Write data rows
			for model in all_models:
				row = [model]
				
				# Activity
				activity_value = ''
				if model in self.calculation_results["activity"]:
					data = self.calculation_results["activity"][model]
					if data["value"] is not None:
						activity_value = f"{data['value']:.6f}"
				row.append(activity_value)
				
				# Activity coefficient
				act_coef_value = ''
				if model in self.calculation_results["activity_coefficient"]:
					data = self.calculation_results["activity_coefficient"][model]
					if data["value"] is not None:
						act_coef_value = f"{data['value']:.6f}"
				row.append(act_coef_value)
				
				writer.writerow(row)
	
	def export_to_excel (self, file_path):
		"""Export data to Excel format"""
		try:
			import xlsxwriter
		except ImportError:
			QMessageBox.warning(self, "缺少依赖", "导出Excel需要安装xlsxwriter模块。将导出为CSV格式。")
			self.export_to_csv(file_path.replace('.xlsx', '.csv'))
			return
		
		# Create workbook and worksheet
		workbook = xlsxwriter.Workbook(file_path)
		worksheet = workbook.add_worksheet('计算结果')
		
		# Set formats
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
		
		# Get all models
		all_models = set()
		
		for prop_data in self.calculation_results.values():
			for model_key in prop_data:
				all_models.add(model_key)
		
		# Sort models
		all_models = sorted(all_models)
		
		# Write header row - parameter info
		worksheet.write(0, 0, '计算参数', header_format)
		worksheet.write(1, 0, '合金组成', param_format)
		worksheet.write(1, 1, self.current_parameters["comp_input"], param_format)
		worksheet.write(2, 0, '溶质元素', param_format)
		worksheet.write(2, 1, self.current_parameters["solute"], param_format)
		worksheet.write(3, 0, '溶剂元素', param_format)
		worksheet.write(3, 1, self.current_parameters["solvent"], param_format)
		worksheet.write(4, 0, '温度', param_format)
		worksheet.write(4, 1, f"{self.current_parameters['temperature']} K", param_format)
		worksheet.write(5, 0, '相态', param_format)
		worksheet.write(5, 1, "固态" if self.current_parameters["phase_state"] == "S" else "液态", param_format)
		worksheet.write(6, 0, '类型', param_format)
		worksheet.write(6, 1, self.current_parameters["order_degree"], param_format)
		worksheet.write(7, 0, '几何模型', param_format)
		worksheet.write(7, 1, self.current_parameters["geo_model"], param_format)
		
		# Write header row - data section
		row = 9
		worksheet.write(row, 0, '外推模型', header_format)
		worksheet.write(row, 1, '活度 (a)', header_format)
		worksheet.write(row, 2, '活度系数 (γ)', header_format)
		
		# Write data rows
		row += 1
		for model in all_models:
			worksheet.write(row, 0, model, param_format)
			
			# Activity
			if model in self.calculation_results["activity"]:
				data = self.calculation_results["activity"][model]
				if data["value"] is not None:
					worksheet.write(row, 1, data["value"], data_format)
			
			# Activity coefficient
			if model in self.calculation_results["activity_coefficient"]:
				data = self.calculation_results["activity_coefficient"][model]
				if data["value"] is not None:
					worksheet.write(row, 2, data["value"], data_format)
			
			row += 1
		
		# Set column widths
		worksheet.set_column(0, 0, 15)
		worksheet.set_column(1, 2, 20)
		
		# Save and close workbook
		workbook.close()