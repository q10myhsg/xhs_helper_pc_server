#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF转图片转换器
支持水印、页眉、页脚添加
"""

from pdf2image import convert_from_path
from PIL import Image
import os
import random
from pathlib import Path

# 兼容不同版本的Pillow
# Pillow 9.0.0+ 使用 Image.Resampling.LANCZOS
# 旧版本使用 Image.LANCZOS 或 Image.ANTIALIAS
try:
    RESAMPLING_LANCZOS = Image.Resampling.LANCZOS
except AttributeError:
    try:
        RESAMPLING_LANCZOS = Image.LANCZOS
    except AttributeError:
        RESAMPLING_LANCZOS = Image.ANTIALIAS


class PDFConverter:
    def __init__(self, watermark_path=None, header_path=None, footer_path=None, upload_folder='static/uploads', watermark_scale=100, icons_folder='static/pdf_images/icons'):
        """
        初始化PDF转换器
        
        参数:
            watermark_path: 水印图片路径，默认使用 resources/imgs/default_watermark.png
            header_path: 页眉图片路径
            footer_path: 页脚图片路径
            upload_folder: 上传文件保存目录
            watermark_scale: 水印缩放比例（百分比），默认100表示原图大小
            icons_folder: 图标文件夹路径，默认使用 static/pdf_images/icons
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
        self.watermark_scale = watermark_scale  # 水印缩放比例
        
        # 图标文件夹
        self.icons_folder = str(self.base_dir / icons_folder)
        
        # 加载图片
        self.watermark_img = self._load_image(self.watermark_path)
        self.header_img = self._load_image(self.header_path) if self.header_path else None
        self.footer_img = self._load_image(self.footer_path) if self.footer_path else None
        
        # 加载图标列表
        self.icon_images = self._load_icons()
    
    def _load_image(self, path):
        """加载图片"""
        if not path:
            return None
        
        # 处理URL路径（以/static开头）转换为文件系统路径
        if path.startswith('/static/'):
            # 移除开头的/，转换为相对路径
            relative_path = path[1:]  # 去掉开头的/
            full_path = str(self.base_dir / relative_path)
        else:
            full_path = path
        
        if os.path.exists(full_path):
            return Image.open(full_path).convert("RGBA")
        return None
    
    def _load_icons(self):
        """加载图标文件夹中的所有图标"""
        icon_images = []
        
        if not os.path.exists(self.icons_folder):
            print(f"图标文件夹不存在: {self.icons_folder}")
            return icon_images
        
        # 遍历文件夹，加载所有图片文件
        for filename in os.listdir(self.icons_folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                icon_path = os.path.join(self.icons_folder, filename)
                try:
                    icon_img = Image.open(icon_path).convert("RGBA")
                    icon_images.append(icon_img)
                except Exception as e:
                    print(f"加载图标失败 {filename}: {e}")
        
        print(f"已加载 {len(icon_images)} 个图标")
        return icon_images
    
    def _add_random_icon_to_image(self, img, icon_size=None, position=None):
        """
        为图片添加随机图标
        
        参数:
            img: 目标图片
            icon_size: 图标大小（像素），默认使用图标原始大小
            position: 位置 {'x': 0-100, 'y': 0-100}，默认随机位置
            
        返回:
            Image: 处理后的图片
        """
        if not self.icon_images:
            return img
        
        img_width, img_height = img.size
        
        # 随机选择一个图标
        icon = random.choice(self.icon_images)
        
        # 如果没有指定图标大小，使用图标原始大小
        if icon_size is None:
            new_icon_width = icon.size[0]
            new_icon_height = icon.size[1]
        else:
            # 调整图标大小
            icon_aspect = icon.size[0] / icon.size[1]
            new_icon_width = icon_size
            new_icon_height = int(icon_size / icon_aspect)
        
        icon_resized = icon.resize((new_icon_width, new_icon_height), RESAMPLING_LANCZOS)
        
        # 计算位置
        if position:
            x_percent = position.get('x', 0.5)
            y_percent = position.get('y', 0.5)
            x = int((img_width - new_icon_width) * x_percent)
            y = int((img_height - new_icon_height) * y_percent)
        else:
            # 随机位置，避免太靠近边缘
            margin = 50
            x = random.randint(margin, img_width - new_icon_width - margin)
            y = random.randint(margin, img_height - new_icon_height - margin)
        
        # 创建透明层
        transparent = Image.new('RGBA', img.size, (0, 0, 0, 0))
        transparent.paste(icon_resized, (x, y), icon_resized)
        
        # 合并
        result = Image.alpha_composite(img, transparent)
        return result
    
    def get_pdf_page_count(self, pdf_path):
        """
        获取PDF文件的总页数
        
        参数:
            pdf_path: PDF文件路径
            
        返回:
            int: 总页数
        """
        try:
            # 尝试使用PyPDF2获取页数
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)
            return total_pages
        except Exception as e:
            print(f"获取PDF页数失败: {e}")
            return 0
    
    def parse_page_range(self, page_range_str, total_pages):
        """
        解析页码范围字符串
        
        支持的格式:
        - "odd": 奇数页
        - "even": 偶数页
        - "all": 全部页面
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
        
        # 全部页面
        if page_range_str == 'all':
            return set(range(1, total_pages + 1))
        
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
                              footer_position=None,
                              output_dir=None,
                              border_width=0, border_color='#000000',
                              background_color='#ffffff',
                              add_random_icon=False, icon_size=None, icon_position=None):
        """
        将PDF转换为图片

        参数:
            pdf_path: PDF文件路径
            dpi: 输出图片DPI
            fmt: 输出格式 (png, jpg)
            add_watermark: 是否添加水印
            generate_simple_pdf: 是否生成精简版PDF（前3页，无处理）
            start_page: 起始页码
            end_page: 结束页码
            add_header: 是否添加页眉
            add_footer: 是否添加页脚
            watermark_page_range: 水印页面范围 ('odd', 'even', 'all', 或自定义)
            watermark_position: 水印位置 {'x': 0-100, 'y': 0-100}
            header_position: 页眉位置 {'top': 像素值}
            footer_position: 页脚位置 {'bottom': 像素值}
            output_dir: 输出目录（可选，默认使用PDF所在目录/imgs/文件名/）
            border_width: 边框宽度（像素），0表示不显示边框
            border_color: 边框颜色（十六进制颜色码）
            background_color: 背景颜色（十六进制颜色码）
            add_random_icon: 是否添加随机图标
            icon_size: 图标大小（像素）
            icon_position: 图标位置 {'x': 0-100, 'y': 0-100}，默认随机位置

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
        end = min(total_pages, end_page) if end_page is not None else total_pages
        print(f"[PDF转换] 实际转换范围: {start+1} - {end} (共 {end - start} 页)")

        # 解析水印页面范围
        watermark_pages = self.parse_page_range(watermark_page_range, total_pages)

        # 创建输出目录
        if output_dir:
            # 使用指定的输出目录
            output_dir = Path(output_dir)
        else:
            # 默认使用PDF相同文件夹/imgs/文件名/
            output_dir = pdf_path.parent / "imgs" / pdf_path.stem
        
        # 记录原始目标目录（用于后续清理）
        original_output_dir = output_dir
        use_fallback = False
        
        # 尝试创建目录，如果失败则使用备用目录
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            # 如果没有权限写入目标目录，使用服务器static目录作为备用
            use_fallback = True
            fallback_dir = self.base_dir / "static" / "outputs" / pdf_path.stem
            fallback_dir.mkdir(parents=True, exist_ok=True)
            output_dir = fallback_dir
            print(f"警告: 无法写入 {original_output_dir}，使用备用目录: {fallback_dir}")
            
            # 尝试删除原目录（如果存在且为空）
            try:
                if original_output_dir.exists():
                    # 检查目录是否为空
                    if not any(original_output_dir.iterdir()):
                        original_output_dir.rmdir()
                        # 尝试删除父目录 imgs（如果为空）
                        imgs_parent = original_output_dir.parent
                        if imgs_parent.exists() and not any(imgs_parent.iterdir()):
                            imgs_parent.rmdir()
                        print(f"已清理空目录: {original_output_dir}")
            except Exception as cleanup_error:
                print(f"清理目录失败: {cleanup_error}")

        output_paths = []

        # 计算页码位数，用于格式化
        page_digits = len(str(total_pages))

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
            
            # 只有在边框宽度大于0时才添加边框和背景色
            if border_width > 0:
                img = self._add_border_and_background(
                    img, 
                    border_width=border_width, 
                    border_color=border_color, 
                    background_color=background_color,
                    scale=0.9
                )
            
            # 添加随机图标
            if add_random_icon:
                img = self._add_random_icon_to_image(img, icon_size=icon_size, position=icon_position)

            # 保存图片 - 使用动态位数格式化页码
            formatted_page = str(page_num).zfill(page_digits)
            output_filename = f"{pdf_path.stem}_page_{formatted_page}.{fmt}"
            output_path = output_dir / output_filename

            # 尝试保存，如果失败且是第一次保存，切换到备用目录
            try:
                # 转换为RGB保存（去除透明通道）
                if fmt.lower() in ['jpg', 'jpeg']:
                    img_rgb = img.convert("RGB")
                    img_rgb.save(output_path, quality=95)
                else:
                    img.save(output_path)
            except (PermissionError, OSError) as save_error:
                if not use_fallback and i == start:
                    # 第一次保存失败，切换到备用目录
                    use_fallback = True
                    fallback_dir = self.base_dir / "static" / "outputs" / pdf_path.stem
                    fallback_dir.mkdir(parents=True, exist_ok=True)
                    output_dir = fallback_dir
                    print(f"警告: 无法写入 {original_output_dir}，切换到备用目录: {fallback_dir}")
                    
                    # 尝试删除原目录（如果存在且为空）
                    try:
                        if original_output_dir.exists():
                            if not any(original_output_dir.iterdir()):
                                original_output_dir.rmdir()
                                imgs_parent = original_output_dir.parent
                                if imgs_parent.exists() and not any(imgs_parent.iterdir()):
                                    imgs_parent.rmdir()
                                print(f"已清理空目录: {original_output_dir}")
                    except Exception as cleanup_error:
                        print(f"清理目录失败: {cleanup_error}")
                    
                    # 重新保存到备用目录
                    output_path = output_dir / output_filename
                    if fmt.lower() in ['jpg', 'jpeg']:
                        img_rgb = img.convert("RGB")
                        img_rgb.save(output_path, quality=95)
                    else:
                        img.save(output_path)
                else:
                    raise save_error

            output_paths.append(str(output_path))

        # 生成精简版PDF（前3页，无水印等处理）
        simple_pdf_path = None
        if generate_simple_pdf:
            # 取前3页（或更少如果PDF页数不足）
            simple_page_count = min(3, total_pages)
            simple_images = []

            for i in range(simple_page_count):
                # 使用原始图片，不做任何处理
                img = images[i].convert("RGB")
                simple_images.append(img)

            if simple_images:
                simple_pdf_filename = f"{pdf_path.stem}_simple.pdf"
                simple_pdf_path = output_dir / simple_pdf_filename
                simple_images[0].save(
                    simple_pdf_path,
                    save_all=True,
                    append_images=simple_images[1:],
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
        
        wm_width, wm_height = watermark.size
        
        # 根据用户设置的缩放比例调整水印大小
        # watermark_scale 是百分比，100表示原图大小
        scale_percent = self.watermark_scale / 100.0
        
        # 计算新的尺寸
        new_width = int(wm_width * scale_percent)
        new_height = int(wm_height * scale_percent)
        
        # 确保水印不超过图片大小
        if new_width > img_width or new_height > img_height:
            scale = min(img_width / new_width, img_height / new_height, 1.0)
            new_width = int(new_width * scale)
            new_height = int(new_height * scale)
        
        watermark_resized = watermark.resize((new_width, new_height), RESAMPLING_LANCZOS)
        
        # 计算位置
        if position:
            x_percent = position.get('x', 0.5)
            y_percent = position.get('y', 0.5)
            x = int((img_width - new_width) * x_percent)
            y = int((img_height - new_height) * y_percent)
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
        header_resized = header.resize((header_width, header_height), RESAMPLING_LANCZOS)
        
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
        footer_resized = footer.resize((footer_width, footer_height), RESAMPLING_LANCZOS)
        
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
    
    def _add_border_and_background(self, img, border_width=0, border_color='#000000', background_color='#ffffff', scale=0.9):
        """
        为图片添加缩放、边框和背景色
        
        参数:
            img: 原始图片
            border_width: 边框宽度（像素）
            border_color: 边框颜色（十六进制颜色码）
            background_color: 背景颜色（十六进制颜色码）
            scale: 缩放比例（0-1之间）
            
        返回:
            Image: 处理后的图片
        """
        if border_width == 0 and scale == 1.0:
            return img
        
        # 解析颜色
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        border_rgb = hex_to_rgb(border_color)
        bg_rgb = hex_to_rgb(background_color)
        
        # 获取原始尺寸
        original_width, original_height = img.size
        
        # 按比例缩放图片
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        img_scaled = img.resize((new_width, new_height), RESAMPLING_LANCZOS)
        
        # 计算新图片的尺寸（包含背景 + 边框）
        # 背景大小等于原始图片大小
        final_width = original_width
        final_height = original_height
        
        # 创建背景图片
        final_img = Image.new('RGBA', (final_width, final_height), (*bg_rgb, 255))
        
        # 计算图片在背景中的位置（居中）
        x = (final_width - new_width - 2 * border_width) // 2
        y = (final_height - new_height - 2 * border_width) // 2
        
        # 如果有边框，先在背景上绘制边框
        if border_width > 0:
            from PIL import ImageDraw
            draw = ImageDraw.Draw(final_img)
            # 边框从图片位置向外扩展
            border_rect = [
                x,
                y,
                x + new_width + 2 * border_width - 1,
                y + new_height + 2 * border_width - 1
            ]
            for i in range(border_width):
                draw.rectangle([
                    border_rect[0] + i,
                    border_rect[1] + i,
                    border_rect[2] - i,
                    border_rect[3] - i
                ], outline=border_rgb)
        
        # 将缩放后的图片粘贴到中心位置（在边框内部）
        paste_x = x + border_width
        paste_y = y + border_width
        final_img.paste(img_scaled, (paste_x, paste_y), img_scaled)
        
        return final_img


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
