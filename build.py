import PyInstaller.__main__
import os
import sys

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 根据操作系统选择正确的路径分隔符和文件扩展名
separator = ';' if sys.platform.startswith('win') else ':'
exe_name = '预案管理系统.exe' if sys.platform.startswith('win') else '预案管理系统'

PyInstaller.__main__.run([
    'app.py',  # 主程序文件
    f'--name={exe_name}',  # 生成的exe名称
    '--onefile',  # 打包成单个文件
    '--windowed',  # 使用窗口模式（不显示控制台）
    f'--add-data=templates{separator}templates',  # 添加模板文件夹
    f'--add-data=static{separator}static',     # 添加静态文件夹
    '--clean',  # 清理临时文件
    '--noconfirm',  # 不询问确认
]) 