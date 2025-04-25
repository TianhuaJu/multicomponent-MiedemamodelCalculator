import os
import sys
import traceback
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QRegExpValidator, QFont
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, QTableWidget,
                             QTableWidgetItem, QMessageBox, QGroupBox, QFormLayout,
                             QTabWidget, QTextEdit, QFileDialog, QDoubleSpinBox,
                             QCheckBox, QSplitter, QGridLayout, QProgressDialog)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import BinarySys as BinaryModel
import UnifiedExtrapolationModel as UEM

# Define the contribution model function type
ContributionModelFunc = Callable[[str, str, str, float, str, str], float]


# 添加这段获取正确路径的代码
def resource_path (relative_path):
	"""获取资源的绝对路径"""
	if hasattr(sys, '_MEIPASS'):
		# PyInstaller 创建临时文件夹并将路径存储在 _MEIPASS 中
		base_path = sys._MEIPASS
	else:
		base_path = os.path.abspath(".")
	return os.path.join(base_path, relative_path)


class PeriodicTableWidget(QWidget):
	"""Widget to display a periodic table for element selection"""
	
	def __init__ (self, parent=None, main_window=None):
		super().__init__(parent)
		self.main_window = main_window  # Store reference to main window
		self.selected_elements = set()  # Track selected elements
		self.element_buttons = {}  # Store references to element buttons
		self.init_ui()
	
	def init_ui (self):
		"""Initialize the UI components"""
		layout = QVBoxLayout()
		
		# Create periodic table layout
		self.create_periodic_table()
		
		title_label = QLabel("Click an element to add it to your composition, click again to remove")
		title_label.setFont(QFont("Arial", 11))
		layout.addWidget(title_label)
		layout.addWidget(self.table_widget)
		
		self.setLayout(layout)
	
	def generate_button_style (self, bg_color, border_color, selected=False):
		"""Generate button style with hover and pressed effects"""
		if selected:
			# Style for selected buttons - darker background with bold border
			return f"""
                background-color: {border_color};
                color: white;
                font-weight: bold;
                border: 2px solid #000000;
            """
		else:
			# Regular style with hover and pressed effects
			return f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: #000000;
                    font-weight: bold;
                    border: 1px solid {border_color};
                }}
                QPushButton:hover {{
                    background-color: {border_color};
                    color: #FFFFFF;
                }}
                QPushButton:pressed {{
                    background-color: #555555;
                    color: #FFFFFF;
                    border: 2px solid #000000;
                }}
            """
	
	def update_button_state (self, element, is_selected):
		"""Update the visual state of a button based on selection state"""
		if element not in self.element_buttons:
			return
		
		button = self.element_buttons[element]
		
		# Determine color scheme based on element type
		if element in ["H", "N", "O", "P", "S"]:
			# Non-metals
			bg_color = "#FF9999"
			border_color = "#CC6666"
		elif element in ["B", "Si", "Ge", "As", "Sb", "Te", "Po"]:
			# Metalloids
			bg_color = "#99CCFF"
			border_color = "#6699CC"
		elif element in ["Li", "Na", "K", "Rb", "Cs", "Fr", "Be", "Mg", "Ca", "Sr", "Ba", "Ra"]:
			# Alkali and Alkaline Earth Metals
			bg_color = "#99FF99"
			border_color = "#66CC66"
		elif element in ["Al", "Ga", "In", "Sn", "Tl", "Pb", "Bi", "Nh", "Fl", "Mc"]:
			# Post-transition metals
			bg_color = "#FFFF99"
			border_color = "#CCCC66"
		else:
			# Transition metals
			bg_color = "#CC99FF"
			border_color = "#9966CC"
		
		button.setStyleSheet(self.generate_button_style(bg_color, border_color, is_selected))
	
	def create_periodic_table (self):
		"""Create a periodic table button grid"""
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
		
		# Define lists of inactive elements
		rare_gases = ["He", "Ne", "Ar", "Kr", "Xe", "Rn", "Og"]
		halogens = ["F", "Cl", "Br", "I", "At", "Ts"]
		other_inactive = ["Lv", "Fr", "Ra", "Ac", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl",
		                  "Mc"]
		rare_earth_inactive = ["Pa", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"]
		# Combine all inactive elements
		inactive_elements = rare_gases + halogens + other_inactive + rare_earth_inactive
		
		# Create a widget to hold the table
		self.table_widget = QWidget()
		grid_layout = QVBoxLayout()
		
		# Create row layouts for each periodic table row
		for row_idx, row in enumerate(elements):
			row_layout = QHBoxLayout()
			
			for col_idx, element in enumerate(row):
				if element:
					# Check if element should be inactive
					if element in inactive_elements:
						# Create disabled button for inactive elements
						button = QPushButton(element)
						button.setFixedSize(40, 40)
						button.setStyleSheet("""
                            background-color: #CCCCCC;
                            color: #666666;
                            font-weight: bold;
                            border: 1px solid #999999;
                        """)
						button.setEnabled(False)  # Disable the button
					else:
						# Create normal button for active elements
						button: QPushButton | QPushButton = QPushButton(element)
						button.setFixedSize(40, 40)
						button.setFont(QFont("Arial", 10, QFont.Bold))
						
						# Store button reference
						self.element_buttons[element] = button
						
						# Connect to toggle function
						button.clicked.connect(lambda checked, elem=element: self.toggle_element(elem))
						
						# Set initial style
						self.update_button_state(element, False)
				
				else:
					# Empty space in the table
					button = QLabel("")
					button.setFixedSize(40, 40)
				
				row_layout.addWidget(button)
			
			# Add spacers to align rows properly
			row_layout.addStretch()
			grid_layout.addLayout(row_layout)
		
		# Add a stretch at the end
		grid_layout.addStretch()
		self.table_widget.setLayout(grid_layout)
		
		# Add a legend to explain the colors
		legend_layout = QHBoxLayout()
		
		legends = [
			("非金属", "#FF9999"),
			("类金属", "#99CCFF"),
			("碱金属/碱土金属", "#99FF99"),
			("后过渡金属", "#FFFF99"),
			("过渡金属", "#CC99FF"),
			("不可用元素", "#CCCCCC")
		]
		
		for text, color in legends:
			legend_item = QWidget()
			item_layout = QHBoxLayout()
			
			color_box = QLabel()
			color_box.setFixedSize(15, 15)
			color_box.setStyleSheet(f"background-color: {color}; border: 1px solid #999999;")
			
			label = QLabel(text)
			label.setFont(QFont("Arial", 9))
			
			item_layout.addWidget(color_box)
			item_layout.addWidget(label)
			item_layout.setContentsMargins(2, 0, 10, 0)
			
			legend_item.setLayout(item_layout)
			legend_layout.addWidget(legend_item)
		
		# Add selection indicator to legend
		selected_item = QWidget()
		selected_layout = QHBoxLayout()
		
		selected_box = QLabel()
		selected_box.setFixedSize(15, 15)
		selected_box.setStyleSheet("background-color: #666666; border: 2px solid #000000;")
		
		selected_label = QLabel("已选中")
		selected_label.setFont(QFont("Arial", 9))
		
		selected_layout.addWidget(selected_box)
		selected_layout.addWidget(selected_label)
		selected_layout.setContentsMargins(2, 0, 10, 0)
		
		selected_item.setLayout(selected_layout)
		legend_layout.addWidget(selected_item)
		
		legend_layout.addStretch()
		grid_layout.addLayout(legend_layout)
	
	def toggle_element (self, element):
		"""Toggle an element's selection state"""
		if element in self.selected_elements:
			# Element is already selected, remove it
			self.selected_elements.remove(element)
			self.update_button_state(element, False)
			
			# Remove from composition
			if self.main_window:
				self.main_window.remove_element(element)
		else:
			# Element is not selected, add it
			self.selected_elements.add(element)
			self.update_button_state(element, True)
			
			# Add to composition
			if self.main_window:
				self.main_window.add_element(element)
	
	def on_element_clicked (self, element):
		"""Legacy method - not used anymore but kept for compatibility"""
		pass


