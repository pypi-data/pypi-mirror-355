# setup.py

from setuptools import setup, find_packages

setup(
    name="kudet-arac-degerleme",
    version="0.1.0",
    description="Makine öğrenmesiyle ikinci el araç fiyat tahmini",
    author="kudetx",
    packages=find_packages(),
    install_requires=[
        "scikit-learn",
        "pandas",
        "numpy"
    ],
    python_requires=">=3.6",
)

