# CompositionVariationWidget.py
import traceback
import re
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
                             QLineEdit, QComboBox, QDoubleSpinBox, QCheckBox, QPushButton,
                             QSplitter, QGridLayout, QLabel, QProgressDialog, QMessageBox,
                             QFileDialog, QFrame, QScrollArea, QSpacerItem, QSizePolicy,
                             QGraphicsDropShadowEffect, QAbstractScrollArea)
from PyQt5.QtGui import QFont, QPalette, QColor, QPixmap, QIcon, QPainter, QBrush, QLinearGradient
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

try:
	import matplotlib.style as mplstyle
except ImportError:
	mplstyle = None
from core import UnifiedExtrapolationModel as UEM
from utils.tool import export_data_to_file


class StyledGroupBox(QGroupBox):
	"""自定义样式的分组框"""
	
	def __init__ (self, title, parent=None):
		super().__init__(title, parent)
		self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                background-color: rgba(52, 152, 219, 0.05);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2980b9;
                background-color: white;
                border-radius: 4px;
            }
        """)


class StyledButton(QPushButton):
	"""自定义样式的按钮"""
	
	def __init__ (self, text, button_type="primary", parent=None):
		super().__init__(text, parent)
		self.button_type = button_type
		self.setMinimumHeight(40)
		self.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
		self.update_style()
	
	def update_style (self):
		if self.button_type == "primary":
			self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3498db, stop:1 #2980b9);
                    border: none;
                    border-radius: 6px;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #3cb0fd, stop:1 #2980b9);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #2980b9, stop:1 #21618c);
                }
                QPushButton:disabled {
                    background: #bdc3c7;
                    color: #7f8c8d;
                }
            """)
		else:  # secondary
			self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #95a5a6, stop:1 #7f8c8d);
                    border: none;
                    border-radius: 6px;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #a2b3b4, stop:1 #7f8c8d);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #7f8c8d, stop:1 #6c7b7c);
                }
            """)


class AnimatedCheckBox(QCheckBox):
	"""带动画效果的复选框"""
	
	def __init__ (self, text, parent=None):
		super().__init__(text, parent)
		self.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                spacing: 8px;
                color: #2c3e50;
                font-weight: 500;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid #bdc3c7;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                border-color: #3498db;
                background-color: rgba(52, 152, 219, 0.1);
            }
            QCheckBox::indicator:checked {
                border-color: #3498db;
                background-color: #3498db;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #2980b9;
            }
        """)