class CompositionTableWidget(QWidget):
	"""Widget to manage element compositions"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.init_ui()
		self.composition = {}  # Dictionary to store element:composition pairs
	
	def init_ui (self):
		"""Initialize the UI components"""
		layout = QVBoxLayout()
		
		# Create table for compositions
		self.table = QTableWidget(0, 3)
		self.table.setHorizontalHeaderLabels(["Element", "Composition", "Actions"])
		self.table.horizontalHeader().setStretchLastSection(True)
		
		# Button to manually add element
		add_layout = QHBoxLayout()
		self.element_input = QLineEdit()
		self.element_input.setPlaceholderText("Element symbol")
		self.element_input.setMaxLength(2)
		
		# Add validator for element symbol (1-2 alphabetic characters)
		regex = QRegExp("[A-Za-z]{1,2}")
		validator = QRegExpValidator(regex)
		self.element_input.setValidator(validator)
		
		self.comp_input = QDoubleSpinBox()
		self.comp_input.setRange(0.01, 100.0)
		self.comp_input.setValue(1.0)
		self.comp_input.setSingleStep(0.1)
		
		add_button = QPushButton("Add")
		add_button.clicked.connect(self.add_element_from_input)
		
		add_layout.addWidget(self.element_input)
		add_layout.addWidget(self.comp_input)
		add_layout.addWidget(add_button)
		
		layout.addWidget(QLabel("Composition Table:"))
		layout.addWidget(self.table)
		layout.addLayout(add_layout)
		
		# Actions layout
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
		"""Add an element to the composition table"""
		# Check if element already exists
		if element in self.composition:
			QMessageBox.warning(self, "Element Exists",
			                    f"Element {element} already exists in the composition. Edit its value instead.")
			return
		
		try:
			# Try to create an Element object to validate
			BinaryModel.Element(element)
			
			# Add to composition dictionary
			self.composition[element] = float(composition)
			
			# Update table
			self.update_table()
		
		except Exception as e:
			QMessageBox.critical(self, "Invalid Element",
			                     f"Error adding element {element}: {str(e)}")
	
	def add_element_from_input (self):
		"""Add element from the input fields"""
		element = self.element_input.text().strip().capitalize()
		composition = self.comp_input.value()
		
		if not element:
			return
		
		self.add_element(element, composition)
		
		# Clear input fields
		self.element_input.clear()
		self.comp_input.setValue(1.0)
	
	def update_table (self):
		"""Update the composition table from the dictionary"""
		self.table.setRowCount(0)
		
		for element, composition in self.composition.items():
			row = self.table.rowCount()
			self.table.insertRow(row)
			
			# Add element
			elem_item = QTableWidgetItem(element)
			elem_item.setFlags(elem_item.flags() & ~Qt.ItemIsEditable)
			self.table.setItem(row, 0, elem_item)
			
			# Add composition
			comp_item = QTableWidgetItem(str(composition))
			self.table.setItem(row, 1, comp_item)
			
			# Add delete button
			delete_button = QPushButton("Delete")
			delete_button.clicked.connect(lambda checked, elem=element: self.remove_element(elem))
			self.table.setCellWidget(row, 2, delete_button)
	
	def remove_element (self, element):
		"""Remove an element from the composition"""
		if element in self.composition:
			del self.composition[element]
			self.update_table()
	
	def normalize_composition (self):
		"""Normalize the composition to sum to 1.0"""
		if not self.composition:
			return
		
		total = sum(self.composition.values())
		if total <= 0:
			return
		
		for element in self.composition:
			self.composition[element] /= total
		
		self.update_table()
	
	def clear_composition (self):
		"""Clear all elements from the composition"""
		self.composition.clear()
		self.table.setRowCount(0)
	
	def get_composition (self):
		"""Get the current composition as a dictionary"""
		return self.composition.copy()


class ResultsWidget(QWidget):
	"""Widget to display calculation results"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.calculation_history = []  # Store history of calculations
		self.init_ui()
	
	def init_ui (self):
		"""Initialize the UI components"""
		layout = QVBoxLayout()
		
		# Results section with larger input fields
		results_group = QGroupBox("Calculation Results")
		results_group.setFont(QFont("Arial", 12, QFont.Bold))
		results_layout = QFormLayout()
		results_layout.setSpacing(15)  # Increase spacing between rows
		results_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
		
		# Create label with larger font
		enthalpy_label = QLabel("Mixing Enthalpy (kJ/mol):")
		enthalpy_label.setFont(QFont("Arial", 12))
		
		self.enthalpy_result = QLineEdit()
		self.enthalpy_result.setReadOnly(True)
		self.enthalpy_result.setMinimumHeight(40)  # Increased height
		self.enthalpy_result.setMinimumWidth(200)  # Ensure width is sufficient
		self.enthalpy_result.setFont(QFont("Arial", 12))  # Larger font
		results_layout.addRow(enthalpy_label, self.enthalpy_result)
		
		gibbs_label = QLabel("Gibbs Energy (kJ/mol):")
		gibbs_label.setFont(QFont("Arial", 12))
		
		self.gibbs_result = QLineEdit()
		self.gibbs_result.setReadOnly(True)
		self.gibbs_result.setMinimumHeight(40)  # Increased height
		self.gibbs_result.setMinimumWidth(200)  # Ensure width is sufficient
		self.gibbs_result.setFont(QFont("Arial", 12))  # Larger font
		results_layout.addRow(gibbs_label, self.gibbs_result)
		
		entropy_label = QLabel("Mixing Entropy (J/mol·K):")
		entropy_label.setFont(QFont("Arial", 12))
		
		self.entropy_result = QLineEdit()
		self.entropy_result.setReadOnly(True)
		self.entropy_result.setMinimumHeight(40)  # Increased height
		self.entropy_result.setMinimumWidth(200)  # Ensure width is sufficient
		self.entropy_result.setFont(QFont("Arial", 12))  # Larger font
		results_layout.addRow(entropy_label, self.entropy_result)
		
		results_group.setLayout(results_layout)
		
		# Details section with history
		details_group = QGroupBox("Calculation History")
		details_group.setFont(QFont("Arial", 12, QFont.Bold))
		details_layout = QVBoxLayout()
		
		self.details_text = QTextEdit()
		self.details_text.setReadOnly(True)
		self.details_text.setMinimumHeight(300)  # Taller to show more history
		self.details_text.setFont(QFont("Consolas", 11))  # Monospaced font for better readability
		self.details_text.setStyleSheet("background-color: #FAFAFA;")  # Light background for better readability
		details_layout.addWidget(self.details_text)
		
		details_group.setLayout(details_layout)
		
		# Add sections to main layout with spacing
		layout.addWidget(results_group)
		layout.addSpacing(15)  # Add space between groups
		layout.addWidget(details_group)
		layout.addSpacing(15)  # Add space before button
		
		# Export button
		export_button = QPushButton("Export Results")
		export_button.setMinimumHeight(40)  # Taller button
		export_button.setFont(QFont("Arial", 12))  # Larger font
		export_button.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
        """)
		export_button.clicked.connect(self.export_results)
		layout.addWidget(export_button)
		
		self.setLayout(layout)
	
	def set_results (self, enthalpy, gibbs, entropy, composition, details, sub_binaries=None):
		"""Set the calculation results and append to history"""
		# Set current results
		self.enthalpy_result.setText(f"{enthalpy:.4f}")
		self.gibbs_result.setText(f"{gibbs:.4f}")
		self.entropy_result.setText(f"{entropy:.4f}")
		
		# Format timestamp for history entry
		from datetime import datetime
		timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		
		# Create history entry with results section
		history_entry = f"\n{'=' * 80}\n"
		history_entry += f"CALCULATION AT {timestamp}\n"
		history_entry += f"{'=' * 80}\n"
		
		# Add results section to history
		history_entry += f"RESULTS:\n"
		history_entry += f"  Mixing Enthalpy (kJ/mol):     {enthalpy:.4f}\n"
		history_entry += f"  Gibbs Energy (kJ/mol): {gibbs:.4f}\n"
		history_entry += f"  Mixing Entropy (J/mol·K):     {entropy:.4f}\n"
		history_entry += f"{'-' * 80}\n\n"
		
		# Add calculation details
		history_entry += f"DETAILS:\n"
		history_entry += details
		history_entry += f"\n{'-' * 80}\n"
		
		# Add to history and update display
		self.calculation_history.append(history_entry)
		self.update_history_display()
	
	def update_history_display (self):
		"""Update the history display with all stored calculations"""
		# Display history in reverse order (newest first)
		full_history = "".join(reversed(self.calculation_history))
		self.details_text.setPlainText(full_history)
	
	def export_results (self):
		"""Export results to a file"""
		filename, _ = QFileDialog.getSaveFileName(self, "Export Results", "", "Text Files (*.txt);;All Files (*)")
		
		if filename:
			try:
				with open(filename, 'w') as f:
					f.write(f"Mixing Enthalpy (kJ/mol): {self.enthalpy_result.text()}\n")
					f.write(f"Energy (kJ/mol): {self.gibbs_result.text()}\n")
					f.write(f"Mixing Entropy (J/mol·K): {self.entropy_result.text()}\n\n")
					f.write("Calculation History:\n")
					f.write(self.details_text.toPlainText())
				
				QMessageBox.information(self, "Export Successful",
				                        f"Results successfully exported to {filename}")
			except Exception as e:
				QMessageBox.critical(self, "Export Failed",
				                     f"Failed to export results: {str(e)}")


class CompositionVariationWidget(QWidget):
	"""用于比较不同外推模型的热力学性质变化窗口"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.parent_window = parent
		
		# 配置matplotlib以支持中文显示
		plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
		plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
		
		# 存储计算结果的数据结构
		self.calculation_results = {
			"enthalpy": {},  # 混合焓数据
			"gibbs": {},  # 吉布斯自由能数据
			"entropy": {}  # 混合熵数据
		}
		
		# 跟踪当前的计算参数，用于导出
		self.current_parameters = {
			"base_matrix": "",
			"add_element": "",
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
		
		self.matrix_input = QLineEdit()
		self.matrix_input.setPlaceholderText("e.g.: Fe0.7Ni0.3")
		self.matrix_input.setMinimumHeight(30)
		matrix_layout.addRow("基体合金组成:", self.matrix_input)
		
		# 添加元素选择
		self.add_element_combo = QComboBox()
		self.add_element_combo.setMinimumHeight(30)
		# 预先填充一些常见元素
		common_elements = ["Al", "Cr", "Mn", "Si", "Co", "Cu", "Ni", "Ti", "V", "Zn", "Mo", "W", "Nb", "Ta", "Rh", "Pd",
		                   "Pt", "Au"]
		self.add_element_combo.addItems(common_elements)
		self.add_element_combo.setEditable(True)
		matrix_layout.addRow("添加元素:", self.add_element_combo)
		
		matrix_group.setLayout(matrix_layout)
		left_layout.addWidget(matrix_group)
		
		# 计算参数区域的改进布局代码
		params_group = QGroupBox("计算参数")
		params_layout = QFormLayout()
		params_layout.setSpacing(12)  # 增加行间距
		params_layout.setContentsMargins(10, 25, 10, 15)  # 增加内边距
		params_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)  # 允许字段增长
		
		# 组成范围 - Changed from horizontal to grid layout for better spacing
		range_widget = QWidget()
		range_layout = QGridLayout()  # Changed from QHBoxLayout to QGridLayout
		range_layout.setContentsMargins(0, 0, 0, 0)
		range_layout.setSpacing(10)
		
		# Create labels with increased width
		min_label = QLabel("min:")
		min_label.setMinimumWidth(40)  # Increased from 30
		max_label = QLabel("max:")
		max_label.setMinimumWidth(40)  # Increased from 30
		step_label = QLabel("step:")
		step_label.setMinimumWidth(40)  # Increased from 30
		
		# Create spinboxes with increased width
		self.min_comp = QDoubleSpinBox()
		self.min_comp.setRange(0.0, 1.0)
		self.min_comp.setValue(0.0)
		self.min_comp.setSingleStep(0.05)
		self.min_comp.setMinimumHeight(30)
		self.min_comp.setMinimumWidth(80)  # Increased from 60
		
		self.max_comp = QDoubleSpinBox()
		self.max_comp.setRange(0.0, 1.0)
		self.max_comp.setValue(1.0)
		self.max_comp.setSingleStep(0.05)
		self.max_comp.setMinimumHeight(30)
		self.max_comp.setMinimumWidth(80)  # Increased from 60
		
		self.step_comp = QDoubleSpinBox()
		self.step_comp.setRange(0.01, 0.5)
		self.step_comp.setValue(0.05)
		self.step_comp.setSingleStep(0.01)
		self.step_comp.setMinimumHeight(30)
		self.step_comp.setMinimumWidth(80)  # Increased from 60
		
		# Add widgets to grid layout - 2 controls per row instead of all in one row
		range_layout.addWidget(min_label, 0, 0)
		range_layout.addWidget(self.min_comp, 0, 1)
		range_layout.addWidget(max_label, 0, 2)
		range_layout.addWidget(self.max_comp, 0, 3)
		range_layout.addWidget(step_label, 1, 0)  # Start of second row
		range_layout.addWidget(self.step_comp, 1, 1)
		
		range_widget.setLayout(range_layout)
		params_layout.addRow("组成范围:", range_widget)
		
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
			"混合焓 (ΔHₘᵢₓ, kJ/mol)",
			"吉布斯自由能 (ΔG, kJ/mol)",
			"混合熵 (ΔSₘᵢₓ, J/mol·K)"
		])
		self.property_combo.setMinimumHeight(30)
		
		# 当热力学性质选择改变时更新图表
		self.property_combo.currentIndexChanged.connect(self.update_plot)
		
		params_layout.addRow("热力学性质:", self.property_combo)
		
		params_group.setLayout(params_layout)
		left_layout.addWidget(params_group)
		
		# 模型选择
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
				"font-size: 12pt; font-weight: bold; background-color: #4A86E8; color: white; border: none; border-radius: 4px;")
		calculate_button.clicked.connect(self.calculate_all_properties)
		buttons_layout.addWidget(calculate_button)
		
		# 导出按钮
		export_button = QPushButton("导出数据")
		export_button.setMinimumHeight(40)
		export_button.setStyleSheet(
				"font-size: 12pt; font-weight: bold; background-color: #28a745; color: white; border: none; border-radius: 4px;")
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
		
		# 应用样式表
		self.apply_stylesheet()
	
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
	
	def parse_matrix_composition (self, matrix_input):
		"""解析基体合金输入字符串，例如Fe0.7Ni0.3"""
		import re
		composition = {}
		# 正则表达式匹配元素和其对应的比例
		pattern = r'([A-Z][a-z]*)(\d*\.?\d*)'
		
		matches = re.findall(pattern, matrix_input)
		
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
		"""计算所有热力学性质"""
		# 获取基本参数
		temperature = self.temp_input.value()
		phase_state = "S" if self.phase_combo.currentText().startswith("固态") else "L"
		
		# 获取有序度
		order_text = self.order_combo.currentText()
		if order_text.startswith("固溶体"):
			order_degree = "SS"
		elif order_text.startswith("非晶态"):
			order_degree = "AMP"
		else:
			order_degree = "IM"
		
		# 解析基体合金组成
		matrix_input = self.matrix_input.text().strip()
		if not matrix_input:
			QMessageBox.warning(self, "输入错误", "请输入基体合金组成")
			return
		
		try:
			base_matrix = self.parse_matrix_composition(matrix_input)
			if not base_matrix:
				QMessageBox.warning(self, "解析错误", "无法解析基体合金组成，请使用格式如Fe0.7Ni0.3")
				return
		except Exception as e:
			QMessageBox.critical(self, "解析错误", f"解析基体合金组成时出错: {str(e)}")
			return
		
		# 获取添加元素
		add_element = self.add_element_combo.currentText().strip()
		if not add_element:
			QMessageBox.warning(self, "输入错误", "请选择或输入添加元素")
			return
		
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
			"add_element": add_element,
			"temperature": temperature,
			"phase_state": phase_state,
			"order_degree": order_degree,
			"comp_range": comp_range.tolist()
		}
		
		# 清空之前的计算结果
		self.calculation_results = {
			"enthalpy": {},  # 混合焓数据
			"gibbs": {},  # 吉布斯自由能数据
			"entropy": {}  # 混合熵数据
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
		progress = QProgressDialog("计算中...", "取消", 0, len(selected_models) * 3, self)
		progress.setWindowTitle("计算进度")
		progress.setWindowModality(Qt.WindowModal)
		progress.setMinimumDuration(0)
		progress.setValue(0)
		
		# 计算每个模型的热力学性质
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
				for prop in ["enthalpy", "gibbs", "entropy"]:
					self.calculation_results[prop][model_key] = {"compositions": [], "values": []}
				
				# 计算混合焓
				progress.setLabelText(f"计算 {model_key} 模型的混合焓...")
				valid_compositions = []
				valid_values = []
				
				for x in comp_range:
					if progress.wasCanceled():
						break
					
					# 创建新的组成字典 (AxBy)_{1-x}C_{x}
					new_comp = {}
					
					# 设置添加元素的组成
					new_comp[add_element] = x
					
					# 设置基体元素的组成，保持它们之间的相对比例
					matrix_fraction = 1.0 - x  # 基体所占的总分数
					for elem, ratio in base_matrix.items():
						new_comp[elem] = ratio * matrix_fraction
					# 验证组成有效性
					if any(v < 0 for v in new_comp.values()) or abs(sum(new_comp.values()) - 1.0) > 1e-10:
						continue  # 跳过无效组成
					
					# 计算混合焓
					try:
						value = UEM.get_mixingEnthalpy_byMiedema(
								new_comp, temperature, phase_state, order_degree, model_func)
						
						valid_compositions.append(x)
						valid_values.append(value)
					except Exception as e:
						print(f"计算组成 {new_comp} 的混合焓时出错: {str(e)}")
						continue
				
				# 存储有效的混合焓结果
				if valid_compositions:
					self.calculation_results["enthalpy"][model_key]["compositions"] = np.array(valid_compositions)
					self.calculation_results["enthalpy"][model_key]["values"] = np.array(valid_values)
				
				progress_count += 1
				progress.setValue(progress_count)
				
				# 计算吉布斯自由能
				progress.setLabelText(f"计算 {model_key} 模型的吉布斯自由能...")
				valid_compositions = []
				valid_values = []
				
				for x in comp_range:
					if progress.wasCanceled():
						break
					
					# 创建新的组成字典
					new_comp = {}
					new_comp[add_element] = x
					matrix_fraction = 1.0 - x
					for elem, ratio in base_matrix.items():
						new_comp[elem] = ratio * matrix_fraction
					
					# 验证组成有效性
					if any(v < 0 for v in new_comp.values()) or abs(sum(new_comp.values()) - 1.0) > 1e-10:
						continue
					
					# 计吉布斯自由能
					try:
						value = UEM.get_Gibbs_byMiedema(new_comp, temperature, phase_state, order_degree, model_func)
						
						valid_compositions.append(x)
						valid_values.append(value)
					except Exception as e:
						print(f"计算组成 {new_comp} 的吉布斯自由能时出错: {str(e)}")
						continue
				
				# 存储有效的吉布斯自由能结果
				if valid_compositions:
					self.calculation_results["gibbs"][model_key]["compositions"] = np.array(valid_compositions)
					self.calculation_results["gibbs"][model_key]["values"] = np.array(valid_values)
				
				progress_count += 1
				progress.setValue(progress_count)
				
				# 计算混合熵 (使用ΔH和ΔG计算得到)
				progress.setLabelText(f"计算 {model_key} 模型的混合熵...")
				valid_compositions = []
				valid_values = []
				
				# 获取已计算的混合焓和吉布斯自由能
				enthalpy_data = self.calculation_results["enthalpy"][model_key]
				gibbs_data = self.calculation_results["gibbs"][model_key]
				
				# 找到两者共有的组成
				if len(enthalpy_data["compositions"]) > 0 and len(gibbs_data["compositions"]) > 0:
					common_compositions = np.intersect1d(enthalpy_data["compositions"], gibbs_data["compositions"])
					
					for x in common_compositions:
						h_idx = np.where(enthalpy_data["compositions"] == x)[0][0]
						g_idx = np.where(gibbs_data["compositions"] == x)[0][0]
						
						enthalpy = enthalpy_data["values"][h_idx]
						gibbs = gibbs_data["values"][g_idx]
						
						# 计算熵 (ΔS = (ΔH - ΔG)/T)
						entropy = (enthalpy - gibbs) * 1000 / temperature  # J/(mol·K)
						
						valid_compositions.append(x)
						valid_values.append(entropy)
				
				# 存储有效的混合熵结果
				if valid_compositions:
					self.calculation_results["entropy"][model_key]["compositions"] = np.array(valid_compositions)
					self.calculation_results["entropy"][model_key]["values"] = np.array(valid_values)
				
				progress_count += 1
				progress.setValue(progress_count)
			
			# 关闭进度对话框
			progress.close()
			
			# 检查是否有有效数据
			has_valid_data = False
			for prop in self.calculation_results:
				if any(len(self.calculation_results[prop][model_key]["compositions"]) > 0 for model_key in
				       self.calculation_results[prop]):
					has_valid_data = True
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
			QMessageBox.information(self, "计算完成",
			                        "所有热力学性质计算完成，您可以通过选择不同的热力学性质来查看图表，也可以导出数据。")
		
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
		property_types = ["enthalpy", "gibbs", "entropy"]
		if property_index >= len(property_types):
			return
		
		selected_property = property_types[property_index]
		
		# 获取该性质的计算结果
		model_results = self.calculation_results[selected_property]
		
		# 没有数据则返回
		if not model_results:
			return
		
		# 绘制图表
		self.plot_model_comparison(model_results, self.current_parameters["add_element"],
		                           selected_property, self.current_parameters["base_matrix"])
	
	def plot_model_comparison (self, model_results, add_element, property_type, matrix_input):
		"""绘制不同模型的对比图"""
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
			if "compositions" not in data or len(data["compositions"]) == 0:
				continue
			
			color_idx = i % len(colors)
			marker_idx = i % len(markers)
			
			# 减少数据点数量，提高清晰度
			compositions = data["compositions"]
			values = data["values"]
			
			if len(compositions) > 20:
				skip = len(compositions) // 20
				plot_comp = compositions[::skip]
				plot_values = values[::skip]
			else:
				plot_comp = compositions
				plot_values = values
			
			line, = ax.plot(compositions, values,
			                color=colors[color_idx],
			                marker=markers[marker_idx],
			                linewidth=2,
			                markersize=6,
			                label=self.model_checkboxes[model_key].text())
			
			plots.append(line)
			labels.append(self.model_checkboxes[model_key].text())
		
		# 设置标题和标签
		if property_type == "enthalpy":
			y_label = r"ΔH$_{mix}$ (kJ/mol)"
			title_property = "Mixing Enthalpy"
		elif property_type == "gibbs":
			y_label = r"$ΔG$ (kJ/mol)"
			title_property = "Gibbs Energy"
		else:  # entropy
			y_label = r"$ΔS_{mix}$ (J/mol·K)"
			title_property = "Mixing Entropy"
		
		# 设置X轴标签，避免使用中文
		ax.set_xlabel(f"{add_element} Mole Fraction (x)", fontsize=12)
		ax.set_ylabel(y_label, fontsize=12)
		
		# 构建基体描述，避免中文
		temperature = self.current_parameters["temperature"]
		phase_dict = {"S": "Solid", "L": "Liquid"}
		phase_text = phase_dict.get(self.current_parameters["phase_state"], "Solid")
		
		order_dict = {"SS": "SS", "AMP": "AMP", "IM": "IM"}
		order_text = order_dict.get(self.current_parameters["order_degree"], "IM")
		
		# 构建标题，使用LaTeX标记
		title = f"({matrix_input})$_{{1-x}}$({add_element})$_{{x}}$ Alloy {title_property}\n" \
		        f"T: {temperature}K, Phase: {phase_text}, Type: {order_text}"
		ax.set_title(title, fontsize=13, pad=10)
		
		# 添加网格
		ax.grid(True, linestyle='--', alpha=0.7)
		
		# 设置坐标轴刻度字体大小
		ax.tick_params(axis='both', which='major', labelsize=10)
		
		# 添加图例，放在图表外部以避免遮挡数据
		if plots:
			self.figure.legend(plots, labels, loc='upper center', bbox_to_anchor=(0.5, 0.98),
			                   ncol=min(3, len(plots)), fontsize=10)
		
		# 调整布局
		self.figure.tight_layout(rect=[0, 0, 1, 0.93])
		
		# 绘制画布
		self.canvas.draw()
	
	def export_data (self):
		"""导出计算数据到CSV文件"""
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
		"""将数据导出为CSV格式"""
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
		
		# 准备数据
		with open(file_path, 'w', newline='') as csvfile:
			writer = csv.writer(csvfile)
			
			# 写入标题行 - 参数信息
			writer.writerow(['计算参数'])
			writer.writerow(['基体合金', self.current_parameters["base_matrix"]])
			writer.writerow(['添加元素', self.current_parameters["add_element"]])
			writer.writerow(['温度', f"{self.current_parameters['temperature']} K"])
			writer.writerow(['相态', "固态" if self.current_parameters["phase_state"] == "S" else "液态"])
			writer.writerow(['类型', self.current_parameters["order_degree"]])
			writer.writerow([])  # 空行
			
			# 写入标题行 - 数据部分
			header = ['组成']
			for model in all_models:
				header.extend([
					f'{model}-混合焓 (kJ/mol)',
					f'{model}-吉布斯自由能 (kJ/mol)',
					f'{model}-混合熵 (J/mol·K)'
				])
			writer.writerow(header)
			
			# 写入数据行
			for comp in all_compositions:
				row = [comp]
				for model in all_models:
					# 混合焓
					enthalpy_value = ''
					if model in self.calculation_results["enthalpy"]:
						data = self.calculation_results["enthalpy"][model]
						if "compositions" in data and len(data["compositions"]) > 0:
							idx = np.where(data["compositions"] == comp)[0]
							if idx.size > 0:
								enthalpy_value = f"{data['values'][idx[0]]:.6f}"
					row.append(enthalpy_value)
					
					# 吉布斯自由能
					gibbs_value = ''
					if model in self.calculation_results["gibbs"]:
						data = self.calculation_results["gibbs"][model]
						if "compositions" in data and len(data["compositions"]) > 0:
							idx = np.where(data["compositions"] == comp)[0]
							if idx.size > 0:
								gibbs_value = f"{data['values'][idx[0]]:.6f}"
					row.append(gibbs_value)
					
					# 混合熵
					entropy_value = ''
					if model in self.calculation_results["entropy"]:
						data = self.calculation_results["entropy"][model]
						if "compositions" in data and len(data["compositions"]) > 0:
							idx = np.where(data["compositions"] == comp)[0]
							if idx.size > 0:
								entropy_value = f"{data['values'][idx[0]]:.6f}"
					row.append(entropy_value)
				
				writer.writerow(row)
	
	def export_to_excel (self, file_path):
		"""将数据导出为Excel格式"""
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
		worksheet.write(2, 0, '添加元素', param_format)
		worksheet.write(2, 1, self.current_parameters["add_element"], param_format)
		worksheet.write(3, 0, '温度', param_format)
		worksheet.write(3, 1, f"{self.current_parameters['temperature']} K", param_format)
		worksheet.write(4, 0, '相态', param_format)
		worksheet.write(4, 1, "固态" if self.current_parameters["phase_state"] == "S" else "液态", param_format)
		worksheet.write(5, 0, '类型', param_format)
		worksheet.write(5, 1, self.current_parameters["order_degree"], param_format)
		
		# 写入标题行 - 数据部分
		row = 7
		worksheet.write(row, 0, '组成', header_format)
		col = 1
		for model in all_models:
			worksheet.write(row, col, f'{model}-混合焓 (kJ/mol)', header_format)
			worksheet.write(row, col + 1, f'{model}-吉布斯自由能 (kJ/mol)', header_format)
			worksheet.write(row, col + 2, f'{model}-混合熵 (J/mol·K)', header_format)
			col += 3
		
		# 写入数据行
		row += 1
		for comp in all_compositions:
			worksheet.write(row, 0, comp, data_format)
			col = 1
			for model in all_models:
				# 混合焓
				if model in self.calculation_results["enthalpy"]:
					data = self.calculation_results["enthalpy"][model]
					if "compositions" in data and len(data["compositions"]) > 0:
						idx = np.where(data["compositions"] == comp)[0]
						if idx.size > 0:
							worksheet.write(row, col, data['values'][idx[0]], data_format)
				col += 1
				
				# 吉布斯自由能
				if model in self.calculation_results["gibbs"]:
					data = self.calculation_results["gibbs"][model]
					if "compositions" in data and len(data["compositions"]) > 0:
						idx = np.where(data["compositions"] == comp)[0]
						if idx.size > 0:
							worksheet.write(row, col, data['values'][idx[0]], data_format)
				col += 1
				
				# 混合熵
				if model in self.calculation_results["entropy"]:
					data = self.calculation_results["entropy"][model]
					if "compositions" in data and len(data["compositions"]) > 0:
						idx = np.where(data["compositions"] == comp)[0]
						if idx.size > 0:
							worksheet.write(row, col, data['values'][idx[0]], data_format)
				col += 1
			
			row += 1
		
		# 设置列宽
		worksheet.set_column(0, 0, 10)
		for i in range(1, 3 * len(all_models) + 1):
			worksheet.set_column(i, i, 20)
		
		# 保存并关闭工作簿
		workbook.close()
	
	# 保留兼容性
	def calculate_variation (self):
		"""兼容原有方法，调用新的计算方法"""
		self.calculate_all_properties()


class TemperatureVariationWidget(QWidget):
	"""用于计算固定组成下热力学性质随温度变化的窗口"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.parent_window = parent
		
		# 配置matplotlib以支持中文显示
		plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
		plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
		
		# 存储计算结果的数据结构
		self.calculation_results = {
			"enthalpy": {},  # 混合焓数据
			"gibbs": {},  # 吉布斯自由能数据
			"entropy": {}  # 混合熵数据
		}
		
		# 跟踪当前的计算参数，用于导出
		self.current_parameters = {
			"composition": {},
			"temp_range": [],
			"phase_state": "",
			"order_degree": ""
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
		
		# 创建 Minimum Temperature 输入框
		self.min_temp = QDoubleSpinBox()
		self.min_temp.setRange(300, 5000)  # 设置允许的最小值和最大值
		self.min_temp.setValue(500)  # 设置默认显示的初始值
		self.min_temp.setSingleStep(50)  # 设置每次点击箭头或按上下键时变化的步长
		self.min_temp.setSuffix(" K")  # 在数值后面添加单位后缀 " K"
		self.min_temp.setMinimumHeight(30)  # 设置控件的最小高度
		self.min_temp.setMinimumWidth(90)  # 调整宽度
		
		# 创建 Maximum Temperature 输入框
		self.max_temp = QDoubleSpinBox()
		self.max_temp.setRange(300, 5000)
		self.max_temp.setValue(2000)
		self.max_temp.setSingleStep(50)
		self.max_temp.setSuffix(" K")
		self.max_temp.setMinimumHeight(30)
		self.max_temp.setMinimumWidth(90)  # 调整宽度
		
		# 创建 Step Temperature 输入框
		self.step_temp = QDoubleSpinBox()
		self.step_temp.setRange(10, 500)  # 设置步长的允许范围
		self.step_temp.setValue(100)
		self.step_temp.setSingleStep(10)  # 步长本身也可以调整，这里是调整步长的步长
		self.step_temp.setSuffix(" K")
		self.step_temp.setMinimumHeight(30)
		self.step_temp.setMinimumWidth(90)  # 调整宽度
		# 控制面板布局 - 使用垂直布局以增加高度
		left_panel = QWidget()
		left_layout = QVBoxLayout()
		left_layout.setSpacing(15)
		left_layout.setContentsMargins(10, 10, 10, 10)
		
		# 合金组成输入
		comp_group = QGroupBox("合金组成")
		comp_layout = QVBoxLayout()
		comp_layout.setSpacing(10)
		comp_layout.setContentsMargins(10, 20, 10, 10)
		
		self.comp_input = QLineEdit()
		self.comp_input.setPlaceholderText("例如: Fe0.7Ni0.3")
		self.comp_input.setMinimumHeight(30)
		comp_layout.addWidget(QLabel("合金组成:"))
		comp_layout.addWidget(self.comp_input)
		
		comp_group.setLayout(comp_layout)
		left_layout.addWidget(comp_group)
		
		# 计算参数区域代码修改部分
		params_group = QGroupBox("计算参数")
		params_layout = QFormLayout()
		params_layout.setSpacing(12)  # 增加行间距
		params_layout.setContentsMargins(10, 25, 10, 15)  # 增加内边距
		params_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)  # 允许字段增长
		
		# 使用网格布局代替水平布局，更好地控制空间分配
		temp_grid = QGridLayout()
		temp_grid.setContentsMargins(0, 0, 0, 0)
		temp_grid.setSpacing(10)  # 增加控件间距
		
		# 标签
		min_label = QLabel("min:")
		min_label.setMinimumWidth(30)
		max_label = QLabel("max:")
		max_label.setMinimumWidth(30)
		step_label = QLabel("step:")
		step_label.setMinimumWidth(30)
		
		# 删除双重定义，只保留一处温度控件定义
		self.min_temp = QDoubleSpinBox()
		self.min_temp.setRange(300, 5000)
		self.min_temp.setValue(500)
		self.min_temp.setSingleStep(50)
		self.min_temp.setSuffix(" K")
		self.min_temp.setMinimumHeight(30)
		self.min_temp.setMinimumWidth(100)  # 增加宽度确保数值完全显示
		
		self.max_temp = QDoubleSpinBox()
		self.max_temp.setRange(300, 5000)
		self.max_temp.setValue(2000)
		self.max_temp.setSingleStep(50)
		self.max_temp.setSuffix(" K")
		self.max_temp.setMinimumHeight(30)
		self.max_temp.setMinimumWidth(100)  # 增加宽度确保数值完全显示
		
		self.step_temp = QDoubleSpinBox()
		self.step_temp.setRange(10, 500)
		self.step_temp.setValue(100)
		self.step_temp.setSingleStep(10)
		self.step_temp.setSuffix(" K")
		self.step_temp.setMinimumHeight(30)
		self.step_temp.setMinimumWidth(100)  # 增加宽度确保数值完全显示
		
		# 分两行布局控件，防止水平空间不足
		temp_grid.addWidget(min_label, 0, 0)
		temp_grid.addWidget(self.min_temp, 0, 1)
		temp_grid.addWidget(max_label, 0, 2)
		temp_grid.addWidget(self.max_temp, 0, 3)
		temp_grid.addWidget(step_label, 1, 0)  # 第二行
		temp_grid.addWidget(self.step_temp, 1, 1)
		
		self.min_temp.setDecimals(1)  # 控制显示的小数位数
		self.max_temp.setDecimals(1)
		self.step_temp.setDecimals(1)
		self.min_temp.setSpecialValueText("最小温度")
		self.max_temp.setSpecialValueText("最大温度")
		# 将网格布局添加到参数表单中
		params_layout.addRow("温度范围（K）:", temp_grid)
		
		# 添加相态选择
		self.phase_combo = QComboBox()
		self.phase_combo.addItems(["固态 (S)", "液态 (L)"])
		self.phase_combo.setMinimumHeight(30)
		self.phase_combo.setMinimumWidth(160)
		params_layout.addRow("相态:", self.phase_combo)
		
		# 添加有序度选择
		self.order_combo = QComboBox()
		self.order_combo.addItems(["固溶体 (SS)", "非晶态 (AMP)", "金属间化合物 (IM)"])
		self.order_combo.setMinimumHeight(30)
		params_layout.addRow("类型:", self.order_combo)
		
		# 热力学性质选择
		self.property_combo = QComboBox()
		self.property_combo.addItems([
			"混合焓 (ΔHₘᵢₓ, kJ/mol)",
			"吉布斯自由能 (ΔG, kJ/mol)",
			"混合熵 (ΔSₘᵢₓ, J/mol·K)"
		])
		self.property_combo.setMinimumHeight(30)
		
		# 当热力学性质选择改变时更新图表
		self.property_combo.currentIndexChanged.connect(self.update_plot)
		
		params_layout.addRow("热力学性质:", self.property_combo)
		
		params_group.setLayout(params_layout)
		
		left_layout.addWidget(params_group)
		
		# 模型选择
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
				"font-size: 12pt; font-weight: bold; background-color: #4A86E8; color: white; border: none; border-radius: 4px;")
		calculate_button.clicked.connect(self.calculate_all_properties)
		buttons_layout.addWidget(calculate_button)
		
		# 导出按钮
		export_button = QPushButton("导出数据")
		export_button.setMinimumHeight(40)
		export_button.setStyleSheet(
				"font-size: 12pt; font-weight: bold; background-color: #28a745; color: white; border: none; border-radius: 4px;")
		export_button.clicked.connect(self.export_data)
		buttons_layout.addWidget(export_button)
		
		left_layout.addLayout(buttons_layout)  # 添加按钮布局
		
		# 设置左侧面板
		left_panel.setLayout(left_layout)
		left_panel.setMinimumWidth(480)
		left_panel.setMaximumWidth(500)
		
		# 绘图区域
		right_panel = QWidget()
		right_layout = QVBoxLayout()
		
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
		
		# 应用样式表
		self.apply_stylesheet()
	
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
		"""计算所有热力学性质"""
		# 获取合金组成
		comp_input = self.comp_input.text().strip()
		if not comp_input:
			QMessageBox.warning(self, "输入错误", "请输入合金组成")
			return
		
		try:
			composition = self.parse_composition(comp_input)
			if not composition or len(composition) < 2:
				QMessageBox.warning(self, "解析错误", "无法解析合金组成或元素数量不足，请使用格式如Fe0.7Ni0.3")
				return
		except Exception as e:
			QMessageBox.critical(self, "解析错误", f"解析合金组成时出错: {str(e)}")
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
			"composition": composition,
			"comp_input": comp_input,
			"temp_range": temp_range.tolist(),
			"phase_state": phase_state,
			"order_degree": order_degree
		}
		
		# 清空之前的计算结果
		self.calculation_results = {
			"enthalpy": {},  # 混合焓数据
			"gibbs": {},  # 吉布斯自由能数据
			"entropy": {}  # 混合熵数据
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
		progress = QProgressDialog("计算中...", "取消", 0, len(selected_models) * 3, self)
		progress.setWindowTitle("计算进度")
		progress.setWindowModality(Qt.WindowModal)
		progress.setMinimumDuration(0)
		progress.setValue(0)
		
		# 计算每个模型的热力学性质
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
				for prop in ["enthalpy", "gibbs", "entropy"]:
					self.calculation_results[prop][model_key] = {"temperatures": [], "values": []}
				
				# 计算混合焓
				progress.setLabelText(f"计算 {model_key} 模型的混合焓...")
				valid_temperatures = []
				valid_values = []
				
				for temp in temp_range:
					if progress.wasCanceled():
						break
					
					# 计算混合焓
					try:
						value = UEM.get_mixingEnthalpy_byMiedema(
								composition, temp, phase_state, order_degree, model_func)
						
						valid_temperatures.append(temp)
						valid_values.append(value)
					except Exception as e:
						print(f"计算温度 {temp}K 的混合焓时出错: {str(e)}")
						continue
				
				# 存储有效的混合焓结果
				if valid_temperatures:
					self.calculation_results["enthalpy"][model_key]["temperatures"] = np.array(valid_temperatures)
					self.calculation_results["enthalpy"][model_key]["values"] = np.array(valid_values)
				
				progress_count += 1
				progress.setValue(progress_count)
				
				# 计算吉布斯自由能
				progress.setLabelText(f"计算 {model_key} 模型的吉布斯自由能...")
				valid_temperatures = []
				valid_values = []
				
				for temp in temp_range:
					if progress.wasCanceled():
						break
					
					# 计算吉布斯自由能
					try:
						value = UEM.get_Gibbs_byMiedema(
								composition, temp, phase_state, order_degree, model_func)
						
						valid_temperatures.append(temp)
						valid_values.append(value)
					except Exception as e:
						print(f"计算温度 {temp}K 的吉布斯自由能时出错: {str(e)}")
						continue
				
				# 存储有效的吉布斯自由能结果
				if valid_temperatures:
					self.calculation_results["gibbs"][model_key]["temperatures"] = np.array(valid_temperatures)
					self.calculation_results["gibbs"][model_key]["values"] = np.array(valid_values)
				
				progress_count += 1
				progress.setValue(progress_count)
				
				# 计算混合熵 (使用ΔH和ΔG计算得到)
				progress.setLabelText(f"计算 {model_key} 模型的混合熵...")
				valid_temperatures = []
				valid_values = []
				
				# 获取已计算的混合焓和吉布斯自由能
				enthalpy_data = self.calculation_results["enthalpy"][model_key]
				gibbs_data = self.calculation_results["gibbs"][model_key]
				
				# 找到两者共有的温度点
				if len(enthalpy_data["temperatures"]) > 0 and len(gibbs_data["temperatures"]) > 0:
					common_temps = np.intersect1d(enthalpy_data["temperatures"], gibbs_data["temperatures"])
					
					for temp in common_temps:
						h_idx = np.where(enthalpy_data["temperatures"] == temp)[0][0]
						g_idx = np.where(gibbs_data["temperatures"] == temp)[0][0]
						
						enthalpy = enthalpy_data["values"][h_idx]
						gibbs = gibbs_data["values"][g_idx]
						
						# 计算熵 (ΔS = (ΔH - ΔG)/T)
						entropy = (enthalpy - gibbs) * 1000 / temp  # J/(mol·K)
						
						valid_temperatures.append(temp)
						valid_values.append(entropy)
				
				# 存储有效的混合熵结果
				if valid_temperatures:
					self.calculation_results["entropy"][model_key]["temperatures"] = np.array(valid_temperatures)
					self.calculation_results["entropy"][model_key]["values"] = np.array(valid_values)
				
				progress_count += 1
				progress.setValue(progress_count)
			
			# 关闭进度对话框
			progress.close()
			
			# 检查是否有有效数据
			has_valid_data = False
			for prop in self.calculation_results:
				if any(len(self.calculation_results[prop][model_key]["temperatures"]) > 0 for model_key in
				       self.calculation_results[prop]):
					has_valid_data = True
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
			QMessageBox.information(self, "计算完成",
			                        "所有热力学性质计算完成，您可以通过选择不同的热力学性质来查看图表，也可以导出数据。")
		
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
		property_types = ["enthalpy", "gibbs", "entropy"]
		if property_index >= len(property_types):
			return
		
		selected_property = property_types[property_index]
		
		# 获取该性质的计算结果
		model_results = self.calculation_results[selected_property]
		
		# 没有数据则返回
		if not model_results:
			return
		
		# 绘制图表
		self.plot_model_comparison(model_results, selected_property)
	
	def plot_model_comparison (self, model_results, property_type):
		"""绘制不同模型的对比图"""
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
			if "temperatures" not in data or len(data["temperatures"]) == 0:
				continue
			
			color_idx = i % len(colors)
			marker_idx = i % len(markers)
			
			# 减少数据点数量，提高清晰度
			temperatures = data["temperatures"]
			values = data["values"]
			
			if len(temperatures) > 20:
				skip = len(temperatures) // 20
				plot_temps = temperatures[::skip]
				plot_values = values[::skip]
			else:
				plot_temps = temperatures
				plot_values = values
			
			line, = ax.plot(temperatures, values,
			                color=colors[color_idx],
			                marker=markers[marker_idx],
			                linewidth=2,
			                markersize=6,
			                label=self.model_checkboxes[model_key].text())
			
			plots.append(line)
			labels.append(self.model_checkboxes[model_key].text())
		
		# 设置标题和标签
		if property_type == "enthalpy":
			y_label = r"ΔH$_{mix}$ (kJ/mol)"
			title_property = "Mixing Enthalpy"
		elif property_type == "gibbs":
			y_label = r"$ΔG$ (kJ/mol)"
			title_property = "Gibbs Energy"
		else:  # entropy
			y_label = r"$ΔS_{mix}$ (J/mol·K)"
			title_property = "Mixing Entropy"
		
		# 设置X轴标签，避免使用中文
		ax.set_xlabel("Temperature (K)", fontsize=12)
		ax.set_ylabel(y_label, fontsize=12)
		
		# 构建标题
		comp_input = self.current_parameters["comp_input"]
		phase_dict = {"S": "Solid", "L": "Liquid"}
		phase_text = phase_dict.get(self.current_parameters["phase_state"], "Solid")
		
		order_dict = {"SS": "SS", "AMP": "AMP", "IM": "IM"}
		order_text = order_dict.get(self.current_parameters["order_degree"], "IM")
		
		title = f"{comp_input} Alloy {title_property} vs Temperature\n" \
		        f"Phase: {phase_text}, Type: {order_text}"
		ax.set_title(title, fontsize=13, pad=10)
		
		# 添加网格
		ax.grid(True, linestyle='--', alpha=0.7)
		
		# 设置坐标轴刻度字体大小
		ax.tick_params(axis='both', which='major', labelsize=10)
		
		# 添加图例，放在图表外部以避免遮挡数据
		if plots:
			self.figure.legend(plots, labels, loc='upper center', bbox_to_anchor=(0.5, 0.98),
			                   ncol=min(3, len(plots)), fontsize=10)
		
		# 调整布局
		self.figure.tight_layout(rect=[0, 0, 1, 0.93])
		
		# 绘制画布
		self.canvas.draw()
	
	def export_data (self):
		"""导出计算数据到CSV文件"""
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
		"""将数据导出为CSV格式"""
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
		
		# 准备数据
		with open(file_path, 'w', newline='') as csvfile:
			writer = csv.writer(csvfile)
			
			# 写入标题行 - 参数信息
			writer.writerow(['计算参数'])
			writer.writerow(['合金组成', self.current_parameters["comp_input"]])
			writer.writerow(['相态', "固态" if self.current_parameters["phase_state"] == "S" else "液态"])
			writer.writerow(['类型', self.current_parameters["order_degree"]])
			writer.writerow([])  # 空行
			
			# 写入标题行 - 数据部分
			header = ['温度 (K)']
			for model in all_models:
				header.extend([
					f'{model}-混合焓 (kJ/mol)',
					f'{model}-吉布斯自由能 (kJ/mol)',
					f'{model}-混合熵 (J/mol·K)'
				])
			writer.writerow(header)
			
			# 写入数据行
			for temp in all_temperatures:
				row = [temp]
				for model in all_models:
					# 混合焓
					enthalpy_value = ''
					if model in self.calculation_results["enthalpy"]:
						data = self.calculation_results["enthalpy"][model]
						if "temperatures" in data and len(data["temperatures"]) > 0:
							idx = np.where(data["temperatures"] == temp)[0]
							if idx.size > 0:
								enthalpy_value = f"{data['values'][idx[0]]:.6f}"
					row.append(enthalpy_value)
					
					# 吉布斯自由能
					gibbs_value = ''
					if model in self.calculation_results["gibbs"]:
						data = self.calculation_results["gibbs"][model]
						if "temperatures" in data and len(data["temperatures"]) > 0:
							idx = np.where(data["temperatures"] == temp)[0]
							if idx.size > 0:
								gibbs_value = f"{data['values'][idx[0]]:.6f}"
					row.append(gibbs_value)
					
					# 混合熵
					entropy_value = ''
					if model in self.calculation_results["entropy"]:
						data = self.calculation_results["entropy"][model]
						if "temperatures" in data and len(data["temperatures"]) > 0:
							idx = np.where(data["temperatures"] == temp)[0]
							if idx.size > 0:
								entropy_value = f"{data['values'][idx[0]]:.6f}"
					row.append(entropy_value)
				
				writer.writerow(row)
	
	def export_to_excel (self, file_path):
		"""将数据导出为Excel格式"""
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
		
		# 写入标题行 - 参数信息
		worksheet.write(0, 0, '计算参数', header_format)
		worksheet.write(1, 0, '合金组成', param_format)
		worksheet.write(1, 1, self.current_parameters["comp_input"], param_format)
		worksheet.write(2, 0, '相态', param_format)
		worksheet.write(2, 1, "固态" if self.current_parameters["phase_state"] == "S" else "液态", param_format)
		worksheet.write(3, 0, '类型', param_format)
		worksheet.write(3, 1, self.current_parameters["order_degree"], param_format)
		
		# 写入标题行 - 数据部分
		row = 5
		worksheet.write(row, 0, '温度 (K)', header_format)
		col = 1
		for model in all_models:
			worksheet.write(row, col, f'{model}-混合焓 (kJ/mol)', header_format)
			worksheet.write(row, col + 1, f'{model}-吉布斯自由能 (kJ/mol)', header_format)
			worksheet.write(row, col + 2, f'{model}-混合熵 (J/mol·K)', header_format)
			col += 3
		
		# 写入数据行
		row += 1
		for temp in all_temperatures:
			worksheet.write(row, 0, temp, data_format)
			col = 1
			for model in all_models:
				# 混合焓
				if model in self.calculation_results["enthalpy"]:
					data = self.calculation_results["enthalpy"][model]
					if "temperatures" in data and len(data["temperatures"]) > 0:
						idx = np.where(data["temperatures"] == temp)[0]
						if idx.size > 0:
							worksheet.write(row, col, data['values'][idx[0]], data_format)
				col += 1
				
				# 吉布斯自由能
				if model in self.calculation_results["gibbs"]:
					data = self.calculation_results["gibbs"][model]
					if "temperatures" in data and len(data["temperatures"]) > 0:
						idx = np.where(data["temperatures"] == temp)[0]
						if idx.size > 0:
							worksheet.write(row, col, data['values'][idx[0]], data_format)
				col += 1
				
				# 混合熵
				if model in self.calculation_results["entropy"]:
					data = self.calculation_results["entropy"][model]
					if "temperatures" in data and len(data["temperatures"]) > 0:
						idx = np.where(data["temperatures"] == temp)[0]
						if idx.size > 0:
							worksheet.write(row, col, data['values'][idx[0]], data_format)
				col += 1
			
			row += 1
		
		# 设置列宽
		worksheet.set_column(0, 0, 12)
		for i in range(1, 3 * len(all_models) + 1):
			worksheet.set_column(i, i, 20)
		
		# 保存并关闭工作簿
		workbook.close()


# 构建标


#父窗口
class MiedemaModelUI(QMainWindow):
	"""Main application window for Miedema model calculations"""
	
	def __init__ (self):
		super().__init__()
		self.init_ui()
		self.setWindowIcon(QIcon(resource_path(icon_path)))
	
	def init_ui (self):
		"""Initialize the UI components"""
		self.setWindowTitle("Multi-Component Miedema Model Calculator")
		self.setGeometry(100, 100, 1200, 800)
		
		# Set global font size
		app_font = QFont()
		app_font.setPointSize(12)  # Increased from default (typically 8 or 9)
		self.setFont(app_font)
		
		# Create central widget and main layout
		central_widget = QWidget()
		main_layout = QVBoxLayout()
		main_layout.setSpacing(15)  # Increase spacing between elements
		
		# Create main tab widget
		main_tabs = QTabWidget()
		main_tabs.setFont(QFont("Arial", 12))  # Larger font for tab labels
		
		# Tab 1: Single calculation
		single_calc_widget = QWidget()
		single_calc_layout = QHBoxLayout()
		single_calc_layout.setSpacing(20)  # Increase spacing between panels
		
		# Left panel (input)
		left_panel = QWidget()
		left_layout = QVBoxLayout()
		left_layout.setSpacing(15)  # Increase spacing between elements
		
		# Create tabs for element selection
		tabs = QTabWidget()
		tabs.setFont(QFont("Arial", 11))  # Larger font for sub-tab labels
		
		# Tab 1: Periodic Table - Pass the main window reference
		self.periodic_table = PeriodicTableWidget(parent=tabs, main_window=self)
		tabs.addTab(self.periodic_table, "Periodic Table")
		
		# Tab 2: Composition
		self.composition_table = CompositionTableWidget(tabs)
		tabs.addTab(self.composition_table, "Composition")
		
		left_layout.addWidget(tabs)
		
		# Parameters section
		params_group = QGroupBox("Calculation Parameters")
		params_group.setFont(QFont("Arial", 12, QFont.Bold))
		params_layout = QFormLayout()
		params_layout.setSpacing(15)  # Increase spacing between rows
		params_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
		
		# Create labels with larger font
		temp_label = QLabel("Temperature:")
		temp_label.setFont(QFont("Arial", 12))
		
		self.temp_input = QDoubleSpinBox()
		self.temp_input.setRange(300, 5000)
		self.temp_input.setValue(1000)
		self.temp_input.setSingleStep(50)
		self.temp_input.setSuffix(" K")
		self.temp_input.setFont(QFont("Arial", 12))
		self.temp_input.setMinimumHeight(35)  # Taller control
		params_layout.addRow(temp_label, self.temp_input)
		
		phase_label = QLabel("Phase State:")
		phase_label.setFont(QFont("Arial", 12))
		
		self.phase_combo = QComboBox()
		self.phase_combo.addItems(["Solid (S)", "Liquid (L)"])
		self.phase_combo.setFont(QFont("Arial", 12))
		self.phase_combo.setMinimumHeight(35)  # Taller control
		params_layout.addRow(phase_label, self.phase_combo)
		
		order_label = QLabel("Order Degree:")
		order_label.setFont(QFont("Arial", 12))
		
		self.order_combo = QComboBox()
		self.order_combo.addItems(["Solid Solution (SS)", "Amorphous (AMP)", "Intermetallic (IM)"])
		self.order_combo.setFont(QFont("Arial", 12))
		self.order_combo.setMinimumHeight(35)  # Taller control
		params_layout.addRow(order_label, self.order_combo)
		
		model_label = QLabel("Extrapolation Model:")
		model_label.setFont(QFont("Arial", 12))
		
		self.model_combo = QComboBox()
		self.model_combo.addItems([
			"Kohler (K)",
			"Muggianu (M)",
			"Toop-Kohler (T-K)",
			"GSM/Chou",
			"UEM1",
			"UEM2_N"
		])
		self.model_combo.setFont(QFont("Arial", 12))
		self.model_combo.setMinimumHeight(35)  # Taller control
		params_layout.addRow(model_label, self.model_combo)
		
		params_group.setLayout(params_layout)
		left_layout.addWidget(params_group)
		
		# Calculate button
		calc_button = QPushButton("Calculate")
		calc_button.clicked.connect(self.calculate)
		calc_button.setFont(QFont("Arial", 14, QFont.Bold))  # Larger, bold font
		calc_button.setMinimumHeight(50)  # Taller button
		calc_button.setStyleSheet("""
	        QPushButton {
	            background-color: #2980b9;
	            color: white;
	            border-radius: 5px;
	            padding: 10px;
	        }
	        QPushButton:hover {
	            background-color: #3498db;
	        }
	        QPushButton:pressed {
	            background-color: #1c6ea4;
	        }
	    """)
		left_layout.addWidget(calc_button)
		
		left_panel.setLayout(left_layout)
		
		# Right panel (results)
		self.results_widget = ResultsWidget()
		
		# Add panels to single calc layout
		single_calc_layout.addWidget(left_panel, 1)
		single_calc_layout.addWidget(self.results_widget, 2)
		
		single_calc_widget.setLayout(single_calc_layout)
		
		# Tab 2: Composition variation
		self.comp_variation_widget = CompositionVariationWidget(self)
		
		# Add tabs to main tab widget
		main_tabs.addTab(single_calc_widget, "Single Calculation")
		main_tabs.addTab(self.comp_variation_widget, "Composition Variation")
		
		# 创建温度变化标签页
		self.temp_variation_widget = TemperatureVariationWidget(self)
		main_tabs.addTab(self.temp_variation_widget, "Temperature Variation")
		# Connect tab change signal
		main_tabs.currentChanged.connect(self.on_tab_changed)
		
		# Add main tabs to layout
		main_layout.addWidget(main_tabs)
		
		central_widget.setLayout(main_layout)
		self.setCentralWidget(central_widget)
		
		# Apply global stylesheet for better look and feel
		self.setStyleSheet("""
	        QGroupBox {
	            border: 1px solid #bdc3c7;
	            border-radius: 5px;
	            margin-top: 20px;
	            padding-top: 15px;
	        }
	        QGroupBox::title {
	            subcontrol-origin: margin;
	            subcontrol-position: top left;
	            left: 10px;
	            padding: 0 5px;
	        }
	        QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {
	            border: 1px solid #bdc3c7;
	            border-radius: 3px;
	            padding: 5px;
	        }
	        QTabWidget::pane {
	            border: 1px solid #bdc3c7;
	            border-radius: 3px;
	        }
	        QTabBar::tab {
	            background: #ecf0f1;
	            border: 1px solid #bdc3c7;
	            border-bottom-color: none;
	            border-top-left-radius: 4px;
	            border-top-right-radius: 4px;
	            padding: 8px 15px;
	        }
	        QTabBar::tab:selected {
	            background: white;
	            margin-bottom: -1px;
	        }
	    """)
	
	# 为MiedemaModelUI类添加remove_element方法
	def remove_element (self, element):
		"""从组成中移除元素"""
		self.composition_table.remove_element(element)
	
	def calculate (self):
		"""Perform the calculation with current parameters"""
		# Get composition
		composition = self.composition_table.get_composition()
		
		if len(composition) < 2:
			QMessageBox.warning(self, "Insufficient Elements",
			                    "Please add at least two elements to the composition.")
			return
		
		# Get parameters
		temperature = self.temp_input.value()
		phase_state = "S" if self.phase_combo.currentText().startswith("Solid") else "L"
		
		# Get order degree
		order_text = self.order_combo.currentText()
		if order_text.startswith("Solid Solution"):
			order_degree = "SS"
		elif order_text.startswith("Amorphous"):
			order_degree = "AMP"
		else:
			order_degree = "IM"
		
		# Get model function
		model_function = self.get_model_function()
		#计算贡献系数
		modellist = ["UEM1", "UEM2_N", 'GSM', 'T-K']
		UEM.print_Contri_Coeff(composition, temperature, phase_state, order_degree, model_function[0],
		                       [model_function[1]])
		try:
			# Calculate enthalpy and  Gibbs energy
			enthalpy = UEM.get_mixingEnthalpy_byMiedema(
					composition, temperature, phase_state, order_degree, model_function[0])
			
			gibbs = UEM.get_Gibbs_byMiedema(composition, temperature, phase_state, order_degree, model_function[0])
			
			# Calculate entropy (ΔS = (ΔH - ΔG)/T)
			# Note: Convert Gibbs and enthalpy to the same units (kJ/mol)
			entropy = (enthalpy - gibbs) * 1000 / temperature  # J/(mol·K)
			
			# Get sub-binary compositions
			sub_binaries = UEM._get_subBinary_composition(
					composition, temperature, phase_state, order_degree, model_function[0])
			
			# Prepare details text
			details = self.prepare_calculation_details(
					composition, temperature, phase_state, order_degree,
					self.model_combo.currentText(), sub_binaries)
			
			# Update results - no more plot
			self.results_widget.set_results(enthalpy, gibbs, entropy, composition, details, sub_binaries)
			
			# Show success message
			status_bar = self.statusBar()
			status_bar.showMessage("Calculation completed successfully", 5000)
		
		except Exception as e:
			# Show detailed error
			error_message = f"Error during calculation: {str(e)}\n\n"
			error_message += "Technical details:\n"
			error_message += traceback.format_exc()
			
			error_dialog = QMessageBox(self)
			error_dialog.setWindowTitle("Calculation Error")
			error_dialog.setIcon(QMessageBox.Critical)
			error_dialog.setText("An error occurred during calculation")
			error_dialog.setDetailedText(error_message)
			error_dialog.setStandardButtons(QMessageBox.Ok)
			error_dialog.setDefaultButton(QMessageBox.Ok)
			error_dialog.exec_()
	
	def on_tab_changed (self, index):
		"""Handle tab change event"""
		if index == 1:  # Composition variation tab
			# Update element comboboxes in variation tab
			pass
	
	def add_element (self, element):
		"""Add an element to the composition from periodic table"""
		self.composition_table.add_element(element)
	
	def get_model_function (self) -> tuple[ContributionModelFunc, str]:
		"""Get the selected extrapolation model function"""
		model_text = self.model_combo.currentText()
		
		# Map model names to functions
		model_map = {
			"Kohler (K)": UEM.Kohler,
			"Muggianu (M)": UEM.Muggianu,
			"Toop-Kohler (T-K)": UEM.Toop_Kohler,
			"GSM/Chou": UEM.GSM,
			"UEM1": UEM.UEM1,
			"UEM2_N": UEM.UEM2_N
		}
		
		# Default to UEM1 if not found
		return model_map.get(model_text, UEM.UEM1), model_text
	
	def prepare_calculation_details (self, composition, temperature, phase_state,
	                                 order_degree, model_name, sub_binaries):
		"""准备计算详细信息的文本

		Args:
			composition (dict): 合金组成
			temperature (float): 温度K
			phase_state (str): 相态
			order_degree (str): 有序度
			model_name (str): 外推模型名称
			sub_binaries (list): 子二元系列表

		Returns:
			str: 详细计算信息文本
		"""
		details = f"计算参数:\n"
		details += f"温度: {temperature} K\n"
		details += f"相态: {'固态' if phase_state == 'S' else '液态'}\n"
		details += f"类型: {order_degree}\n"
		details += f"外推模型: {model_name}\n\n"
		
		details += f"合金组成:\n"
		for element, fraction in composition.items():
			details += f"{element}: {fraction:.4f}\n"
		
		details += f"\n子二元系:\n"
		for i, binary in enumerate(sub_binaries):
			details += f"{i + 1}. {binary.A.symbol}-{binary.B.symbol}: {binary.xA:.4f}/{binary.xB:.4f}\n"
		
		return details
	
	def calculate (self):
		"""Perform the calculation with current parameters"""
		# Get composition
		composition = self.composition_table.get_composition()
		
		if len(composition) < 2:
			QMessageBox.warning(self, "Insufficient Elements",
			                    "Please add at least two elements to the composition.")
			return
		
		# Get parameters
		temperature = self.temp_input.value()
		phase_state = "S" if self.phase_combo.currentText().startswith("Solid") else "L"
		
		# Get order degree
		order_text = self.order_combo.currentText()
		if order_text.startswith("Solid Solution"):
			order_degree = "SS"
		elif order_text.startswith("Amorphous"):
			order_degree = "AMP"
		else:
			order_degree = "IM"
		
		# Get model function
		model_function = self.get_model_function()
		#计算贡献系数
		UEM.print_Contri_Coeff(composition, temperature, phase_state, order_degree, model_function[0],
		                       [model_function[1]])
		
		try:
			# Calculate enthalpy and  Gibbs energy
			enthalpy = UEM.get_mixingEnthalpy_byMiedema(
					composition, temperature, phase_state, order_degree, model_function[0])
			
			gibbs = UEM.get_Gibbs_byMiedema(composition, temperature, phase_state, order_degree, model_function[0])
			
			# Calculate entropy (ΔS = (ΔH - ΔG)/T)
			# Note: Convert Gibbs and enthalpy to the same units (kJ/mol)
			entropy = (enthalpy - gibbs) * 1000 / temperature  # J/(mol·K)
			
			# Get sub-binary compositions
			sub_binaries = UEM._get_subBinary_composition(
					composition, temperature, phase_state, order_degree, model_function[0])
			
			# Prepare details text
			details = self.prepare_calculation_details(
					composition, temperature, phase_state, order_degree,
					self.model_combo.currentText(), sub_binaries)
			
			# Update results
			self.results_widget.set_results(enthalpy, gibbs, entropy, composition, details, sub_binaries)
		
		except Exception as e:
			QMessageBox.critical(self, "Calculation Error",
			                     f"Error during calculation: {str(e)}")


# 获取脚本所在目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 拼接图标文件路径
icon_path = os.path.join(current_dir, "app_icon.ico")
if __name__ == "__main__":
	# Create and show application
	app = QApplication(sys.argv)
	app.setWindowIcon(QIcon(resource_path(icon_path)))
	
	window = MiedemaModelUI()
	window.show()
	sys.exit(app.exec_())
