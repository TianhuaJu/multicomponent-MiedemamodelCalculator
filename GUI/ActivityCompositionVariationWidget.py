# ActivityCompositionVariationWidget.py (UI Optimized)
import sys
import traceback
import re
from typing import Dict

import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
                             QLineEdit, QComboBox, QDoubleSpinBox, QCheckBox, QPushButton,
                             QSplitter, QGridLayout, QLabel, QProgressDialog, QMessageBox,
                             QFileDialog, QFrame, QGraphicsDropShadowEffect)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

try:
	import matplotlib.style as mplstyle
except ImportError:
	mplstyle = None

from core import UnifiedExtrapolationModel as UEM
from utils.tool import export_data_to_file


# ==============================================================================
# 现代化的自定义UI控件
# ==============================================================================
class StyledGroupBox(QGroupBox):
	def __init__ (self, title, parent=None):
		super().__init__(title, parent)
		self.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
		self.setStyleSheet("""
            QGroupBox {
                font-weight: bold; border: 1px solid #e0e0e0; border-radius: 8px;
                margin-top: 10px; background-color: #ffffff; padding: 15px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
        """)


class StyledButton(QPushButton):
	def __init__ (self, text, button_type="primary", parent=None):
		super().__init__(text, parent)
		self.setMinimumHeight(40)
		self.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
		base_style = "border: none; border-radius: 6px; color: white; padding: 8px 16px;"
		if button_type == "primary":
			self.setStyleSheet(f"""QPushButton {{ background-color: #6366f1; {base_style} }}
                                 QPushButton:hover {{ background-color: #4f46e5; }}
                                 QPushButton:pressed {{ background-color: #4338ca; }}""")
		else:
			self.setStyleSheet(f"""QPushButton {{ background-color: #6b7280; {base_style} }}
                                 QPushButton:hover {{ background-color: #4b5563; }}
                                 QPushButton:pressed {{ background-color: #374151; }}""")


class AnimatedCheckBox(QCheckBox):
	def __init__ (self, text, parent=None):
		super().__init__(text, parent)
		self.setFont(QFont("Microsoft YaHei", 12))
		self.setStyleSheet("""
            QCheckBox { spacing: 8px; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 1px solid #d1d5db; background-color: #f9fafb; }
            QCheckBox::indicator:hover { border-color: #a5b4fc; }
            QCheckBox::indicator:checked { border-color: #6366f1; background-color: #6366f1; }""")


class StyledComboBox(QComboBox):
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.setMinimumHeight(32)
		self.setFont(QFont("Microsoft YaHei", 12))
		self.setStyleSheet("""
            QComboBox { border: 1px solid #d1d5db; border-radius: 4px; padding: 5px; background-color: white; }
            QComboBox:hover { border-color: #a5b4fc; }
            QComboBox::drop-down { width: 20px; border-left: 1px solid #d1d5db; }""")


class StyledLineEdit(QLineEdit):
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.setMinimumHeight(32)
		self.setFont(QFont("Microsoft YaHei", 12))
		self.setStyleSheet("""
            QLineEdit { border: 1px solid #d1d5db; border-radius: 4px; padding: 5px; background-color: white; }
            QLineEdit:hover { border-color: #a5b4fc; }
            QLineEdit:focus { border-color: #6366f1; }""")


class StyledSpinBox(QDoubleSpinBox):
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.setMinimumHeight(32)
		self.setFont(QFont("Microsoft YaHei", 12))
		self.setStyleSheet("""
            QDoubleSpinBox { border: 1px solid #d1d5db; border-radius: 4px; padding: 5px; background-color: white; }
            QDoubleSpinBox:hover { border-color: #a5b4fc; }
            QDoubleSpinBox:focus { border-color: #6366f1; }""")


class StatusIndicator(QLabel):
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.setFixedSize(12, 12)
		self.set_status("idle")
	
	def set_status (self, status):
		color_map = {"idle": "#95a5a6", "calculating": "#f39c12", "success": "#27ae60", "error": "#e74c3c"}
		self.setStyleSheet(
			f"background-color: {color_map.get(status, '#95a5a6')}; border-radius: 6px; border: 2px solid white;")


# ==============================================================================
# 主控件
# ==============================================================================

