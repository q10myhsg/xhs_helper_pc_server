import re
import os
import time
import requests
import logging
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

class XhsParser:
    """小红书笔记解析器"""
    
    def __init__(self):
        """初始化解析器"""
        self.logger = logging.getLogger(__name__)
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36'
        }
    
    def extract_note_url(self, input_text: str) -> Optional[str]:
        """
        从输入文本中提取小红书笔记链接
        :param input_text: 输入文本，可能包含小红书笔记链接
        :return: 提取的小红书笔记链接，若未找到返回None
        """
        try:
            # 匹配小红书笔记链接的正则表达式
            xhs_pattern = r'(https?://www\.xiaohongshu\.com/[\w\-./?%&=]+)'
            match = re.search(xhs_pattern, input_text)
            if match:
                url = match.group(1)
                self.logger.info(f"提取到小红书笔记链接: {url}")
                return url
            self.logger.warning("未找到小红书笔记链接")
            return None
        except Exception as e:
            self.logger.error(f"提取链接失败: {e}")
            return None
    
    def extract_note_id(self, note_url: str) -> Optional[str]:
        """
        从小红书笔记链接中提取笔记ID
        :param note_url: 小红书笔记链接
        :return: 提取的笔记ID，若提取失败返回None
        """
        try:
            # 从URL中提取笔记ID
            # 格式：https://www.xiaohongshu.com/discovery/item/{note_id}?source=...
            note_id = note_url.split('/')[-1].split('?')[0]
            if note_id:
                self.logger.info(f"提取到笔记ID: {note_id}")
                return note_id
            self.logger.warning("未找到笔记ID")
            return None
        except Exception as e:
            self.logger.error(f"提取笔记ID失败: {e}")
            return None
    
    def parse_note(self, note_url: str) -> Optional[Dict]:
        """
        解析小红书笔记内容
        :param note_url: 小红书笔记链接
        :return: 包含笔记信息的字典，若解析失败返回None
        """
        try:
            self.logger.info(f"开始解析笔记: {note_url}")
            
            # 发送请求获取页面内容
            response = requests.get(note_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            # 保存响应内容到tmp目录
            timestamp = int(time.time())
            tmp_dir = os.path.join(os.path.dirname(__file__), '..', 'tmp')
            os.makedirs(tmp_dir, exist_ok=True)
            file_name = f"tmp_{timestamp}.html"
            file_path = os.path.join(tmp_dir, file_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            self.logger.info(f"响应内容已保存到: {file_path}")
            # 解析HTML内容
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 从meta标签提取信息
            meta_data = self._extract_meta_data(soup)
            
            # 提取标题（优先使用meta中的标题）
            title = meta_data.get('title')
            
            # 从HTML结构中提取正文
            content = self._extract_content(soup)
            
            # 提取标签（优先使用meta中的标签）
            tags = meta_data.get('tags') 
            
            # 提取图片链接（优先使用meta中的图片链接）
            image_urls = meta_data.get('image_urls', [])

            # 提取笔记ID
            note_id = self.extract_note_id(note_url)
            
            note_info = {
                'url': note_url,
                'note_id': note_id,
                'title': title,
                'content': content,
                'tags': tags,
                'image_urls': image_urls,
                # 'meta_data': meta_data
            }
            
            self.logger.info(f"笔记解析完成，标题: {title}, 图片数量: {len(image_urls)}")
            return note_info
        except Exception as e:
            self.logger.error(f"解析笔记失败: {e}")
            return None
    
    def _extract_meta_data(self, soup: BeautifulSoup) -> Dict:
        """
        从HTML的meta标签中提取笔记信息
        :param soup: BeautifulSoup对象
        :return: 提取的meta信息
        """
        try:
            meta_data = {}
            
            # 提取标题
            title_meta = soup.find('meta', {'name': 'og:title'})
            if title_meta and title_meta.get('content'):
                title = title_meta.get('content')
                # 移除末尾的 " - 小红书"
                if title.endswith(' - 小红书'):
                    title = title[:-6]
                meta_data['title'] = title
            
            # 提取描述（可能包含标签信息）
            desc_meta = soup.find('meta', {'name': 'description'})
            if desc_meta and desc_meta.get('content'):
                description = desc_meta.get('content')
                meta_data['description'] = description
                # 尝试从描述中提取标签
                # if description.startswith('#'):
                #     tags = [f"#{tag.strip()}" for tag in description.split('#') if tag.strip()]
                #     meta_data['tags'] = tags
            
            # 提取标签
            keywords_meta = soup.find('meta', {'name': 'keywords'})
            if keywords_meta and keywords_meta.get('content'):
                keywords = keywords_meta.get('content')
                tags = [tag.strip() for tag in keywords.split('，') if tag.strip()]
                meta_data['tags'] = tags
            
            # 提取图片链接
            image_urls = []
            image_metas = soup.find_all('meta', {'name': 'og:image'})
            for img_meta in image_metas:
                img_url = img_meta.get('content')
                if img_url:
                    # 确保链接完整
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif not img_url.startswith('http'):
                        img_url = requests.compat.urljoin('https://www.xiaohongshu.com', img_url)
                    # 获取无水印图片链接
                    no_watermark_url = self._get_note_no_water_img(img_url)
                    image_urls.append(no_watermark_url)
            
            # 去重
            if image_urls:
                meta_data['image_urls'] = list(set(image_urls))
            
            # 提取点赞数
            like_meta = soup.find('meta', {'name': 'og:xhs:note_like'})
            if like_meta and like_meta.get('content'):
                meta_data['likes'] = like_meta.get('content')
            
            # 提取收藏数
            collect_meta = soup.find('meta', {'name': 'og:xhs:note_collect'})
            if collect_meta and collect_meta.get('content'):
                meta_data['collections'] = collect_meta.get('content')
            
            # 提取评论数
            comment_meta = soup.find('meta', {'name': 'og:xhs:note_comment'})
            if comment_meta and comment_meta.get('content'):
                meta_data['comments'] = comment_meta.get('content')
            
            return meta_data
        except Exception as e:
            self.logger.error(f"提取meta信息失败: {e}")
            return {}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        从HTML中提取标题
        :param soup: BeautifulSoup对象
        :return: 提取的标题
        """
        try:
            # 尝试不同的选择器提取标题
            title_selector = soup.find('h1')
            if title_selector:
                return title_selector.text.strip()
            
            # 尝试从meta标签提取
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                return meta_title.get('content', '').strip()
            
            return ""
        except Exception as e:
            self.logger.error(f"提取标题失败: {e}")
            return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """
        从HTML中提取正文
        :param soup: BeautifulSoup对象
        :return: 提取的正文（已清理标签）
        """
        try:
            # 尝试不同的选择器提取正文
            content_selectors = [
                'div[id="detail-desc"]',  # 优先使用detail-desc元素
                'div[class*="content"]', 
                'div[class*="note"]', 
                'article'
            ]
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.text.strip()
                    # 清理标签内容
                    content = self._clean_tags(content)
                    return content
            
            return ""
        except Exception as e:
            self.logger.error(f"提取正文失败: {e}")
            return ""
    
    def _clean_tags(self, content: str) -> str:
        """
        清理正文中的标签内容
        :param content: 原始正文内容
        :return: 清理后的正文内容
        """
        try:
            # 按空格分割内容
            words = content.split()
            # 过滤掉所有以 # 开头的标签
            filtered_words = [word for word in words if not word.startswith('#')]
            # 重新组合内容
            cleaned_content = ' '.join(filtered_words)
            # 移除多余的空格和空行
            cleaned_content = re.sub(r'\\s+', ' ', cleaned_content).strip()
            return cleaned_content
        except Exception as e:
            self.logger.error(f"清理标签失败: {e}")
            return content
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """
        从HTML中提取标签
        :param soup: BeautifulSoup对象
        :return: 提取的标签列表
        """
        try:
            tags = []
            
            # 尝试不同的选择器提取标签
            tag_selectors = ['a[class*="tag"]', 'span[class*="tag"]']
            for selector in tag_selectors:
                tag_elems = soup.select(selector)
                for elem in tag_elems:
                    tag_text = elem.text.strip()
                    if tag_text and tag_text not in tags:
                        tags.append(tag_text)
            
            return tags
        except Exception as e:
            self.logger.error(f"提取标签失败: {e}")
            return []
    
    def _get_note_no_water_img(self, img_url):
        """
        获取笔记无水印图片
        :param img_url: 你想要获取的图片的url
        :return: 无水印图片url
        """
        try:
            # 直接返回原始URL，不进行任何转换
            # 因为生成的无水印URL格式不正确，会导致404错误
            return img_url
        except Exception as e:
            self.logger.error(f"获取无水印图片失败 ({img_url}): {e}")
            return img_url
    
    def _extract_image_urls(self, soup: BeautifulSoup) -> List[str]:
        """
        从HTML中提取图片链接
        :param soup: BeautifulSoup对象
        :return: 提取的图片链接列表
        """
        try:
            image_urls = []
            
            # 查找所有图片标签
            img_tags = soup.find_all('img')
            for img in img_tags:
                # 尝试从不同属性获取图片链接
                src = img.get('src') or img.get('data-src') or img.get('data-original')
                if src:
                    # 确保链接完整
                    if not src.startswith('http'):
                        src = requests.compat.urljoin('https://www.xiaohongshu.com', src)
                    # 获取无水印图片链接
                    no_watermark_url = self._get_note_no_water_img(src)
                    image_urls.append(no_watermark_url)
            
            # 去重
            image_urls = list(set(image_urls))
            return image_urls
        except Exception as e:
            self.logger.error(f"提取图片链接失败: {e}")
            return []
    
    def download_images(self, image_urls: List[str], save_dir: str) -> List[str]:
        """
        下载图片到指定目录
        :param image_urls: 图片链接列表
        :param save_dir: 保存目录
        :return: 下载成功的图片路径列表
        """
        try:
            # 创建保存目录（如果不存在则创建）
            os.makedirs(save_dir, exist_ok=True)
            self.logger.info(f"创建保存目录: {save_dir}")
            
            # 初始化存储下载成功图片路径的列表
            downloaded_paths = []
            
            for i, img_url in enumerate(image_urls):
                try:
                    # 发送请求获取图片
                    response = requests.get(img_url, headers=self.headers, timeout=10)
                    response.raise_for_status()
                    
                    # 生成保存文件名
                    file_ext = img_url.split('.')[-1].split('?')[0] if '.' in img_url else 'jpg'
                    if len(file_ext) > 5:
                        file_ext = 'jpg'
                    file_name = f"image_{i+1}.{file_ext}"
                    save_path = os.path.join(save_dir, file_name)
                    
                    # 保存图片
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    
                    downloaded_paths.append(save_path)
                    self.logger.info(f"下载图片成功: {file_name}")
                except Exception as e:
                    self.logger.error(f"下载图片失败 ({img_url}): {e}")
                    continue
            
            self.logger.info(f"图片下载完成，成功下载 {len(downloaded_paths)} 张图片")
            return downloaded_paths
        except Exception as e:
            self.logger.error(f"下载图片失败: {e}")
            return []
