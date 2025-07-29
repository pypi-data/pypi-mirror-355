from setuptools import setup, find_packages
import os

# خواندن README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# وابستگی‌های اصلی پروژه (به جای خواندن از requirements.txt)
install_requires = [
    "Pillow>=10.0.0",
    "pytesseract>=0.3.10",
    "pdf2image>=1.16.0",
    # هر کتابخانه دیگری که پروژه شما به آن نیاز دارد را اینجا اضافه کنید
    # مثال: "numpy>=1.20.0", "opencv-python>=4.5.0"
]

setup(
    name="persian-ocr-toolkit",
    version="1.0.0",
    author="MohammadHNdev", # نام کاربری گیت‌هاب یا نام کامل شما
    author_email="hosein.norozi434@gmail.com", # ایمیل شما
    description="Professional OCR library for Persian/Farsi text extraction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MohammadHNdev/persian-ocr-toolkit", # لینک مخزن گیت‌هاب شما
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
    install_requires=install_requires, # حالا از لیست بالا استفاده می‌کند
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