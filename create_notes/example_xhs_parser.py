#!/usr/bin/env python3
"""
小红书笔记解析示例脚本

功能：
1. 从用户输入中提取小红书笔记链接
2. 解析笔记内容（标题、正文、标签、图片）
3. 下载图片到指定目录
4. 打印解析结果
"""

import os
import sys
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import xhs_parser as xhs

def main():
    """主函数"""
    print("===== 小红书笔记解析工具 =====")
    print()
    
    # 初始化解析器
    parser = xhs.XhsParser()
    
    # 获取输入文本
    if len(sys.argv) > 1:
        # 从命令行参数获取
        input_text = ' '.join(sys.argv[1:])
        print(f"从命令行获取输入: {input_text}")
    else:
        # 从用户输入获取
        # input_text = input("请输入包含小红书笔记链接的文本: ")
        input_text = """
       21 【寒假预习；新三下数学全册知识点汇总|| - 朱采 | 小红书 - 你的生活兴趣社区】 😆 bXXJDGhNc7ZGFiv 😆 https://www.xiaohongshu.com/discovery/item/69804b06000000002200b14d?source=webshare&xhsshare=pc_web&xsec_token=ABsnulZivvFN7ltiFQMrrguIqJk7FrvyRxpfN_Hg-jfzQ=&xsec_source=pc_share
        """
    print()
    
    # 提取链接
    note_url = parser.extract_note_url(input_text)
    if not note_url:
        print("❌ 未找到小红书笔记链接")
        return
    
    print(f"✅ 提取到链接: {note_url}")
    
    # 解析笔记
    print("🔍 正在解析笔记内容...")
    note_info = parser.parse_note(note_url)
    if not note_info:
        print("❌ 解析笔记失败")
        return
    
    print("✅ 笔记解析完成")
    print()
    
    # 打印笔记信息
    print("📋 笔记信息:")
    print(f"标题: {note_info['title']}")
    print(f"内容: {note_info['content']}" if note_info['content'] else "内容: 无")
    print(f"标签: {note_info['tags']}")
    print(f"图片数量: {len(note_info['image_urls'])}")
    print()
    
    # 下载图片
    if note_info['image_urls']:
        # 使用parse_note方法返回的note_id字段
        note_id = note_info.get('note_id', 'unknown')
        # 生成保存目录
        save_dir = os.path.join(os.getcwd(), "xhs_images", note_id)
        print(f"💾 正在下载图片到: {save_dir}")
        
        # 下载图片
        downloaded_paths = parser.download_images(note_info['image_urls'], save_dir)
        
        # 将note_info存储为JSON文件
        json_file_path = os.path.join(save_dir, f"{note_id}.json")
        try:
            with open(json_file_path, 'w', encoding='utf-8') as f:
                json.dump(note_info, f, ensure_ascii=False, indent=2)
            print(f"✅ 成功保存笔记信息到: {json_file_path}")
        except Exception as e:
            print(f"❌ 保存笔记信息失败: {e}")
        if downloaded_paths:
            print(f"✅ 成功下载 {len(downloaded_paths)} 张图片")
            print("下载的图片路径:")
            for path in downloaded_paths:
                print(f"- {path}")
        else:
            print("❌ 图片下载失败")
    else:
        print("ℹ️  该笔记无图片")
    
    print()
    print("===== 处理完成 =====")


if __name__ == "__main__":
    main()
