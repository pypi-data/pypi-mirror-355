# setup.py
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ru-python-kod",  # ИМЯ ПАКЕТА (ДЛЯ pip install)
    version="0.1.1",
    author="fan",  # Замените на свое имя
    description="Библиотека для Python на русском языке",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(), # Автоматический поиск пакетов
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)