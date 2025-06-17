# ActivityCoefficientWidget.py (Layout Optimized)
import sys
import traceback
from typing import Dict
from datetime import datetime

import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
                             QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
                             QLabel, QLineEdit, QMessageBox,
                             QProgressDialog, QPushButton, QSplitter, QTextEdit, QVBoxLayout, QWidget)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# 假设这些模块与此文件在同一目录或已正确安装
from core import UnifiedExtrapolationModel as UEM
from utils.tool import export_data_to_file

class ActivityCoefficientWidget(QWidget):
	"""用于计算和显示活度及活度系数的窗口组件"""
	
	def __init__ (self, parent=None):
		super().__init__(parent)
		self.parent_window = parent
		plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
		plt.rcParams['axes.unicode_minus'] = False
		self.calculation_results = {"activity": {}, "activity_coefficient": {}}
		self.current_parameters = {}
		self.has_calculated = False
		self.init_ui()
		self.update_element_dropdowns()
	
	def init_ui (self):
		"""初始化用户界面组件"""
		app_font = QFont("Arial", 10)
		self.setFont(app_font)
		
		# --- 主布局从这里开始 ---
		main_layout = QHBoxLayout(self)  # 使用 QHBoxLayout 替换 QVBoxLayout
		main_layout.setSpacing(15)
		
		# --- 左侧控制面板 ---
		left_panel = QWidget()
		left_layout = QVBoxLayout(left_panel)
		left_layout.setSpacing(15)
		left_panel.setMinimumWidth(400)
		left_panel.setMaximumWidth(450)
		
		# 合金组成输入
		comp_group = self.create_composition_group()
		left_layout.addWidget(comp_group)
		
		# 计算参数
		params_group = self.create_parameters_group()
		left_layout.addWidget(params_group)
		
		# 外推模型选择
		models_group = self.create_models_group()
		left_layout.addWidget(models_group)
		
		left_layout.addStretch(1)
		
		# 按钮区域
		buttons_layout = QHBoxLayout()
		calculate_button = QPushButton("计算")
		calculate_button.setMinimumHeight(40)
		calculate_button.clicked.connect(self.calculate_all_properties)
		export_button = QPushButton("导出数据")
		export_button.setMinimumHeight(40)
		export_button.clicked.connect(self.export_data)
		buttons_layout.addWidget(calculate_button)
		buttons_layout.addWidget(export_button)
		left_layout.addLayout(buttons_layout)
		
		# --- 右侧面板 (包含结果和绘图) ---
		# 使用垂直分割器来容纳结果框和绘图区
		right_splitter = QSplitter(Qt.Vertical)
		
		# 1. 结果显示区域 (现在是右侧分割器的顶部)
		results_display_group = QGroupBox("计算结果")
		results_display_layout = QVBoxLayout(results_display_group)
		self.results_text = QTextEdit()
		self.results_text.setReadOnly(True)
		self.results_text.setMinimumHeight(150)  # 设置一个最小高度
		self.results_text.setFont(QFont("Consolas", 10))
		results_display_layout.addWidget(self.results_text)
		
		# 2. 绘图区域 (现在是右侧分割器的底部)
		plot_container = QWidget()
		plot_layout = QVBoxLayout(plot_container)
		self.figure = Figure(figsize=(7, 5), dpi=100)
		self.canvas = FigureCanvas(self.figure)
		self.toolbar = NavigationToolbar(self.canvas, self)
		plot_layout.addWidget(self.toolbar)
		plot_layout.addWidget(self.canvas)
		
		# 将结果框和绘图区添加到垂直分割器
		right_splitter.addWidget(results_display_group)
		right_splitter.addWidget(plot_container)
		
		# 设置初始高度比例 (例如 30% 给结果框, 70% 给绘图)
		right_splitter.setSizes([200, 550])
		
		# --- 组装主分割器 ---
		main_splitter = QSplitter(Qt.Horizontal)
		main_splitter.addWidget(left_panel)
		main_splitter.addWidget(right_splitter)
		main_splitter.setSizes([420, 780])
		
		main_layout.addWidget(main_splitter)
		
		self.apply_stylesheet()
		self.comp_input.setText("Fe0.7Ni0.3")
	
	# --- 辅助创建UI的方法 (为了让init_ui更清晰) ---
	def create_composition_group (self):
		group = QGroupBox("合金组成")
		layout = QVBoxLayout(group)
		layout.addWidget(QLabel("合金组成 (例如: Fe0.7Ni0.3):"))
		input_row = QHBoxLayout()
		self.comp_input = QLineEdit()
		self.comp_input.setMinimumHeight(30)
		self.comp_input.textChanged.connect(self.update_element_dropdowns)
		input_row.addWidget(self.comp_input)
		update_btn = QPushButton("更新元素")
		update_btn.setFixedWidth(80)
		update_btn.clicked.connect(self.update_element_dropdowns)
		input_row.addWidget(update_btn)
		layout.addLayout(input_row)
		solute_solvent_layout = QFormLayout()
		self.solvent_combo = QComboBox();
		self.solvent_combo.setMinimumHeight(30)
		self.solute_combo = QComboBox();
		self.solute_combo.setMinimumHeight(30)
		solute_solvent_layout.addRow("溶剂元素:", self.solvent_combo)
		solute_solvent_layout.addRow("溶质元素:", self.solute_combo)
		layout.addLayout(solute_solvent_layout)
		return group
	
	def create_parameters_group (self):
		group = QGroupBox("计算参数")
		layout = QFormLayout(group)
		self.temp_input = QDoubleSpinBox();
		self.temp_input.setRange(300, 5000);
		self.temp_input.setValue(1000);
		self.temp_input.setSuffix(" K")
		self.phase_combo = QComboBox();
		self.phase_combo.addItems(["固态 (S)", "液态 (L)"])
		self.order_combo = QComboBox();
		self.order_combo.addItems(["固溶体 (SS)", "非晶态 (AMP)", "金属间化合物 (IM)"])
		self.property_combo = QComboBox();
		self.property_combo.addItems(["活度 (a)", "活度系数 (ln γ)"]);
		self.property_combo.currentIndexChanged.connect(self.update_plot)
		layout.addRow("温度:", self.temp_input)
		layout.addRow("相态:", self.phase_combo)
		layout.addRow("类型:", self.order_combo)
		layout.addRow("绘图性质:", self.property_combo)
		return group
	
	def create_models_group (self):
		group = QGroupBox("外推模型选择")
		layout = QVBoxLayout(group)
		self.model_checkboxes = {}
		models = [("Kohler (K)", "K"), ("Muggianu (M)", "M"), ("Toop-Kohler (T-K)", "T-K"), ("GSM/Chou", "GSM"),
		          ("UEM1", "UEM1"), ("UEM2_N", "UEM2_N")]
		for name, key in models:
			checkbox = QCheckBox(name)
			if key in ["UEM1", "GSM"]: checkbox.setChecked(True)
			self.model_checkboxes[key] = checkbox
			layout.addWidget(checkbox)
		return group
	
	# ... (apply_stylesheet, update_element_dropdowns, parse_composition 等方法保持不变) ...
	def apply_stylesheet (self):
		"""应用样式表以统一外观"""
		self.setStyleSheet("""
			QWidget { font-size: 12pt; }
			QGroupBox {
				font-weight: bold; border: 1px solid #cccccc; border-radius: 5px;
				margin-top: 10px; padding-top: 20px;
			}
			QGroupBox::title {
				subcontrol-origin: margin; subcontrol-position: top left;
				padding: 0 5px; left: 10px; color: #333333;
			}
			QLineEdit, QComboBox, QDoubleSpinBox {
				padding: 4px; min-height: 28px; border: 1px solid #cccccc;
				border-radius: 3px; background-color: white;
			}
			QPushButton {
				font-size: 10pt; padding: 8px 12px; background-color: #0078d7;
				color: white; border: none; border-radius: 4px;
			}
			QPushButton:hover { background-color: #005a9e; }
			QPushButton:pressed { background-color: #003c6c; }
			QTextEdit { border: 1px solid #cccccc; border-radius: 3px; }
			QSplitter::handle { background: #e0e0e0; }
			QSplitter::handle:vertical { height: 4px; }
			QSplitter::handle:horizontal { width: 4px; }
		""")
	
	def update_element_dropdowns (self):
		"""根据当前输入的合金组成更新溶质和溶剂元素下拉列表"""
		self.solute_combo.blockSignals(True)
		self.solvent_combo.blockSignals(True)
		try:
			comp_input_str = self.comp_input.text().strip()
			current_solute = self.solute_combo.currentText()
			current_solvent = self.solvent_combo.currentText()
			
			self.solute_combo.clear()
			self.solvent_combo.clear()
			
			if comp_input_str:
				composition = self.parse_composition(comp_input_str)
				if composition:
					elements = sorted(list(composition.keys()))
					self.solute_combo.addItems(elements)
					self.solvent_combo.addItems(elements)
					
					if current_solute in elements:
						self.solute_combo.setCurrentText(current_solute)
					elif len(elements) > 1:
						self.solute_combo.setCurrentIndex(1)
					
					if current_solvent in elements:
						self.solvent_combo.setCurrentText(current_solvent)
					elif elements:
						self.solvent_combo.setCurrentIndex(0)
					
					if len(elements) > 1 and self.solute_combo.currentText() == self.solvent_combo.currentText():
						if self.solvent_combo.currentIndex() == 0:
							self.solute_combo.setCurrentIndex(1)
						else:
							self.solute_combo.setCurrentIndex(0)
		finally:
			self.solute_combo.blockSignals(False)
			self.solvent_combo.blockSignals(False)
	
	def parse_composition (self, comp_input_str: str) -> Dict[str, float]:
		import re
		composition = {}
		pattern = r'([A-Z][a-z]*)(\d*\.?\d*)'
		matches = re.findall(pattern, comp_input_str)
		if not matches: return {}
		
		total_ratio = 0.0
		for element, ratio_str in matches:
			ratio = float(ratio_str) if ratio_str else 1.0
			composition[element] = composition.get(element, 0) + ratio
			total_ratio += ratio
		
		if total_ratio > 0:
			return {el: r / total_ratio for el, r in composition.items()}
		return {}
	
	def calculate_all_properties (self):
		"""计算所有热力学性质"""
		comp_input = self.comp_input.text().strip()
		if not comp_input:
			QMessageBox.warning(self, "输入错误", "请输入合金组成");
			return
		
		composition = self.parse_composition(comp_input)
		if not composition:
			QMessageBox.warning(self, "解析错误", "无法解析合金组成或组成无效。");
			return
		
		solute = self.solute_combo.currentText()
		solvent = self.solvent_combo.currentText()
		if not solute or not solvent:
			QMessageBox.warning(self, "输入错误", "请选择溶质和溶剂元素。");
			return
		if solute == solvent and len(composition) > 1:
			QMessageBox.warning(self, "元素错误", "溶质和溶剂元素不能相同。");
			return
		
		temperature = self.temp_input.value()
		phase_state = "S" if "固态" in self.phase_combo.currentText() else "L"
		order_text = self.order_combo.currentText()
		order_degree = "SS" if "固溶体" in order_text else "AMP" if "非晶态" in order_text else "IM"
		
		selected_models = [key for key, cb in self.model_checkboxes.items() if cb.isChecked()]
		if not selected_models:
			QMessageBox.warning(self, "模型选择", "请至少选择一个外推模型。");
			return
		
		self.current_parameters = locals()  # Store all local variables
		self.calculation_results = {"activity": {}, "activity_coefficient": {}}
		model_functions = {"K": UEM.Kohler, "M": UEM.Muggianu, "T-K": UEM.Toop_Kohler, "GSM": UEM.GSM, "UEM1": UEM.UEM1,
		                   "UEM2_N": UEM.UEM2_N}
		
		# --- 结果显示与历史记录 ---
		current_history = self.results_text.toHtml()
		is_initial = "计算结果将显示在此" in current_history or not self.results_text.toPlainText().strip()
		
		new_result_html = f"""
			<h3>计算: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h3>
			<p><b>参数:</b> {comp_input}; 溶质={solute}, 溶剂={solvent}; T={temperature:.0f}K; 相态={phase_state}; 类型={order_degree}</p>
			<table width='100%' border='1' cellspacing='0' cellpadding='4'>
				<tr><th>模型</th><th>活度 (a)</th><th>活度系数 (ln γ)</th></tr>
		"""
		
		successful_models = 0
		for model_key in selected_models:
			func = model_functions.get(model_key)
			if not func: continue
			
			try:
				activity = UEM.calculate_activity(composition, solute, solvent, temperature, phase_state, order_degree,
				                                  func)
				act_coeff = UEM.calculate_activity_coefficient(composition, solute, solvent, temperature, phase_state,
				                                               order_degree, func)
				
				self.calculation_results["activity"][model_key] = {"value": activity}
				self.calculation_results["activity_coefficient"][model_key] = {"value": act_coeff}
				
				new_result_html += f"<tr><td>{self.model_checkboxes[model_key].text()}</td><td>{activity:.6f}</td><td>{act_coeff:.6f}</td></tr>"
				successful_models += 1
			except Exception as e:
				new_result_html += f"<tr><td>{self.model_checkboxes[model_key].text()}</td><td colspan='2' style='color:red;'>计算失败: {e}</td></tr>"
		
		new_result_html += "</table>"
		
		self.results_text.setHtml(new_result_html + "<hr>" + (current_history if not is_initial else ""))
		
		if successful_models > 0:
			self.has_calculated = True
			self.update_plot()
			QMessageBox.information(self, "计算完成", f"{successful_models}个模型的计算已完成。")
		else:
			QMessageBox.warning(self, "计算失败", "所有选定模型的计算均未成功。")
	
	def update_plot (self):
		"""根据选择的热力学性质更新图表"""
		if not self.has_calculated:
			self.figure.clear();
			self.canvas.draw();
			return
		
		selected_text = self.property_combo.currentText()
		data_key = "activity" if "活度 (a)" in selected_text else "activity_coefficient"
		y_label = f"$a_{{{self.current_parameters['solute']}}}$" if data_key == "activity" else f"ln $\\gamma_{{{self.current_parameters['solute']}}}$"
		title_prop = f"活度 of {self.current_parameters['solute']}" if data_key == "activity" else f"活度系数 of {self.current_parameters['solute']}"
		
		results = self.calculation_results.get(data_key, {})
		models_plot = [self.model_checkboxes[k].text() for k, v in results.items() if v.get("value") is not None]
		values_plot = [v["value"] for v in results.values() if v.get("value") is not None]
		
		if not models_plot:
			self.figure.clear()
			self.canvas.draw()
			return
		
		self.figure.clear()
		ax = self.figure.add_subplot(111)
		bars = ax.bar(models_plot, values_plot, width=0.6)
		ax.set_ylabel(y_label, fontsize=11)
		ax.set_title(
			f"{title_prop} in {self.current_parameters['comp_input']} @ {self.current_parameters['temperature']:.0f}K",
			fontsize=10)
		plt.setp(ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")
		ax.grid(True, linestyle='--', alpha=0.6, axis='y')
		ax.bar_label(bars, fmt='%.4f', padding=3)
		self.figure.tight_layout()
		self.canvas.draw()
	
	def export_data (self):
		"""
		准备数据并调用通用的导出函数。
		"""
		if not self.has_calculated:
			QMessageBox.warning(self, "导出错误", "请先计算数据再导出。")
			return
		
		# 1. 准备 parameters 字典
		solute = self.current_parameters.get("solute", "i")
		parameters = {
			'合金组成': self.current_parameters.get("comp_input", ""),
			'溶质元素': solute,
			'溶剂元素': self.current_parameters.get("solvent", "j"),
			'温度 (K)': self.current_parameters.get("temperature", 0),
			'相态': self.current_parameters.get("phase_state", ""),
			'类型': self.current_parameters.get("order_degree", "")
		}
		
		# 2. 准备 header 列表
		header = [
			'外推模型',
			f'活度 (a_{solute})',
			f'活度系数 (ln γ_{solute})'
		]
		
		# 3. 准备 data (列表的列表)
		data_rows = []
		# 仅遍历已选中的模型
		for model_key, checkbox in self.model_checkboxes.items():
			if checkbox.isChecked():
				model_name = checkbox.text()
				# 安全地获取结果，如果计算失败则为 None
				activity_val = self.calculation_results["activity"].get(model_key, {}).get("value")
				coeff_val = self.calculation_results["activity_coefficient"].get(model_key, {}).get("value")
				data_rows.append([model_name, activity_val, coeff_val])
		
		# 4. 调用通用导出函数
		export_data_to_file(
				parent=self,
				parameters=parameters,
				header=header,
				data=data_rows,
				default_filename=f'{parameters["合金组成"]}_activity_data'
		)


# 主程序入口 (用于独立测试)
if __name__ == '__main__':
	app = QApplication(sys.argv)
	window = ActivityCoefficientWidget()
	window.setWindowTitle("活度与活度系数计算器")
	window.setGeometry(100, 100, 1200, 750)
	window.show()
	sys.exit(app.exec_())