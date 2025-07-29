from setuptools import setup, find_packages
import os

# Đọc README
def read_readme():
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return "Công cụ phát hiện và cắt các hàng từ bảng trong ảnh"

setup(
    name="detect-row",
    version="1.0.7",
    packages=find_packages(),
    include_package_data=True,
    
    install_requires=[
        "numpy>=1.19.0",
        "opencv-python>=4.5.0",
        "matplotlib>=3.4.0",
        "pytesseract>=0.3.8",
        "Pillow>=8.2.0",
    ],
    
    # Entry points cho command line
    entry_points={
        'console_scripts': [
            'detect-row-basic=detect_row.basic_row_extractor:main',
            'detect-row-advanced=detect_row.advanced_row_extractor:main',
            'detect-row-ocr=detect_row.tesseract_ocr_extractor:main',
            'detect-row-table=detect_row.advanced_table_extractor:main',
        ],
    },
    
    # Metadata
    author="Row Detection Team",
    author_email="detect.row.team@gmail.com",
    description="Công cụ phát hiện và cắt các hàng từ bảng trong ảnh với OCR",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    keywords="computer vision, table extraction, row detection, OCR, vietnamese, image processing",
    url="https://github.com/detectrow/detect-row",
    project_urls={
        "Bug Reports": "https://github.com/detectrow/detect-row/issues",
        "Source": "https://github.com/detectrow/detect-row",
        "Documentation": "https://github.com/detectrow/detect-row/blob/main/README.md",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    zip_safe=False,
)
