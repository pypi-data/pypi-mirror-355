import sys
import os
from pathlib import Path

current_dir = str(Path(__file__).resolve().parent)
print(f"✅ 当前目录: {current_dir}")
print(f"📁 目录内容: {os.listdir(current_dir)}")

sys.path.insert(0, current_dir)
print(f"🔍 sys.path列表: {sys.path}")

try:
    import before
    print("✔️ 模块导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {str(e)}")
    print("💡 请检查：")
    print("1. 文件名是否确为 before.py")
    print("2. 文件权限是否可读")
    print("3. Python版本是否匹配")
import before