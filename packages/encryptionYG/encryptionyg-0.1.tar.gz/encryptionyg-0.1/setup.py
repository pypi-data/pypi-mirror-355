from setuptools import setup, find_packages
from setuptools.command.install import install
import os

# 自动包含所有pyd文件
package_data = {}
start_dir = os.getcwd()
for root, dirs, files in os.walk("src"):
    rel_dir = os.path.relpath(root, start_dir)
    pyd_files = [f for f in files if f.endswith('.pyd')]
    if pyd_files:
        package_data.setdefault(rel_dir.replace(os.sep, "."), []).extend(pyd_files)

setup(
    name="encryptionYG",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data=package_data,
    include_package_data=True,
    install_requires=[
        # 添加你的依赖项
    ],
)