class ActivityCompositionVariationWidget(QWidget):
	"""活度/活度系数随成分变化计算器 (UI优化版)"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.parent_window = parent
		plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
		plt.rcParams['axes.unicode_minus'] = False
		if mplstyle:
			try:
				mplstyle.use('seaborn-v0_8-whitegrid')
			except:
				pass
		
		self.calculation_results = {"activity": {}, "activity_coefficient": {}}
		self.current_parameters = {}
		self.has_calculated = False
		
		self.init_ui()
	
	def init_ui (self):
		"""初始化用户界面组件 (优化版)"""
		self.setStyleSheet("background-color: #f3f4f6;")
		main_layout = QVBoxLayout(self)
		main_layout.setContentsMargins(15, 15, 15, 15)
		main_layout.setSpacing(15)
		
		main_layout.addWidget(self.create_title_frame())
		
		splitter = QSplitter(Qt.Horizontal)
		splitter.setHandleWidth(2)
		
		left_panel = self.create_left_panel()
		right_panel = self.create_right_panel()
		
		splitter.addWidget(left_panel)
		splitter.addWidget(right_panel)
		splitter.setSizes([420, 780])
		
		main_layout.addWidget(splitter)
		self.update_element_dropdowns()
	
	def create_title_frame (self):
		"""创建标题栏"""
		frame = QFrame(
			styleSheet="background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #818cf8, stop:1 #6366f1); border-radius: 8px;")
		layout = QHBoxLayout(frame)
		
		text_layout = QVBoxLayout()
		text_layout.addWidget(QLabel("活度随成分变化分析",
		                             styleSheet="color: white; font-size: 18px; font-weight: bold; background: transparent;"))
		text_layout.addWidget(QLabel("Activity vs. Composition Analysis",
		                             styleSheet="color: rgba(255, 255, 255, 0.8); background: transparent;"))
		
		status_layout = QHBoxLayout()
		self.status_indicator = StatusIndicator()
		self.status_label = QLabel("就绪",
		                           styleSheet="color: white; font-size: 12px; background: transparent; margin-left: 8px;")
		status_layout.addWidget(self.status_indicator)
		status_layout.addWidget(self.status_label)
		
		layout.addLayout(text_layout)
		layout.addStretch()
		layout.addLayout(status_layout)
		return frame
	
	def create_left_panel (self):
		"""创建左侧控制面板"""
		panel = QWidget()
		panel.setMinimumWidth(380);
		panel.setMaximumWidth(450)
		
		layout = QVBoxLayout(panel)
		layout.setSpacing(15);
		layout.setContentsMargins(0, 0, 0, 0)
		
		layout.addWidget(self.create_alloy_definition_group())
		layout.addWidget(self.create_calculation_params_group())
		layout.addWidget(self.create_model_selection_group())
		layout.addStretch(1)
		layout.addWidget(self.create_action_buttons())
		
		return panel
	
	def create_alloy_definition_group (self):
		"""创建合金定义和成分变化范围的组合框"""
		group = StyledGroupBox("🔬 合金与成分范围")
		layout = QFormLayout(group)
		layout.setSpacing(10)
		
		# 合金组成
		input_row = QHBoxLayout()
		self.matrix_input = StyledLineEdit("Fe0.7Ni0.3")
		self.matrix_input.setPlaceholderText("例如: Fe0.7Ni0.3")
		update_btn = QPushButton("更新")
		update_btn.setMinimumHeight(32);
		update_btn.setFixedWidth(60)
		update_btn.clicked.connect(self.update_element_dropdowns)
		input_row.addWidget(self.matrix_input);
		input_row.addWidget(update_btn)
		layout.addRow("基体合金:", input_row)
		
		# 元素选择
		self.solvent_combo = StyledComboBox()
		self.target_element_combo = StyledComboBox()
		self.var_element_combo = StyledComboBox()
		layout.addRow("溶剂元素:", self.solvent_combo)
		layout.addRow("目标元素:", self.target_element_combo)
		layout.addRow("变化元素:", self.var_element_combo)
		
		# 组成范围
		range_widget = QWidget()
		range_layout = QGridLayout(range_widget)
		range_layout.setContentsMargins(0, 0, 0, 0);
		range_layout.setSpacing(5)
		self.min_comp = StyledSpinBox();
		self.min_comp.setRange(0.0, 1.0);
		self.min_comp.setValue(0.0)
		self.max_comp = StyledSpinBox();
		self.max_comp.setRange(0.0, 1.0);
		self.max_comp.setValue(0.5)
		self.step_comp = StyledSpinBox();
		self.step_comp.setRange(0.01, 0.2);
		self.step_comp.setValue(0.05)
		range_layout.addWidget(QLabel("min:"), 0, 0);
		range_layout.addWidget(self.min_comp, 0, 1)
		range_layout.addWidget(QLabel("max:"), 0, 2);
		range_layout.addWidget(self.max_comp, 0, 3)
		range_layout.addWidget(QLabel("step:"), 1, 0);
		range_layout.addWidget(self.step_comp, 1, 1)
		layout.addRow("变化范围:", range_widget)
		
		return group
	
	def create_calculation_params_group (self):
		"""创建固定的计算参数区域"""
		group = StyledGroupBox("⚙️ 计算参数")
		layout = QFormLayout(group)
		layout.setSpacing(10)
		
		self.temp_input = StyledSpinBox()
		self.temp_input.setRange(300, 5000);
		self.temp_input.setValue(1000);
		self.temp_input.setSuffix(" K")
		
		self.phase_combo = StyledComboBox();
		self.phase_combo.addItems(["固态 (S)", "液态 (L)"])
		self.order_combo = StyledComboBox();
		self.order_combo.addItems(["固溶体 (SS)", "非晶态 (AMP)", "金属间化合物 (IM)"])
		self.property_combo = StyledComboBox();
		self.property_combo.addItems(["活度 (a)", "活度系数 (γ)"])
		self.property_combo.currentIndexChanged.connect(self.update_plot)
		self.geo_model_combo = StyledComboBox();
		self.geo_model_combo.addItems(["UEM1", "UEM2_N", "GSM", "T-K", "K", "M"])
		
		layout.addRow("固定温度:", self.temp_input)
		layout.addRow("相态:", self.phase_combo)
		layout.addRow("类型:", self.order_combo)
		layout.addRow("几何模型:", self.geo_model_combo)
		layout.addRow("绘图性质:", self.property_combo)
		return group
	
	def create_model_selection_group (self):
		"""创建外推模型选择区域"""
		group = StyledGroupBox("🧮 外推模型选择")
		layout = QGridLayout(group)
		layout.setSpacing(10)
		
		self.model_checkboxes = {}
		models = [("Kohler", "K"), ("Muggianu", "M"), ("Toop-Kohler", "T-K"),
		          ("GSM/Chou", "GSM"), ("UEM1", "UEM1"), ("UEM2_N", "UEM2_N")]
		for index, (name, key) in enumerate(models):
			checkbox = AnimatedCheckBox(name)
			if key in ["UEM1", "GSM"]: checkbox.setChecked(True)
			self.model_checkboxes[key] = checkbox
			layout.addWidget(checkbox, index // 2, index % 2)
		return group
	
	def create_action_buttons (self):
		"""创建操作按钮区域"""
		container = QWidget()
		layout = QHBoxLayout(container)
		layout.setSpacing(15);
		layout.setContentsMargins(0, 10, 0, 0)
		
		calculate_button = StyledButton("🚀 计算", "primary")
		export_button = StyledButton("📊 导出数据", "secondary")
		calculate_button.clicked.connect(self.calculate_all_properties)
		export_button.clicked.connect(self.export_data)
		
		layout.addWidget(calculate_button, 1)
		layout.addWidget(export_button, 1)
		return container
	
	def create_right_panel (self):
		"""创建右侧绘图面板"""
		panel = QWidget()
		layout = QVBoxLayout(panel)
		layout.setContentsMargins(0, 0, 0, 0)
		
		title = QLabel("📈 计算结果可视化",
		               styleSheet="font-size: 16px; font-weight: bold; color: #2c3e50; padding: 8px;")
		
		self.figure = Figure(figsize=(8, 8), dpi=100)
		self.canvas = FigureCanvas(self.figure)
		self.toolbar = NavigationToolbar(self.canvas, self)
		
		layout.addWidget(title)
		layout.addWidget(self.toolbar)
		layout.addWidget(self.canvas)
		return panel
	
	def update_status (self, status, message):
		"""更新状态指示器"""
		self.status_indicator.set_status(status)
		self.status_label.setText(message)
	
	def update_element_dropdowns (self):
		"""根据当前输入的合金组成更新元素下拉列表"""
		comp_input = self.matrix_input.text().strip()
		if not comp_input: return
		try:
			composition = self.parse_composition(comp_input)
			if not composition: return
			elements = sorted(list(composition.keys()))
			combos = [self.target_element_combo, self.var_element_combo, self.solvent_combo]
			for combo in combos: combo.blockSignals(True); combo.clear(); combo.addItems(elements)
			
			# 智能的默认选择逻辑
			if len(elements) > 0: self.solvent_combo.setCurrentIndex(0)
			if len(elements) > 1: self.target_element_combo.setCurrentIndex(1)
			if len(elements) > 2:
				self.var_element_combo.setCurrentIndex(2)
			else:
				self.var_element_combo.setCurrentIndex(0)
			
			# 确保三者不同（如果元素足够多）
			if len(set([self.solvent_combo.currentText(), self.target_element_combo.currentText(),
			            self.var_element_combo.currentText()])) < 3:
				if len(elements) > 1 and self.target_element_combo.currentText() == self.var_element_combo.currentText():
					self.var_element_combo.setCurrentIndex(
						(self.target_element_combo.currentIndex() + 1) % len(elements))
			
			for combo in combos: combo.blockSignals(False)
		except Exception as e:
			print(f"更新元素下拉列表时出错: {str(e)}")
	
	def parse_composition (self, comp_input):
		"""解析合金组成输入字符串，例如Fe0.7Ni0.3"""
		composition = {}
		pattern = r'([A-Z][a-z]*)(\d*\.?\d*)'
		matches = re.findall(pattern, comp_input)
		
		total = sum(float(r) if r else 1.0 for _, r in matches)
		if total > 0:
			for e, r in matches:
				composition[e] = (float(r) if r else 1.0) / total
		return composition
	
	def calculate_all_properties (self):
		"""计算所有热力学性质随组分变化（已修正和优化）"""
		self.update_status("calculating", "计算中...")
		
		# 1. 安全地获取所有UI输入参数
		matrix_input = self.matrix_input.text().strip()
		target_element = self.target_element_combo.currentText()
		var_element = self.var_element_combo.currentText()
		solvent = self.solvent_combo.currentText()
		
		if not all([matrix_input, target_element, var_element, solvent]):
			self.update_status("error", "输入不完整");
			QMessageBox.warning(self, "输入错误", "请填写所有合金与元素信息。");
			return
		
		try:
			base_matrix = self.parse_composition(matrix_input)
		except Exception as e:
			self.update_status("error", "解析错误");
			QMessageBox.critical(self, "解析错误", f"解析基体合金时出错: {e}");
			return
		
		temperature = self.temp_input.value()
		phase_state = "S" if "固态" in self.phase_combo.currentText() else "L"
		order_text = self.order_combo.currentText()
		order_degree = "SS" if "固溶体" in order_text else "AMP" if "非晶态" in order_text else "IM"
		geo_model = self.geo_model_combo.currentText()
		selected_models = [k for k, cb in self.model_checkboxes.items() if cb.isChecked()]
		if not selected_models:
			self.update_status("error", "模型未选择");
			QMessageBox.warning(self, "模型选择", "请至少选择一个模型。");
			return
		
		comp_range = np.arange(self.min_comp.value(), self.max_comp.value() + self.step_comp.value() / 2,
		                       self.step_comp.value())
		
		self.current_parameters = locals()
		self.calculation_results = {p: {m: {"compositions": [], "values": []} for m in selected_models} for p in
		                            ["activity", "activity_coefficient"]}
		model_functions = {"K": UEM.Kohler, "M": UEM.Muggianu, "T-K": UEM.Toop_Kohler, "GSM": UEM.GSM, "UEM1": UEM.UEM1,
		                   "UEM2_N": UEM.UEM2_N}
		
		progress = QProgressDialog("正在计算...", "取消", 0, len(selected_models) * len(comp_range), self)
		progress.setWindowModality(Qt.WindowModal);
		progress.show()
		
		try:
			for model_key in selected_models:
				if progress.wasCanceled(): break
				model_func = model_functions.get(model_key)
				if not model_func: continue
				progress.setLabelText(f"处理模型: {model_key}...")
				
				for x in comp_range:
					if progress.wasCanceled(): break
					progress.setValue(progress.value() + 1)
					
					# 健壮的成分计算逻辑
					new_comp = {var_element: x}
					for element, ratio in base_matrix.items():
						new_comp[element] = new_comp.get(element, 0) + ratio * (1.0 - x)
					
					total = sum(new_comp.values())
					if abs(total - 1.0) > 1e-9:
						for k in new_comp: new_comp[k] /= total
					
					try:
						activity_val = UEM.calculate_activity(new_comp, target_element, solvent, temperature,
						                                      phase_state, order_degree, model_func, geo_model)
						self.calculation_results["activity"][model_key]["compositions"].append(x)
						self.calculation_results["activity"][model_key]["values"].append(activity_val)
						
						mole_fraction_i = new_comp.get(target_element, 1e-12)
						coeff_val = activity_val / mole_fraction_i
						self.calculation_results["activity_coefficient"][model_key]["compositions"].append(x)
						self.calculation_results["activity_coefficient"][model_key]["values"].append(coeff_val)
					except Exception as e:
						print(f"在 x={x:.3f}, 模型 {model_key} 计算失败: {e}")
			
			progress.close()
			for prop in self.calculation_results.values():
				for model in prop.values():
					model["compositions"] = np.array(model["compositions"])
					model["values"] = np.array(model["values"])
			
			if not any(data['values'].size > 0 for prop in self.calculation_results.values() for data in prop.values()):
				self.update_status("error", "无有效数据");
				QMessageBox.warning(self, "无有效数据", "在指定范围内未能获得有效计算结果。");
				return
			
			self.has_calculated = True
			self.update_status("success", "计算完成")
			self.update_plot()
		except Exception as e:
			progress.close();
			self.update_status("error", "计算错误");
			QMessageBox.critical(self, "计算错误", f"计算时发生严重错误: {e}\n{traceback.format_exc()}")
	
	def update_plot (self):
		"""基于选择的热力学性质更新图表"""
		if not self.has_calculated: return
		prop_idx = self.property_combo.currentIndex()
		prop_key = ["activity", "activity_coefficient"][prop_idx]
		self.plot_property_variation(self.calculation_results.get(prop_key, {}), prop_key)
	
	def plot_property_variation (self, model_results, property_type):
		"""绘制热力学性质随组分变化的图表"""
		self.figure.clear()
		ax = self.figure.add_subplot(111)
		colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
		linestyles = ['-', '--', '-.', ':', (0, (3, 5, 1, 5)), (0, (5, 1))]
		markers = ['o', 's', '^', 'D', 'v', 'p']
		
		plotted_models = 0
		for i, (model_key, data) in enumerate(model_results.items()):
			if data and len(data.get("values", [])) > 0:
				ax.plot(data["compositions"], data["values"],
				        color=colors[i % len(colors)],
				        linestyle=linestyles[i % len(linestyles)],
				        marker=markers[i % len(markers)],
				        linewidth=2, markersize=5,
				        label=self.model_checkboxes[model_key].text())
				plotted_models += 1
		
		target = self.current_parameters.get('target_element', 'i')
		var = self.current_parameters.get('var_element', 'X')
		y_label, title_prop = (f"活度 $a_{{{target}}}$", "活度") if property_type == "activity" else (
		f"活度系数 $\\gamma_{{{target}}}$", "活度系数")
		
		ax.set_xlabel(f"{var} 摩尔分数 (x)", fontsize=12, fontweight='bold')
		ax.set_ylabel(y_label, fontsize=12, fontweight='bold')
		ax.set_title(f"{self.current_parameters.get('base_matrix', '')} 中 {target} 的{title_prop}", fontsize=14,
		             fontweight='bold', pad=12)
		ax.grid(True, linestyle='--', alpha=0.6)
		if plotted_models > 0: ax.legend()
		self.figure.tight_layout()
		self.canvas.draw()
	
	def export_data (self):
		"""准备数据并调用通用的导出函数"""
		if not self.has_calculated:
			QMessageBox.warning(self, "导出错误", "请先计算数据再导出。");
			return
		
		params = self.current_parameters
		var_element = params.get("var_element", "X")
		target_element = params.get("target_element", "i")
		parameters = {
			'基体合金': params.get("matrix_input", ""), '目标元素': target_element,
			'变化元素': var_element, '溶剂元素': params.get("solvent", "j"),
			'固定温度 (K)': params.get("temperature", 0), '相态': params.get("phase_state", ""),
			'类型': params.get("order_degree", ""), '几何模型': params.get("geo_model", "")
		}
		
		all_models = sorted([k for k, cb in self.model_checkboxes.items() if cb.isChecked()])
		all_compositions = sorted(list(set(np.concatenate(
				[data.get("compositions", []) for res in self.calculation_results.values() for data in res.values()]))))
		
		header = [f'{var_element} 摩尔分数 (x)']
		for model_key in all_models:
			header.extend([f'{self.model_checkboxes[model_key].text()}-活度',
			               f'{self.model_checkboxes[model_key].text()}-活度系数(γ)'])
		
		data_rows = []
		for comp in all_compositions:
			row = [comp]
			for model_key in all_models:
				for prop in ["activity", "activity_coefficient"]:
					data = self.calculation_results[prop].get(model_key, {})
					comps, vals = data.get("compositions", np.array([])), data.get("values", np.array([]))
					idx = np.where(comps == comp)[0]
					row.append(vals[idx[0]] if idx.size > 0 else None)
			data_rows.append(row)
		
		export_data_to_file(self, parameters, header, data_rows, f'{parameters["基体合金"]}_activity_vs_{var_element}')