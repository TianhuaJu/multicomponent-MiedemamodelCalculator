import csv
import traceback
from PyQt5.QtWidgets import QFileDialog, QMessageBox


def export_data_to_file (parent, parameters: dict, header: list, data: list, default_filename='exported_data'):
	"""
	一个通用的导出函数，可将数据保存为CSV或Excel文件。

	Args:
		parent (QWidget): 调用此函数的父窗口，用于QFileDialog的定位。
		parameters (dict): 一个包含计算参数的字典，将显示在数据表格的上方。
		header (list): 数据表格的表头（列名）列表。
		data (list of lists): 包含数据的二维列表，每个子列表代表一行。
		default_filename (str): 文件保存对话框中默认显示的文件名。
	"""
	# 弹出文件保存对话框
	file_path, selected_filter = QFileDialog.getSaveFileName(
			parent,
			"导出数据",
			default_filename,
			"Excel 文件 (*.xlsx);;CSV 文件 (*.csv);;所有文件 (*.*)"
	)
	
	if not file_path:
		return  # 用户取消了操作
	
	try:
		# 根据用户选择的文件类型调用相应的写入函数
		if 'xlsx' in selected_filter or file_path.lower().endswith('.xlsx'):
			if not file_path.lower().endswith('.xlsx'):
				file_path += '.xlsx'
			_export_to_excel(file_path, parameters, header, data)
		else:
			if not file_path.lower().endswith('.csv'):
				file_path += '.csv'
			_export_to_csv(file_path, parameters, header, data)
		
		QMessageBox.information(parent, "导出成功", f"数据已成功导出到:\n{file_path}")
	
	except ImportError:
		QMessageBox.warning(parent, "缺少依赖",
		                    "导出为Excel需要`xlsxwriter`模块。\n请通过 'pip install xlsxwriter' 安装。")
	except Exception as e:
		QMessageBox.critical(parent, "导出错误", f"导出数据时发生错误: {str(e)}\n\n{traceback.format_exc()}")


def _export_to_csv (file_path, parameters, header, data):
	"""将数据写入CSV文件"""
	with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
		writer = csv.writer(csvfile)
		
		# 写入参数
		writer.writerow(['计算参数'])
		for key, value in parameters.items():
			writer.writerow([key, value])
		writer.writerow([])  # 空行分隔
		
		# 写入表头和数据
		writer.writerow(header)
		writer.writerows(data)


def _export_to_excel (file_path, parameters, header, data):
	"""将数据写入Excel文件"""
	import xlsxwriter  # 在函数内部导入，以处理ImportError
	
	workbook = xlsxwriter.Workbook(file_path)
	worksheet = workbook.add_worksheet('计算结果')
	
	# 定义格式
	header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1})
	param_header_format = workbook.add_format({'bold': True})
	data_format = workbook.add_format({'num_format': '0.000000', 'align': 'center'})
	
	# 写入参数
	row = 0
	worksheet.write(row, 0, '计算参数', param_header_format)
	row += 1
	for key, value in parameters.items():
		worksheet.write(row, 0, key)
		worksheet.write(row, 1, str(value))
		row += 1
	
	row += 1  # 空行分隔
	
	# 写入表头和数据
	worksheet.write_row(row, 0, header, header_format)
	row += 1
	for r_idx, row_data in enumerate(data):
		for c_idx, cell_data in enumerate(row_data):
			try:
				# 尝试将数据转为浮点数写入，否则作为字符串写入
				worksheet.write(row + r_idx, c_idx, float(cell_data), data_format)
			except (ValueError, TypeError):
				worksheet.write(row + r_idx, c_idx, cell_data)
	
	# 自动调整列宽
	for i, col in enumerate(header):
		worksheet.set_column(i, i, max(len(col), 15))
	
	workbook.close()