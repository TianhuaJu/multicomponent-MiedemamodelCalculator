# MiedemamodelApp.py
import os
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget

# ------------------- 步骤 3：导入新的模块化Widget -------------------
# 假设您的文件结构如指南中所示
from GUI.SingleCalculationWidget import SingleCalculationWidget
from GUI.CompositionVariationWidget import CompositionVariationWidget
from GUI.TemperatureVariationWidget import TemperatureVariationWidget
from GUI.ActivityCoefficientWidget import ActivityCoefficientWidget
from GUI.ActivityCompositionVariationWidget import ActivityCompositionVariationWidget
from GUI.ActivityTemperatureVariationWidget import ActivityTemperatureVariationWidget


def resource_path (relative_path):
	""" 获取资源的绝对路径 """
	if hasattr(sys, '_MEIPASS'):
		base_path = sys._MEIPASS
	else:
		base_path = os.path.abspath(".")
	return os.path.join(base_path, relative_path)


class MiedemaModelUI(QMainWindow):
	"""
	Miedema模型计算器的主应用窗口。
	这个类现在只负责创建窗口框架和组装从外部导入的各个功能模块。
	"""
	
	def __init__ (self):
		super().__init__()
		# 假设图标文件在项目根目录
		self.icon_path = resource_path("app_icon.ico")
		self.init_ui()
		self.setWindowIcon(QIcon(self.icon_path))
	
	def init_ui (self):
		"""初始化UI组件"""
		self.setWindowTitle("Multi-Component Miedema Model Calculator")
		self.setGeometry(100, 100, 1200, 800)  # 设置一个合适的窗口大小
		
		self.setFont(QFont("Arial", 11))
		
		central_widget = QWidget()
		self.setCentralWidget(central_widget)
		main_layout = QVBoxLayout(central_widget)
		
		# 创建主选项卡小部件
		main_tabs = QTabWidget()
		main_tabs.setFont(QFont("Arial", 12))
		
		# ------------------- 步骤 4：实例化并组装所有Tabs -------------------
		
		# 1. 实例化从外部文件导入的各个功能Widget
		single_calc_widget = SingleCalculationWidget(self)
		comp_variation_widget = CompositionVariationWidget(self)
		temp_variation_widget = TemperatureVariationWidget(self)
		activity_widget = ActivityCoefficientWidget(self)
		activity_comp_variation_widget = ActivityCompositionVariationWidget(self)
		activity_tem_variation_widget = ActivityTemperatureVariationWidget(self)
		
		# 2. 将实例化的Widget作为独立的选项卡添加到主界面
		main_tabs.addTab(single_calc_widget, "Single Calculation")
		main_tabs.addTab(comp_variation_widget, "Composition Variation")
		main_tabs.addTab(temp_variation_widget, "Temperature Variation")
		main_tabs.addTab(activity_widget, "Activity / Coefficient")
		main_tabs.addTab(activity_comp_variation_widget, "Activity vs Composition")
		main_tabs.addTab(activity_tem_variation_widget, "Activity vs Temperature")
		
		# 将选项卡控件添加到主布局
		main_layout.addWidget(main_tabs)
		
		# 全局样式表保持不变
		self.apply_stylesheet()
	
	def apply_stylesheet (self):
		"""应用全局样式表以统一外观"""
		self.setStyleSheet("""
            QGroupBox {
                font-size: 12pt; font-weight: bold; border: 1px solid #AAAAAA;
                border-radius: 5px; margin-top: 15px; padding-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; subcontrol-position: top left;
                padding: 0 5px; left: 10px;
            }
            QTabWidget::pane {
                border: 1px solid #AAAAAA; border-radius: 5px;
            }
            QTabBar::tab {
                background: #f0f0f0; border: 1px solid #AAAAAA; border-bottom: none;
                border-top-left-radius: 4px; border-top-right-radius: 4px;
                padding: 8px 15px;
            }
            QTabBar::tab:selected {
                background: white; margin-bottom: -1px;
            }
        """)


# --- 主程序入口 ---
if __name__ == "__main__":
	app = QApplication(sys.argv)
	window = MiedemaModelUI()
	window.show()
	sys.exit(app.exec_())