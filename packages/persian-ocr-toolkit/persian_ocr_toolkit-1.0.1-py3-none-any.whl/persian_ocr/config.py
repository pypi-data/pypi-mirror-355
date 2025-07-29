
"""
Configuration module for Persian OCR Toolkit
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any


class ProcessingMethod(Enum):
    """روش‌های پیش‌پردازش تصویر"""
    STANDARD = "standard"
    ADVANCED = "advanced"
    DOCUMENT = "document"
    HIGH_QUALITY = "high_quality"


class OCRMode(Enum):
    """حالت‌های OCR"""
    FAST = "fast"
    ACCURATE = "accurate"
    MIXED = "mixed"
    SINGLE_BLOCK = "single_block"


@dataclass
class OCRConfig:
    """تنظیمات OCR"""
    
    # تنظیمات عمومی
    language: str = "fas"
    dpi: int = 300
    max_workers: int = 3
    
    # تنظیمات OCR
    ocr_mode: OCRMode = OCRMode.ACCURATE
    psm: int = 3  # Page Segmentation Mode
    oem: int = 3  # OCR Engine Mode
    
    # تنظیمات پیش‌پردازش
    scale_factor: float = 2.0
    enhance_contrast: bool = True
    contrast_factor: float = 2.0
    remove_noise: bool = True
    
    # تنظیمات پیشرفته
    timeout_per_page: int = 30
    batch_size: int = 15
    quality: int = 95
    
    def get_tesseract_config(self) -> str:
        """تولید کانفیگ tesseract"""
        configs = {
            OCRMode.FAST: f"--psm {self.psm} --oem {self.oem}",
            OCRMode.ACCURATE: f"--psm {self.psm} --oem {self.oem}",
            OCRMode.MIXED: f"--psm 4 --oem 1",
            OCRMode.SINGLE_BLOCK: f"--psm 6 --oem {self.oem}"
        }
        return configs.get(self.ocr_mode, configs[OCRMode.ACCURATE])
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            "language": self.language,
            "dpi": self.dpi,
            "max_workers": self.max_workers,
            "ocr_mode": self.ocr_mode.value,
            "psm": self.psm,
            "oem": self.oem,
            "scale_factor": self.scale_factor,
            "enhance_contrast": self.enhance_contrast,
            "contrast_factor": self.contrast_factor,
            "remove_noise": self.remove_noise,
            "timeout_per_page": self.timeout_per_page,
            "batch_size": self.batch_size,
            "quality": self.quality
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'OCRConfig':
        """ساخت از دیکشنری"""
        config = cls()
        for key, value in config_dict.items():
            if hasattr(config, key):
                if key == 'ocr_mode':
                    setattr(config, key, OCRMode(value))
                else:
                    setattr(config, key, value)
        return config


# پیش‌تنظیمات آماده
PRESETS = {
    "fast": OCRConfig(
        dpi=200,
        max_workers=4,
        ocr_mode=OCRMode.FAST,
        scale_factor=1.5,
        contrast_factor=1.5
    ),
    
    "balanced": OCRConfig(
        dpi=300,
        max_workers=3,
        ocr_mode=OCRMode.ACCURATE,
        scale_factor=2.0,
        contrast_factor=2.0
    ),
    
    "high_quality": OCRConfig(
        dpi=400,
        max_workers=2,
        ocr_mode=OCRMode.ACCURATE,
        scale_factor=2.5,
        contrast_factor=2.5,
        timeout_per_page=60
    ),
    
    "colab_optimized": OCRConfig(
        dpi=300,
        max_workers=3,
        ocr_mode=OCRMode.ACCURATE,
        scale_factor=2.0,
        batch_size=15,
        timeout_per_page=30
    )
}


def get_preset(name: str) -> OCRConfig:
    """دریافت پیش‌تنظیم"""
    if name not in PRESETS:
        raise ValueError(f"Preset '{name}' not found. Available: {list(PRESETS.keys())}")
    return PRESETS[name]

"""
Configuration module for Persian OCR Toolkit
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any


