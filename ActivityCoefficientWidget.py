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
		
		self.comp_input = QLineEdit()
		self.comp_input.setPlaceholderText("例如: Fe0.7Ni0.3")
		self.comp_input.setMinimumHeight(30)
		comp_layout.addWidget(QLabel("合金组成:"))
		comp_layout.addWidget(self.comp_input)
		
		# Solute and solvent selection
		solute_layout = QHBoxLayout()
		solute_layout.setSpacing(10)
		
		self.solute_combo = QComboBox()
		self.solute_combo.setMinimumHeight(30)
		self.solute_combo.setEditable(True)
		common_elements = ["Al", "Cr", "Mn", "Si", "Co", "Cu", "Ni", "Ti", "V", "Zn", "Mo", "W", "Nb", "Ta", "Rh", "Pd",
		                   "Pt", "Au"]
		self.solute_combo.addItems(common_elements)
		
		self.solvent_combo = QComboBox()
		self.solvent_combo.setMinimumHeight(30)
		self.solvent_combo.setEditable(True)
		self.solvent_combo.addItems(common_elements)
		
		solute_layout.addWidget(QLabel("溶质元素:"))
		solute_layout.addWidget(self.solute_combo)
		solute_layout.addWidget(QLabel("溶剂元素:"))
		solute_layout.addWidget(self.solvent_combo)
		
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
		self.results_text.setMinimumHeight(100)
		self.results_text.setFont(QFont("Consolas", 11))
		self.results_text.setStyleSheet("background-color: #FAFAFA;")
		results_layout.addWidget(self.results_text)
		
		results_group.setLayout(results_layout)
		left_layout.addWidget(results_group)
		
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
				
				try:
					activity_value = UEM.activity_calc(
							composition, solute, solvent, temperature,
							phase_state, order_degree, model_func, geo_model
					)
					
					self.calculation_results["activity"][model_key]["value"] = activity_value
					results_text += f"{model_key} 模型活度: {activity_value:.6f}\n"
				
				except Exception as e:
					print(f"计算活度时出错 ({model_key}): {str(e)}")
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