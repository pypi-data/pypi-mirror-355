from setuptools import setup, find_packages

setup(
    name="geometry-inetsmol",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.7",
    author="iNetsmol",
    description="Вычисление площади круга и треугольника",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
