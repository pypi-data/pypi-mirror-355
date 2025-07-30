from setuptools import setup, find_packages
import os

def find_pyd_files(root):
    pyd_files = []
    for path, _, files in os.walk(os.path.join("src", root)):
        for name in files:
            if name.endswith(".pyd"):
                full_path = os.path.join(path, name)
                pyd_files.append(full_path.replace("src/", "").replace(os.sep, "/"))
    return {root: pyd_files}

setup(
    name="encryptionYG",
    version="0.6",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    package_data=find_pyd_files("encryptionYG"),  # 改为明确指定包名
    include_package_data=True,
    zip_safe=False,  # 必须关闭压缩模式
)
# python setup.py sdist bdist_wheel
# twine upload dist/*