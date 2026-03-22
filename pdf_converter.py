#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF转图片工具模块
功能：将PDF文件的每一页转换为高质量的PNG/JPG图像
支持单文件转换和批量转换
支持在偶数页添加水印
支持生成仅包含前三页的simple PDF版本
"""

import os
import shutil
import tempfile
from pdf2image import convert_from_path
from PIL import Image

# 尝试导入PyPDF2用于PDF页面提取
PYPDF_AVAILABLE = False
try:
    try:
        from pypdf import PdfReader, PdfWriter
        PYPDF_AVAILABLE = True
    except ImportError:
        from PyPDF2 import PdfReader, PdfWriter
        PYPDF_AVAILABLE = True
except ImportError:
    pass


class PDFConverter:
    """PDF转换器类"""
    
    def __init__(self, upload_folder='static/uploads', output_folder='static/pdf_outputs',
                 watermark_path=None, header_path=None, footer_path=None):
        """
        初始化PDF转换器
        
        参数:
            upload_folder: PDF文件上传目录
            output_folder: 转换后的图片输出目录
            watermark_path: 水印图片路径
            header_path: 页眉图片路径
            footer_path: 页脚图片路径
        """
        self.upload_folder = upload_folder
        self.output_folder = output_folder
        
        # 确保目录存在
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)
        
        # 水印图片路径
        self.watermark_path = watermark_path or os.path.join(os.path.dirname(__file__), 'strong_watermark.png')
        
        # 页眉页脚图片路径
        self.header_path = header_path or os.path.join(os.path.dirname(__file__), 'header.png')
        self.footer_path = footer_path or os.path.join(os.path.dirname(__file__), 'footer.png')
    
    def create_simple_pdf(self, pdf_path, output_folder):
        """
        创建只包含PDF前3页的simple版本
        
        参数:
            pdf_path: 原始PDF文件路径
            output_folder: 输出目录
        
        返回:
            str: 创建的simple PDF文件路径，如果失败返回None
        """
        if not PYPDF_AVAILABLE:
            return None
        
        try:
            if not os.path.exists(pdf_path):
                return None
            
            pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]
            
            # 去掉文件名中的"-组卷网"字符
            if "-组卷网" in pdf_filename:
                pdf_filename = pdf_filename.replace("-组卷网", "")
            
            simple_pdf_path = os.path.join(output_folder, f"{pdf_filename}_simple.pdf")
            
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                writer = PdfWriter()
                
                num_pages_to_extract = min(3, len(reader.pages))
                
                for i in range(num_pages_to_extract):
                    page = reader.pages[i]
                    writer.add_page(page)
                
                with open(simple_pdf_path, 'wb') as output_pdf:
                    writer.write(output_pdf)
            
            return simple_pdf_path
            
        except Exception as e:
            print(f"创建simple PDF版本时出错：{str(e)}")
            return None
    
    def parse_page_range(self, page_range_str, total_pages):
        """
        解析页码范围字符串
        
        支持的格式:
        - "odd": 奇数页
        - "even": 偶数页
        - "1,3,5,7": 离散页码
        - "1-3": 连续页码范围
        - "1,3,5-7": 混合格式
        
        参数:
            page_range_str: 页码范围字符串
            total_pages: 总页数
        
        返回:
            set: 页码集合
        """
        if not page_range_str or page_range_str.strip() == '':
            return set(range(1, total_pages + 1))
        
        page_range_str = page_range_str.strip().lower()
        pages = set()
        
        # 奇数页
        if page_range_str == 'odd':
            return set(i for i in range(1, total_pages + 1) if i % 2 == 1)
        
        # 偶数页
        if page_range_str == 'even':
            return set(i for i in range(1, total_pages + 1) if i % 2 == 0)
        
        # 解析混合格式
        parts = page_range_str.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                # 范围格式: 1-3
                try:
                    start, end = part.split('-')
                    start = int(start.strip())
                    end = int(end.strip())
                    pages.update(range(max(1, start), min(total_pages + 1, end + 1)))
                except ValueError:
                    continue
            else:
                # 单个页码
                try:
                    page = int(part)
                    if 1 <= page <= total_pages:
                        pages.add(page)
                except ValueError:
                    continue
        
        return pages if pages else set(range(1, total_pages + 1))
    
    def convert_pdf_to_images(self, pdf_path, dpi=300, fmt='png', add_watermark=True,
                              generate_simple_pdf=True, start_page=1, end_page=None,
                              add_header=False, add_footer=False,
                              watermark_page_range='even', watermark_position=None,
                              header_position=None, footer_position=None):
        """
        将PDF文件的每一页转换为图像
        
        参数:
            pdf_path: PDF文件的路径
            dpi: 图像的DPI（清晰度），默认为300
            fmt: 输出图像格式，默认为'png'
            add_watermark: 是否添加水印，默认为True
            generate_simple_pdf: 是否生成仅包含前三页的simple PDF版本，默认为True
            start_page: 起始页码，默认为1
            end_page: 结束页码，默认为None（全部）
            add_header: 是否添加页眉，默认为False
            add_footer: 是否添加页脚，默认为False
            watermark_page_range: 水印页码范围，可选值: 'odd', 'even', 'all', 或自定义格式如'1,3,5'或'1-5'
            watermark_position: 水印位置，{'x': 0.5, 'y': 0.5} 表示相对位置（0-1）
            header_position: 页眉位置，{'y': 0} 表示顶部偏移
            footer_position: 页脚位置，{'y': 0} 表示底部偏移
        
        返回:
            dict: 包含图像路径列表和simple PDF路径的字典
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]
        
        # 去掉文件名中的"-组卷网"字符
        if "-组卷网" in pdf_filename:
            pdf_filename = pdf_filename.replace("-组卷网", "")
        
        # 创建输出子文件夹
        output_subfolder = os.path.join(self.output_folder, pdf_filename)
        os.makedirs(output_subfolder, exist_ok=True)
        
        # 生成simple PDF版本
        simple_pdf_path = None
        if generate_simple_pdf:
            simple_pdf_path = self.create_simple_pdf(pdf_path, output_subfolder)
        
        # 尝试不同的poppler路径
        poppler_paths = ['/usr/local/bin', '/opt/homebrew/bin', '']
        images = None
        
        for poppler_path in poppler_paths:
            try:
                if poppler_path:
                    images = convert_from_path(pdf_path, dpi=dpi, fmt=fmt, poppler_path=poppler_path)
                else:
                    images = convert_from_path(pdf_path, dpi=dpi, fmt=fmt)
                break
            except Exception as e:
                continue
        
        if images is None:
            raise RuntimeError("无法找到或使用poppler。请确认已正确安装并在PATH中。")
        
        # 保存指定页码范围的图像
        output_paths = []
        
        if start_page < 1:
            start_page = 1
        
        if end_page is None:
            end_page = len(images)
        else:
            end_page = min(end_page, len(images))
        
        total_pages = len(images)
        page_digits = len(str(total_pages))
        
        # 解析水印页码范围
        watermark_pages = set()
        if add_watermark:
            watermark_pages = self.parse_page_range(watermark_page_range, total_pages)
        
        for i in range(len(images)):
            current_page = i + 1
            if current_page < start_page or current_page > end_page:
                continue
            
            image = images[i]
            formatted_page = str(current_page).zfill(page_digits)
            output_filename = f"{pdf_filename}_page_{formatted_page}.{fmt}"
            output_path = os.path.join(output_subfolder, output_filename)
            
            # 检查当前页是否在水印页码范围内
            if add_watermark and current_page in watermark_pages:
                try:
                    if os.path.exists(self.watermark_path):
                        image = self._add_watermark_to_image(image, watermark_position)
                except Exception as e:
                    print(f"添加水印时出错: {str(e)}")
            
            # 添加页眉和页脚
            if add_header or add_footer:
                try:
                    image = self._add_header_footer_to_image(image, add_header, add_footer, header_position, footer_position)
                except Exception as e:
                    print(f"添加页眉页脚时出错: {str(e)}")
            
            # 保存图像
            try:
                image.save(output_path, fmt.upper())
                output_paths.append(output_path)
            except Exception as e:
                print(f"保存图像失败: {str(e)}")
        
        return {
            'images': output_paths,
            'simple_pdf': simple_pdf_path,
            'output_folder': output_subfolder
        }
    
    def _add_watermark_to_image(self, image, position=None):
        """
        为图像添加水印
        
        参数:
            image: PIL图像对象
            position: 水印位置，{'x': 0.5, 'y': 0.5} 表示相对位置（0-1），None表示居中
        """
        if not os.path.exists(self.watermark_path):
            return image
        
        image = image.convert('RGBA')
        watermark = Image.open(self.watermark_path)
        
        page_width, page_height = image.size
        
        # 将水印图片缩放到页面宽度的70%
        new_width = int(page_width * 0.7)
        width_percent = (new_width / float(watermark.size[0]))
        new_height = int((float(watermark.size[1]) * float(width_percent)))
        
        watermark_resized = watermark.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 计算水印位置
        if position is None:
            # 默认居中
            position_x = (page_width - new_width) // 2
            position_y = (page_height - new_height) // 2
        else:
            # 使用相对位置
            x_ratio = position.get('x', 0.5)
            y_ratio = position.get('y', 0.5)
            position_x = int((page_width - new_width) * x_ratio)
            position_y = int((page_height - new_height) * y_ratio)
        
        # 确保位置在有效范围内
        position_x = max(0, min(position_x, page_width - new_width))
        position_y = max(0, min(position_y, page_height - new_height))
        
        # 粘贴水印
        if watermark_resized.mode == 'RGBA':
            base = image.copy()
            base.paste(watermark_resized, (position_x, position_y), watermark_resized.split()[3])
            image = base
        else:
            watermark_resized = watermark_resized.convert('RGBA')
            base = image.copy()
            base.paste(watermark_resized, (position_x, position_y), watermark_resized.split()[3])
            image = base
        
        return image.convert('RGB')
    
    def _add_header_footer_to_image(self, image, add_header, add_footer, header_position=None, footer_position=None):
        """
        为图像添加页眉页脚
        
        参数:
            image: PIL图像对象
            add_header: 是否添加页眉
            add_footer: 是否添加页脚
            header_position: 页眉位置，{'y': 0} 表示顶部偏移（像素）
            footer_position: 页脚位置，{'y': 0} 表示底部偏移（像素）
        """
        image = image.convert('RGBA')
        page_width, page_height = image.size
        
        # 添加页眉
        if add_header and os.path.exists(self.header_path):
            header_image = Image.open(self.header_path)
            header_resized = header_image.resize(
                (page_width, int(header_image.size[1] * (page_width / header_image.size[0]))),
                Image.Resampling.LANCZOS
            )
            
            # 计算页眉位置
            header_y = 0
            if header_position and 'y' in header_position:
                header_y = header_position['y']
            
            header_y = max(0, header_y)
            
            if header_resized.mode == 'RGBA':
                base = image.copy()
                base.paste(header_resized, (0, header_y), header_resized.split()[3])
                image = base
            else:
                base = image.copy()
                base.paste(header_resized, (0, header_y))
                image = base
        
        # 添加页脚
        if add_footer and os.path.exists(self.footer_path):
            footer_image = Image.open(self.footer_path)
            footer_resized = footer_image.resize(
                (page_width, int(footer_image.size[1] * (page_width / footer_image.size[0]))),
                Image.Resampling.LANCZOS
            )
            
            # 计算页脚位置
            footer_y = page_height - footer_resized.size[1]
            if footer_position and 'y' in footer_position:
                footer_y = page_height - footer_resized.size[1] - footer_position['y']
            
            footer_y = max(0, min(footer_y, page_height - footer_resized.size[1]))
            
            if footer_resized.mode == 'RGBA':
                base = image.copy()
                base.paste(footer_resized, (0, footer_y), footer_resized.split()[3])
                image = base
            else:
                base = image.copy()
                base.paste(footer_resized, (0, footer_y))
                image = base
        
        return image.convert('RGB')
    
    def create_key_page(self, output_folder):
        """
        在output_folder下创建key_page目录，并拷贝每个PDF的前两页图片
        
        参数:
            output_folder: 输出图像的保存目录
        """
        key_page_dir = os.path.join(output_folder, 'key_page')
        os.makedirs(key_page_dir, exist_ok=True)
        
        image_files = []
        for f in os.listdir(output_folder):
            if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_files.append(f)
        
        if image_files:
            image_files.sort()
            selected_pages = image_files[:2]
            
            for img_file in selected_pages:
                src_path = os.path.join(output_folder, img_file)
                dst_path = os.path.join(key_page_dir, img_file)
                shutil.copy2(src_path, dst_path)
        
        return key_page_dir
    
    def cleanup_old_files(self, max_age_hours=24):
        """
        清理超过指定时间的旧文件
        
        参数:
            max_age_hours: 最大保留时间（小时），默认24小时
        """
        import time
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for folder_name in os.listdir(self.output_folder):
            folder_path = os.path.join(self.output_folder, folder_name)
            if os.path.isdir(folder_path):
                folder_age = current_time - os.path.getctime(folder_path)
                if folder_age > max_age_seconds:
                    shutil.rmtree(folder_path)
                    print(f"已清理旧文件夹: {folder_path}")


# 全局转换器实例
pdf_converter = PDFConverter()