class ProcessingMethod(Enum):
    """روش‌های پیش‌پردازش تصویر"""
    STANDARD = "standard"
    ADVANCED = "advanced"
    DOCUMENT = "document"
    HIGH_QUALITY = "high_quality"


class OCRMode(Enum):
    """حالت‌های OCR"""
    FAST = "fast"
    ACCURATE = "accurate"
    MIXED = "mixed"
    SINGLE_BLOCK = "single_block"


@dataclass
class OCRConfig:
    """تنظیمات OCR"""
    
    # تنظیمات عمومی
    language: str = "fas"
    dpi: int = 300
    max_workers: int = 3
    
    # تنظیمات OCR
    ocr_mode: OCRMode = OCRMode.ACCURATE
    psm: int = 3  # Page Segmentation Mode
    oem: int = 3  # OCR Engine Mode
    
    # تنظیمات پیش‌پردازش
    scale_factor: float = 2.0
    enhance_contrast: bool = True
    contrast_factor: float = 2.0
    remove_noise: bool = True
    
    # تنظیمات پیشرفته
    timeout_per_page: int = 30
    batch_size: int = 15
    quality: int = 95
    
    def get_tesseract_config(self) -> str:
        """تولید کانفیگ tesseract"""
        configs = {
            OCRMode.FAST: f"--psm {self.psm} --oem {self.oem}",
            OCRMode.ACCURATE: f"--psm {self.psm} --oem {self.oem}",
            OCRMode.MIXED: f"--psm 4 --oem 1",
            OCRMode.SINGLE_BLOCK: f"--psm 6 --oem {self.oem}"
        }
        return configs.get(self.ocr_mode, configs[OCRMode.ACCURATE])
    
    def to_dict(self) -> Dict[str, Any]:
        """تبدیل به دیکشنری"""
        return {
            "language": self.language,
            "dpi": self.dpi,
            "max_workers": self.max_workers,
            "ocr_mode": self.ocr_mode.value,
            "psm": self.psm,
            "oem": self.oem,
            "scale_factor": self.scale_factor,
            "enhance_contrast": self.enhance_contrast,
            "contrast_factor": self.contrast_factor,
            "remove_noise": self.remove_noise,
            "timeout_per_page": self.timeout_per_page,
            "batch_size": self.batch_size,
            "quality": self.quality
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'OCRConfig':
        """ساخت از دیکشنری"""
        config = cls()
        for key, value in config_dict.items():
            if hasattr(config, key):
                if key == 'ocr_mode':
                    setattr(config, key, OCRMode(value))
                else:
                    setattr(config, key, value)
        return config


# پیش‌تنظیمات آماده
PRESETS = {
    "fast": OCRConfig(
        dpi=200,
        max_workers=4,
        ocr_mode=OCRMode.FAST,
        scale_factor=1.5,
        contrast_factor=1.5
    ),
    
    "balanced": OCRConfig(
        dpi=300,
        max_workers=3,
        ocr_mode=OCRMode.ACCURATE,
        scale_factor=2.0,
        contrast_factor=2.0
    ),
    
    "high_quality": OCRConfig(
        dpi=400,
        max_workers=2,
        ocr_mode=OCRMode.ACCURATE,
        scale_factor=2.5,
        contrast_factor=2.5,
        timeout_per_page=60
    ),
    
    "colab_optimized": OCRConfig(
        dpi=300,
        max_workers=3,
        ocr_mode=OCRMode.ACCURATE,
        scale_factor=2.0,
        batch_size=15,
        timeout_per_page=30
    )
}


def get_preset(name: str) -> OCRConfig:
    """دریافت پیش‌تنظیم"""
    if name not in PRESETS:
        raise ValueError(f"Preset '{name}' not found. Available: {list(PRESETS.keys())}")
    return PRESETS[name]

