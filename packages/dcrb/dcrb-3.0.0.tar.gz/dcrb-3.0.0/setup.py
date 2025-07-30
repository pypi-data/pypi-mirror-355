# setup.py（完整）
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="dcrb",                     # 套件名稱
    version="3.0.0",
    description="Discord Remote Bot by H.L.2025",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="H.L.2025",
    author_email="wum85352@gmail.com",
    url="https://github.com/wum85352/dcrb",
    packages=find_packages(),
    package_data={ "": ["scripts/*.exe"] },
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "dcrb = dcrb.launcher:main",   # 安裝後指令叫 dcrb
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.6",
)
