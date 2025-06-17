# SingleCalculationWidget.py
import sys
import os
import traceback
from typing import Callable
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QRegExpValidator, QFont
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
                             QMessageBox, QGroupBox, QFormLayout, QTabWidget,
                             QTextEdit, QFileDialog, QDoubleSpinBox)

from core import UnifiedExtrapolationModel as UEM, BinarySys as BinaryModel

# 定义贡献模型函数类型
ContributionModelFunc = Callable[[str, str, str, float, str, str], float]


def resource_path (relative_path):
	""" 获取资源的绝对路径 """
	if hasattr(sys, '_MEIPASS'):
		base_path = sys._MEIPASS
	else:
		base_path = os.path.abspath(".")
	return os.path.join(base_path, relative_path)


class PeriodicTableWidget(QWidget):
	"""用于元素选择的周期表小部件"""
	
	def __init__ (self, parent=None, main_window=None):
		super().__init__(parent)
		self.main_window = main_window  # 存储对父窗口(SingleCalculationWidget)的引用
		self.selected_elements = set()
		self.element_buttons = {}
		self.init_ui()
	
	def init_ui (self):
		layout = QVBoxLayout()
		self.create_periodic_table()
		
		title_label = QLabel("Click an element to add it to your composition, click again to remove")
		title_label.setFont(QFont("Arial", 11))
		layout.addWidget(title_label)
		layout.addWidget(self.table_widget)
		
		self.setLayout(layout)
	
	def generate_button_style (self, bg_color, border_color, selected=False):
		if selected:
			return f"""
                background-color: {border_color}; color: white; font-weight: bold; border: 2px solid #000000;
            """
		else:
			return f"""
                QPushButton {{ background-color: {bg_color}; color: #000000; font-weight: bold; border: 1px solid {border_color}; }}
                QPushButton:hover {{ background-color: {border_color}; color: #FFFFFF; }}
                QPushButton:pressed {{ background-color: #555555; color: #FFFFFF; border: 2px solid #000000; }}
            """
	
	def update_button_state (self, element, is_selected):
		if element not in self.element_buttons:
			return
		
		button = self.element_buttons[element]
		
		if element in ["H", "N", "O", "P", "S"]:
			bg_color, border_color = "#FF9999", "#CC6666"
		elif element in ["B", "Si", "Ge", "As", "Sb", "Te", "Po"]:
			bg_color, border_color = "#99CCFF", "#6699CC"
		elif element in ["Li", "Na", "K", "Rb", "Cs", "Fr", "Be", "Mg", "Ca", "Sr", "Ba", "Ra"]:
			bg_color, border_color = "#99FF99", "#66CC66"
		elif element in ["Al", "Ga", "In", "Sn", "Tl", "Pb", "Bi", "Nh", "Fl", "Mc"]:
			bg_color, border_color = "#FFFF99", "#CCCC66"
		else:
			bg_color, border_color = "#CC99FF", "#9966CC"
		
		button.setStyleSheet(self.generate_button_style(bg_color, border_color, is_selected))
	
	def create_periodic_table (self):
		elements = [
			["H", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "He"],
			["Li", "Be", "", "", "", "", "", "", "", "", "", "", "B", "C", "N", "O", "F", "Ne"],
			["Na", "Mg", "", "", "", "", "", "", "", "", "", "", "Al", "Si", "P", "S", "Cl", "Ar"],
			["K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga", "Ge", "As", "Se", "Br", "Kr"],
			["Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe"],
			["Cs", "Ba", "La", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn"],
			["Fr", "Ra", "Ac", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts",
			 "Og"],
			["", "", "", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", ""],
			["", "", "", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr", ""]
		]
		inactive_elements = ["He", "Ne", "Ar", "Kr", "Xe", "Rn", "Og", "F", "Cl", "Br", "I", "At", "Ts", "Lv", "Fr",
		                     "Ra", "Ac", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Pa",
		                     "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"]
		
		self.table_widget = QWidget()
		grid_layout = QVBoxLayout()
		
		for row in elements:
			row_layout = QHBoxLayout()
			for element in row:
				if element:
					button = QPushButton(element)
					button.setFixedSize(40, 40)
					if element in inactive_elements:
						button.setStyleSheet(
							"background-color: #CCCCCC; color: #666666; font-weight: bold; border: 1px solid #999999;")
						button.setEnabled(False)
					else:
						button.setFont(QFont("Arial", 10, QFont.Bold))
						self.element_buttons[element] = button
						button.clicked.connect(lambda checked, elem=element: self.toggle_element(elem))
						self.update_button_state(element, False)
				else:
					button = QLabel("")
					button.setFixedSize(40, 40)
				row_layout.addWidget(button)
			row_layout.addStretch()
			grid_layout.addLayout(row_layout)
		grid_layout.addStretch()
		self.table_widget.setLayout(grid_layout)
		
		legend_layout = QHBoxLayout()
		legends = [("非金属", "#FF9999"), ("类金属", "#99CCFF"), ("碱金属/碱土金属", "#99FF99"),
		           ("后过渡金属", "#FFFF99"), ("过渡金属", "#CC99FF"), ("不可用元素", "#CCCCCC")]
		for text, color in legends:
			legend_item, item_layout = QWidget(), QHBoxLayout()
			color_box = QLabel()
			color_box.setFixedSize(15, 15)
			color_box.setStyleSheet(f"background-color: {color}; border: 1px solid #999999;")
			item_layout.addWidget(color_box)
			item_layout.addWidget(QLabel(text))
			item_layout.setContentsMargins(2, 0, 10, 0)
			legend_item.setLayout(item_layout)
			legend_layout.addWidget(legend_item)
		
		selected_item, selected_layout = QWidget(), QHBoxLayout()
		selected_box = QLabel()
		selected_box.setFixedSize(15, 15)
		selected_box.setStyleSheet("background-color: #666666; border: 2px solid #000000;")
		selected_layout.addWidget(selected_box)
		selected_layout.addWidget(QLabel("已选中"))
		selected_item.setLayout(selected_layout)
		legend_layout.addWidget(selected_item)
		legend_layout.addStretch()
		grid_layout.addLayout(legend_layout)
	
	def toggle_element (self, element):
		if element in self.selected_elements:
			self.selected_elements.remove(element)
			self.update_button_state(element, False)
			if self.main_window:
				self.main_window.remove_element(element)
		else:
			self.selected_elements.add(element)
			self.update_button_state(element, True)
			if self.main_window:
				self.main_window.add_element(element)


class CompositionTableWidget(QWidget):
	"""管理元素组成的小部件"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.composition = {}
		self.init_ui()
	
	def init_ui (self):
		layout = QVBoxLayout()
		
		self.table = QTableWidget(0, 3)
		self.table.setHorizontalHeaderLabels(["Element", "Composition", "Actions"])
		self.table.horizontalHeader().setStretchLastSection(True)
		
		add_layout = QHBoxLayout()
		self.element_input = QLineEdit()
		self.element_input.setPlaceholderText("Element symbol")
		self.element_input.setValidator(QRegExpValidator(QRegExp("[A-Za-z]{1,2}")))
		self.comp_input = QDoubleSpinBox()
		self.comp_input.setRange(0.01, 100.0)
		self.comp_input.setValue(1.0)
		add_button = QPushButton("Add")
		add_button.clicked.connect(self.add_element_from_input)
		add_layout.addWidget(self.element_input)
		add_layout.addWidget(self.comp_input)
		add_layout.addWidget(add_button)
		
		layout.addWidget(QLabel("Composition Table:"))
		layout.addWidget(self.table)
		layout.addLayout(add_layout)
		
		actions_layout = QHBoxLayout()
		normalize_button = QPushButton("Normalize")
		normalize_button.clicked.connect(self.normalize_composition)
		clear_button = QPushButton("Clear All")
		clear_button.clicked.connect(self.clear_composition)
		actions_layout.addWidget(normalize_button)
		actions_layout.addWidget(clear_button)
		
		layout.addLayout(actions_layout)
		self.setLayout(layout)
	
	def add_element (self, element, composition=1.0):
		if element in self.composition:
			QMessageBox.warning(self, "Element Exists", f"Element {element} already exists.")
			return
		try:
			BinaryModel.Element(element)
			self.composition[element] = float(composition)
			self.update_table()
		except Exception as e:
			QMessageBox.critical(self, "Invalid Element", f"Error adding element {element}: {str(e)}")
	
	def add_element_from_input (self):
		element = self.element_input.text().strip().capitalize()
		if element:
			self.add_element(element, self.comp_input.value())
			self.element_input.clear()
			self.comp_input.setValue(1.0)
	
	def update_table (self):
		self.table.setRowCount(0)
		for element, composition in self.composition.items():
			row = self.table.rowCount()
			self.table.insertRow(row)
			elem_item = QTableWidgetItem(element)
			elem_item.setFlags(elem_item.flags() & ~Qt.ItemIsEditable)
			self.table.setItem(row, 0, elem_item)
			self.table.setItem(row, 1, QTableWidgetItem(str(composition)))
			delete_button = QPushButton("Delete")
			delete_button.clicked.connect(lambda checked, elem=element: self.remove_element(elem))
			self.table.setCellWidget(row, 2, delete_button)
	
	def remove_element (self, element):
		if element in self.composition:
			del self.composition[element]
			self.update_table()
	
	def normalize_composition (self):
		total = sum(self.composition.values())
		if total > 0:
			for element in self.composition:
				self.composition[element] /= total
			self.update_table()
	
	def clear_composition (self):
		self.composition.clear()
		self.table.setRowCount(0)
	
	def get_composition (self):
		return self.composition.copy()


class ResultsWidget(QWidget):
	"""显示计算结果的小部件"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.calculation_history = []
		self.init_ui()
	
	def init_ui (self):
		layout = QVBoxLayout()
		
		results_group = QGroupBox("Calculation Results")
		results_group.setFont(QFont("Arial", 12, QFont.Bold))
		results_layout = QFormLayout()
		results_layout.setSpacing(15)
		
		self.enthalpy_result = self.create_result_field()
		self.gibbs_result = self.create_result_field()
		self.entropy_result = self.create_result_field()
		
		results_layout.addRow(QLabel("Mixing Enthalpy (kJ/mol):"), self.enthalpy_result)
		results_layout.addRow(QLabel("Gibbs Energy (kJ/mol):"), self.gibbs_result)
		results_layout.addRow(QLabel("Mixing Entropy (J/mol·K):"), self.entropy_result)
		results_group.setLayout(results_layout)
		
		details_group = QGroupBox("Calculation History")
		details_group.setFont(QFont("Arial", 12, QFont.Bold))
		details_layout = QVBoxLayout()
		self.details_text = QTextEdit()
		self.details_text.setReadOnly(True)
		self.details_text.setFont(QFont("Consolas", 11))
		details_layout.addWidget(self.details_text)
		details_group.setLayout(details_layout)
		
		export_button = QPushButton("Export Results")
		export_button.clicked.connect(self.export_results)
		
		layout.addWidget(results_group)
		layout.addWidget(details_group)
		layout.addWidget(export_button)
		self.setLayout(layout)
	
	def create_result_field (self):
		line_edit = QLineEdit()
		line_edit.setReadOnly(True)
		line_edit.setFont(QFont("Arial", 12))
		return line_edit
	
	def set_results (self, enthalpy, gibbs, entropy, composition, details, sub_binaries=None):
		self.enthalpy_result.setText(f"{enthalpy:.4f}")
		self.gibbs_result.setText(f"{gibbs:.4f}")
		self.entropy_result.setText(f"{entropy:.4f}")
		
		from datetime import datetime
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		history_entry = f"\n{'=' * 80}\nCALCULATION AT {timestamp}\n{'=' * 80}\n"
		history_entry += f"RESULTS:\n  Mixing Enthalpy (kJ/mol): {enthalpy:.4f}\n  Gibbs Energy (kJ/mol): {gibbs:.4f}\n  Mixing Entropy (J/mol·K): {entropy:.4f}\n"
		history_entry += f"{'-' * 80}\n\nDETAILS:\n{details}\n{'-' * 80}\n"
		
		self.calculation_history.append(history_entry)
		self.details_text.setPlainText("".join(reversed(self.calculation_history)))
	
	def export_results (self):
		filename, _ = QFileDialog.getSaveFileName(self, "Export Results", "", "Text Files (*.txt)")
		if filename:
			try:
				with open(filename, 'w') as f:
					f.write(f"Mixing Enthalpy (kJ/mol): {self.enthalpy_result.text()}\n")
					f.write(f"Gibbs Energy (kJ/mol): {self.gibbs_result.text()}\n")
					f.write(f"Mixing Entropy (J/mol·K): {self.entropy_result.text()}\n\n")
					f.write("Calculation History:\n")
					f.write(self.details_text.toPlainText())
				QMessageBox.information(self, "Export Successful", f"Results exported to {filename}")
			except Exception as e:
				QMessageBox.critical(self, "Export Failed", f"Failed to export results: {str(e)}")


class SingleCalculationWidget(QWidget):
	"""用于单个计算的主小部件，整合了所有相关组件"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.init_ui()
	
	def init_ui (self):
		layout = QHBoxLayout()
		layout.setSpacing(20)
		
		# 左侧面板 (输入)
		left_panel = QWidget()
		left_layout = QVBoxLayout()
		left_layout.setSpacing(15)
		
		tabs = QTabWidget()
		tabs.setFont(QFont("Arial", 11))
		
		# 将自身(SingleCalculationWidget)作为main_window传递
		self.periodic_table = PeriodicTableWidget(parent=tabs, main_window=self)
		self.composition_table = CompositionTableWidget(tabs)
		
		tabs.addTab(self.periodic_table, "Periodic Table")
		tabs.addTab(self.composition_table, "Composition")
		left_layout.addWidget(tabs)
		
		# 参数区域
		params_group = QGroupBox("Calculation Parameters")
		params_group.setFont(QFont("Arial", 12, QFont.Bold))
		params_layout = QFormLayout()
		params_layout.setSpacing(15)
		
		self.temp_input = QDoubleSpinBox()
		self.temp_input.setRange(300, 5000)
		self.temp_input.setValue(1000)
		self.temp_input.setSuffix(" K")
		params_layout.addRow(QLabel("Temperature:"), self.temp_input)
		
		self.phase_combo = QComboBox()
		self.phase_combo.addItems(["Solid (S)", "Liquid (L)"])
		params_layout.addRow(QLabel("Phase State:"), self.phase_combo)
		
		self.order_combo = QComboBox()
		self.order_combo.addItems(["Solid Solution (SS)", "Amorphous (AMP)", "Intermetallic (IM)"])
		params_layout.addRow(QLabel("Order Degree:"), self.order_combo)
		
		self.model_combo = QComboBox()
		self.model_combo.addItems(["Kohler (K)", "Muggianu (M)", "Toop-Kohler (T-K)", "GSM/Chou", "UEM1", "UEM2_N"])
		params_layout.addRow(QLabel("Extrapolation Model:"), self.model_combo)
		
		params_group.setLayout(params_layout)
		left_layout.addWidget(params_group)
		
		# 计算按钮
		calc_button = QPushButton("Calculate")
		calc_button.clicked.connect(self.calculate)
		calc_button.setFont(QFont("Arial", 14, QFont.Bold))
		left_layout.addWidget(calc_button)
		left_panel.setLayout(left_layout)
		
		# 右侧面板 (结果)
		self.results_widget = ResultsWidget()
		
		layout.addWidget(left_panel, 1)
		layout.addWidget(self.results_widget, 2)
		self.setLayout(layout)
	
	def add_element (self, element):
		"""从周期表添加元素到成分表"""
		self.composition_table.add_element(element)
	
	def remove_element (self, element):
		"""从成分表中移除元素"""
		self.composition_table.remove_element(element)
		# 更新周期表按钮状态
		if element in self.periodic_table.selected_elements:
			self.periodic_table.selected_elements.remove(element)
			self.periodic_table.update_button_state(element, False)
	
	def get_model_function (self) -> tuple[ContributionModelFunc, str]:
		model_text = self.model_combo.currentText()
		model_map = {"Kohler (K)": UEM.Kohler, "Muggianu (M)": UEM.Muggianu, "Toop-Kohler (T-K)": UEM.Toop_Kohler,
		             "GSM/Chou": UEM.GSM, "UEM1": UEM.UEM1, "UEM2_N": UEM.UEM2_N}
		return model_map.get(model_text, UEM.UEM1), model_text
	
	def prepare_calculation_details (self, composition, temperature, phase_state, order_degree, model_name,
	                                 sub_binaries):
		details = f"计算参数:\n"
		details += f"  温度: {temperature} K\n"
		details += f"  相态: {'固态' if phase_state == 'S' else '液态'}\n"
		details += f"  类型: {order_degree}\n"
		details += f"  外推模型: {model_name}\n\n"
		details += f"合金组成:\n"
		for element, fraction in composition.items():
			details += f"  {element}: {fraction:.4f}\n"
		details += f"\n子二元系:\n"
		for i, binary in enumerate(sub_binaries):
			details += f"  {i + 1}. {binary.A.symbol}-{binary.B.symbol}: {binary.xA:.4f}/{binary.xB:.4f}\n"
		return details
	
	def calculate (self):
		composition = self.composition_table.get_composition()
		if len(composition) < 2:
			QMessageBox.warning(self, "Insufficient Elements", "Please add at least two elements.")
			return
		
		temperature = self.temp_input.value()
		phase_state = "S" if self.phase_combo.currentText().startswith("Solid") else "L"
		order_text = self.order_combo.currentText()
		if order_text.startswith("Solid Solution"):
			order_degree = "SS"
		elif order_text.startswith("Amorphous"):
			order_degree = "AMP"
		else:
			order_degree = "IM"
		
		model_function, model_name = self.get_model_function()
		
		UEM.print_Contri_Coeff(composition, temperature, phase_state, order_degree, model_function, [model_name])
		
		try:
			enthalpy = UEM.get_mixingEnthalpy_byMiedema(composition, temperature, phase_state, order_degree,
			                                            model_function)
			gibbs = UEM.get_Gibbs_byMiedema(composition, temperature, phase_state, order_degree, model_function)
			entropy = (enthalpy - gibbs) * 1000 / temperature  # J/(mol·K)
			
			sub_binaries = UEM._get_subBinary_composition(composition, temperature, phase_state, order_degree,
			                                              model_function)
			details = self.prepare_calculation_details(composition, temperature, phase_state, order_degree, model_name,
			                                           sub_binaries)
			
			self.results_widget.set_results(enthalpy, gibbs, entropy, composition, details, sub_binaries)
		
		except Exception as e:
			error_message = f"Error during calculation: {str(e)}\n\n{traceback.format_exc()}"
			QMessageBox.critical(self, "Calculation Error", error_message)