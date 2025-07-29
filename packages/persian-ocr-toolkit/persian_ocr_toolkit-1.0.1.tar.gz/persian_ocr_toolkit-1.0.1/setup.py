from setuptools import setup, find_packages
import os

# خواندن README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="persian-ocr-toolkit",
    version="1.0.1",
    author="MohammadHNdev",
    author_email="hosein.norozi434@gmail.com",
    description="کتابخانه حرفه‌ای OCR برای زبان فارسی",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MohammadHNdev/persian-ocr-toolkit",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Text Processing :: Linguistic",
        "Natural Language :: Persian",
    ],
    python_requires=">=3.8",
    install_requires=[
        'numpy',
        'opencv-python',
        'Pillow',
        'scikit-image',
        'pytesseract',
        'python-bidi',
        'arabic-reshaper',
        # 'tesseract-ocr' از اینجا حذف شد زیرا یک پکیج پایتون نیست و باید جداگانه نصب شود.
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.910",
            "pytest-cov>=2.12",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=0.5",
        ],
    },
    entry_points={
        "console_scripts": [
            "persian-ocr=persian_ocr.cli:main",
        ],
    },
    keywords="persian farsi ocr tesseract text-extraction pdf image-processing",
    project_urls={
        "Bug Reports": "https://github.com/MohammadHNdev/persian-ocr-toolkit/issues",
        "Source": "https://github.com/MohammadHNdev/persian-ocr-toolkit",
        "Documentation": "https://persian-ocr-toolkit.readthedocs.io/",
    },
    include_package_data=True,
    zip_safe=False,
)