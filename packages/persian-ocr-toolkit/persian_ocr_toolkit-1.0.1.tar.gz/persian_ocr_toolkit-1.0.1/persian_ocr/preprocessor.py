
"""
Image preprocessing module for Persian OCR Toolkit
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Union
from .config import ProcessingMethod


class ImagePreprocessor:
    """کلاس پیش‌پردازش تصویر"""
    
    def __init__(self, config=None):
        self.config = config
    
    def process(self, image: Image.Image, method: ProcessingMethod) -> Image.Image:
        """پیش‌پردازش تصویر با روش انتخابی"""
        
        if method == ProcessingMethod.STANDARD:
            return self._standard_processing(image)
        elif method == ProcessingMethod.ADVANCED:
            return self._advanced_processing(image)
        elif method == ProcessingMethod.DOCUMENT:
            return self._document_processing(image)
        elif method == ProcessingMethod.HIGH_QUALITY:
            return self._high_quality_processing(image)
        else:
            return self._standard_processing(image)
    
    def _standard_processing(self, img: Image.Image) -> Image.Image:
        """پردازش استاندارد"""
        # تبدیل به grayscale
        if img.mode != 'L':
            img = img.convert('L')
        
        # افزایش کنتراست
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        # افزایش وضوح
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.2)
        
        return img
    
    def _advanced_processing(self, img: Image.Image) -> Image.Image:
        """پردازش پیشرفته"""
        # تبدیل به numpy array
        img_array = np.array(img.convert('L'))
        
        # حذف نویز
        img_array = cv2.medianBlur(img_array, 3)
        
        # بهبود کنتراست تطبیقی
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img_array = clahe.apply(img_array)
        
        return Image.fromarray(img_array)
    
    def _document_processing(self, img: Image.Image) -> Image.Image:
        """پردازش مخصوص اسناد"""
        img_array = np.array(img.convert('L'))
        
        # فیلتر گوسی
        img_array = cv2.GaussianBlur(img_array, (1, 1), 0)
        
        # آستانه‌گذاری تطبیقی
        img_array = cv2.adaptiveThreshold(
            img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return Image.fromarray(img_array)
    
    def _high_quality_processing(self, img: Image.Image) -> Image.Image:
        """پردازش با کیفیت بالا"""
        # ترکیب چندین روش
        img = self._advanced_processing(img)
        
        # تبدیل مجدد به numpy
        img_array = np.array(img)
        
        # فیلتر bilateral
        img_array = cv2.bilateralFilter(img_array, 9, 75, 75)
        
        return Image.fromarray(img_array)

"""
Image preprocessing module for Persian OCR Toolkit
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from typing import Union
from .config import ProcessingMethod


class ImagePreprocessor:
    """کلاس پیش‌پردازش تصویر"""
    
    def __init__(self, config=None):
        self.config = config
    
    def process(self, image: Image.Image, method: ProcessingMethod) -> Image.Image:
        """پیش‌پردازش تصویر با روش انتخابی"""
        
        if method == ProcessingMethod.STANDARD:
            return self._standard_processing(image)
        elif method == ProcessingMethod.ADVANCED:
            return self._advanced_processing(image)
        elif method == ProcessingMethod.DOCUMENT:
            return self._document_processing(image)
        elif method == ProcessingMethod.HIGH_QUALITY:
            return self._high_quality_processing(image)
        else:
            return self._standard_processing(image)
    
    def _standard_processing(self, img: Image.Image) -> Image.Image:
        """پردازش استاندارد"""
        # تبدیل به grayscale
        if img.mode != 'L':
            img = img.convert('L')
        
        # افزایش کنتراست
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        # افزایش وضوح
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.2)
        
        return img
    
    def _advanced_processing(self, img: Image.Image) -> Image.Image:
        """پردازش پیشرفته"""
        # تبدیل به numpy array
        img_array = np.array(img.convert('L'))
        
        # حذف نویز
        img_array = cv2.medianBlur(img_array, 3)
        
        # بهبود کنتراست تطبیقی
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img_array = clahe.apply(img_array)
        
        return Image.fromarray(img_array)
    
    def _document_processing(self, img: Image.Image) -> Image.Image:
        """پردازش مخصوص اسناد"""
        img_array = np.array(img.convert('L'))
        
        # فیلتر گوسی
        img_array = cv2.GaussianBlur(img_array, (1, 1), 0)
        
        # آستانه‌گذاری تطبیقی
        img_array = cv2.adaptiveThreshold(
            img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return Image.fromarray(img_array)
    
    def _high_quality_processing(self, img: Image.Image) -> Image.Image:
        """پردازش با کیفیت بالا"""
        # ترکیب چندین روش
        img = self._advanced_processing(img)
        
        # تبدیل مجدد به numpy
        img_array = np.array(img)
        
        # فیلتر bilateral
        img_array = cv2.bilateralFilter(img_array, 9, 75, 75)
        
        return Image.fromarray(img_array)

