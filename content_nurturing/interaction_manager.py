import random
import logging
from typing import List, Optional
import uiautomator2 as u2
from .utils import random_delay, safe_click, simulate_typing

class InteractionManager:
    """互动管理器"""
    
    def __init__(self):
        """初始化互动管理器"""
        self.logger = logging.getLogger(__name__)
    
    def do_interaction(self, device: u2.Device, config: dict):
        """
        执行互动行为
        :param device: 设备实例
        :param config: 配置字典
        """
        interaction_cfg = config.get('interaction', {})
        
        # 点赞
        self.do_like(device, config=config)
        
        # 收藏
        self.do_collect(device, config=config)
        
        # 评论
        comments = interaction_cfg.get('comment_templates', [])
        self.do_comment(device, comments, config=config)
    
    def do_like(self, device: u2.Device, image_container=None, config=None) -> bool:
        """
        执行点赞
        :param device: 设备实例
        :param image_container: 图片容器
        :param config: 配置字典
        :return: 是否点赞成功
        """
        try:
            rand= random.random()
            like_probability = config.get('interaction', {}).get('like_prob', 50.0) if config else 50.0
            if rand< like_probability/100.0:
                # 如果没有传入image_container，尝试查找
                if not image_container:
                    image_container = self._find_image_container(device)
                
                if image_container:
                    # 从image_container获取边界信息并计算中心坐标
                    image_bounds = image_container.info.get('bounds', {})
                    if image_bounds:
                        image_width = image_bounds['right'] - image_bounds['left']
                        image_height = image_bounds['bottom'] - image_bounds['top']
                        center_x = image_bounds['left'] + image_width / 2
                        center_y = image_bounds['top'] + image_height / 2
                        device.double_click(center_x, center_y)
                        self.logger.info("双击图片点赞")
                        random_delay(1, 2)
                        return True
               
                self.logger.warning("未找到点赞按钮")
                return False
            else:
                self.logger.debug(f"未命中点赞概率 ({like_probability:.2f})，跳过点赞")
                return False
        except Exception as e:
            self.logger.error(f"点赞失败: {e}")
            return False
    
    def do_collect(self, device: u2.Device, config=None) -> bool:
        """
        执行收藏
        :param device: 设备实例
        :param config: 配置字典
        :return: 是否收藏成功
        """
        try:
            collect_probability = config.get('interaction', {}).get('collect_prob', 30.0) if config else 30.0
            if random.random() < collect_probability/100.0:
                # 查找收藏按钮
                collect_buttons = [
                    device(className="android.widget.Button",descriptionContains="收藏"),
                    # device(resourceId="com.xingin.xhs:id/collect_btn", clickable=True),
                    # device(resourceId="com.xingin.xhs:id/collect_button", clickable=True),
                    # device(description="收藏", clickable=True),
                    # device(text="收藏", clickable=True)
                ]
                for button in collect_buttons:
                    if button.exists:
                        if safe_click(device, button):
                            self.logger.info("点击收藏按钮")
                            random_delay(1, 2)
                            return True
                self.logger.warning("未找到收藏按钮")
                return False
            else:
                self.logger.debug(f"未命中收藏概率 ({collect_probability:.2f})，跳过收藏")
                return False
        except Exception as e:
            self.logger.error(f"收藏失败: {e}")
            return False
    
    def do_comment(self, device: u2.Device, comment_templates: List[str], config=None) -> bool:
        """
        执行评论
        :param device: 设备实例
        :param comment_templates: 评论模板列表
        :param config: 配置字典
        :return: 是否评论成功
        """
        try:
            comment_probability = config.get('interaction', {}).get('comment_prob', 0.2) if config else 0.2
            if random.random() < comment_probability/100.0:
                if not comment_templates:
                    self.logger.warning("评论模板列表为空")
                    return False
                
                # 查找评论按钮
                comment_buttons = [
                    device(className="android.widget.TextView", textContains="说点什么", descriptionContains="评论框"),
                    # device(resourceId="com.xingin.xhs:id/comment_btn", clickable=True),
                    # device(resourceId="com.xingin.xhs:id/comment_button", clickable=True),
                    # device(description="评论", clickable=True),
                    # device(text="评论", clickable=True)
                ]
                # 遍历所有可能的评论按钮
                for button in comment_buttons:
                    if button.exists:
                        if safe_click(device, button):
                            self.logger.info("点击评论按钮")
                            random_delay(1, 2)
                            
                            editText = device(className="android.widget.EditText")
                            if editText.exists:
                                if comment_templates:
                                    comment = random.choice(comment_templates)
                                    self.logger.info(f"准备评论: {comment}")
                                        
                                    # 输入评论内容
                                    # comment_input = device(className="android.widget.EditText")
                                    simulate_typing(editText, comment)
                                    random_delay(1, 2)
                                        
                                    # 查找发送按钮
                                    send_buttons = [
                                        device(className="android.widget.TextView", text="发送"),
                                        # device(resourceId="com.xingin.xhs:id/comment_send_btn", clickable=True),
                                        # device(resourceId="com.xingin.xhs:id/send_button", clickable=True),
                                        # device(text="发送", clickable=True),
                                        # device(description="发送", clickable=True)
                                    ]
                                        
                                    for send_button in send_buttons:
                                        if send_button.exists:
                                            if safe_click(device, send_button):
                                                self.logger.info("评论发送成功")
                                                random_delay(2, 3)
                                                return True
                            # 未找到评论输入框或发送按钮
                            random_delay(0.5, 1)
                            return False
                self.logger.warning("未找到评论按钮")
                return False
            else:
                self.logger.debug(f"未命中评论概率 ({comment_probability:.2f})，跳过评论")
                return False
        except Exception as e:
            self.logger.error(f"评论失败: {e}")
            try:
                random_delay(0.5, 1)
            except:
                pass
            return False
    
    def do_follow(self, device: u2.Device) -> bool:
        """
        执行关注
        :param device: 设备实例
        :return: 是否关注成功
        """
        try:
            # 尝试多种可能的关注按钮选择器
            follow_selectors = [
                device(resourceId="com.xingin.xhs:id/follow_btn", clickable=True),
                device(resourceId="com.xingin.xhs:id/follow_button", clickable=True),
                device(text="关注", clickable=True),
                device(description="关注", clickable=True)
            ]
            
            for selector in follow_selectors:
                if selector.exists:
                    if safe_click(device, selector):
                        self.logger.info("已关注")
                        random_delay(1, 2)
                        return True
            
            self.logger.warning("未找到关注按钮")
            return False
        except Exception as e:
            self.logger.error(f"关注失败: {e}")
            return False
    
    def do_share(self, device: u2.Device) -> bool:
        """
        执行分享
        :param device: 设备实例
        :return: 是否分享成功
        """
        try:
            # 尝试多种可能的分享按钮选择器
            share_selectors = [
                device(resourceId="com.xingin.xhs:id/share_btn", clickable=True),
                device(resourceId="com.xingin.xhs:id/share_button", clickable=True),
                device(text="分享", clickable=True),
                device(description="分享", clickable=True)
            ]
            
            for selector in share_selectors:
                if selector.exists:
                    if safe_click(device, selector):
                        self.logger.info("已打开分享面板")
                        random_delay(1, 2)
                        # 关闭分享面板
                        device.press("back")
                        random_delay(1, 2)
                        return True
            
            self.logger.warning("未找到分享按钮")
            return False
        except Exception as e:
            self.logger.error(f"分享失败: {e}")
            try:
                device.press("back")
            except:
                pass
            return False
    
    def _find_image_container(self, device):
        """
        查找图片容器
        :param device: 设备实例
        :return: 图片容器或None
        """
        try:
            frame_layouts = device(className="android.widget.FrameLayout")
            for fl in frame_layouts:
                try:
                    content_desc = fl.info.get('contentDescription', '')
                    if '图片' in content_desc:
                        return fl
                except Exception as e:
                    self.logger.debug(f"获取FrameLayout信息失败: {e}")
                    continue
            return None
        except Exception as e:
            self.logger.error(f"查找图片容器失败: {e}")
            return None
    
    def _extract_image_count(self, image_container):
        """
        提取图片数量
        :param image_container: 图片容器
        :return: 图片数量
        """
        try:
            content_desc = image_container.info.get('contentDescription', '')
            self.logger.info(f"图片容器contentDescription: {content_desc}")
            
            import re
            match = re.search(r'共(\d+)张', content_desc)
            if match:
                total_images = int(match.group(1))
                self.logger.info(f"识别到图片数量: {total_images}张")
                return total_images
            else:
                self.logger.warning("无法识别图片数量")
                return 1
        except Exception as e:
            self.logger.error(f"提取图片数量失败: {e}")
            return 1
    
    def _swipe_through_images(self, device, image_container, config=None):
        """
        滑动浏览图片
        :param device: 设备实例
        :param image_container: 图片容器
        :param config: 配置字典
        """
        try:
            # 检查是否需要停止
            # 由于现在通过杀死线程来停止养号，这里不再需要停止检查
            pass
            
            # 提取图片数量
            total_images = self._extract_image_count(image_container)
            # 确保total_images是整数
            total_images = int(total_images)
            # 实际可滑动次数为图片数-1（因为第一张已经显示）
            max_possible_swipe = max(0, total_images - 1)
            
            # 获取图片边界信息
            image_bounds = image_container.info.get('bounds', {})
            if not image_bounds:
                self.logger.warning("无法获取图片边界信息")
                return
            
            # 计算图片区域的宽高
            image_width = image_bounds['right'] - image_bounds['left']
            image_height = image_bounds['bottom'] - image_bounds['top']
            
            # 随机选择要浏览的图片数量
            if max_possible_swipe > 0:
                # 确保参数都是整数
                min_swipe = max(0, max_possible_swipe // 2)
                max_swipe = max_possible_swipe
                # 确保min_swipe <= max_swipe
                if min_swipe <= max_swipe:
                    num_images_to_view = random.randint(min_swipe, max_swipe)
                    self.logger.info(f"随机选择浏览 {num_images_to_view+1} 张图片")
                    
                    i = 0
                    while i < num_images_to_view:
                        # 检查是否需要停止
                        # 由于现在通过杀死线程来停止养号，这里不再需要停止检查
                        pass
                        # 20%的概率向左滑动（查看上一张）
                        if random.random() < 0.1 and i > 0:
                            # 从左向右滑动（查看上一张）
                            start_x = image_bounds['left'] + image_width * random.uniform(0.2, 0.4)
                            end_x = image_bounds['left'] + image_width * random.uniform(0.6, 0.8)
                            y = image_bounds['top'] + image_height * random.uniform(0.4, 0.6)
                            device.swipe(start_x, y, end_x, y, duration=0.1)
                            self.logger.info(f"向右滑动浏览第{i+1}张图片")
                            # 从配置中读取滑动间隔
                            slide_interval = config.get('visit_control', {}).get('slide_interval', [3, 5]) if config else [3, 5]
                            random_delay(slide_interval[0], slide_interval[1])
                            i -= 1
                        else:
                            # 从右向左滑动（查看下一张），使用图片容器的边界信息
                            start_x = image_bounds['left'] + image_width * random.uniform(0.6, 0.8)
                            end_x = image_bounds['left'] + image_width * random.uniform(0.2, 0.4)
                            y = image_bounds['top'] + image_height * random.uniform(0.4, 0.6)
                            device.swipe(start_x, y, end_x, y, duration=0.1)
                            self.logger.info(f"向左滑动浏览第{i+2}张图片")
                            # 从配置中读取滑动间隔
                            slide_interval = config.get('visit_control', {}).get('slide_interval', [3, 5]) if config else [3, 5]
                            random_delay(slide_interval[0], slide_interval[1])
                            i += 1
                else:
                    self.logger.warning(f"滑动范围无效: min={min_swipe}, max={max_swipe}")
            else:
                self.logger.info("只有1张图片，无需滑动")
        except Exception as e:
            self.logger.error(f"滑动浏览图片失败: {e}")
    
    def _get_screen_size(self, device):
        """
        获取屏幕尺寸
        :param device: 设备实例
        :return: (width, height)
        """
        try:
            device_info = device.info
            if device_info:
                screen_width = device_info.get('displayWidth', 1080)
                screen_height = device_info.get('displayHeight', 1920)
                return screen_width, screen_height
            return 1080, 1920
        except Exception as e:
            self.logger.error(f"获取屏幕尺寸失败: {e}")
            return 1080, 1920
    
    def _visit_user_homepage(self, device):
        """
        访问用户主页并向上滑动
        :param device: 设备实例
        :return: 是否访问成功
        """
        try:
            # 查找用户头像或用户名
            user_elements = [
                device(className="android.widget.TextView", resourceId="com.xingin.xhs:id/nickNameTV"),
            ]
            
            if not user_elements or len(user_elements) == 0: 
                self.logger.warning("未找到用户信息元素")
                return False
            
            user_element = user_elements[0]
            # 点击进入用户主页
            if safe_click(device, user_element):
                self.logger.info("进入用户主页")
                random_delay(2, 4)
                
                # 向上滑动2-3次
                screen_width, screen_height = self._get_screen_size(device)
                scroll_times = random.randint(2, 3)
                for i in range(scroll_times):
                    # 向上滚动
                    start_y = screen_height * random.uniform(0.7, 0.9)
                    end_y = screen_height * random.uniform(0.1, 0.3)
                    x = screen_width * random.uniform(0.4, 0.6)
                    device.swipe(x, start_y, x, end_y, duration=0.2)
                    self.logger.info(f"在用户主页向上滑动 {i+1}/{scroll_times}")
                    random_delay(1, 2)
                
                # 返回帖子页面
                device.press("back")
                self.logger.info("返回帖子页面")
                random_delay(0.5, 2)
                return True
            else:
                self.logger.warning("点击用户信息失败")
                return False
        except Exception as e:
            self.logger.error(f"访问用户主页失败: {e}")
            try:
                device.press("back")
            except:
                pass
            return False
    
    def view_image_note_with_interaction(self, device, config):
        """
        浏览图片笔记并执行互动操作
        :param device: 设备实例
        :param config: 配置字典
        :return: 是否为图片笔记
        """
        import time
        try:
            # 检查是否需要停止
            # 由于现在通过杀死线程来停止养号，这里不再需要停止检查
            pass
                
            # 记录开始时间
            start_time = time.time()
            
            # 查找图片容器
            image_container = self._find_image_container(device)
            if not image_container:
                self.logger.info("当前笔记不是图片笔记")
                random_delay(0.1, 0.5)
                return False

            # 检查是否需要停止
            # 由于现在通过杀死线程来停止养号，这里不再需要停止检查
            pass
                
            # 滑动浏览图片
            self._swipe_through_images(device, image_container, config)
            
            # 检查是否需要停止
            # 由于现在通过杀死线程来停止养号，这里不再需要停止检查
            pass
            if self.do_like(device, image_container, config):
                random_delay(1, 3)     
                           
            self._scroll_randomly(device)
            self.logger.info("向上滚动查看评论")

            random_delay(1, 3)
            
            # 检查是否需要停止
            # 由于现在通过杀死线程来停止养号，这里不再需要停止检查
            pass
                
            # 执行互动操作

                        #
                        # 浏览完图片后，向上滚动查看评论
            
            # 检查是否需要停止
            # 由于现在通过杀死线程来停止养号，这里不再需要停止检查
            pass
                
            if self.do_collect(device, config):
                random_delay(2, 5)
                
            # 检查是否需要停止
            # 由于现在通过杀死线程来停止养号，这里不再需要停止检查
            pass
                
            # 执行评论
            interaction_cfg = config.get('interaction', {})
            comment_templates = interaction_cfg.get('comment_templates', [])
            if comment_templates:
                if self.do_comment(device, comment_templates, config):
                    random_delay(2, 5)
            
            # 检查是否需要停止
            # 由于现在通过杀死线程来停止养号，这里不再需要停止检查
            pass
            
            # 计算停留时间
            elapsed_time = time.time() - start_time
            self.logger.info(f"在帖子内停留时间: {elapsed_time:.2f}秒")
            
            # 如果停留时间超过40秒，有一定概率访问用户主页
            if elapsed_time > 40:
                visit_homepage_prob = config.get('interaction', {}).get('visit_homepage_prob', 30.0)
                if random.random() < visit_homepage_prob / 100.0:
                    # 检查是否需要停止
                    # 由于现在通过杀死线程来停止养号，这里不再需要停止检查
                    pass
                        
                    self.logger.info(f"停留时间超过40秒，触发访问用户主页概率 ({visit_homepage_prob:.2f}%)")
                    self._visit_user_homepage(device)
            
            # 检查是否需要停止
            # 由于现在通过杀死线程来停止养号，这里不再需要停止检查
            pass
            
            random_delay(1, 3)
            return True
        except Exception as e:
            self.logger.error(f"浏览图片笔记失败: {e}")
            return False
    
    def _scroll_randomly(self, device):
        """
        随机滚动
        :param device: 设备实例
        """
        try:
            screen_width, screen_height = self._get_screen_size(device)
            if screen_width and screen_height:
                # 随机选择滚动方向
                if random.choice([True, False]):
                    # 向上滚动
                    start_y = screen_height * random.uniform(0.7, 0.9)
                    end_y = screen_height * random.uniform(0.1, 0.3)
                    x = screen_width * random.uniform(0.4, 0.6)
                    device.swipe(x, start_y, x, end_y, duration=0.2)
                else:
                    # 向下滚动
                    start_y = screen_height * random.uniform(0.1, 0.3)
                    end_y = screen_height * random.uniform(0.7, 0.9)
                    x = screen_width * random.uniform(0.4, 0.6)
                    device.swipe(x, start_y, x, end_y, duration=0.2)
        except Exception as e:
            self.logger.error(f"随机滚动失败: {e}")