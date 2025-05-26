import os
import sys
import traceback
from typing import Callable, Dict, List, Optional, Tuple, Union
from datetime import datetime

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

# 假设这些模块与此文件在同一目录或已正确安装
import BinarySys as BinaryModel
import UnifiedExtrapolationModel as UEM


class ActivityCoefficientWidget(QWidget):
	"""用于计算和显示活度及活度系数的窗口组件"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.parent_window = parent
		
		# 配置matplotlib以支持中文显示
		plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
		plt.rcParams['axes.unicode_minus'] = False
		
		# 存储计算结果
		self.calculation_results = {
			"activity": {},  # 活度数据
			"activity_coefficient": {}  # 活度系数数据 (ln γ)
		}
		
		# 跟踪当前计算参数，用于导出
		self.current_parameters = {
			"composition": {},
			"comp_input": "",
			"solute": "",
			"solvent": "",
			"temperature": 0,
			"phase_state": "",
			"order_degree": "",
			"geo_model": ""
		}
		
		self.has_calculated = False
		self.init_ui()
		self.update_element_dropdowns()  # Initial population based on placeholder
	
	def init_ui (self):
		"""初始化用户界面组件"""
		# 设置整体字体
		app_font = QFont()
		app_font.setPointSize(10)
		self.setFont(app_font)
		
		# 主布局
		main_layout = QVBoxLayout()
		main_layout.setSpacing(15)
		
		# 控制面板布局
		left_panel = QWidget()
		left_layout = QVBoxLayout()
		left_layout.setSpacing(15)
		left_layout.setContentsMargins(10, 10, 10, 10)
		
		# 合金组成输入
		comp_group = QGroupBox("合金组成")
		comp_group_layout = QVBoxLayout()  # Changed to QVBoxLayout for better structure
		comp_group_layout.setSpacing(10)
		comp_group_layout.setContentsMargins(10, 20, 10, 10)
		
		comp_group_layout.addWidget(QLabel("合金组成 (例如: Fe0.7Ni0.3):"))
		
		comp_input_row = QHBoxLayout()
		self.comp_input = QLineEdit()
		self.comp_input.setPlaceholderText("例如: Fe0.7Ni0.3")
		self.comp_input.setMinimumHeight(30)
		self.comp_input.textChanged.connect(self.update_element_dropdowns)  # Connect signal
		comp_input_row.addWidget(self.comp_input)
		
		update_btn = QPushButton("更新元素")
		update_btn.setFixedWidth(80)
		update_btn.clicked.connect(self.update_element_dropdowns)
		comp_input_row.addWidget(update_btn)
		comp_group_layout.addLayout(comp_input_row)
		
		# 溶质和溶剂选择
		solute_solvent_layout = QFormLayout()  # Using QFormLayout for better label alignment
		solute_solvent_layout.setSpacing(10)
		
		self.solvent_combo = QComboBox()
		self.solvent_combo.setMinimumHeight(30)
		self.solvent_combo.setEditable(False)
		solute_solvent_layout.addRow("溶剂元素:", self.solvent_combo)
		
		self.solute_combo = QComboBox()
		self.solute_combo.setMinimumHeight(30)
		self.solute_combo.setEditable(False)
		solute_solvent_layout.addRow("溶质元素:", self.solute_combo)
		
		
		comp_group_layout.addLayout(solute_solvent_layout)
		comp_group.setLayout(comp_group_layout)
		left_layout.addWidget(comp_group)
		
		# 计算参数
		params_group = QGroupBox("计算参数")
		params_layout = QFormLayout()
		params_layout.setSpacing(12)
		params_layout.setContentsMargins(10, 25, 10, 15)
		params_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
		
		# 温度输入
		self.temp_input = QDoubleSpinBox()
		self.temp_input.setRange(300, 5000)
		self.temp_input.setValue(1000)
		self.temp_input.setSingleStep(50)
		self.temp_input.setSuffix(" K")
		self.temp_input.setMinimumHeight(30)
		params_layout.addRow("温度:", self.temp_input)
		
		# 相态选择
		self.phase_combo = QComboBox()
		self.phase_combo.addItems(["固态 (S)", "液态 (L)"])
		self.phase_combo.setMinimumHeight(30)
		params_layout.addRow("相态:", self.phase_combo)
		
		# 有序度选择
		self.order_combo = QComboBox()
		self.order_combo.addItems(["固溶体 (SS)", "非晶态 (AMP)", "金属间化合物 (IM)"])
		self.order_combo.setMinimumHeight(30)
		params_layout.addRow("类型:", self.order_combo)
		
		# 热力学性质选择 (用于绘图)
		self.property_combo = QComboBox()
		self.property_combo.addItems([
			"活度 (a)",
			"活度系数 (ln γ)"  # Displaying ln gamma
		])
		self.property_combo.setMinimumHeight(30)
		self.property_combo.currentIndexChanged.connect(self.update_plot)
		params_layout.addRow("绘图性质:", self.property_combo)
		
		
		params_group.setLayout(params_layout)
		left_layout.addWidget(params_group)
		
		# 外推模型选择
		models_group = QGroupBox("外推模型选择")
		models_layout = QVBoxLayout()  # Changed to QVBoxLayout for vertical list
		models_layout.setSpacing(10)
		models_layout.setContentsMargins(15, 15, 15, 15)  # Adjusted margins
		
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
			if key in ["UEM1", "GSM"]:  # 默认选中模型
				checkbox.setChecked(True)
			self.model_checkboxes[key] = checkbox
			models_layout.addWidget(checkbox)
		
		models_group.setLayout(models_layout)
		left_layout.addWidget(models_group)
		
		# 结果显示区域
		results_display_group = QGroupBox("计算结果")  # Changed title
		results_display_layout = QVBoxLayout()
		self.results_text = QTextEdit()
		self.results_text.setReadOnly(True)
		# --- MODIFICATION: Increased height for results text area ---
		self.results_text.setMinimumHeight(250)  # Increased from 150
		self.results_text.setFont(QFont("Consolas", 10))  # Monospaced font
		self.results_text.setStyleSheet("background-color: #f0f0f0;")
		results_display_layout.addWidget(self.results_text)
		results_display_group.setLayout(results_display_layout)
		left_layout.addWidget(results_display_group)
		
		left_layout.addStretch(1)  # Add stretch to push buttons to bottom
		
		# 按钮区域
		buttons_layout = QHBoxLayout()
		calculate_button = QPushButton("计算")
		calculate_button.setMinimumHeight(40)
		calculate_button.clicked.connect(self.calculate_all_properties)
		buttons_layout.addWidget(calculate_button)
		
		export_button = QPushButton("导出数据")
		export_button.setMinimumHeight(40)
		export_button.clicked.connect(self.export_data)
		buttons_layout.addWidget(export_button)
		left_layout.addLayout(buttons_layout)
		
		left_panel.setLayout(left_layout)
		left_panel.setMinimumWidth(400)  # Adjusted min width
		left_panel.setMaximumWidth(450)  # Adjusted max width
		
		# 绘图区域
		right_panel = QWidget()
		right_layout = QVBoxLayout()
		self.figure = Figure(figsize=(7, 5), dpi=100)  # Adjusted figure size
		self.canvas = FigureCanvas(self.figure)
		self.toolbar = NavigationToolbar(self.canvas, self)
		right_layout.addWidget(self.toolbar)
		right_layout.addWidget(self.canvas)
		right_panel.setLayout(right_layout)
		
		# 使用分割器
		splitter = QSplitter(Qt.Horizontal)
		splitter.addWidget(left_panel)
		splitter.addWidget(right_panel)
		splitter.setSizes([420, 780])  # Adjusted initial sizes
		
		main_layout.addWidget(splitter)
		self.setLayout(main_layout)
		
		self.apply_stylesheet()
		self.comp_input.setText("Fe0.7Ni0.3")  # Set default for initial population
	
	def apply_stylesheet (self):
		"""应用样式表以统一外观"""
		self.setStyleSheet("""
            QWidget {
                font-size: 10pt;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px; /* Space for title */
                padding-top: 20px; /* Space for content below title */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px 0 5px;
                left: 10px;
                color: #333333;
            }
            QLineEdit, QComboBox, QDoubleSpinBox {
                padding: 4px;
                min-height: 28px; /* Slightly taller controls */
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: white;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 20px;
                border-left: 1px solid #cccccc;
            }
            QPushButton {
                font-size: 10pt;
                padding: 8px 12px;
                background-color: #0078d7; /* A modern blue */
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #003c6c;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
        """)
	
	def update_element_dropdowns (self):
		"""根据当前输入的合金组成更新溶质和溶剂元素下拉列表"""
		comp_input_str = self.comp_input.text().strip()
		# Block signals to prevent multiple updates if not necessary
		self.solute_combo.blockSignals(True)
		self.solvent_combo.blockSignals(True)
		
		current_solute = self.solute_combo.currentText()
		current_solvent = self.solvent_combo.currentText()
		
		self.solute_combo.clear()
		self.solvent_combo.clear()
		
		if not comp_input_str:
			self.solute_combo.blockSignals(False)
			self.solvent_combo.blockSignals(False)
			return
		
		try:
			composition = self.parse_composition(comp_input_str)
			if not composition:
				self.solute_combo.blockSignals(False)
				self.solvent_combo.blockSignals(False)
				return
			
			elements = list(composition.keys())
			self.solute_combo.addItems(elements)
			self.solvent_combo.addItems(elements)
			
			if current_solute in elements:
				self.solute_combo.setCurrentText(current_solute)
			elif len(elements) >= 1:  # Default if previous not found
				self.solute_combo.setCurrentIndex(0 if len(elements) == 1 else 1)
			
			if current_solvent in elements:
				self.solvent_combo.setCurrentText(current_solvent)
			elif len(elements) >= 1:  # Default if previous not found
				self.solvent_combo.setCurrentIndex(0)
			
			# Ensure solute and solvent are different if possible
			if len(elements) >= 2 and self.solute_combo.currentText() == self.solvent_combo.currentText():
				if self.solute_combo.currentIndex() == 0:
					self.solvent_combo.setCurrentIndex(1)
				else:
					self.solvent_combo.setCurrentIndex(0)
		
		
		except Exception as e:
			print(f"更新元素下拉列表时出错: {str(e)}")
		finally:
			self.solute_combo.blockSignals(False)
			self.solvent_combo.blockSignals(False)
	
	def parse_composition (self, comp_input_str: str) -> Dict[str, float]:
		"""解析合金组成输入字符串，例如Fe0.7Ni0.3"""
		import re
		composition = {}
		pattern = r'([A-Z][a-z]*)(\d*\.?\d*)'
		matches = re.findall(pattern, comp_input_str)
		
		if not matches:
			# QMessageBox.warning(self, "解析错误", "未找到元素。请使用格式如 Fe0.7Ni0.3。")
			return {}
		
		parsed_elements = {}
		total_ratio = 0.0
		for element, ratio_str in matches:
			try:
				# 尝试验证元素是否存在 (可选，取决于 BinaryModel.Element 的行为)
				# BinaryModel.Element(element)
				ratio = float(ratio_str) if ratio_str else 1.0
				if ratio < 0:
					# QMessageBox.warning(self, "解析错误", f"元素 {element} 的比例不能为负。")
					return {}  # Invalid composition
				parsed_elements[element] = parsed_elements.get(element, 0) + ratio  # Sum if element repeats
			except Exception as e:  # Catch specific errors from Element creation if needed
				# QMessageBox.warning(self, "元素无效", f"无法识别元素 '{element}': {e}")
				return {}
		
		for ratio in parsed_elements.values():
			total_ratio += ratio
		
		if total_ratio == 0 and parsed_elements:
			# QMessageBox.warning(self, "解析错误", "所有元素比例之和为零。")
			return {}  # Or handle as equal parts if desired
		elif not parsed_elements:
			return {}
		
		# 归一化组成
		normalized_composition = {el: r / total_ratio for el, r in parsed_elements.items()}
		return normalized_composition
	
	def calculate_all_properties (self):
		"""计算所有热力学性质"""
		comp_input = self.comp_input.text().strip()
		if not comp_input:
			QMessageBox.warning(self, "输入错误", "请输入合金组成")
			return
		
		try:
			composition = self.parse_composition(comp_input)
			if not composition:
				if not self.comp_input.text().strip():
					pass
				else:
					QMessageBox.warning(self, "解析错误", "无法解析合金组成或组成无效。请使用格式如Fe0.7Ni0.3。")
				return
		except Exception as e:
			QMessageBox.critical(self, "解析错误", f"解析合金组成时发生严重错误: {str(e)}")
			traceback.print_exc()
			return
		
		solute = self.solute_combo.currentText().strip()
		solvent = self.solvent_combo.currentText().strip()
		
		if not solute or not solvent:
			QMessageBox.warning(self, "输入错误", "请选择溶质和溶剂元素。")
			return
		
		if solute not in composition or solvent not in composition:
			QMessageBox.warning(self, "元素错误", "溶质和溶剂元素必须存在于已解析的合金组成中。")
			return
		
		if solute == solvent and len(composition) > 1:
			QMessageBox.warning(self, "元素错误", "溶质和溶剂元素不能相同。")
			return
		
		temperature = self.temp_input.value()
		phase_state = "S" if self.phase_combo.currentText().startswith("固态") else "L"
		order_text = self.order_combo.currentText()
		order_degree = "SS" if order_text.startswith("固溶体") else \
			"AMP" if order_text.startswith("非晶态") else "IM"
		
		
		selected_models = [key for key, checkbox in self.model_checkboxes.items() if checkbox.isChecked()]
		if not selected_models:
			QMessageBox.warning(self, "模型选择", "请至少选择一个外推模型。")
			return
		
		self.current_parameters = {
			"composition": composition, "comp_input": comp_input, "solute": solute,
			"solvent": solvent, "temperature": temperature, "phase_state": phase_state,
			"order_degree": order_degree
		}
		
		self.calculation_results = {"activity": {}, "activity_coefficient": {}}
		
		model_functions = {
			"K": UEM.Kohler, "M": UEM.Muggianu, "T-K": UEM.Toop_Kohler,
			"GSM": UEM.GSM, "UEM1": UEM.UEM1, "UEM2_N": UEM.UEM2_N
		}
		
		progress = QProgressDialog("计算中...", "取消", 0, len(selected_models) * 2, self)
		progress.setWindowTitle("计算进度")
		progress.setWindowModality(Qt.WindowModal)
		progress.setMinimumDuration(500)
		progress.setValue(0)
		
		current_history_html = self.results_text.toHtml()
		is_initial_placeholder = "计算结果将显示在此" in current_history_html or \
		                         current_history_html.strip() == "" or \
		                         current_history_html == "<html><head/><body><p><br/></p></body></html>"
		
		new_calculation_html = f"<h3>计算批次: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h3>"
		new_calculation_html += "<div style='font-family: Consolas, monospace; font-size: 10pt;'>"
		new_calculation_html += f"<b>合金组成:</b> {comp_input}<br>"
		new_calculation_html += f"<b>溶质:</b> {solute}, <b>溶剂:</b> {solvent}<br>"
		new_calculation_html += (f"<b>温度:</b> {temperature:.2f} K, <b>相态:</b> {phase_state}, "
		                         f"<b>类型:</b> {order_degree}")
		new_calculation_html += "</div><hr>"
		new_calculation_html += "<h4>各外推模型计算详情:</h4>"
		
		calculation_successful_for_any_model = False
		calculation_was_cancelled_by_user = False  # Flag for user cancellation
		progress_count = 0
		
		try:
			for model_key in selected_models:
				if progress.wasCanceled():
					calculation_was_cancelled_by_user = True
					break
				
				extrapolation_func = model_functions.get(model_key)
				if not extrapolation_func:
					new_calculation_html += f"<p><b>{model_key} 模型:</b> 未知的模型函数。</p>"
					continue
				
				self.calculation_results["activity"][model_key] = {"value": None}
				self.calculation_results["activity_coefficient"][model_key] = {"value": None}
				
				model_display_name = self.model_checkboxes[model_key].text()
				new_calculation_html += f"<div style='margin-bottom: 10px;'>"
				new_calculation_html += f"<b>{model_display_name}:</b><br>"
				
				activity_val = None
				act_coef_ln_val = None
				
				progress.setLabelText(f"计算 {model_display_name} 活度...")
				QApplication.processEvents()
				if progress.wasCanceled(): calculation_was_cancelled_by_user = True; break
				try:
					activity_val = UEM.calculate_activity(
							composition, solute, solvent, temperature, phase_state,
							order_degree, extrapolation_func
					)
					self.calculation_results["activity"][model_key]["value"] = activity_val
					new_calculation_html += f"&nbsp;&nbsp;活度 (a<sub>{solute}</sub>): {activity_val:.6f}<br>"
					calculation_successful_for_any_model = True
				except Exception as e:
					error_msg = str(e)
					print(f"计算活度时出错 ({model_key}): {error_msg}")
					traceback.print_exc()
					new_calculation_html += f"&nbsp;&nbsp;活度 (a<sub>{solute}</sub>): <span style='color:red;'>计算失败 ({error_msg})</span><br>"
				
				progress_count += 1
				progress.setValue(progress_count)
				if progress.wasCanceled(): calculation_was_cancelled_by_user = True; break
				QApplication.processEvents()
				
				progress.setLabelText(f"计算 {model_display_name} 活度系数...")
				QApplication.processEvents()
				if progress.wasCanceled(): calculation_was_cancelled_by_user = True; break
				try:
					act_coef_ln_val = UEM.calculate_activity_coefficient(
							composition, solute, solvent, temperature,
							phase_state, order_degree, extrapolation_func
					)
					self.calculation_results["activity_coefficient"][model_key]["value"] = act_coef_ln_val
					new_calculation_html += f"&nbsp;&nbsp;活度系数 (ln &gamma;<sub>{solute}</sub>): {act_coef_ln_val:.6f}"
					calculation_successful_for_any_model = True
				except Exception as e:
					error_msg = str(e)
					print(f"计算活度系数时出错 ({model_key}): {error_msg}")
					traceback.print_exc()
					new_calculation_html += f"&nbsp;&nbsp;活度系数 (ln &gamma;<sub>{solute}</sub>): <span style='color:red;'>计算失败 ({error_msg})</span>"
				
				new_calculation_html += "</div>"
				progress_count += 1
				progress.setValue(progress_count)
				QApplication.processEvents()
			
			progress.close()  # Close progress dialog once loop is done or broken
			
			if is_initial_placeholder:
				final_html_output = new_calculation_html
			else:
				final_html_output = new_calculation_html + "<hr style='border-top: 2px dashed #bbb; margin-top:15px; margin-bottom:15px;'>" + current_history_html
			
			self.results_text.setHtml(final_html_output)
			
			if calculation_was_cancelled_by_user:
				QMessageBox.information(self, "计算取消", "计算已由用户取消。")
				# Update plot even if cancelled, to show any partial results
				self.has_calculated = calculation_successful_for_any_model
				self.update_plot()
				return  # Important to return here
			
			if not calculation_successful_for_any_model:
				QMessageBox.warning(self, "计算问题", "所有选定模型的计算均未成功。请检查参数或控制台输出。")
				# No need to modify results_text here as it already contains the attempt
				return
			
			self.has_calculated = calculation_successful_for_any_model
			self.update_plot()
			
			QMessageBox.information(self, "计算完成", "活度和活度系数计算完成。")
		
		except Exception as e:
			if not progress.isHidden():  # Check if progress dialog is still open
				progress.close()
			QMessageBox.critical(self, "计算错误", f"计算过程中发生严重错误: {str(e)}")
			traceback.print_exc()
			error_html = f"<p style='color:red;'>计算过程中发生严重错误: {str(e)}</p>"
			if is_initial_placeholder:
				self.results_text.setHtml(error_html)
			else:
				self.results_text.setHtml(
					error_html + "<hr style='border-top: 2px dashed #bbb; margin-top:15px; margin-bottom:15px;'>" + current_history_html)
	
	def update_plot (self):
		"""根据选择的热力学性质更新图表"""
		if not self.has_calculated:
			self.figure.clear()
			ax = self.figure.add_subplot(111)
			ax.text(0.5, 0.5, "请先进行计算", horizontalalignment='center', verticalalignment='center', fontsize=12,
			        color='gray')
			self.canvas.draw()
			return
		
		selected_property_text = self.property_combo.currentText()
		
		data_source_key = ""
		y_label_plot = ""
		plot_title_property = ""
		
		if "活度系数" in selected_property_text:
			data_source_key = "activity_coefficient"
			y_label_plot = f"ln $\\gamma_{{{self.current_parameters['solute']}}}$"  # LaTeX for plot
			plot_title_property = f"活度系数 (ln γ) of {self.current_parameters['solute']}"
		elif "活度" in selected_property_text:
			data_source_key = "activity"
			y_label_plot = f"$a_{{{self.current_parameters['solute']}}}$"  # LaTeX for plot
			plot_title_property = f"活度 (a) of {self.current_parameters['solute']}"
		else:
			self.figure.clear()
			self.canvas.draw()
			return
		
		model_results_for_plot = self.calculation_results.get(data_source_key, {})
		if not model_results_for_plot:
			self.figure.clear()
			ax = self.figure.add_subplot(111)
			ax.text(0.5, 0.5, "无数据可供绘图", horizontalalignment='center', verticalalignment='center', fontsize=12,
			        color='gray')
			self.canvas.draw()
			return
		
		models_plot = []
		values_plot = []
		
		for model_key, data_dict in model_results_for_plot.items():
			if data_dict and data_dict.get("value") is not None:
				# Only include models that were selected for calculation
				if model_key in self.model_checkboxes and self.model_checkboxes[model_key].isChecked():
					model_display_name = self.model_checkboxes.get(model_key).text()
					models_plot.append(model_display_name)
					values_plot.append(data_dict["value"])
		
		if not models_plot:
			self.figure.clear()
			ax = self.figure.add_subplot(111)
			ax.text(0.5, 0.5, "无有效数据可供绘图", horizontalalignment='center', verticalalignment='center',
			        fontsize=12, color='gray')
			self.canvas.draw()
			return
		
		self.figure.clear()
		ax = self.figure.add_subplot(111)
		
		# 使用Matplotlib的颜色循环
		prop_cycle = plt.rcParams['axes.prop_cycle']
		colors = prop_cycle.by_key()['color']
		
		bars = ax.bar(models_plot, values_plot, color=[colors[i % len(colors)] for i in range(len(models_plot))],
		              width=0.6)
		
		ax.set_ylabel(y_label_plot, fontsize=11)
		ax.set_title(
				f"{plot_title_property} in {self.current_parameters['comp_input']} @ {self.current_parameters['temperature']:.0f}K\n"
				,
				fontsize=10, pad=10
		)
		# Corrected line: removed 'ha' from tick_params for axis 'x'
		ax.tick_params(axis='x', rotation=25, labelsize=9)
		plt.setp(ax.get_xticklabels(), ha='right', rotation_mode='anchor')  # Set horizontal alignment separately
		ax.tick_params(axis='y', labelsize=9)
		ax.grid(True, linestyle='--', alpha=0.6, axis='y')
		
		for bar in bars:
			yval = bar.get_height()
			# Adjust text position slightly for better visibility
			va_offset = 0.02 * (max(values_plot, default=1) - min(values_plot, default=0))  # Dynamic offset
			if yval < 0: va_offset = -va_offset - 0.03 * abs(yval)
			
			ax.text(bar.get_x() + bar.get_width() / 2.0, yval + va_offset,
			        f'{yval:.4f}', ha='center', va='bottom' if yval >= 0 else 'top', fontsize=8)
		
		self.figure.tight_layout()
		self.canvas.draw()
	
	def export_data (self):
		"""导出计算数据到CSV或Excel文件"""
		if not self.has_calculated:
			QMessageBox.warning(self, "导出错误", "请先计算数据再导出。")
			return
		
		file_path, _ = QFileDialog.getSaveFileName(
				self, "导出数据", "", "CSV 文件 (*.csv);;Excel 文件 (*.xlsx);;所有文件 (*.*)"
		)
		
		if not file_path:
			return
		
		try:
			if file_path.lower().endswith('.xlsx'):
				self.export_to_excel(file_path)
			else:
				if not file_path.lower().endswith('.csv'):
					file_path += '.csv'
				self.export_to_csv(file_path)
			QMessageBox.information(self, "导出成功", f"数据已成功导出到: {file_path}")
		except Exception as e:
			QMessageBox.critical(self, "导出错误", f"导出数据时发生错误: {str(e)}")
			traceback.print_exc()
	
	def export_to_csv (self, file_path):
		"""将数据导出为CSV格式"""
		import csv
		all_models = sorted(self.model_checkboxes.keys())  # Use all defined models for headers
		
		with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:  # Added encoding
			writer = csv.writer(csvfile)
			
			writer.writerow(['计算参数'])
			writer.writerow(['合金组成', self.current_parameters["comp_input"]])
			writer.writerow(['溶质元素', self.current_parameters["solute"]])
			writer.writerow(['溶剂元素', self.current_parameters["solvent"]])
			writer.writerow(['温度 (K)', self.current_parameters["temperature"]])
			writer.writerow(['相态', self.current_parameters["phase_state"]])
			writer.writerow(['类型', self.current_parameters["order_degree"]])
			
			writer.writerow([])
			
			header = ['外推模型']
			# Check if activity and activity_coefficient keys exist
			if self.calculation_results.get("activity"):
				header.append(f'活度 (a_{self.current_parameters["solute"]})')
			if self.calculation_results.get("activity_coefficient"):
				header.append(f'活度系数 (ln γ_{self.current_parameters["solute"]})')
			writer.writerow(header)
			
			for model_key in all_models:
				if not self.model_checkboxes[model_key].isChecked():  # Only export selected models
					continue
				
				model_display_name = self.model_checkboxes[model_key].text()
				row_data = [model_display_name]
				
				activity_val_str = ""
				if model_key in self.calculation_results["activity"]:
					val = self.calculation_results["activity"][model_key].get("value")
					if val is not None:
						activity_val_str = f"{val:.6f}"
				if "活度" in header[1]:  # Check if column exists
					row_data.append(activity_val_str)
				
				act_coef_val_str = ""
				if model_key in self.calculation_results["activity_coefficient"]:
					val = self.calculation_results["activity_coefficient"][model_key].get("value")
					if val is not None:
						act_coef_val_str = f"{val:.6f}"
				if "活度系数" in header[-1]:  # Check if column exists
					row_data.append(act_coef_val_str)
				
				writer.writerow(row_data)
	
	def export_to_excel (self, file_path):
		"""将数据导出为Excel格式"""
		try:
			import xlsxwriter
		except ImportError:
			QMessageBox.warning(self, "缺少依赖", "导出Excel需要安装xlsxwriter模块。将导出为CSV格式。")
			csv_path = file_path.rsplit('.', 1)[0] + '.csv'
			self.export_to_csv(csv_path)
			return
		
		workbook = xlsxwriter.Workbook(file_path)
		worksheet = workbook.add_worksheet('计算结果')
		
		header_format = workbook.add_format(
				{'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#DDEBF7'})
		param_label_format = workbook.add_format({'bold': True, 'align': 'right'})
		param_value_format = workbook.add_format({'align': 'left'})
		data_format = workbook.add_format({'num_format': '0.000000', 'align': 'center', 'border': 1})
		model_name_format = workbook.add_format({'align': 'left', 'border': 1})
		
		row_num = 0
		worksheet.merge_range(row_num, 0, row_num, 3, '计算参数', header_format)
		row_num += 1
		
		params_to_write = [
			("合金组成:", self.current_parameters["comp_input"]),
			("溶质元素:", self.current_parameters["solute"]),
			("溶剂元素:", self.current_parameters["solvent"]),
			("温度 (K):", self.current_parameters["temperature"]),
			("相态:", self.current_parameters["phase_state"]),
			("类型:", self.current_parameters["order_degree"])
		]
		for label, value in params_to_write:
			worksheet.write(row_num, 0, label, param_label_format)
			worksheet.write(row_num, 1, value, param_value_format)
			row_num += 1
		
		row_num += 1  # Empty row
		data_header_col = 0
		worksheet.write(row_num, data_header_col, '外推模型', header_format);
		data_header_col += 1
		
		# Check if activity and activity_coefficient keys exist for header
		has_activity_data = bool(self.calculation_results.get("activity"))
		has_coeff_data = bool(self.calculation_results.get("activity_coefficient"))
		
		if has_activity_data:
			worksheet.write(row_num, data_header_col, f'活度 (a_{self.current_parameters["solute"]})', header_format);
			data_header_col += 1
		if has_coeff_data:
			worksheet.write(row_num, data_header_col, f'活度系数 (ln γ_{self.current_parameters["solute"]})',
			                header_format);
			data_header_col += 1
		row_num += 1
		
		all_models_sorted = sorted(self.model_checkboxes.keys())
		
		for model_key in all_models_sorted:
			if not self.model_checkboxes[model_key].isChecked():
				continue
			
			current_col = 0
			model_display_name = self.model_checkboxes[model_key].text()
			worksheet.write(row_num, current_col, model_display_name, model_name_format);
			current_col += 1
			
			if has_activity_data:
				activity_val = self.calculation_results["activity"].get(model_key, {}).get("value")
				if activity_val is not None:
					worksheet.write(row_num, current_col, activity_val, data_format)
				else:
					worksheet.write(row_num, current_col, "N/A", data_format)
				current_col += 1
			
			if has_coeff_data:
				act_coef_val = self.calculation_results["activity_coefficient"].get(model_key, {}).get("value")
				if act_coef_val is not None:
					worksheet.write(row_num, current_col, act_coef_val, data_format)
				else:
					worksheet.write(row_num, current_col, "N/A", data_format)
				current_col += 1
			row_num += 1
		
		worksheet.set_column(0, 0, 25)  # Model name
		if has_activity_data and has_coeff_data:
			worksheet.set_column(1, 2, 20)
		elif has_activity_data or has_coeff_data:
			worksheet.set_column(1, 1, 20)
		
		workbook.close()


# 主程序入口 (用于独立测试)
if __name__ == '__main__':
	app = QApplication(sys.argv)
	
	window = ActivityCoefficientWidget()
	window.setWindowTitle("活度与活度系数计算器")
	window.setGeometry(100, 100, 1200, 750)  # 调整窗口大小
	window.show()
	sys.exit(app.exec_())
