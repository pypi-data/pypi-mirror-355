from setuptools import setup, find_packages

setup(
    name="constants_and_tools",
    version="1.1.0",
    author="Aletheia_corp",
    author_email="dsarabiatorres@gmail.com",
    description="Librería para desarrollo rápido y debug",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/aletheIA-Corp/constants_and_tools",
    packages=find_packages(),  # Busca automáticamente todos los paquetes
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "colorama==0.4.6",
        "openpyxl==3.1.5",
        "pandas==2.2.3",
        "pyarrow==19.0.1",
        "polars==1.30.0",
        "tabulate==0.9.0"
    ],
    python_requires=">=3.10",
)
