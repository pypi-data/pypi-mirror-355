import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前文件所在目录的绝对路径
sys.path.append(current_dir)  # 添加到Python路径
import before