class StyledComboBox(QComboBox):
	"""自定义样式的下拉框"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.setMinimumHeight(32)
		self.setStyleSheet("""
            QComboBox {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
                background-color: white;
                selection-background-color: #3498db;
            }
            QComboBox:hover {
                border-color: #3498db;
            }
            QComboBox:focus {
                border-color: #2980b9;
                outline: none;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #bdc3c7;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
                selection-background-color: #3498db;
                selection-color: white;
                padding: 4px;
            }
        """)


class StyledLineEdit(QLineEdit):
	"""自定义样式的文本输入框"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.setMinimumHeight(32)
		self.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                background-color: white;
                selection-background-color: #3498db;
            }
            QLineEdit:hover {
                border-color: #3498db;
            }
            QLineEdit:focus {
                border-color: #2980b9;
                outline: none;
            }
        """)


class StyledSpinBox(QDoubleSpinBox):
	"""自定义样式的数字输入框"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.setMinimumHeight(32)
		self.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
                background-color: white;
                selection-background-color: #3498db;
            }
            QDoubleSpinBox:hover {
                border-color: #3498db;
            }
            QDoubleSpinBox:focus {
                border-color: #2980b9;
                outline: none;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                width: 20px;
                border-left: 1px solid #bdc3c7;
                background-color: #ecf0f1;
            }
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #d5dbdb;
            }
        """)


class StatusIndicator(QLabel):
	"""状态指示器"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.setFixedSize(12, 12)
		self.set_status("idle")
	
	def set_status (self, status):
		if status == "idle":
			color = "#95a5a6"
		elif status == "calculating":
			color = "#f39c12"
		elif status == "success":
			color = "#27ae60"
		elif status == "error":
			color = "#e74c3c"
		else:
			color = "#95a5a6"
		
		self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 6px;
                border: 2px solid white;
            }}
        """)


class CompositionVariationWidget(QWidget):
	"""用于比较不同外推模型的热力学性质随成分变化窗口"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		
		# 设置现代化主题
		self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QLabel {
                color: #2c3e50;
                font-size: 13px;
                font-weight: 500;
            }
        """)
		
		# 设置matplotlib样式
		plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
		plt.rcParams['axes.unicode_minus'] = False
		if mplstyle:
			try:
				mplstyle.use('seaborn-v0_8-whitegrid')
			except:
				pass
		
		self.calculation_results = {"enthalpy": {}, "gibbs": {}, "entropy": {}}
		self.current_parameters = {}
		self.has_calculated = False
		self.init_ui()
	
	def init_ui (self):
		main_layout = QVBoxLayout()
		main_layout.setContentsMargins(16, 16, 16, 16)
		main_layout.setSpacing(16)
		
		# 创建顶部标题栏
		title_frame = self.create_title_frame()
		main_layout.addWidget(title_frame)
		
		# 创建主内容区域
		left_panel = QWidget()
		left_layout = QVBoxLayout()
		
		# 合金组成
		matrix_group = StyledGroupBox("🔬 合金组成")
		matrix_layout = QFormLayout()
		matrix_layout.setSpacing(2)  # 减少间距
		matrix_layout.setContentsMargins(6, 4, 6, 4)  # 减少边距
		
		self.matrix_input = StyledLineEdit()
		self.matrix_input.setPlaceholderText("e.g.: Fe0.7Ni0.3")
		matrix_layout.addRow("基体合金组成:", self.matrix_input)
		self.add_element_combo = StyledComboBox()
		self.add_element_combo.addItems(
				["Al", "Cr", "Mn", "Si", "Co", "Cu", "Ni", "Ti", "V", "Zn", "Mo", "W", "Nb", "Ta"])
		self.add_element_combo.setEditable(True)
		matrix_layout.addRow("添加元素:", self.add_element_combo)
		matrix_group.setLayout(matrix_layout)
		matrix_group.setFixedHeight(120)
		left_layout.addWidget(matrix_group)
		
		# 计算参数
		params_group = StyledGroupBox("⚙️ 计算参数")
		params_layout = QFormLayout()
		
		range_widget = QWidget()
		range_layout = QGridLayout()
		self.min_comp = StyledSpinBox()
		self.min_comp.setRange(0.0, 1.0)
		self.min_comp.setValue(0.0)
		self.min_comp.setSingleStep(0.05)
		
		self.max_comp = StyledSpinBox()
		self.max_comp.setRange(0.0, 1.0)
		self.max_comp.setValue(1.0)
		self.max_comp.setSingleStep(0.05)
		
		self.step_comp = StyledSpinBox()
		self.step_comp.setRange(0.01, 0.5)
		self.step_comp.setValue(0.05)
		self.step_comp.setSingleStep(0.01)
		
		range_layout.addWidget(QLabel("min:"), 0, 0)
		range_layout.addWidget(self.min_comp, 0, 1)
		range_layout.addWidget(QLabel("max:"), 0, 2)
		range_layout.addWidget(self.max_comp, 0, 3)
		range_layout.addWidget(QLabel("step:"), 1, 0)
		range_layout.addWidget(self.step_comp, 1, 1)
		range_widget.setLayout(range_layout)
		params_layout.addRow("组成范围:", range_widget)
		
		self.temp_input = StyledSpinBox()
		self.temp_input.setRange(300, 5000)
		self.temp_input.setValue(1000)
		self.temp_input.setSuffix(" K")
		params_layout.addRow("温度:", self.temp_input)
		
		self.phase_combo = StyledComboBox()
		self.phase_combo.addItems(["固态 (S)", "液态 (L)"])
		params_layout.addRow("相态:", self.phase_combo)
		
		self.order_combo = StyledComboBox()
		self.order_combo.addItems(["固溶体 (SS)", "非晶态 (AMP)", "金属间化合物 (IM)"])
		params_layout.addRow("类型:", self.order_combo)
		
		self.property_combo = StyledComboBox()
		self.property_combo.addItems([
			"混合焓 (ΔHₘᵢₓ, kJ/mol)",
			"吉布斯自由能 (ΔG, kJ/mol)",
			"混合熵 (ΔSₘᵢₓ, J/mol·K)"
		])
		self.property_combo.currentIndexChanged.connect(self.update_plot)
		params_layout.addRow("热力学性质:", self.property_combo)
		params_group.setLayout(params_layout)
		left_layout.addWidget(params_group)
		
		# 模型选择
		models_group = StyledGroupBox("🧮 外推模型选择")
		models_layout = QVBoxLayout()
		self.model_checkboxes = {}
		models = [("Kohler (K)", "K"), ("Muggianu (M)", "M"), ("Toop-Kohler (T-K)", "T-K"),
		          ("GSM/Chou", "GSM"), ("UEM1", "UEM1"), ("UEM2_N", "UEM2_N")]
		for name, key in models:
			checkbox = AnimatedCheckBox(name)
			if key in ["UEM1", "GSM"]: checkbox.setChecked(True)
			self.model_checkboxes[key] = checkbox
			models_layout.addWidget(checkbox)
		models_group.setLayout(models_layout)
		left_layout.addWidget(models_group)
		
		# 按钮
		buttons_layout = QHBoxLayout()
		calculate_button = StyledButton("🚀 计算", "primary")
		calculate_button.clicked.connect(self.calculate_all_properties)
		export_button = StyledButton("📊 导出数据", "secondary")
		export_button.clicked.connect(self.export_data)
		buttons_layout.addWidget(calculate_button)
		buttons_layout.addWidget(export_button)
		left_layout.addLayout(buttons_layout)
		
		left_panel.setLayout(left_layout)
		left_panel.setMaximumWidth(420)
		left_panel.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 12px;
            }
        """)
		
		# 添加阴影效果
		shadow = QGraphicsDropShadowEffect()
		shadow.setBlurRadius(20)
		shadow.setXOffset(0)
		shadow.setYOffset(2)
		shadow.setColor(QColor(0, 0, 0, 30))
		left_panel.setGraphicsEffect(shadow)
		
		# 绘图区
		right_panel = QWidget()
		right_layout = QVBoxLayout()
		right_layout.setContentsMargins(16, 16, 16, 16)
		
		# 绘图区域标题
		plot_title = QLabel("📈 计算结果可视化")
		plot_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 8px 0px;
            }
        """)
		right_layout.addWidget(plot_title)
		
		self.figure = Figure(figsize=(10, 8), dpi=100)
		self.figure.patch.set_facecolor('white')
		self.canvas = FigureCanvas(self.figure)
		self.toolbar = NavigationToolbar(self.canvas, self)
		self.toolbar.setStyleSheet("""
            QToolBar {
                border: none;
                background-color: #ecf0f1;
                border-radius: 6px;
                spacing: 4px;
                padding: 4px;
            }
            QToolButton {
                border: none;
                border-radius: 4px;
                padding: 6px;
                margin: 2px;
                background-color: transparent;
            }
            QToolButton:hover {
                background-color: #d5dbdb;
            }
        """)
		right_layout.addWidget(self.toolbar)
		right_layout.addWidget(self.canvas)
		right_panel.setLayout(right_layout)
		right_panel.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 12px;
            }
        """)
		
		# 为右侧面板添加阴影
		right_shadow = QGraphicsDropShadowEffect()
		right_shadow.setBlurRadius(20)
		right_shadow.setXOffset(0)
		right_shadow.setYOffset(2)
		right_shadow.setColor(QColor(0, 0, 0, 30))
		right_panel.setGraphicsEffect(right_shadow)
		
		splitter = QSplitter(Qt.Horizontal)
		splitter.addWidget(left_panel)
		splitter.addWidget(right_panel)
		splitter.setSizes([400, 800])
		main_layout.addWidget(splitter)
		self.setLayout(main_layout)
	
	def create_title_frame (self):
		"""创建标题栏"""
		title_frame = QFrame()
		title_frame.setFixedHeight(80)
		title_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 12px;
                margin-bottom: 8px;
            }
        """)
		
		title_layout = QHBoxLayout()
		title_layout.setContentsMargins(24, 16, 24, 16)
		
		# 标题文本
		title_label = QLabel("Alloy Composition Variation Thermodynamic Properties Analysis")
		title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }
        """)
		
		
		
		title_text_layout = QVBoxLayout()
		title_text_layout.addWidget(title_label)
		
		title_text_layout.setSpacing(2)
		
		title_layout.addLayout(title_text_layout)
		title_layout.addStretch()
		
		# 状态指示器
		self.status_indicator = StatusIndicator()
		self.status_label = QLabel("就绪")
		self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 10px;
                background: transparent;
                margin-left: 8px;
            }
        """)
		
		status_layout = QHBoxLayout()
		status_layout.addWidget(self.status_indicator)
		status_layout.addWidget(self.status_label)
		
		title_layout.addLayout(status_layout)
		title_frame.setLayout(title_layout)
		
		return title_frame
	
	def parse_matrix_composition (self, matrix_input):
		composition = {}
		pattern = r'([A-Z][a-z]*)(\d*\.?\d*)'
		matches = re.findall(pattern, matrix_input)
		for element, ratio_str in matches:
			composition[element] = float(ratio_str) if ratio_str else 1.0
		total = sum(composition.values())
		if total > 0:
			for element in composition:
				composition[element] /= total
		return composition
	
	def calculate_all_properties (self):
		"""计算所有热力学性质"""
		self.status_indicator.set_status("calculating")
		self.status_label.setText("计算中...")
		
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
			self.status_indicator.set_status("error")
			self.status_label.setText("输入错误")
			QMessageBox.warning(self, "输入错误", "请输入基体合金组成")
			return
		
		try:
			base_matrix = self.parse_matrix_composition(matrix_input)
			if not base_matrix:
				self.status_indicator.set_status("error")
				self.status_label.setText("解析错误")
				QMessageBox.warning(self, "解析错误", "无法解析基体合金组成，请使用格式如Fe0.7Ni0.3")
				return
		except Exception as e:
			self.status_indicator.set_status("error")
			self.status_label.setText("解析错误")
			QMessageBox.critical(self, "解析错误", f"解析基体合金组成时出错: {str(e)}")
			return
		
		# 获取添加元素
		add_element = self.add_element_combo.currentText().strip()
		if not add_element:
			self.status_indicator.set_status("error")
			self.status_label.setText("输入错误")
			QMessageBox.warning(self, "输入错误", "请选择或输入添加元素")
			return
		
		# 检查选中的模型
		selected_models = [key for key, checkbox in self.model_checkboxes.items() if checkbox.isChecked()]
		if not selected_models:
			self.status_indicator.set_status("error")
			self.status_label.setText("模型未选择")
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
			"enthalpy": {}, "gibbs": {}, "entropy": {}
		}
		
		model_functions = {
			"K": UEM.Kohler, "M": UEM.Muggianu, "T-K": UEM.Toop_Kohler,
			"GSM": UEM.GSM, "UEM1": UEM.UEM1, "UEM2_N": UEM.UEM2_N
		}
		
		progress = QProgressDialog("计算中...", "取消", 0, len(selected_models) * 3, self)
		progress.setWindowTitle("计算进度")
		progress.setWindowModality(Qt.WindowModal)
		progress.show()
		
		try:
			progress_count = 0
			for model_key in selected_models:
				if progress.wasCanceled(): break
				
				model_func = model_functions.get(model_key)
				if not model_func: continue
				
				for prop in ["enthalpy", "gibbs", "entropy"]:
					self.calculation_results[prop][model_key] = {"compositions": [], "values": []}
				
				h_comp, h_values = [], []
				for x in comp_range:
					new_comp = {elem: ratio * (1.0 - x) for elem, ratio in base_matrix.items()}
					new_comp[add_element] = x
					if any(v < 0 for v in new_comp.values()) or abs(sum(new_comp.values()) - 1.0) > 1e-9: continue
					try:
						value = UEM.get_mixingEnthalpy_byMiedema(new_comp, temperature, phase_state, order_degree,
						                                         model_func)
						h_comp.append(x)
						h_values.append(value)
					except Exception:
						continue
				if h_comp:
					self.calculation_results["enthalpy"][model_key] = {"compositions": np.array(h_comp),
					                                                   "values": np.array(h_values)}
				progress_count += 1
				progress.setValue(progress_count)
				
				g_comp, g_values = [], []
				for x in comp_range:
					new_comp = {elem: ratio * (1.0 - x) for elem, ratio in base_matrix.items()}
					new_comp[add_element] = x
					if any(v < 0 for v in new_comp.values()) or abs(sum(new_comp.values()) - 1.0) > 1e-9: continue
					try:
						value = UEM.get_Gibbs_byMiedema(new_comp, temperature, phase_state, order_degree, model_func)
						g_comp.append(x)
						g_values.append(value)
					except Exception:
						continue
				if g_comp:
					self.calculation_results["gibbs"][model_key] = {"compositions": np.array(g_comp),
					                                                "values": np.array(g_values)}
				progress_count += 1
				progress.setValue(progress_count)
				
				enthalpy_data = self.calculation_results["enthalpy"][model_key]
				gibbs_data = self.calculation_results["gibbs"][model_key]
				if enthalpy_data.get("compositions", []).size > 0 and gibbs_data.get("compositions", []).size > 0:
					common_comp, h_indices, g_indices = np.intersect1d(enthalpy_data["compositions"],
					                                                   gibbs_data["compositions"], return_indices=True)
					enthalpies = enthalpy_data["values"][h_indices]
					gibbs_energies = gibbs_data["values"][g_indices]
					entropies = (enthalpies - gibbs_energies) * 1000 / temperature
					self.calculation_results["entropy"][model_key] = {"compositions": common_comp, "values": entropies}
				progress_count += 1
				progress.setValue(progress_count)
			
			progress.close()
			
			if not any(data for prop in self.calculation_results.values() for data in prop.values()):
				self.status_indicator.set_status("error")
				self.status_label.setText("无有效数据")
				QMessageBox.warning(self, "无有效数据", "在指定范围内未能获得有效计算结果。")
				return
			
			self.has_calculated = True
			self.status_indicator.set_status("success")
			self.status_label.setText("计算完成")
			self.update_plot()
			QMessageBox.information(self, "计算完成", "计算已完成。")
		except Exception as e:
			progress.close()
			self.status_indicator.set_status("error")
			self.status_label.setText("计算错误")
			QMessageBox.critical(self, "计算错误", f"计算过程中发生错误: {str(e)}\n{traceback.format_exc()}")
	
	def update_plot (self):
		if not self.has_calculated: return
		property_index = self.property_combo.currentIndex()
		property_types = ["enthalpy", "gibbs", "entropy"]
		selected_property = property_types[property_index]
		model_results = self.calculation_results[selected_property]
		if not model_results: return
		self.plot_model_comparison(model_results, self.current_parameters["add_element"], selected_property,
		                           self.current_parameters["base_matrix"])
	
	def plot_model_comparison (self, model_results, add_element, property_type, matrix_input):
		self.figure.clear()
		ax = self.figure.add_subplot(111)
		
		# 使用更现代的颜色方案
		colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#34495e']
		markers = ['o', 's', '^', 'D', 'v', '<', '>']
		linestyles = ['-', '--', '-.', ':', '-', '--', '-.']
		
		plotted_models = 0
		for i, (model_key, data) in enumerate(model_results.items()):
			if "compositions" in data and data["compositions"].size > 0:
				ax.plot(data["compositions"], data["values"],
				        color=colors[i % len(colors)],
				        marker=markers[i % len(markers)],
				        linestyle=linestyles[i % len(linestyles)],
				        linewidth=2.5,
				        markersize=6,
				        markerfacecolor='white',
				        markeredgewidth=2,
				        markeredgecolor=colors[i % len(colors)],
				        label=self.model_checkboxes[model_key].text(),
				        alpha=0.8)
				plotted_models += 1
		
		if property_type == "enthalpy":
			y_label, title_prop = r"$\Delta H_{mix}$ (kJ/mol)", "混合焓"
		elif property_type == "gibbs":
			y_label, title_prop = r"$\Delta G$ (kJ/mol)", "吉布斯自由能"
		else:
			y_label, title_prop = r"$\Delta S_{mix}$ (J/mol·K)", "混合熵"
		
		ax.set_xlabel(f"{add_element} 摩尔分数 (x)", fontsize=12, fontweight='bold')
		ax.set_ylabel(y_label, fontsize=12, fontweight='bold')
		
		temperature = self.current_parameters["temperature"]
		phase_text = "固态" if self.current_parameters["phase_state"] == "S" else "液态"
		order_text = self.current_parameters["order_degree"]
		
		ax.set_title(f"({matrix_input})$_{{1-x}}$({add_element})$_{{x}}$ 合金 {title_prop}\n"
		             f"温度: {temperature}K, 相态: {phase_text}, 类型: {order_text}",
		             fontsize=13, fontweight='bold', pad=20)
		
		ax.grid(True, linestyle='--', alpha=0.3, linewidth=1)
		ax.set_facecolor('#fafafa')
		
		# 设置坐标轴样式
		ax.spines['top'].set_visible(False)
		ax.spines['right'].set_visible(False)
		ax.spines['left'].set_linewidth(1.5)
		ax.spines['bottom'].set_linewidth(1.5)
		
		if plotted_models > 0:
			legend = ax.legend(frameon=True, fancybox=True, shadow=True,
			                   framealpha=0.9, loc='best')
			legend.get_frame().set_facecolor('white')
			legend.get_frame().set_edgecolor('#bdc3c7')
		
		self.figure.tight_layout()
		self.canvas.draw()
	
	def export_data (self):
		if not self.has_calculated:
			QMessageBox.warning(self, "导出错误", "请先计算数据再导出")
			return
		
		parameters = {
			'基体合金': self.current_parameters.get("base_matrix", ""),
			'添加元素': self.current_parameters.get("add_element", ""),
			'温度 (K)': self.current_parameters.get("temperature", ""),
			'相态': "固态 (S)" if self.current_parameters.get("phase_state") == "S" else "液态 (L)",
			'类型': self.current_parameters.get("order_degree", "")
		}
		
		all_models = sorted(self.calculation_results["enthalpy"].keys())
		all_compositions = set()
		for prop_data in self.calculation_results.values():
			for model_key in all_models:
				if model_key in prop_data and "compositions" in prop_data[model_key]:
					all_compositions.update(prop_data[model_key]["compositions"])
		
		sorted_compositions = sorted(list(all_compositions))
		
		header = ['组成 (x)']
		for model in all_models:
			header.extend([f'{model}-混合焓 (kJ/mol)', f'{model}-吉布斯自由能 (kJ/mol)', f'{model}-混合熵 (J/mol·K)'])
		
		data_rows = []
		for comp in sorted_compositions:
			row = [comp]
			for model in all_models:
				h_val = self.calculation_results["enthalpy"].get(model, {})
				h_idx = np.where(h_val.get("compositions", []) == comp)[0]
				row.append(h_val["values"][h_idx[0]] if len(h_idx) > 0 else None)
				
				g_val = self.calculation_results["gibbs"].get(model, {})
				g_idx = np.where(g_val.get("compositions", []) == comp)[0]
				row.append(g_val["values"][g_idx[0]] if len(g_idx) > 0 else None)
				
				s_val = self.calculation_results["entropy"].get(model, {})
				s_idx = np.where(s_val.get("compositions", []) == comp)[0]
				row.append(s_val["values"][s_idx[0]] if len(s_idx) > 0 else None)
			data_rows.append(row)
		
		export_data_to_file(
				parent=self,
				parameters=parameters,
				header=header,
				data=data_rows,
				default_filename=f'{parameters["基体合金"]}-{parameters["添加元素"]}_composition_variation'
		)