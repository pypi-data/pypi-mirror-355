"""
Persian OCR Toolkit - A professional OCR library for Persian/Farsi text

این کتابخانه امکانات کاملی برای استخراج متن فارسی از تصاویر و PDF ها فراهم می‌کند.

Example:
    >>> from persian_ocr import PersianOCR
    >>> ocr = PersianOCR()
    >>> result = ocr.extract_from_pdf("document.pdf")
    >>> print(f"استخراج شد: {result.total_characters} کاراکتر")
"""

__version__ = "1.0.0"
__author__ = "MohammadHNdev"
__email__ = "hosein.norozi434@gmail.com"
__license__ = "MIT"

# اصلی imports
from .core import PersianOCR, OCRResult, PageResult
from .config import OCRConfig, ProcessingMethod, OCRMode, get_preset, PRESETS

# توابع سطح بالا
from .core import extract_text_from_image, extract_text_from_pdf

# تنظیمات لاگ
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    # کلاس‌های اصلی
    'PersianOCR',
    'OCRResult', 
    'PageResult',
    
    # تنظیمات
    'OCRConfig',
    'ProcessingMethod',
    'OCRMode',
    'get_preset',
    'PRESETS',
    
    # توابع سطح بالا
    'extract_text_from_image',
    'extract_text_from_pdf',
]

# اطلاعات پکیج
def get_version():
    """دریافت نسخه کتابخانه"""
    return __version__

def get_info():
    """دریافت اطلاعات کامل کتابخانه"""
    return {
        'name': 'Persian OCR Toolkit',
        'version': __version__,
        'author': __author__,
        'email': __email__,
        'license': __license__,
        'description': 'Professional OCR library for Persian/Farsi text extraction',
        'homepage': 'https://github.com/yourusername/persian-ocr-toolkit',
        'documentation': 'https://persian-ocr-toolkit.readthedocs.io/',
    }