
"""
Utility functions for Persian OCR Toolkit
"""

import os
import logging
from pathlib import Path
from typing import List, Union


def setup_logging(level: str = "INFO") -> logging.Logger:
    """راه‌اندازی لاگ"""
    logger = logging.getLogger("persian_ocr")
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    logger.setLevel(getattr(logging, level.upper()))
    return logger


def validate_file(file_path: Union[str, Path], 
                 allowed_extensions: List[str]) -> None:
    """بررسی اعتبار فایل"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"فایل یافت نشد: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"مسیر به فایل اشاره نمی‌کند: {file_path}")
    
    if file_path.suffix.lower() not in allowed_extensions:
        raise ValueError(
            f"فرمت فایل پشتیبانی نمی‌شود. "
            f"فرمت‌های مجاز: {allowed_extensions}"
        )


def estimate_processing_time(pdf_path: Union[str, Path]) -> float:
    """تخمین زمان پردازش PDF"""
    try:
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        # تخمین ساده: 1MB ≈ 1 دقیقه
        estimated_minutes = file_size_mb * 0.8
        return max(estimated_minutes, 1.0)  # حداقل 1 دقیقه
    except:
        return 5.0  # تخمین پیش‌فرض


def format_time(seconds: float) -> str:
    """فرمت زمان به صورت خوانا"""
    if seconds < 60:
        return f"{seconds:.1f} ثانیه"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} دقیقه"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} ساعت"


def get_file_info(file_path: Union[str, Path]) -> dict:
    """دریافت اطلاعات فایل"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {"exists": False}
    
    stat = file_path.stat()
    
    return {
        "exists": True,
        "name": file_path.name,
        "size_bytes": stat.st_size,
        "size_mb": stat.st_size / (1024 * 1024),
        "extension": file_path.suffix,
        "modified": stat.st_mtime
    }


def clean_text(text: str) -> str:
    """پاکسازی متن استخراج شده"""
    if not text:
        return ""
    
    # حذف خطوط خالی اضافی
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def calculate_accuracy_estimate(text: str) -> float:
    """تخمین دقت OCR"""
    if not text:
        return 0.0
    
    # محاسبه ساده بر اساس کاراکترهای معتبر
    total_chars = len(text)
    valid_chars = sum(1 for c in text if c.isalnum() or c.isspace() or c in '.,;:!?()[]{}')
    
    if total_chars == 0:
        return 0.0
    
    return min((valid_chars / total_chars) * 100, 100.0)
=======
"""
Utility functions for Persian OCR Toolkit
"""

import os
import logging
from pathlib import Path
from typing import List, Union


def setup_logging(level: str = "INFO") -> logging.Logger:
    """راه‌اندازی لاگ"""
    logger = logging.getLogger("persian_ocr")
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    logger.setLevel(getattr(logging, level.upper()))
    return logger


def validate_file(file_path: Union[str, Path], 
                 allowed_extensions: List[str]) -> None:
    """بررسی اعتبار فایل"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"فایل یافت نشد: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"مسیر به فایل اشاره نمی‌کند: {file_path}")
    
    if file_path.suffix.lower() not in allowed_extensions:
        raise ValueError(
            f"فرمت فایل پشتیبانی نمی‌شود. "
            f"فرمت‌های مجاز: {allowed_extensions}"
        )


def estimate_processing_time(pdf_path: Union[str, Path]) -> float:
    """تخمین زمان پردازش PDF"""
    try:
        file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        # تخمین ساده: 1MB ≈ 1 دقیقه
        estimated_minutes = file_size_mb * 0.8
        return max(estimated_minutes, 1.0)  # حداقل 1 دقیقه
    except:
        return 5.0  # تخمین پیش‌فرض


def format_time(seconds: float) -> str:
    """فرمت زمان به صورت خوانا"""
    if seconds < 60:
        return f"{seconds:.1f} ثانیه"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} دقیقه"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} ساعت"


def get_file_info(file_path: Union[str, Path]) -> dict:
    """دریافت اطلاعات فایل"""
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {"exists": False}
    
    stat = file_path.stat()
    
    return {
        "exists": True,
        "name": file_path.name,
        "size_bytes": stat.st_size,
        "size_mb": stat.st_size / (1024 * 1024),
        "extension": file_path.suffix,
        "modified": stat.st_mtime
    }


def clean_text(text: str) -> str:
    """پاکسازی متن استخراج شده"""
    if not text:
        return ""
    
    # حذف خطوط خالی اضافی
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def calculate_accuracy_estimate(text: str) -> float:
    """تخمین دقت OCR"""
    if not text:
        return 0.0
    
    # محاسبه ساده بر اساس کاراکترهای معتبر
    total_chars = len(text)
    valid_chars = sum(1 for c in text if c.isalnum() or c.isspace() or c in '.,;:!?()[]{}')
    
    if total_chars == 0:
        return 0.0
    
    return min((valid_chars / total_chars) * 100, 100.0)
>>>>>>> db21877dee46cce8b280ee1697fe638be51800de
