# TemperatureVariationWidget.py
import traceback
import re
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout,
                             QLineEdit, QDoubleSpinBox, QSplitter, QGridLayout, QLabel,
                             QProgressDialog, QMessageBox, QComboBox, QCheckBox,
                             QHBoxLayout, QPushButton, QFrame, QGraphicsDropShadowEffect)
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from GUI.CompositionVariationWidget import StatusIndicator
from core import UnifiedExtrapolationModel as UEM
from utils.tool import export_data_to_file


class TemperatureVariationWidget(QWidget):
	"""用于计算固定组成下热力学性质随温度变化的窗口"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		
		# 设置样式
		self.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
                font-family: 'Microsoft YaHei';
                font-size: 13px;
            }
            QLabel {
                color: #6366f1;
                font-weight: 500;
            }
        """)
		
		# matplotlib设置
		plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial']
		plt.rcParams['axes.unicode_minus'] = False
		
		# 初始化变量
		self.calculation_results = {"enthalpy": {}, "gibbs": {}, "entropy": {}}
		self.current_parameters = {}
		self.has_calculated = False
		
		self.init_ui()
	
	def init_ui (self):
		main_layout = QVBoxLayout()
		main_layout.setContentsMargins(16, 16, 16, 16)
		main_layout.setSpacing(14)
		
		# 标题栏
		title_frame = self.create_title_frame()
		
		main_layout.addWidget(title_frame)
		
		# 主体分割器
		splitter = QSplitter(Qt.Horizontal)
		
		# 左侧面板
		left_panel = self.create_left_panel()
		splitter.addWidget(left_panel)
		
		# 右侧面板
		right_panel = self.create_right_panel()
		splitter.addWidget(right_panel)
		
		splitter.setSizes([420, 800])
		main_layout.addWidget(splitter)
		self.setLayout(main_layout)
	
	def create_title_frame (self):
		"""创建标题栏"""
		title_frame = QFrame()
		title_frame.setFixedHeight(80)
		title_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:1 #7c3aed);
                border-radius: 12px;
                margin-bottom: 8px;
            }
        """)
		
		title_layout = QHBoxLayout()
		title_layout.setContentsMargins(24, 16, 24, 16)
		
		# 标题文本
		title_label = QLabel("Thermodynamic Properties vs Temperature Analysis")
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
	
	def create_left_panel (self):
		left_widget = QWidget()
		left_widget.setMaximumWidth(450)
		left_widget.setStyleSheet("background-color: white; border-radius: 12px;")
		
		# 添加阴影
		shadow = QGraphicsDropShadowEffect()
		shadow.setBlurRadius(20)
		shadow.setColor(QColor(0, 0, 0, 30))
		left_widget.setGraphicsEffect(shadow)
		
		layout = QVBoxLayout()
		layout.setContentsMargins(20, 20, 20, 20)
		layout.setSpacing(16)
		
		# 合金组成
		comp_group = QGroupBox("🧪 合金组成设置")
		comp_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; font-size: 14px; border: 2px solid #c7d2fe;
                border-radius: 8px; margin-top: 12px; padding-top: 8px;
                background-color: rgba(199, 210, 254, 0.08);
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 10px; padding: 0 8px;
                color: #6366f1; background-color: white; border-radius: 4px;
            }
        """)
		comp_layout = QFormLayout()
		
		self.comp_input = QLineEdit()
		self.comp_input.setPlaceholderText("例如: Fe0.7Ni0.3")
		self.comp_input.setMinimumHeight(32)
		self.comp_input.setStyleSheet("""
            border: 2px solid #c7d2fe; border-radius: 6px; padding: 6px 10px;
            font-size: 13px; background-color: white;
            QLineEdit:focus { border-color: #8b5cf6; }
        """)
		comp_layout.addRow("合金组成:", self.comp_input)
		comp_group.setLayout(comp_layout)
		layout.addWidget(comp_group)
		
		# 计算参数
		params_group = QGroupBox("🌡️ 计算参数设置")
		params_group.setStyleSheet(comp_group.styleSheet())
		params_layout = QFormLayout()
		
		# 温度范围
		temp_widget = QWidget()
		temp_layout = QGridLayout()
		
		spinbox_style = """
            QDoubleSpinBox {
                border: 2px solid #c7d2fe; border-radius: 6px; padding: 4px 8px;
                font-size: 13px; background-color: white; min-height: 24px;
            }
            QDoubleSpinBox:focus { border-color: #8b5cf6; }
        """
		
		self.min_temp = QDoubleSpinBox()
		self.min_temp.setRange(300, 5000)
		self.min_temp.setValue(500)
		self.min_temp.setSuffix(" K")
		self.min_temp.setStyleSheet(spinbox_style)
		
		self.max_temp = QDoubleSpinBox()
		self.max_temp.setRange(300, 5000)
		self.max_temp.setValue(2000)
		self.max_temp.setSuffix(" K")
		self.max_temp.setStyleSheet(spinbox_style)
		
		self.step_temp = QDoubleSpinBox()
		self.step_temp.setRange(10, 500)
		self.step_temp.setValue(100)
		self.step_temp.setSuffix(" K")
		self.step_temp.setStyleSheet(spinbox_style)
		
		temp_layout.addWidget(QLabel("min:"), 0, 0)
		temp_layout.addWidget(self.min_temp, 0, 1)
		temp_layout.addWidget(QLabel("max:"), 0, 2)
		temp_layout.addWidget(self.max_temp, 0, 3)
		temp_layout.addWidget(QLabel("step:"), 1, 0)
		temp_layout.addWidget(self.step_temp, 1, 1)
		temp_widget.setLayout(temp_layout)
		params_layout.addRow("温度范围:", temp_widget)
		
		combo_style = """
            QComboBox {
                border: 2px solid #c7d2fe; border-radius: 6px; padding: 4px 8px;
                font-size: 13px; background-color: white; min-height: 24px;
            }
            QComboBox:focus { border-color: #8b5cf6; }
        """
		
		self.phase_combo = QComboBox()
		self.phase_combo.addItems(["固态 (S)", "液态 (L)"])
		self.phase_combo.setStyleSheet(combo_style)
		params_layout.addRow("相态:", self.phase_combo)
		
		self.order_combo = QComboBox()
		self.order_combo.addItems(["固溶体 (SS)", "非晶态 (AMP)", "金属间化合物 (IM)"])
		self.order_combo.setStyleSheet(combo_style)
		params_layout.addRow("类型:", self.order_combo)
		
		self.property_combo = QComboBox()
		self.property_combo.addItems([
			"混合焓 (ΔHₘᵢₓ, kJ/mol)",
			"吉布斯自由能 (ΔG, kJ/mol)",
			"混合熵 (ΔSₘᵢₓ, J/mol·K)"
		])
		self.property_combo.setStyleSheet(combo_style)
		self.property_combo.currentIndexChanged.connect(self.update_plot)
		params_layout.addRow("热力学性质:", self.property_combo)
		
		params_group.setLayout(params_layout)
		layout.addWidget(params_group)
		
		# 模型选择
		models_group = QGroupBox("🧮 外推模型选择")
		models_group.setStyleSheet(comp_group.styleSheet())
		models_layout = QVBoxLayout()
		
		self.model_checkboxes = {}
		models = [("Kohler 模型", "K"), ("Muggianu 模型", "M"), ("Toop-Kohler 模型", "T-K"),
		          ("GSM/Chou 模型", "GSM"), ("UEM1 模型", "UEM1"), ("UEM2_N 模型", "UEM2_N")]
		
		checkbox_style = """
            QCheckBox { font-size: 13px; color: #6366f1; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 9px; border: 2px solid #c7d2fe; }
            QCheckBox::indicator:checked { background-color: #8b5cf6; border-color: #8b5cf6; }
        """
		
		for name, key in models:
			checkbox = QCheckBox(name)
			checkbox.setStyleSheet(checkbox_style)
			if key in ["UEM1", "GSM"]:
				checkbox.setChecked(True)
			self.model_checkboxes[key] = checkbox
			models_layout.addWidget(checkbox)
		
		models_group.setLayout(models_layout)
		layout.addWidget(models_group)
		
		# 按钮
		button_layout = QVBoxLayout()
		
		calculate_button = QPushButton("🚀 开始计算")
		calculate_button.setMinimumHeight(40)
		calculate_button.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
		calculate_button.setStyleSheet("""
		    QPushButton {
		        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #8b5cf6, stop:1 #7c3aed);
		        border: none; border-radius: 6px; color: white; font-weight: bold;
		    }
		    QPushButton:hover {
		        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #a78bfa, stop:1 #8b5cf6);
		    }
		    QPushButton:pressed {
		        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #6d28d9, stop:1 #5b21b6);
		    }
		""")
		calculate_button.clicked.connect(self.calculate_all_properties)
		
		export_button = QPushButton("📊 导出数据")
		export_button.setMinimumHeight(40)
		export_button.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
		export_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #a78bfa, stop:1 #9333ea);
                border: none; border-radius: 6px; color: white; font-weight: bold;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #c4b5fd, stop:1 #a78bfa); }
        """)
		export_button.clicked.connect(self.export_data)
		
		button_layout.addWidget(calculate_button)
		button_layout.addWidget(export_button)
		layout.addLayout(button_layout)
		
		layout.addStretch()
		left_widget.setLayout(layout)
		return left_widget
	
	def create_right_panel (self):
		right_widget = QWidget()
		right_widget.setStyleSheet("background-color: white; border-radius: 12px;")
		
		# 添加阴影
		shadow = QGraphicsDropShadowEffect()
		shadow.setBlurRadius(20)
		shadow.setColor(QColor(0, 0, 0, 30))
		right_widget.setGraphicsEffect(shadow)
		
		layout = QVBoxLayout()
		layout.setContentsMargins(16, 16, 16, 16)
		
		plot_title = QLabel("📈 计算结果可视化")
		plot_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #6366f1; padding: 8px 0;")
		layout.addWidget(plot_title)
		
		# matplotlib图形
		self.figure = Figure(figsize=(10, 8), dpi=100, facecolor='white')
		self.canvas = FigureCanvas(self.figure)
		
		# 初始图形
		ax = self.figure.add_subplot(111)
		ax.text(0.5, 0.5, 'Ready for calculation...',
		        horizontalalignment='center', verticalalignment='center',
		        transform=ax.transAxes, fontsize=14, color='gray')
		self.canvas.draw()
		
		self.toolbar = NavigationToolbar(self.canvas, self)
		self.toolbar.setStyleSheet("background-color: #ecf0f1; border-radius: 6px; border: none;")
		
		layout.addWidget(self.toolbar)
		layout.addWidget(self.canvas)
		
		right_widget.setLayout(layout)
		return right_widget
	
	def parse_composition (self, comp_input):
		composition = {}
		pattern = r'([A-Z][a-z]*)(\d*\.?\d*)'
		matches = re.findall(pattern, comp_input)
		for element, ratio_str in matches:
			composition[element] = float(ratio_str) if ratio_str else 1.0
		total = sum(composition.values())
		if total > 0:
			for element in composition:
				composition[element] /= total
		return composition
	
	def calculate_all_properties (self):
		self.status_label.setText("计算中...")
		
		# 获取输入
		comp_input = self.comp_input.text().strip()
		if not comp_input:
			QMessageBox.warning(self, "输入错误", "请输入合金组成")
			self.status_label.setText("输入错误")
			return
		
		try:
			composition = self.parse_composition(comp_input)
			if not composition or len(composition) < 2:
				QMessageBox.warning(self, "解析错误", "无法解析合金组成，请使用格式如Fe0.7Ni0.3")
				self.status_label.setText("解析错误")
				return
		except Exception as e:
			QMessageBox.critical(self, "解析错误", f"解析合金组成时出错: {str(e)}")
			self.status_label.setText("解析错误")
			return
		
		# 获取参数
		phase_state = "S" if self.phase_combo.currentText().startswith("固态") else "L"
		order_text = self.order_combo.currentText()
		if order_text.startswith("固溶体"):
			order_degree = "SS"
		elif order_text.startswith("非晶态"):
			order_degree = "AMP"
		else:
			order_degree = "IM"
		
		selected_models = [key for key, checkbox in self.model_checkboxes.items() if checkbox.isChecked()]
		if not selected_models:
			QMessageBox.warning(self, "模型选择", "请至少选择一个外推模型")
			self.status_label.setText("模型未选择")
			return
		
		# 创建温度范围
		temp_range = np.arange(self.min_temp.value(),
		                       self.max_temp.value() + self.step_temp.value() / 2,
		                       self.step_temp.value())
		
		# 保存参数
		self.current_parameters = {
			"composition": composition,
			"comp_input": comp_input,
			"temp_range": temp_range.tolist(),
			"phase_state": phase_state,
			"order_degree": order_degree
		}
		
		# 清空结果
		self.calculation_results = {"enthalpy": {}, "gibbs": {}, "entropy": {}}
		
		model_functions = {
			"K": UEM.Kohler, "M": UEM.Muggianu, "T-K": UEM.Toop_Kohler,
			"GSM": UEM.GSM, "UEM1": UEM.UEM1, "UEM2_N": UEM.UEM2_N
		}
		
		# 进度条
		progress = QProgressDialog("计算中...", "取消", 0, len(selected_models) * 3, self)
		progress.setWindowModality(Qt.WindowModal)
		progress.show()
		
		try:
			progress_count = 0
			
			for model_key in selected_models:
				if progress.wasCanceled():
					break
				
				model_func = model_functions.get(model_key)
				if not model_func:
					continue
				
				# 初始化数据结构
				for prop in ["enthalpy", "gibbs", "entropy"]:
					self.calculation_results[prop][model_key] = {"temperatures": [], "values": []}
				
				# 计算混合焓
				h_temps, h_values = [], []
				for temp in temp_range:
					try:
						value = UEM.get_mixingEnthalpy_byMiedema(composition, temp, phase_state, order_degree,
						                                         model_func)
						h_temps.append(temp)
						h_values.append(value)
					except:
						continue
				
				if h_temps:
					self.calculation_results["enthalpy"][model_key]["temperatures"] = np.array(h_temps)
					self.calculation_results["enthalpy"][model_key]["values"] = np.array(h_values)
				
				progress_count += 1
				progress.setValue(progress_count)
				
				# 计算吉布斯自由能
				g_temps, g_values = [], []
				for temp in temp_range:
					try:
						value = UEM.get_Gibbs_byMiedema(composition, temp, phase_state, order_degree, model_func)
						g_temps.append(temp)
						g_values.append(value)
					except:
						continue
				
				if g_temps:
					self.calculation_results["gibbs"][model_key]["temperatures"] = np.array(g_temps)
					self.calculation_results["gibbs"][model_key]["values"] = np.array(g_values)
				
				progress_count += 1
				progress.setValue(progress_count)
				
				# 计算混合熵
				enthalpy_data = self.calculation_results["enthalpy"][model_key]
				gibbs_data = self.calculation_results["gibbs"][model_key]
				
				if len(enthalpy_data["temperatures"]) > 0 and len(gibbs_data["temperatures"]) > 0:
					common_temps = np.intersect1d(enthalpy_data["temperatures"], gibbs_data["temperatures"])
					s_temps, s_values = [], []
					
					for temp in common_temps:
						h_idx = np.where(enthalpy_data["temperatures"] == temp)[0][0]
						g_idx = np.where(gibbs_data["temperatures"] == temp)[0][0]
						
						enthalpy = enthalpy_data["values"][h_idx]
						gibbs = gibbs_data["values"][g_idx]
						entropy = (enthalpy - gibbs) * 1000 / temp
						
						s_temps.append(temp)
						s_values.append(entropy)
					
					if s_temps:
						self.calculation_results["entropy"][model_key]["temperatures"] = np.array(s_temps)
						self.calculation_results["entropy"][model_key]["values"] = np.array(s_values)
				
				progress_count += 1
				progress.setValue(progress_count)
			
			progress.close()
			
			# 检查是否有数据
			has_data = any(data for prop in self.calculation_results.values() for data in prop.values()
			               if data.get("temperatures", []).size > 0)
			
			if not has_data:
				QMessageBox.warning(self, "无有效数据", "在指定范围内未能获得有效计算结果")
				self.status_label.setText("无有效数据")
				return
			
			self.has_calculated = True
			self.status_label.setText("计算完成")
			self.update_plot()
			QMessageBox.information(self, "计算完成", "计算已完成")
		
		except Exception as e:
			progress.close()
			QMessageBox.critical(self, "计算错误", f"计算过程中发生错误: {str(e)}")
			self.status_label.setText("计算错误")
	
	def update_plot (self):
		if not self.has_calculated:
			return
		
		property_index = self.property_combo.currentIndex()
		property_types = ["enthalpy", "gibbs", "entropy"]
		selected_property = property_types[property_index]
		model_results = self.calculation_results[selected_property]
		
		if not model_results:
			return
		
		self.plot_model_comparison(model_results, selected_property)
	
	def plot_model_comparison (self, model_results, property_type):
		try:
			self.figure.clear()
			ax = self.figure.add_subplot(111)
			
			colors = ['#8b5cf6', '#a78bfa', '#c4b5fd', '#34d399', '#60a5fa', '#f59e0b']
			markers = ['o', 's', '^', 'D', 'v', '<']
			
			plotted = 0
			for i, (model_key, data) in enumerate(model_results.items()):
				if "temperatures" in data and len(data["temperatures"]) > 0:
					ax.plot(data["temperatures"], data["values"],
					        color=colors[i % len(colors)], marker=markers[i % len(markers)],
					        linewidth=2.5, markersize=6, markerfacecolor='white',
					        markeredgewidth=2, markeredgecolor=colors[i % len(colors)],
					        label=self.model_checkboxes[model_key].text(), alpha=0.8)
					plotted += 1
			
			if plotted == 0:
				ax.text(0.5, 0.5, 'No data to display',
				        horizontalalignment='center', verticalalignment='center',
				        transform=ax.transAxes, fontsize=14)
				self.canvas.draw()
				return
			
			# 设置标签
			if property_type == "enthalpy":
				y_label, title_prop = r"$\Delta H_{mix}$ (kJ/mol)", "Mixing Enthalpy"
			elif property_type == "gibbs":
				y_label, title_prop = r"$\Delta G$ (kJ/mol)", "Gibbs Energy"
			else:
				y_label, title_prop = r"$\Delta S_{mix}$ (J/mol·K)", "Mixing Entropy"
			
			ax.set_xlabel("Temperature (K)", fontsize=12, fontweight='bold')
			ax.set_ylabel(y_label, fontsize=12, fontweight='bold')
			
			comp_input = self.current_parameters["comp_input"]
			phase_text = "Solid" if self.current_parameters["phase_state"] == "S" else "Liquid"
			order_text = self.current_parameters["order_degree"]
			
			ax.set_title(f"{comp_input} Alloy {title_prop} vs Temperature\n"
			             f"Phase: {phase_text}, Type: {order_text}",
			             fontsize=13, fontweight='bold', pad=20)
			
			ax.grid(True, linestyle='--', alpha=0.3)
			ax.set_facecolor('#fafafa')
			ax.spines['top'].set_visible(False)
			ax.spines['right'].set_visible(False)
			
			if plotted > 0:
				legend = ax.legend(frameon=True, fancybox=True, shadow=True,
				                   framealpha=0.9, loc='best')
				legend.get_frame().set_facecolor('white')
			
			self.figure.tight_layout()
			self.canvas.draw()
		
		except Exception as e:
			self.figure.clear()
			ax = self.figure.add_subplot(111)
			ax.text(0.5, 0.5, f'Plot Error: {str(e)}',
			        horizontalalignment='center', verticalalignment='center',
			        transform=ax.transAxes, fontsize=12, color='red')
			self.canvas.draw()
	
	def export_data (self):
		if not self.has_calculated:
			QMessageBox.warning(self, "导出错误", "请先计算数据再导出")
			return
		
		parameters = {
			'合金组成': self.current_parameters.get("comp_input", ""),
			'相态': "固态 (S)" if self.current_parameters.get("phase_state") == "S" else "液态 (L)",
			'类型': self.current_parameters.get("order_degree", "")
		}
		
		all_models = sorted(self.calculation_results["enthalpy"].keys())
		all_temperatures = set()
		for prop_data in self.calculation_results.values():
			for model_key in all_models:
				if model_key in prop_data and "temperatures" in prop_data[model_key]:
					all_temperatures.update(prop_data[model_key]["temperatures"])
		
		sorted_temperatures = sorted(list(all_temperatures))
		
		header = ['温度 (K)']
		for model in all_models:
			header.extend([f'{model}-混合焓 (kJ/mol)', f'{model}-吉布斯自由能 (kJ/mol)', f'{model}-混合熵 (J/mol·K)'])
		
		data_rows = []
		for temp in sorted_temperatures:
			row = [temp]
			for model in all_models:
				# 混合焓
				h_data = self.calculation_results["enthalpy"].get(model, {})
				h_idx = np.where(h_data.get("temperatures", np.array([])) == temp)[0]
				row.append(h_data["values"][h_idx[0]] if len(h_idx) > 0 else None)
				
				# 吉布斯自由能
				g_data = self.calculation_results["gibbs"].get(model, {})
				g_idx = np.where(g_data.get("temperatures", np.array([])) == temp)[0]
				row.append(g_data["values"][g_idx[0]] if len(g_idx) > 0 else None)
				
				# 混合熵
				s_data = self.calculation_results["entropy"].get(model, {})
				s_idx = np.where(s_data.get("temperatures", np.array([])) == temp)[0]
				row.append(s_data["values"][s_idx[0]] if len(s_idx) > 0 else None)
			
			data_rows.append(row)
		
		export_data_to_file(
				parent=self,
				parameters=parameters,
				header=header,
				data=data_rows,
				default_filename=f'{parameters["合金组成"]}_temperature_variation'
		)