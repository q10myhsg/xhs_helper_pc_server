import random
import time
import logging
from typing import Tuple, Optional
import uiautomator2 as u2

logger = logging.getLogger(__name__)

def random_delay(min_delay: float = 1.0, max_delay: float = 3.0):
    """
    随机延迟
    :param min_delay: 最小延迟时间（秒）
    :param max_delay: 最大延迟时间（秒）
    """
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)
    logger.debug(f"随机延迟 {delay:.2f} 秒")

def get_screen_size(device: u2.Device) -> Optional[Tuple[int, int]]:
    """
    获取屏幕尺寸
    :param device: 设备实例
    :return: (宽度, 高度) 元组
    """
    try:
        size = device.window_size()
        logger.debug(f"屏幕尺寸: {size}")
        return size
    except Exception as e:
        logger.error(f"获取屏幕尺寸失败: {e}")
        return None

def get_effective_screen_area(device: u2.Device) -> Optional[dict]:
    """
    获取屏幕的有效区域（高度20%~95%，宽度10%~90%）
    :param device: 设备实例
    :return: 有效区域的bounds {'left': left, 'top': top, 'right': right, 'bottom': bottom}
    """
    try:
        screen_width, screen_height = get_screen_size(device)
        if not screen_width or not screen_height:
            return None
        
        # 计算有效区域
        effective_left = int(screen_width * 0.1)
        effective_top = int(screen_height * 0.2)
        effective_right = int(screen_width * 0.9)
        effective_bottom = int(screen_height * 0.95)
        
        return {
            'left': effective_left,
            'top': effective_top,
            'right': effective_right,
            'bottom': effective_bottom
        }
    except Exception as e:
        logger.error(f"获取有效屏幕区域失败: {e}")
        return None

def calculate_bounds_intersection(bounds: dict, effective_area: dict) -> Optional[dict]:
    """
    计算元素bounds与屏幕有效区域的交集
    :param bounds: 元素的bounds {'left': left, 'top': top, 'right': right, 'bottom': bottom}
    :param effective_area: 有效区域的bounds
    :return: 交集区域的bounds，如果没有交集则返回None
    """
    try:
        if not bounds or not effective_area:
            return None
        
        # 计算交集
        intersection_left = max(bounds['left'], effective_area['left'])
        intersection_top = max(bounds['top'], effective_area['top'])
        intersection_right = min(bounds['right'], effective_area['right'])
        intersection_bottom = min(bounds['bottom'], effective_area['bottom'])
        
        # 检查是否有交集
        if intersection_left < intersection_right and intersection_top < intersection_bottom:
            return {
                'left': intersection_left,
                'top': intersection_top,
                'right': intersection_right,
                'bottom': intersection_bottom
            }
        else:
            logger.info(f"元素bounds与有效区域没有交集: {bounds}")
            return None
    except Exception as e:
        logger.error(f"计算bounds交集失败: {e}")
        return None

def random_click_inside_bounds(device: u2.Device, bounds: dict) -> bool:
    """
    在指定区域内随机点击
    :param device: 设备实例
    :param bounds: 区域bounds
    :return: 是否点击成功
    """
    try:
        if not bounds:
            return False
        
        x = random.uniform(bounds['left'], bounds['right'])
        y = random.uniform(bounds['top'], bounds['bottom'])
        device.click(x, y)
        logger.debug(f"随机点击坐标: ({x:.0f}, {y:.0f})")
        return True
    except Exception as e:
        logger.error(f"随机点击失败: {e}")
        return False

def safe_click(device: u2.Device, element, max_attempts: int = 3) -> bool:
    """
    安全点击元素
    :param device: 设备实例
    :param element: 元素对象
    :param max_attempts: 最大尝试次数
    :return: 是否点击成功
    """
    for attempt in range(max_attempts):
        try:
            if element.exists:
                element.click()
                logger.debug(f"点击元素成功，尝试次数: {attempt + 1}")
                random_delay(0.5, 1.5)
                return True
            else:
                logger.warning(f"元素不存在，尝试次数: {attempt + 1}")
                random_delay(1, 2)
        except Exception as e:
            logger.error(f"点击元素失败: {e}")
            random_delay(1, 2)
    return False

def scroll_randomly(device: u2.Device, min_distance_ratio: float = 0.3, max_distance_ratio: float = 0.7):
    """
    随机滚动页面
    :param device: 设备实例
    :param min_distance_ratio: 最小滚动距离比例
    :param max_distance_ratio: 最大滚动距离比例
    """
    try:
        screen_width, screen_height = get_screen_size(device)
        if not screen_width or not screen_height:
            return
        
        # 随机滚动距离
        scroll_distance = random.randint(int(screen_height * min_distance_ratio), int(screen_height * max_distance_ratio))
        
        # 向上滚动
        start_y = screen_height * 0.7
        end_y = screen_height * 0.3
        device.swipe(screen_width // 2, start_y, screen_width // 2, end_y, 0.2)
        logger.debug(f"随机滚动: 向上滚动{scroll_distance}像素")
    except Exception as e:
        logger.error(f"随机滚动失败: {e}")

def format_time(seconds: int) -> str:
    """
    格式化时间
    :param seconds: 秒数
    :return: 格式化后的时间字符串
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}小时{minutes}分钟{seconds}秒"
    elif minutes > 0:
        return f"{minutes}分钟{seconds}秒"
    else:
        return f"{seconds}秒"

def validate_keywords(keywords: list) -> bool:
    """
    验证关键词列表
    :param keywords: 关键词列表
    :return: 是否有效
    """
    if not isinstance(keywords, list):
        return False
    
    # 允许空列表通过验证（清除全部关键词的情况）
    if len(keywords) == 0:
        return True
    
    for keyword in keywords:
        if not isinstance(keyword, str) or not keyword.strip():
            return False
    
    return True

def validate_comment_templates(templates: list) -> bool:
    """
    验证评论模板列表
    :param templates: 评论模板列表
    :return: 是否有效
    """
    if not isinstance(templates, list):
        return False
    
    if len(templates) == 0:
        return False
    
    for template in templates:
        if not isinstance(template, str) or not template.strip():
            return False
    
    return True

def simulate_typing(selector, text: str, delay_per_char: float = 1):
    """
    模拟人类打字，一个字符一个字符地输入
    :param selector: 元素选择器
    :param text: 要输入的文本
    :param delay_per_char: 每个字符之间的延迟（秒）
    """
    try:
        logger.info(f"模拟输入文本: {text}")
        
        # 先清空输入框
        selector.clear_text()
        random_delay(0.5, 1.0)
        
        # 逐字输入
        current_text = ""
        for char in text:
            current_text += char
            selector.set_text(current_text)
            delay = random.uniform(delay_per_char * 0.8, delay_per_char * 1.2)
            time.sleep(delay)
            logger.debug(f"输入字符: '{char}', 延迟: {delay:.2f}秒")
        
        random_delay(0.5, 1.0)
        logger.info("模拟输入完成")
        return True
    except Exception as e:
        logger.error(f"模拟输入失败: {e}")
        # 失败时使用普通输入作为备用
        try:
            selector.set_text(text)
            logger.warning("使用普通输入作为备用")
            return True
        except:
            return False