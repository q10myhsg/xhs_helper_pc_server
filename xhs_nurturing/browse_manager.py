import random
import time
import logging
from typing import List, Optional
import uiautomator2 as u2
from .utils import random_delay, get_screen_size, random_click_inside_bounds, scroll_randomly, safe_click, simulate_typing

class BrowseManager:
    """浏览管理器"""
    
    def __init__(self):
        """初始化浏览管理器"""
        self.logger = logging.getLogger(__name__)
    
    def browse_recommended_notes(self, device: u2.Device, browse_time: int, max_notes_to_open: int = 10, config: dict = None) -> bool:
        """
        在推荐页浏览笔记
        :param device: 设备实例
        :param browse_time: 浏览总时间（秒）
        :param max_notes_to_open: 随机打开笔记的最大数量
        :param config: 配置字典
        :return: 是否成功
        """
        try:
            # 默认配置
            if config is None:
                config = {}
            
            self.logger.info(f"开始在推荐页浏览，总时长: {browse_time}秒，最多打开{max_notes_to_open}篇笔记")
            
            start_time = time.time()
            notes_opened = 0
            
            while time.time() - start_time < browse_time:
                random_delay()
                # 随机决定是否打开一篇笔记
                if notes_opened < max_notes_to_open:
                    if self._open_random_note(device, config):
                        notes_opened += 1
                        # 返回推荐页
                        device.press('back')
                        random_delay(2, 3)
                
                # 随机滚动
                scroll_randomly(device)
                random_delay(1, 3)
        
            self.logger.info(f"浏览完成，共打开{notes_opened}篇笔记")
            return True
        except Exception as e:
            self.logger.error(f"浏览过程中发生错误: {e}")
            return False
    
    def start_xiaohongshu(self, device: u2.Device) -> bool:
        """
        启动小红书应用
        :param device: 设备实例
        :return: 是否成功
        """
        try:
            self.logger.info("启动小红书应用")
            # 启动小红书包名
            device.app_start("com.xingin.xhs")
            random_delay(5, 8)  # 给应用启动时间
            
            # 检查是否启动成功
            if device.app_wait("com.xingin.xhs", timeout=10):
                self.logger.info("小红书启动成功")
                return True
            else:
                self.logger.error("小红书启动失败")
                return False
        except Exception as e:
            self.logger.error(f"启动小红书失败: {e}")
            return False
    
    def browse_discovery_page(self, device: u2.Device, browse_time: int, config: dict = None, stop_check_callback=None) -> bool:
        """
        在发现页浏览
        :param device: 设备实例
        :param browse_time: 浏览时间（秒）
        :param config: 配置字典
        :param stop_check_callback: 停止检查回调函数
        :return: 是否成功
        """
        try:
            # 默认配置
            if config is None:
                config = {}
            
            self.logger.info(f"在发现页浏览 {browse_time} 秒")
            
            start_time = time.time()
            
            while time.time() - start_time < browse_time:
                # 检查是否需要停止
                if stop_check_callback and stop_check_callback():
                    self.logger.info("收到停止请求，终止发现页浏览")
                    return True
                
                random_delay()
                # 随机滚动
                scroll_randomly(device)
                random_delay(2, 4)
                
                # 检查是否需要停止
                if stop_check_callback and stop_check_callback():
                    self.logger.info("收到停止请求，终止发现页浏览")
                    return True
            
            self.logger.info("发现页浏览完成")
            return True
        except Exception as e:
            self.logger.error(f"发现页浏览失败: {e}")
            return False
    
    def search_and_browse(self, device: u2.Device, keyword: str, config: dict, max_posts: int = 10, device_id: str = None, stop_check_callback=None, count_callback=None) -> int:
        """
        搜索关键词并浏览相关内容
        :param device: 设备实例
        :param keyword: 搜索关键词
        :param config: 配置字典
        :param max_posts: 每个关键词浏览的帖子数量
        :param device_id: 设备ID
        :param stop_check_callback: 停止检查回调函数
        :param count_callback: 计数回调函数，每次浏览完成一个笔记时调用
        :return: 访问帖子的数量
        """
        try:
            # 检查设备是否在线
            if not device:
                self.logger.error("设备未连接")
                return 0
            
            self.logger.info(f"搜索关键词: {keyword}, 计划浏览 {max_posts} 个帖子")
            
            # 检查是否需要停止
            if stop_check_callback and stop_check_callback():
                self.logger.info("收到停止请求，终止搜索浏览")
                return 0
            
            # 1. 打开搜索框
            if not self._open_search(device):
                return 0
            
            # 检查是否需要停止
            if stop_check_callback and stop_check_callback():
                self.logger.info("收到停止请求，终止搜索浏览")
                return 0
            
            # 2. 输入关键词
            if not self._input_search_keyword(device, keyword):
                return 0
            
            # 检查是否需要停止
            if stop_check_callback and stop_check_callback():
                self.logger.info("收到停止请求，终止搜索浏览")
                return 0
            
            # 3. 执行搜索
            if not self._execute_search(device):
                return 0
            
            # 检查是否需要停止
            if stop_check_callback and stop_check_callback():
                self.logger.info("收到停止请求，终止搜索浏览")
                return 0
            
            # 4. 浏览搜索结果
            visited_count = 0
            scroll_count = 0
            # max_scrolls = max_posts * 2  # 确保能找到足够的帖子
            
            while visited_count < max_posts :                # 检查是否需要停止
                if stop_check_callback and stop_check_callback():
                    self.logger.info("收到停止请求，终止搜索浏览")
                    return visited_count
                
                # 访问帖子
                if self._visit_post(device, config):
                        
                        # 访问帖子详情
                        duration_range = config.get('visit_control', {}).get('duration_range', [25, 45])
                        self._visit_post_detail(device, duration_range, config, stop_check_callback)
                        visited_count += 1
                        # 如果提供了计数回调函数，调用它通知NurturingManager增加访问计数
                        if count_callback:
                            count_callback()
                        # 如果提供了设备ID，通知NurturingManager增加访问计数
                        if device_id:
                            # 这里需要调用NurturingManager的increment_visited_count方法
                            # 由于BrowseManager没有直接引用NurturingManager，这里需要通过其他方式实现
                            pass
                        # 返回列表
                        device.press("back")
                        random_delay(2, 3)
                
                # 检查是否需要停止
                if stop_check_callback and stop_check_callback():
                    self.logger.info("收到停止请求，终止搜索浏览")
                    return visited_count
                
                # 滑动到下一个帖子
                scroll_randomly(device)
                random_delay(1, 3)
                scroll_count += 1
            
            self.logger.info(f"关键词 {keyword} 浏览完成，共访问 {visited_count} 个帖子")
            return visited_count
        except Exception as e:
            self.logger.error(f"搜索浏览失败: {e}")
            return 0
    
    def _open_search(self, device: u2.Device) -> bool:
        """
        打开搜索框
        :param device: 设备实例
        :return: 是否成功
        """
        try:
            # 尝试多种可能的搜索按钮选择器
            search_selectors = [
                # device(resourceId="com.xingin.xhs:id/search_bar", focusable=True),
                # device(resourceId="com.xingin.xhs:id/search_button", clickable=True),
                device(description="搜索", className="android.widget.Button", clickable=True),
                # device(text="搜索", className="android.widget.Button", clickable=True),
                # device(text="搜索", clickable=True)
            ]
            for selector in search_selectors:
                if selector.exists:
                    if safe_click(device, selector):
                        random_delay(1, 2)
                        return True
            search_selectors2 = [
                device(text="搜索", className="android.widget.TextView", clickable=True),
                device(text="搜索", className="android.widget.Button", clickable=True)
            ]

            for selector in search_selectors2:
                if selector.exists:
                    return True
            
            self.logger.warning("未找到搜索按钮")
            return False
        except Exception as e:
            self.logger.error(f"打开搜索框失败: {e}")
            return False
    
    def _input_search_keyword(self, device: u2.Device, keyword: str) -> bool:
        """
        输入搜索关键词
        :param device: 设备实例
        :param keyword: 搜索关键词
        :return: 是否成功
        """
        try:

            # 清除搜索框内容
            clear_selectors=[
                device(description="全部删除", clickable=True)
            ]
            for selector in clear_selectors:
                    safe_click(device, selector)
                    random_delay(1, 2)
            # 尝试多种可能的搜索输入框选择器
            input_selectors = [
                # device(resourceId="com.xingin.xhs:id/search_input", focusable=True),
                # device(resourceId="com.xingin.xhs:id/search_edit_text", focusable=True),
                device(className="android.widget.EditText", textContains="搜索", focusable=True)
            ]
            
            for selector in input_selectors:
                if selector.exists:
                    simulate_typing(selector, keyword)
                    self.logger.debug(f"输入搜索关键词: {keyword}")
                    random_delay(1, 2)
                    return True
            
            self.logger.warning("未找到搜索输入框")
            return False
        except Exception as e:
            self.logger.error(f"输入搜索关键词失败: {e}")
            return False
    
    def _execute_search(self, device: u2.Device) -> bool:
        """
        执行搜索
        :param device: 设备实例
        :return: 是否成功
        """
        try:
            # 按回车执行搜索
            device.press("enter")
            random_delay(2, 4)
            return True
        except Exception as e:
            self.logger.error(f"执行搜索失败: {e}")
            return False
    
    def _open_random_note(self, device: u2.Device, config: dict) -> bool:
        """
        随机打开一篇笔记
        :param device: 设备实例
        :param config: 配置字典
        :return: 是否成功
        """
        try:
            # 获取访问概率配置
            post_visit_ratio = config.get('post_visit_ratio', 22) / 100.0  # 默认22%
            
            # 检查是否命中访问概率
            if random.random() < post_visit_ratio:
                # 在推荐页找到所有笔记卡片
                notes = device(className="androidx.recyclerview.widget.RecyclerView").child(className="android.widget.FrameLayout")
                
                if not notes.exists:
                    self.logger.warning("未找到笔记卡片")
                    return False
                
                # 筛选可见的笔记
                visible_notes = [note for note in notes if note.info.get('visible', False)]
                if not visible_notes:
                    self.logger.warning("未找到可见的笔记卡片")
                    return False
                
                # 随机选择一篇笔记
                random_note = random.choice(visible_notes)
                
                if random_note.exists:
                    # 点击笔记
                    bounds = random_note.info.get('bounds')
                    if bounds:
                        x = random.uniform(bounds['left'], bounds['right'])
                        y = random.uniform(bounds['top'], bounds['bottom'])
                        device.click(x, y)
                        self.logger.info("随机打开了一篇笔记")
                        random_delay(2, 3)
                        # 浏览图片笔记
                        from .interaction_manager import InteractionManager
                        interaction_manager = InteractionManager()
                        interaction_manager.view_image_note_with_interaction(device, config)
                        return True
                
                self.logger.warning("无法打开选中的笔记")
                return False
            else:
                self.logger.debug(f"未命中访问概率 ({post_visit_ratio:.2f})，跳过打开笔记")
                return False
        except Exception as e:
            self.logger.error(f"打开随机笔记失败: {e}")
            return False
    
    def _calculate_bounds_intersection(self, device, bounds):
        """
        计算元素bounds与屏幕有效区域的交集
        :param device: 设备实例
        :param bounds: 元素的bounds
        :return: 有效点击区域的bounds
        """
        try:
            # 从设备获取屏幕尺寸
            screen_width = 1080  # 默认值
            screen_height = 1920  # 默认值
            
            try:
                device_info = device.info
                if device_info:
                    screen_width = device_info.get('displayWidth', 1080)
                    screen_height = device_info.get('displayHeight', 1920)
                    self.logger.debug(f"从设备获取屏幕尺寸: {screen_width}x{screen_height}")
            except Exception as e:
                self.logger.warning(f"获取设备屏幕尺寸失败，使用默认值: {e}")
            
            # 计算交集
            effective_left = max(bounds.get('left', 0), 0)
            effective_top = max(bounds.get('top', 0), screen_height*0.2)
            effective_right = min(bounds.get('right', screen_width), screen_width)
            effective_bottom = min(bounds.get('bottom', screen_height), screen_height)
            
            # 确保有效区域存在
            if effective_left < effective_right and effective_top < effective_bottom:
                # 避开边缘15像素
                padding = 15
                effective_left += padding
                effective_top += padding
                effective_right -= padding
                effective_bottom -= padding
                
                # 再次确保有效区域存在
                if  effective_right-effective_left>100 and effective_bottom-effective_top >100 :
                    return {
                        'left': effective_left,
                        'top': effective_top,
                        'right': effective_right,
                        'bottom': effective_bottom
                    }
            return None
        except Exception as e:
            self.logger.error(f"计算有效点击区域失败: {e}")
            return None
    

    
    def _visit_post(self, device: u2.Device, config: dict) -> bool:
        """
        访问帖子
        :param device: 设备实例
        :param config: 配置字典
        :return: 是否成功
        """
        try:
            # 获取访问概率配置
            post_visit_ratio = config.get('post_visit_ratio', 22) / 100.0  # 默认22%
            
            # 尝试从搜索结果中打开帖子（参考_open_note_from_search方法）
            # 找到搜索结果中的笔记卡片
            recycler_view = device(className="androidx.recyclerview.widget.RecyclerView")
            if recycler_view.exists:
                # 尝试从RecyclerView中找到帖子的图片
                notes = recycler_view.child(className="android.widget.ImageView")
                if notes.exists:
                    # 尝试获取所有可见的笔记
                    note_list = []
                    try:
                        # 尝试获取笔记数量，使用notes.length和10的最小值
                        max_attempts = 10
                        try:
                            # 尝试获取notes的长度
                            notes_count = len(notes)
                            max_attempts = min(notes_count, 10)
                            self.logger.debug(f"找到 {notes_count} 个笔记，最多尝试 {max_attempts} 个")
                        except Exception as e:
                            self.logger.debug(f"获取笔记数量失败，使用默认值10: {e}")
                        
                        # 使用while循环遍历笔记
                        i = 0
                        while i < max_attempts:
                            try:
                                note = notes[i]
                                if note.exists:
                                    bounds = note.info.get('bounds', {})
                                    if bounds:
                                        # 先判断有效点击区域，只把有效的note放进列表
                                        effective_bounds = self._calculate_bounds_intersection(device, bounds)
                                       
                                        if effective_bounds:
                                            note_list.append(note)
                                            self.logger.debug(f"添加有效笔记 {i} 到列表")
                                        else:
                                            self.logger.debug(f"笔记 {i} 超出有效点击区域，跳过")
                            except Exception as e:
                                self.logger.debug(f"获取笔记 {i} 失败: {e}")
                            finally:
                                i += 1
                    except Exception as e:
                        self.logger.debug(f"获取笔记列表失败: {e}")
                    
                    # 如果找到笔记，随机选择一个
                    if note_list:
                        for note in note_list:
                            # 对每个帖子应用概率判断
                            if random.random() < post_visit_ratio:
                                # 点击笔记
                                bounds = note.info.get('bounds')
                                if bounds:
                                    # 计算有效点击区域（元素bounds与屏幕有效区域的交集）
                                    effective_bounds = self._calculate_bounds_intersection(device, bounds)
                                    if effective_bounds:
                                        # 在有效区域内随机选择点击位置，避开边缘15像素
                                        x = random.uniform(effective_bounds['left'], effective_bounds['right'])
                                        y = random.uniform(effective_bounds['top'], effective_bounds['bottom'])
                                        device.click(x, y)
                                        self.logger.info("从搜索结果中打开了一篇帖子")
                                        random_delay(2, 3)
                                        return True
                                    else:
                                        self.logger.info(f"帖子超出有效点击区域，跳过该帖子: {bounds}")
                                else:
                                    self.logger.debug(f"帖子边界信息不存在，跳过")
                            else:
                                self.logger.debug(f"未命中访问概率 ({post_visit_ratio:.2f})，跳过当前帖子")
            # 如果上面的方法失败，尝试传统的选择器方法
            self.logger.warning("未找到可点击的帖子")
            return False
        except Exception as e:
            self.logger.error(f"访问帖子失败: {e}")
            return False
    
    def _visit_post_detail(self, device: u2.Device, duration_range: List[int], config: dict, stop_check_callback=None):
        """
        访问帖子详情
        :param device: 设备实例
        :param duration_range: 浏览时间范围
        :param config: 配置字典
        :param stop_check_callback: 停止检查回调函数
        """
        try:
            # 检查是否需要停止
            if stop_check_callback and stop_check_callback():
                self.logger.info("收到停止请求，终止访问帖子详情")
                return
            
            # 检查设备是否在线
            try:
                device.info
            except Exception as e:
                self.logger.error(f"设备离线: {e}")
                return
                
            # 随机访问时长
            visit_duration = random.randint(duration_range[0], duration_range[1])
            self.logger.info(f"访问帖子详情，预计停留 {visit_duration} 秒")
            
            # 浏览图片笔记并执行互动操作
            from .interaction_manager import InteractionManager
            interaction_manager = InteractionManager()
            interaction_manager.view_image_note_with_interaction(device, config)
            
            # 执行互动行为（点赞、收藏、评论）
            # self.logger.info("执行互动行为")
            # interaction_manager.do_interaction(device, config)
            
        except Exception as e:
            self.logger.error(f"访问帖子详情失败: {e}")
    
