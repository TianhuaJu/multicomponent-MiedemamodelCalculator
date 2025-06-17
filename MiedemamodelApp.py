import os
import sys
from typing import Callable

from PyQt5.QtGui import QFont
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget)

from GUI.CompositionVariationWidget import CompositionVariationWidget
from GUI.SingleCalculationWidget import SingleCalculationWidget
from GUI.TemperatureVariationWidget import TemperatureVariationWidget

# Define the contribution model function type
ContributionModelFunc = Callable[[str, str, str, float, str, str], float]

# 获取脚本所在目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 拼接图标文件路径
icon_path = os.path.join(current_dir, "app_icon.ico")
# 添加这段获取正确路径的代码
def resource_path (relative_path):
	"""获取资源的绝对路径"""
	if hasattr(sys, '_MEIPASS'):
		# PyInstaller 创建临时文件夹并将路径存储在 _MEIPASS 中
		base_path = sys._MEIPASS
	else:
		base_path = os.path.abspath(".")
	return os.path.join(base_path, relative_path)


#父窗口
class MiedemaModelUI(QMainWindow):
	"""Main application window for Miedema model calculations"""
	
	def __init__ (self):
		super().__init__()
		self.init_ui()
		self.icon_path = resource_path("app_icon.ico")
		self.init_ui()
		self.setWindowIcon(QIcon(self.icon_path))
	
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
		self.setCentralWidget(central_widget)
		main_layout = QVBoxLayout(central_widget)
		
		main_tabs = QTabWidget()
		main_tabs.setFont(QFont("Arial", 12))
		main_layout.setSpacing(15)  # Increase spacing between elements
		
		single_calc_widget = SingleCalculationWidget(self)
		comp_variation_widget = CompositionVariationWidget(self)
		temp_variation_widget = TemperatureVariationWidget(self)
		
		main_tabs.addTab(single_calc_widget, "Single Calculation")
		main_tabs.addTab(comp_variation_widget, "Composition Variation")
		main_tabs.addTab(temp_variation_widget, "Temperature Variation")
		
		main_layout.addWidget(main_tabs)
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
	


if __name__ == "__main__":
	# Create and show application
	app = QApplication(sys.argv)
	app.setWindowIcon(QIcon(resource_path(icon_path)))
	
	window = MiedemaModelUI()
	window.show()
	sys.exit(app.exec_())
