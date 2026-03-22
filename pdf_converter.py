#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF转图片转换器
支持水印、页眉、页脚添加
"""

from pdf2image import convert_from_path
from PIL import Image
import os
from pathlib import Path


class PDFConverter:
    def __init__(self, watermark_path=None, header_path=None, footer_path=None, upload_folder='static/uploads'):
        """
        初始化PDF转换器
        
        参数:
            watermark_path: 水印图片路径，默认使用 resources/imgs/default_watermark.png
            header_path: 页眉图片路径
            footer_path: 页脚图片路径
            upload_folder: 上传文件保存目录
        """
        # 获取当前文件所在目录
        self.base_dir = Path(__file__).parent
        
        # 上传文件夹
        self.upload_folder = str(self.base_dir / upload_folder)
        os.makedirs(self.upload_folder, exist_ok=True)
        
        # 默认水印路径（相对路径）
        default_watermark = self.base_dir / "resources" / "imgs" / "default_watermark.png"
        self.watermark_path = watermark_path or str(default_watermark)
        self.header_path = header_path
        self.footer_path = footer_path
        
        # 加载图片
        self.watermark_img = self._load_image(self.watermark_path)
        self.header_img = self._load_image(self.header_path) if self.header_path else None
        self.footer_img = self._load_image(self.footer_path) if self.footer_path else None
    
    def _load_image(self, path):
        """加载图片"""
        if path and os.path.exists(path):
            return Image.open(path).convert("RGBA")
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
    
    def convert_pdf_to_images(self, pdf_path, dpi=200, fmt='png', 
                              add_watermark=True, generate_simple_pdf=False,
                              start_page=1, end_page=None,
                              add_header=False, add_footer=False,
                              watermark_page_range='even',
                              watermark_position=None,
                              header_position=None,
                              footer_position=None):
        """
        将PDF转换为图片
        
        参数:
            pdf_path: PDF文件路径
            dpi: 输出图片DPI
            fmt: 输出格式 (png, jpg)
            add_watermark: 是否添加水印
            generate_simple_pdf: 是否生成精简版PDF
            start_page: 起始页码
            end_page: 结束页码
            add_header: 是否添加页眉
            add_footer: 是否添加页脚
            watermark_page_range: 水印页面范围 ('odd', 'even', 'all', 或自定义)
            watermark_position: 水印位置 {'x': 0-100, 'y': 0-100}
            header_position: 页眉位置 {'top': 像素值}
            footer_position: 页脚位置 {'bottom': 像素值}
        
        返回:
            dict: 包含生成的图片路径列表和简版PDF路径
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        # 转换PDF为图片
        images = convert_from_path(str(pdf_path), dpi=dpi)
        total_pages = len(images)
        
        # 确定页码范围
        start = max(0, start_page - 1)
        end = min(total_pages, end_page) if end_page else total_pages
        
        # 解析水印页面范围
        watermark_pages = self.parse_page_range(watermark_page_range, total_pages)
        
        # 创建输出目录: PDF相同文件夹/imgs/文件名/
        output_dir = pdf_path.parent / "imgs" / pdf_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_paths = []
        simple_pdf_images = []
        
        for i in range(start, end):
            img = images[i].convert("RGBA")
            page_num = i + 1
            
            # 添加页眉
            if add_header and self.header_img:
                img = self._add_header_to_image(img, self.header_img, header_position)
            
            # 添加页脚
            if add_footer and self.footer_img:
                img = self._add_footer_to_image(img, self.footer_img, footer_position)
            
            # 添加水印（只在指定页面添加）
            if add_watermark and self.watermark_img and page_num in watermark_pages:
                img = self._add_watermark_to_image(img, self.watermark_img, watermark_position)
            
            # 保存图片
            output_filename = f"{pdf_path.stem}_page_{page_num:02d}.{fmt}"
            output_path = output_dir / output_filename
            
            # 转换为RGB保存（去除透明通道）
            if fmt.lower() in ['jpg', 'jpeg']:
                img_rgb = img.convert("RGB")
                img_rgb.save(output_path, quality=95)
            else:
                img.save(output_path)
            
            output_paths.append(str(output_path))
            
            # 为简版PDF保存
            if generate_simple_pdf:
                simple_pdf_images.append(img.convert("RGB"))
        
        # 生成简版PDF
        simple_pdf_path = None
        if generate_simple_pdf and simple_pdf_images:
            simple_pdf_filename = f"{pdf_path.stem}_simple.pdf"
            simple_pdf_path = output_dir / simple_pdf_filename
            simple_pdf_images[0].save(
                simple_pdf_path,
                save_all=True,
                append_images=simple_pdf_images[1:],
                resolution=dpi
            )
            simple_pdf_path = str(simple_pdf_path)
        
        return {
            'images': output_paths,
            'simple_pdf': simple_pdf_path,
            'output_dir': str(output_dir)
        }
    
    def _add_watermark_to_image(self, img, watermark, position=None):
        """
        添加水印到图片
        
        参数:
            img: 目标图片
            watermark: 水印图片
            position: 位置 {'x': 0-100, 'y': 0-100}，默认居中
        """
        img_width, img_height = img.size
        
        # 调整水印大小（不超过图片的30%）
        wm_max_width = int(img_width * 0.3)
        wm_max_height = int(img_height * 0.3)
        
        wm_width, wm_height = watermark.size
        scale = min(wm_max_width / wm_width, wm_max_height / wm_height, 1.0)
        
        new_width = int(wm_width * scale)
        new_height = int(wm_height * scale)
        watermark_resized = watermark.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 计算位置
        if position:
            x_percent = position.get('x', 50)
            y_percent = position.get('y', 50)
            x = int((img_width - new_width) * x_percent / 100)
            y = int((img_height - new_height) * y_percent / 100)
        else:
            # 默认居中
            x = (img_width - new_width) // 2
            y = (img_height - new_height) // 2
        
        # 创建透明层
        transparent = Image.new('RGBA', img.size, (0, 0, 0, 0))
        transparent.paste(watermark_resized, (x, y), watermark_resized)
        
        # 合并
        result = Image.alpha_composite(img, transparent)
        return result
    
    def _add_header_to_image(self, img, header, position=None):
        """
        添加页眉到图片
        
        参数:
            img: 目标图片
            header: 页眉图片
            position: 位置 {'top': 像素值}
        """
        img_width, img_height = img.size
        
        # 调整页眉宽度匹配图片
        header_width = img_width
        header_height = int(header.size[1] * (header_width / header.size[0]))
        header_resized = header.resize((header_width, header_height), Image.Resampling.LANCZOS)
        
        # 计算位置
        top_offset = position.get('top', 0) if position else 0
        x = 0
        y = top_offset
        
        # 创建透明层
        transparent = Image.new('RGBA', img.size, (0, 0, 0, 0))
        transparent.paste(header_resized, (x, y), header_resized)
        
        # 合并
        result = Image.alpha_composite(img, transparent)
        return result
    
    def _add_footer_to_image(self, img, footer, position=None):
        """
        添加页脚到图片
        
        参数:
            img: 目标图片
            footer: 页脚图片
            position: 位置 {'bottom': 像素值}
        """
        img_width, img_height = img.size
        
        # 调整页脚宽度匹配图片
        footer_width = img_width
        footer_height = int(footer.size[1] * (footer_width / footer.size[0]))
        footer_resized = footer.resize((footer_width, footer_height), Image.Resampling.LANCZOS)
        
        # 计算位置
        bottom_offset = position.get('bottom', 0) if position else 0
        x = 0
        y = img_height - footer_height - bottom_offset
        
        # 创建透明层
        transparent = Image.new('RGBA', img.size, (0, 0, 0, 0))
        transparent.paste(footer_resized, (x, y), footer_resized)
        
        # 合并
        result = Image.alpha_composite(img, transparent)
        return result


# 便捷函数
def convert_pdf(pdf_path, **kwargs):
    """
    便捷的PDF转换函数
    
    参数:
        pdf_path: PDF文件路径
        **kwargs: 传递给 PDFConverter.convert_pdf_to_images 的参数
    
    返回:
        dict: 转换结果
    """
    converter = PDFConverter()
    return converter.convert_pdf_to_images(pdf_path, **kwargs)


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        converter = PDFConverter()
        result = converter.convert_pdf_to_images(
            pdf_file,
            dpi=200,
            add_watermark=True,
            generate_simple_pdf=True
        )
        print(f"转换完成！")
        print(f"生成图片: {len(result['images'])} 张")
        print(f"输出目录: {result['output_dir']}")
        if result['simple_pdf']:
            print(f"简版PDF: {result['simple_pdf']}")
    else:
        print("用法: python pdf_converter.py <pdf文件路径>")
