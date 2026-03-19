#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试养号核心功能的实际运行
"""

import time
import logging
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from xhs_nurturing.nurturing_manager import NurturingManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(funcName)s:%(lineno)d - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_run_nurturing():
    """
    测试养号核心功能的实际运行
    """
    logger.info("开始测试养号核心功能的实际运行")
    
    # 初始化养号管理器
    nurturing_manager = NurturingManager() 
    
    # 获取设备列表
    devices = nurturing_manager.get_all_devices()
    logger.info(f"当前连接的设备: {devices}")
    
    if not devices:
        logger.error("没有检测到连接的设备，请先连接Android设备并确保ADB正常工作")
        return
    
    # 选择第一个设备
    device = devices[0]
    device_id = device["id"]
    device_name = device["name"]
    
    logger.info(f"选择测试设备: {device_name} (ID: {device_id})")
    
    # 检查设备状态
    status = nurturing_manager.get_device_status(device_id)
    logger.info(f"设备初始状态: {status}")
    
    # 临时更新设备关键词，添加指定的关键词
    # logger.info("更新设备关键词...")
    # test_keywords = ["四上数学", "四上寒假"]
    # keyword_update_result = nurturing_manager.update_keywords(device_id, test_keywords)
    # if keyword_update_result:
    #     logger.info(f"关键词更新成功: {test_keywords}")
    # else:
    #     logger.warning("关键词更新失败，使用默认关键词")
    
    # 启动养号
    logger.info("启动养号测试...")
    result = nurturing_manager.start_nurturing(device_id)
    
    if not result:
        logger.error("启动养号失败")
        return
    
    logger.info("养号测试已启动，正在执行中...")
    logger.info("测试流程包括：")
    logger.info("1. 启动小红书应用")
    logger.info("2. 在发现页浏览一段时间")
    logger.info("3. 搜索关键词")
    logger.info("4. 浏览相关帖子")
    logger.info("5. 执行互动行为（点赞、收藏、评论）")
    
    # 监控养号状态
    try:
        for i in range(1000):  # 监控30秒
            time.sleep(20)
            status = nurturing_manager.get_device_status(device_id)
            if i % 5 == 0:  # 每5秒打印一次状态
                logger.info(f"养号状态: 运行中={status.get('is_running', False)}, "
                         f"剩余时间={status.get('remain_time', 0)}分钟, "
                         f"已访问={status.get('visited', 0)}帖子, "
                         f"当前关键词={status.get('current_keyword', '')}")
            
            # 检查是否已停止
            if not status.get('is_running', False):
                logger.info("养号已完成")
                break
    except KeyboardInterrupt:
        logger.info("用户中断测试")
    finally:
        # 停止养号（如果还在运行）
        if nurturing_manager.is_device_running(device_id):
            logger.info("停止养号测试")
            nurturing_manager.stop_nurturing(device_id)
    
    # 打印最终状态
    final_status = nurturing_manager.get_device_status(device_id)
    logger.info(f"最终状态: {final_status}")
    logger.info("养号核心功能测试完成")

if __name__ == "__main__":
    test_run_nurturing()
