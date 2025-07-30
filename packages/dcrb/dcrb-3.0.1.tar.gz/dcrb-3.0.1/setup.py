# setup.py
from setuptools import setup, find_packages

setup(
    name="dcrb",
    version="3.0.1",
    description="透過 pip 安裝並執行 dcrb.exe 的套件",
    packages=find_packages(),   # 會自動找到 dcrb/ 這個套件
    package_data={
        "dcrb": ["dcrb.exe"],   # 把 dcrb.exe 放到 dcrb 套件中
    },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "dcrb = dcrb.launcher:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.6",
)
