from setuptools import setup, find_packages

# Чтение README.md с обработкой ошибок
try:
    with open("README.md", encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "A library for exam preparation with questions, tickets, and algorithms for mathematical analysis and computational methods."

setup(
    name="mathans",
    version="0.1.6",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "matplotlib>=3.4.0",
    ],
    author="Your Name",  # Замените на ваше имя
    author_email="your.email@example.com",  # Замените на ваш email
    description="A library for exam preparation with questions, tickets, and algorithms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",  # Пустая строка, так как нет репозитория
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
