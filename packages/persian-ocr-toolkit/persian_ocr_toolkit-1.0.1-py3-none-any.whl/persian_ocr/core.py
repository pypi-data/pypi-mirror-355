"""
Persian OCR Toolkit - Core Module
A professional OCR library for Persian/Farsi text extraction

Author: YourName
License: MIT
Version: 1.0.0
"""

import os
import time
import logging
from typing import List, Dict, Optional, Union, Tuple
from pathlib import Path
import concurrent.futures
from dataclasses import dataclass

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from pdf2image import convert_from_path
import cv2
import numpy as np

from .preprocessor import ImagePreprocessor
from .config import OCRConfig, ProcessingMethod
from .utils import setup_logging, validate_file, estimate_processing_time


@dataclass
class OCRResult:
    """نتیجه OCR برای یک سند"""
    success: bool
    total_pages: int
    successful_pages: int
    total_characters: int
    processing_time: float
    output_file: Optional[str] = None
    error_message: Optional[str] = None
    page_results: Optional[List[Dict]] = None


@dataclass
class PageResult:
    """نتیجه OCR برای یک صفحه"""
    page_number: int
    text: str
    character_count: int
    confidence: float
    processing_time: float
    success: bool
    error_message: Optional[str] = None


class PersianOCR:
    """
    کلاس اصلی OCR فارسی
    
    این کلاس امکانات کاملی برای استخراج متن فارسی از تصاویر و PDF ها فراهم می‌کند.
    
    مثال استفاده:
        >>> from persian_ocr import PersianOCR
        >>> ocr = PersianOCR()
        >>> result = ocr.extract_from_pdf("document.pdf")
        >>> print(f"متن استخراج شده: {result.total_characters} کاراکتر")
    """
    
    def __init__(self, 
                 config: Optional[OCRConfig] = None,
                 temp_dir: Optional[str] = None,
                 log_level: str = "INFO"):
        """
        مقداردهی اولیه OCR
        
        Args:
            config: تنظیمات OCR
            temp_dir: پوشه موقت برای ذخیره تصاویر
            log_level: سطح لاگ (DEBUG, INFO, WARNING, ERROR)
        """
        self.config = config or OCRConfig()
        self.temp_dir = Path(temp_dir or "/tmp/persian_ocr")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = setup_logging(log_level)
        self.preprocessor = ImagePreprocessor(self.config)
        
        self.logger.info("Persian OCR initialized successfully")
        self._validate_dependencies()
    
    def _validate_dependencies(self) -> None:
        """بررسی وجود ابزارهای مورد نیاز"""
        try:
            # بررسی Tesseract
            pytesseract.get_tesseract_version()
            self.logger.info("Tesseract found")
            
            # بررسی زبان فارسی
            languages = pytesseract.get_languages()
            if 'fas' not in languages:
                self.logger.warning("Persian language pack (fas) not found in Tesseract")
            else:
                self.logger.info("Persian language pack available")
                
        except Exception as e:
            self.logger.error(f"Dependency validation failed: {e}")
            raise RuntimeError("Required dependencies not available")
    
    def extract_from_image(self, 
                          image_path: Union[str, Path],
                          processing_method: ProcessingMethod = ProcessingMethod.ADVANCED) -> PageResult:
        """
        استخراج متن از یک تصویر
        
        Args:
            image_path: مسیر تصویر
            processing_method: روش پیش‌پردازش تصویر
            
        Returns:
            PageResult: نتیجه OCR
        """
        start_time = time.time()
        image_path = Path(image_path)
        
        self.logger.info(f"Processing image: {image_path.name}")
        
        try:
            # بررسی فایل
            validate_file(image_path, ['.jpg', '.jpeg', '.png', '.tiff', '.bmp'])
            
            # بارگذاری و پیش‌پردازش
            image = Image.open(image_path)
            processed_image = self.preprocessor.process(image, processing_method)
            
            # OCR
            text = self._perform_ocr(processed_image)
            
            # محاسبه اعتماد (ساده)
            confidence = self._calculate_confidence(text)
            
            processing_time = time.time() - start_time
            
            result = PageResult(
                page_number=1,
                text=text,
                character_count=len(text),
                confidence=confidence,
                processing_time=processing_time,
                success=True
            )
            
            self.logger.info(f"Image processed successfully: {len(text)} characters")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Error processing image {image_path}: {e}")
            
            return PageResult(
                page_number=1,
                text="",
                character_count=0,
                confidence=0.0,
                processing_time=processing_time,
                success=False,
                error_message=str(e)
            )
    
    def extract_from_pdf(self, 
                        pdf_path: Union[str, Path],
                        processing_method: ProcessingMethod = ProcessingMethod.ADVANCED,
                        max_workers: Optional[int] = None,
                        batch_size: int = 15) -> OCRResult:
        """
        استخراج متن از PDF
        
        Args:
            pdf_path: مسیر فایل PDF
            processing_method: روش پیش‌پردازش
            max_workers: تعداد worker های موازی
            batch_size: اندازه دسته برای پردازش
            
        Returns:
            OCRResult: نتیجه کامل OCR
        """
        start_time = time.time()
        pdf_path = Path(pdf_path)
        max_workers = max_workers or min(self.config.max_workers, 4)
        
        self.logger.info(f"Starting PDF processing: {pdf_path.name}")
        
        try:
            # بررسی فایل
            validate_file(pdf_path, ['.pdf'])
            
            # تخمین زمان
            estimated_time = estimate_processing_time(pdf_path)
            self.logger.info(f"Estimated processing time: {estimated_time:.1f} minutes")
            
            # تبدیل PDF به تصاویر
            image_paths = self._convert_pdf_to_images(pdf_path, batch_size)
            total_pages = len(image_paths)
            
            if not image_paths:
                return OCRResult(
                    success=False,
                    total_pages=0,
                    successful_pages=0,
                    total_characters=0,
                    processing_time=time.time() - start_time,
                    error_message="No images extracted from PDF"
                )
            
            # پردازش موازی صفحات
            page_results = self._process_pages_parallel(
                image_paths, processing_method, max_workers
            )
            
            # تولید فایل نهایی
            output_file = self._generate_output_file(pdf_path, page_results)
            
            # محاسبه آمار
            successful_pages = sum(1 for r in page_results if r.success)
            total_characters = sum(r.character_count for r in page_results if r.success)
            processing_time = time.time() - start_time
            
            result = OCRResult(
                success=True,
                total_pages=total_pages,
                successful_pages=successful_pages,
                total_characters=total_characters,
                processing_time=processing_time,
                output_file=output_file,
                page_results=page_results
            )
            
            self.logger.info(f"PDF processing completed: {successful_pages}/{total_pages} pages, "
                           f"{total_characters} characters in {processing_time:.1f}s")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Error processing PDF {pdf_path}: {e}")
            
            return OCRResult(
                success=False,
                total_pages=0,
                successful_pages=0,
                total_characters=0,
                processing_time=processing_time,
                error_message=str(e)
            )
        
        finally:
            self._cleanup_temp_files()
    
    def _convert_pdf_to_images(self, pdf_path: Path, batch_size: int) -> List[Tuple[Path, int]]:
        """تبدیل PDF به تصاویر"""
        self.logger.info("Converting PDF to images...")
        
        # تشخیص تعداد صفحات
        total_pages = self._get_pdf_page_count(pdf_path)
        self.logger.info(f"PDF has {total_pages} pages")
        
        image_paths = []
        
        for start_page in range(1, total_pages + 1, batch_size):
            end_page = min(start_page + batch_size - 1, total_pages)
            
            try:
                images = convert_from_path(
                    str(pdf_path),
                    dpi=self.config.dpi,
                    first_page=start_page,
                    last_page=end_page,
                    fmt='jpeg',
                    thread_count=2
                )
                
                for i, img in enumerate(images):
                    page_num = start_page + i
                    img_path = self.temp_dir / f"page_{page_num:04d}.jpg"
                    img.save(img_path, 'JPEG', quality=95, optimize=True)
                    image_paths.append((img_path, page_num))
                
                # پاکسازی حافظه
                for img in images:
                    del img
                del images
                
            except Exception as e:
                self.logger.warning(f"Error converting pages {start_page}-{end_page}: {e}")
                continue
        
        return image_paths
    
    def _process_pages_parallel(self, 
                               image_paths: List[Tuple[Path, int]], 
                               processing_method: ProcessingMethod,
                               max_workers: int) -> List[PageResult]:
        """پردازش موازی صفحات"""
        self.logger.info(f"Processing {len(image_paths)} pages with {max_workers} workers")
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # ارسال کارها
            future_to_page = {
                executor.submit(self._process_single_page, img_path, page_num, processing_method): page_num
                for img_path, page_num in image_paths
            }
            
            # جمع‌آوری نتایج
            for future in concurrent.futures.as_completed(future_to_page):
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    page_num = future_to_page[future]
                    self.logger.error(f"Error processing page {page_num}: {e}")
                    results.append(PageResult(
                        page_number=page_num,
                        text="",
                        character_count=0,
                        confidence=0.0,
                        processing_time=0.0,
                        success=False,
                        error_message=str(e)
                    ))
        
        # مرتب‌سازی بر اساس شماره صفحه
        results.sort(key=lambda x: x.page_number)
        return results
    
    def _process_single_page(self, 
                           img_path: Path, 
                           page_num: int,
                           processing_method: ProcessingMethod) -> PageResult:
        """پردازش یک صفحه"""
        start_time = time.time()
        
        try:
            # بارگذاری و پیش‌پردازش
            image = Image.open(img_path)
            processed_image = self.preprocessor.process(image, processing_method)
            
            # OCR
            text = self._perform_ocr(processed_image)
            confidence = self._calculate_confidence(text)
            
            # پاکسازی
            del image, processed_image
            if img_path.exists():
                img_path.unlink()
            
            processing_time = time.time() - start_time
            
            return PageResult(
                page_number=page_num,
                text=text,
                character_count=len(text),
                confidence=confidence,
                processing_time=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return PageResult(
                page_number=page_num,
                text="",
                character_count=0,
                confidence=0.0,
                processing_time=processing_time,
                success=False,
                error_message=str(e)
            )
    
    def _perform_ocr(self, image: Image.Image) -> str:
        """انجام OCR روی تصویر"""
        try:
            text = pytesseract.image_to_string(
                image,
                lang=self.config.language,
                config=self.config.get_tesseract_config()
            )
            return text.strip()
        except Exception as e:
            self.logger.error(f"OCR failed: {e}")
            return ""
    
    def _calculate_confidence(self, text: str) -> float:
        """محاسبه اعتماد به نتیجه OCR"""
        if not text:
            return 0.0
        
        # محاسبه ساده بر اساس طول متن و کاراکترهای معتبر
        valid_chars = sum(1 for c in text if c.isalnum() or c.isspace())
        return min(valid_chars / len(text) * 100, 100.0) if text else 0.0
    
    def _get_pdf_page_count(self, pdf_path: Path) -> int:
        """تشخیص تعداد صفحات PDF"""
        try:
            import subprocess
            result = subprocess.run(['pdfinfo', str(pdf_path)], 
                                  capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if 'Pages:' in line:
                    return int(line.split(':')[1].strip())
        except:
            pass
        
        # روش جایگزین
        try:
            images = convert_from_path(str(pdf_path), dpi=72, first_page=1, last_page=1)
            return len(images) if images else 100  # تخمین
        except:
            return 100  # تخمین پیش‌فرض
    
    def _generate_output_file(self, pdf_path: Path, page_results: List[PageResult]) -> str:
        """تولید فایل خروجی"""
        timestamp = int(time.time())
        output_filename = f"{pdf_path.stem}_extracted_{timestamp}.txt"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(f"# نتیجه OCR فایل: {pdf_path.name}\n")
            f.write(f"# تاریخ: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# ابزار: Persian OCR Toolkit\n")
            f.write("\n" + "="*80 + "\n\n")
            
            for result in page_results:
                f.write(f"\n{'='*60}\n")
                f.write(f"صفحه {result.page_number}\n")
                f.write(f"{'='*60}\n")
                
                if result.success:
                    f.write(result.text)
                else:
                    f.write(f"خطا در پردازش: {result.error_message}")
                
                f.write("\n\n")
        
        return output_filename
    
    def _cleanup_temp_files(self) -> None:
        """پاکسازی فایل‌های موقت"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug("Temporary files cleaned up")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup temp files: {e}")
    
    def get_stats(self) -> Dict:
        """دریافت آمار عملکرد"""
        return {
            "version": "1.0.0",
            "config": self.config.__dict__,
            "temp_dir": str(self.temp_dir),
            "tesseract_version": pytesseract.get_tesseract_version(),
            "available_languages": pytesseract.get_languages()
        }


# توابع سطح بالا برای سادگی استفاده
def extract_text_from_image(image_path: Union[str, Path], **kwargs) -> str:
    """تابع ساده برای استخراج متن از تصویر"""
    ocr = PersianOCR()
    result = ocr.extract_from_image(image_path, **kwargs)
    return result.text if result.success else ""


def extract_text_from_pdf(pdf_path: Union[str, Path], **kwargs) -> OCRResult:
    """تابع ساده برای استخراج متن از PDF"""
    ocr = PersianOCR()
    return ocr.extract_from_pdf(pdf_path, **kwargs)

"""
Persian OCR Toolkit - Core Module
A professional OCR library for Persian/Farsi text extraction

Author: YourName
License: MIT
Version: 1.0.0
"""

import os
import time
import logging
from typing import List, Dict, Optional, Union, Tuple
from pathlib import Path
import concurrent.futures
from dataclasses import dataclass

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from pdf2image import convert_from_path
import cv2
import numpy as np

from .preprocessor import ImagePreprocessor
from .config import OCRConfig, ProcessingMethod
from .utils import setup_logging, validate_file, estimate_processing_time


@dataclass
class OCRResult:
    """نتیجه OCR برای یک سند"""
    success: bool
    total_pages: int
    successful_pages: int
    total_characters: int
    processing_time: float
    output_file: Optional[str] = None
    error_message: Optional[str] = None
    page_results: Optional[List[Dict]] = None


@dataclass
class PageResult:
    """نتیجه OCR برای یک صفحه"""
    page_number: int
    text: str
    character_count: int
    confidence: float
    processing_time: float
    success: bool
    error_message: Optional[str] = None


class PersianOCR:
    """
    کلاس اصلی OCR فارسی
    
    این کلاس امکانات کاملی برای استخراج متن فارسی از تصاویر و PDF ها فراهم می‌کند.
    
    مثال استفاده:
        >>> from persian_ocr import PersianOCR
        >>> ocr = PersianOCR()
        >>> result = ocr.extract_from_pdf("document.pdf")
        >>> print(f"متن استخراج شده: {result.total_characters} کاراکتر")
    """
    
    def __init__(self, 
                 config: Optional[OCRConfig] = None,
                 temp_dir: Optional[str] = None,
                 log_level: str = "INFO"):
        """
        مقداردهی اولیه OCR
        
        Args:
            config: تنظیمات OCR
            temp_dir: پوشه موقت برای ذخیره تصاویر
            log_level: سطح لاگ (DEBUG, INFO, WARNING, ERROR)
        """
        self.config = config or OCRConfig()
        self.temp_dir = Path(temp_dir or "/tmp/persian_ocr")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = setup_logging(log_level)
        self.preprocessor = ImagePreprocessor(self.config)
        
        self.logger.info("Persian OCR initialized successfully")
        self._validate_dependencies()
    
    def _validate_dependencies(self) -> None:
        """بررسی وجود ابزارهای مورد نیاز"""
        try:
            # بررسی Tesseract
            pytesseract.get_tesseract_version()
            self.logger.info("Tesseract found")
            
            # بررسی زبان فارسی
            languages = pytesseract.get_languages()
            if 'fas' not in languages:
                self.logger.warning("Persian language pack (fas) not found in Tesseract")
            else:
                self.logger.info("Persian language pack available")
                
        except Exception as e:
            self.logger.error(f"Dependency validation failed: {e}")
            raise RuntimeError("Required dependencies not available")
    
    def extract_from_image(self, 
                          image_path: Union[str, Path],
                          processing_method: ProcessingMethod = ProcessingMethod.ADVANCED) -> PageResult:
        """
        استخراج متن از یک تصویر
        
        Args:
            image_path: مسیر تصویر
            processing_method: روش پیش‌پردازش تصویر
            
        Returns:
            PageResult: نتیجه OCR
        """
        start_time = time.time()
        image_path = Path(image_path)
        
        self.logger.info(f"Processing image: {image_path.name}")
        
        try:
            # بررسی فایل
            validate_file(image_path, ['.jpg', '.jpeg', '.png', '.tiff', '.bmp'])
            
            # بارگذاری و پیش‌پردازش
            image = Image.open(image_path)
            processed_image = self.preprocessor.process(image, processing_method)
            
            # OCR
            text = self._perform_ocr(processed_image)
            
            # محاسبه اعتماد (ساده)
            confidence = self._calculate_confidence(text)
            
            processing_time = time.time() - start_time
            
            result = PageResult(
                page_number=1,
                text=text,
                character_count=len(text),
                confidence=confidence,
                processing_time=processing_time,
                success=True
            )
            
            self.logger.info(f"Image processed successfully: {len(text)} characters")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Error processing image {image_path}: {e}")
            
            return PageResult(
                page_number=1,
                text="",
                character_count=0,
                confidence=0.0,
                processing_time=processing_time,
                success=False,
                error_message=str(e)
            )
    
    def extract_from_pdf(self, 
                        pdf_path: Union[str, Path],
                        processing_method: ProcessingMethod = ProcessingMethod.ADVANCED,
                        max_workers: Optional[int] = None,
                        batch_size: int = 15) -> OCRResult:
        """
        استخراج متن از PDF
        
        Args:
            pdf_path: مسیر فایل PDF
            processing_method: روش پیش‌پردازش
            max_workers: تعداد worker های موازی
            batch_size: اندازه دسته برای پردازش
            
        Returns:
            OCRResult: نتیجه کامل OCR
        """
        start_time = time.time()
        pdf_path = Path(pdf_path)
        max_workers = max_workers or min(self.config.max_workers, 4)
        
        self.logger.info(f"Starting PDF processing: {pdf_path.name}")
        
        try:
            # بررسی فایل
            validate_file(pdf_path, ['.pdf'])
            
            # تخمین زمان
            estimated_time = estimate_processing_time(pdf_path)
            self.logger.info(f"Estimated processing time: {estimated_time:.1f} minutes")
            
            # تبدیل PDF به تصاویر
            image_paths = self._convert_pdf_to_images(pdf_path, batch_size)
            total_pages = len(image_paths)
            
            if not image_paths:
                return OCRResult(
                    success=False,
                    total_pages=0,
                    successful_pages=0,
                    total_characters=0,
                    processing_time=time.time() - start_time,
                    error_message="No images extracted from PDF"
                )
            
            # پردازش موازی صفحات
            page_results = self._process_pages_parallel(
                image_paths, processing_method, max_workers
            )
            
            # تولید فایل نهایی
            output_file = self._generate_output_file(pdf_path, page_results)
            
            # محاسبه آمار
            successful_pages = sum(1 for r in page_results if r.success)
            total_characters = sum(r.character_count for r in page_results if r.success)
            processing_time = time.time() - start_time
            
            result = OCRResult(
                success=True,
                total_pages=total_pages,
                successful_pages=successful_pages,
                total_characters=total_characters,
                processing_time=processing_time,
                output_file=output_file,
                page_results=page_results
            )
            
            self.logger.info(f"PDF processing completed: {successful_pages}/{total_pages} pages, "
                           f"{total_characters} characters in {processing_time:.1f}s")
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Error processing PDF {pdf_path}: {e}")
            
            return OCRResult(
                success=False,
                total_pages=0,
                successful_pages=0,
                total_characters=0,
                processing_time=processing_time,
                error_message=str(e)
            )
        
        finally:
            self._cleanup_temp_files()
    
    def _convert_pdf_to_images(self, pdf_path: Path, batch_size: int) -> List[Tuple[Path, int]]:
        """تبدیل PDF به تصاویر"""
        self.logger.info("Converting PDF to images...")
        
        # تشخیص تعداد صفحات
        total_pages = self._get_pdf_page_count(pdf_path)
        self.logger.info(f"PDF has {total_pages} pages")
        
        image_paths = []
        
        for start_page in range(1, total_pages + 1, batch_size):
            end_page = min(start_page + batch_size - 1, total_pages)
            
            try:
                images = convert_from_path(
                    str(pdf_path),
                    dpi=self.config.dpi,
                    first_page=start_page,
                    last_page=end_page,
                    fmt='jpeg',
                    thread_count=2
                )
                
                for i, img in enumerate(images):
                    page_num = start_page + i
                    img_path = self.temp_dir / f"page_{page_num:04d}.jpg"
                    img.save(img_path, 'JPEG', quality=95, optimize=True)
                    image_paths.append((img_path, page_num))
                
                # پاکسازی حافظه
                for img in images:
                    del img
                del images
                
            except Exception as e:
                self.logger.warning(f"Error converting pages {start_page}-{end_page}: {e}")
                continue
        
        return image_paths
    
    def _process_pages_parallel(self, 
                               image_paths: List[Tuple[Path, int]], 
                               processing_method: ProcessingMethod,
                               max_workers: int) -> List[PageResult]:
        """پردازش موازی صفحات"""
        self.logger.info(f"Processing {len(image_paths)} pages with {max_workers} workers")
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # ارسال کارها
            future_to_page = {
                executor.submit(self._process_single_page, img_path, page_num, processing_method): page_num
                for img_path, page_num in image_paths
            }
            
            # جمع‌آوری نتایج
            for future in concurrent.futures.as_completed(future_to_page):
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    page_num = future_to_page[future]
                    self.logger.error(f"Error processing page {page_num}: {e}")
                    results.append(PageResult(
                        page_number=page_num,
                        text="",
                        character_count=0,
                        confidence=0.0,
                        processing_time=0.0,
                        success=False,
                        error_message=str(e)
                    ))
        
        # مرتب‌سازی بر اساس شماره صفحه
        results.sort(key=lambda x: x.page_number)
        return results
    
    def _process_single_page(self, 
                           img_path: Path, 
                           page_num: int,
                           processing_method: ProcessingMethod) -> PageResult:
        """پردازش یک صفحه"""
        start_time = time.time()
        
        try:
            # بارگذاری و پیش‌پردازش
            image = Image.open(img_path)
            processed_image = self.preprocessor.process(image, processing_method)
            
            # OCR
            text = self._perform_ocr(processed_image)
            confidence = self._calculate_confidence(text)
            
            # پاکسازی
            del image, processed_image
            if img_path.exists():
                img_path.unlink()
            
            processing_time = time.time() - start_time
            
            return PageResult(
                page_number=page_num,
                text=text,
                character_count=len(text),
                confidence=confidence,
                processing_time=processing_time,
                success=True
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            return PageResult(
                page_number=page_num,
                text="",
                character_count=0,
                confidence=0.0,
                processing_time=processing_time,
                success=False,
                error_message=str(e)
            )
    
    def _perform_ocr(self, image: Image.Image) -> str:
        """انجام OCR روی تصویر"""
        try:
            text = pytesseract.image_to_string(
                image,
                lang=self.config.language,
                config=self.config.get_tesseract_config()
            )
            return text.strip()
        except Exception as e:
            self.logger.error(f"OCR failed: {e}")
            return ""
    
    def _calculate_confidence(self, text: str) -> float:
        """محاسبه اعتماد به نتیجه OCR"""
        if not text:
            return 0.0
        
        # محاسبه ساده بر اساس طول متن و کاراکترهای معتبر
        valid_chars = sum(1 for c in text if c.isalnum() or c.isspace())
        return min(valid_chars / len(text) * 100, 100.0) if text else 0.0
    
    def _get_pdf_page_count(self, pdf_path: Path) -> int:
        """تشخیص تعداد صفحات PDF"""
        try:
            import subprocess
            result = subprocess.run(['pdfinfo', str(pdf_path)], 
                                  capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if 'Pages:' in line:
                    return int(line.split(':')[1].strip())
        except:
            pass
        
        # روش جایگزین
        try:
            images = convert_from_path(str(pdf_path), dpi=72, first_page=1, last_page=1)
            return len(images) if images else 100  # تخمین
        except:
            return 100  # تخمین پیش‌فرض
    
    def _generate_output_file(self, pdf_path: Path, page_results: List[PageResult]) -> str:
        """تولید فایل خروجی"""
        timestamp = int(time.time())
        output_filename = f"{pdf_path.stem}_extracted_{timestamp}.txt"
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(f"# نتیجه OCR فایل: {pdf_path.name}\n")
            f.write(f"# تاریخ: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# ابزار: Persian OCR Toolkit\n")
            f.write("\n" + "="*80 + "\n\n")
            
            for result in page_results:
                f.write(f"\n{'='*60}\n")
                f.write(f"صفحه {result.page_number}\n")
                f.write(f"{'='*60}\n")
                
                if result.success:
                    f.write(result.text)
                else:
                    f.write(f"خطا در پردازش: {result.error_message}")
                
                f.write("\n\n")
        
        return output_filename
    
    def _cleanup_temp_files(self) -> None:
        """پاکسازی فایل‌های موقت"""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                self.temp_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug("Temporary files cleaned up")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup temp files: {e}")
    
    def get_stats(self) -> Dict:
        """دریافت آمار عملکرد"""
        return {
            "version": "1.0.0",
            "config": self.config.__dict__,
            "temp_dir": str(self.temp_dir),
            "tesseract_version": pytesseract.get_tesseract_version(),
            "available_languages": pytesseract.get_languages()
        }


# توابع سطح بالا برای سادگی استفاده
def extract_text_from_image(image_path: Union[str, Path], **kwargs) -> str:
    """تابع ساده برای استخراج متن از تصویر"""
    ocr = PersianOCR()
    result = ocr.extract_from_image(image_path, **kwargs)
    return result.text if result.success else ""


def extract_text_from_pdf(pdf_path: Union[str, Path], **kwargs) -> OCRResult:
    """تابع ساده برای استخراج متن از PDF"""
    ocr = PersianOCR()
    return ocr.extract_from_pdf(pdf_path, **kwargs)

