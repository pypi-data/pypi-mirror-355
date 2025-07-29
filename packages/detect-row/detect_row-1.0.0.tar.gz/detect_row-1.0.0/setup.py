from setuptools import setup, find_packages
import os

# Đọc README.md với encoding UTF-8
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="detect-row",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.19.0",
        "opencv-python>=4.5.0",
        "matplotlib>=3.4.0",
        "pytesseract>=0.3.8",
        "Pillow>=8.2.0",
    ],
    
    # Metadata
    author="KiemPhieu Team",
    author_email="shumi2011@gmail.com",
    description="Thư viện phát hiện và cắt các hàng từ bảng trong ảnh, với khả năng tích hợp OCR",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="computer vision, table extraction, row detection, OCR, vietnamese",
    url="https://github.com/CoderTeam20266/detect_row",
    project_urls={
        "Bug Tracker": "https://github.com/CoderTeam20266/detect_row/issues",
        "Documentation": "https://github.com/CoderTeam20266/detect_row/wiki",
        "Source Code": "https://github.com/CoderTeam20266/detect_row",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Image Processing",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.6",
    include_package_data=True,
    package_data={
        "detect_row": ["*.txt", "*.md"],
    },
    entry_points={
        "console_scripts": [
            "detect-row=detect_row.cli:main",
        ],
    },
)
