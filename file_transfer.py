#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件传输模块
功能：将电脑上的文件/文件夹传输到手机，并支持清理操作
"""

import os
import shutil
import subprocess
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class FileTransferManager:
    """文件传输管理器类"""
    
    def __init__(self, device_id: Optional[str] = None):
        """
        初始化文件传输管理器
        
        参数:
            device_id: 设备ID，用于多设备环境
        """
        self.device_id = device_id
        self._check_adb()
    
    def _check_adb(self) -> bool:
        """检查ADB是否可用"""
        try:
            subprocess.run(['adb', 'version'], check=True, capture_output=True, text=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("ADB命令不可用，请确保已安装Android SDK并将adb添加到环境变量")
    
    def _build_adb_cmd(self, cmd: List[str]) -> List[str]:
        """构建ADB命令"""
        adb_cmd = ['adb']
        if self.device_id:
            adb_cmd.extend(['-s', self.device_id])
        adb_cmd.extend(cmd)
        return adb_cmd
    
    def _check_path_exists_on_device(self, path: str) -> bool:
        """检查手机上的路径是否存在"""
        try:
            adb_cmd = self._build_adb_cmd(['shell', 'test', '-e', path, '&&', 'echo', 'yes', '||', 'echo', 'no'])
            result = subprocess.run(adb_cmd, capture_output=True, text=True, check=True)
            return 'yes' in result.stdout
        except Exception as e:
            logger.error(f"检查设备路径时发生错误: {str(e)}")
            return False
    
    def _create_dir_on_device(self, path: str) -> bool:
        """在手机上创建目录"""
        try:
            adb_cmd = self._build_adb_cmd(['shell', 'mkdir', '-p', path])
            subprocess.run(adb_cmd, check=True, capture_output=True)
            return True
        except Exception as e:
            logger.error(f"创建设备目录失败: {str(e)}")
            return False
    
    def _delete_dir_on_device(self, path: str) -> bool:
        """删除手机上的目录"""
        try:
            if not self._check_path_exists_on_device(path):
                logger.info(f"目录不存在，无需删除: {path}")
                return True
            
            adb_cmd = self._build_adb_cmd(['shell', 'rm', '-rf', path])
            subprocess.run(adb_cmd, check=True, capture_output=True)
            logger.info(f"已删除设备目录: {path}")
            return True
        except Exception as e:
            logger.error(f"删除设备目录失败: {str(e)}")
            return False
    
    def _send_media_scanner_broadcast(self, path: str) -> bool:
        """
        发送媒体扫描广播，让系统识别新传输的文件或文件夹
        
        参数:
            path: 手机上的文件或目录路径
            
        返回:
            bool: 发送成功返回True，失败返回False
        """
        try:
            logger.info(f"正在发送媒体扫描广播: {path}")
            # 执行ADB广播命令，支持多设备
            adb_cmd = self._build_adb_cmd([
                'shell', 'am', 'broadcast', 
                '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE', 
                '-d', f"'file://{path}'"
            ])
            
            result = subprocess.run(
                adb_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"媒体扫描广播发送成功: {result.stdout.strip()}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"ADB广播命令执行失败: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"发送媒体扫描广播时发生错误: {str(e)}")
            return False
    
    def _scan_directory_media(self, dir_path: str) -> bool:
        """
        扫描目录中的所有图片/视频文件，发送媒体扫描广播
        
        参数:
            dir_path: 手机上的目录路径
            
        返回:
            bool: 扫描成功返回True
        """
        try:
            # 先扫描目录本身
            self._send_media_scanner_broadcast(dir_path)
            
            # 列出目录中的所有文件
            adb_cmd = self._build_adb_cmd(['shell', 'ls', '-a', dir_path])
            result = subprocess.run(adb_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                for filename in files:
                    if filename and filename not in ['.', '..']:
                        # 对每个文件发送扫描广播
                        file_path = f"{dir_path}/{filename}"
                        self._send_media_scanner_broadcast(file_path)
            
            return True
        except Exception as e:
            logger.error(f"扫描目录媒体时发生错误: {str(e)}")
            return False
    
    def clear_phone_directory(self, phone_dir: str) -> Dict:
        """
        清理手机上的传输目录
        
        参数:
            phone_dir: 手机上的目标目录路径
            
        返回:
            Dict: 包含操作结果的字典
        """
        try:
            logger.info(f"开始清理手机传输目录: {phone_dir}")
            
            # 删除目录
            success = self._delete_dir_on_device(phone_dir)
            
            if success:
                # 重新创建空目录
                create_success = self._create_dir_on_device(phone_dir)
                if create_success:
                    logger.info("手机传输目录清理并重建成功")
                    return {"success": True, "message": "手机传输目录清理成功"}
                else:
                    return {"success": False, "error": "重建目录失败"}
            else:
                return {"success": False, "error": "删除目录失败"}
                
        except Exception as e:
            logger.error(f"清理手机传输目录时发生错误: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def transfer_files_to_phone(self, computer_dir: str, phone_dir: str) -> Dict:
        """
        将电脑上的文件/文件夹传输到手机
        
        参数:
            computer_dir: 电脑上的源目录路径
            phone_dir: 手机上的目标目录路径
            
        返回:
            Dict: 包含操作结果的字典
        """
        try:
            logger.info(f"开始传输文件: {computer_dir} -> {phone_dir}")
            
            # 检查电脑源目录是否存在
            if not os.path.exists(computer_dir):
                return {"success": False, "error": f"电脑源目录不存在: {computer_dir}"}
            
            # 确保手机目标目录存在
            self._create_dir_on_device(phone_dir)
            
            file_count = 0
            success = True
            
            # 如果是单个文件，直接传输
            if os.path.isfile(computer_dir):
                adb_cmd = self._build_adb_cmd(['push', computer_dir, phone_dir])
                result = subprocess.run(adb_cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    file_count = 1
                    logger.info(f"文件传输成功")
                else:
                    logger.error(f"文件传输失败: {result.stderr}")
                    return {"success": False, "error": result.stderr}
            else:
                # 如果是目录，先获取所有文件，按文件名排序后逐个传输
                dir_name = os.path.basename(computer_dir)
                target_dir = f"{phone_dir}/{dir_name}"
                
                # 创建目标目录
                self._create_dir_on_device(target_dir)
                
                # 获取所有文件并排序
                all_files = []
                for root, dirs, files in os.walk(computer_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 计算相对路径
                        rel_path = os.path.relpath(file_path, computer_dir)
                        all_files.append((file_path, rel_path))
                
                # 按文件名自然排序
                all_files.sort(key=lambda x: x[1])
                
                # 逐个传输文件
                logger.info(f"准备传输 {len(all_files)} 个文件，按顺序传输...")
                
                for file_path, rel_path in all_files:
                    # 计算目标路径
                    target_file_dir = os.path.join(target_dir, os.path.dirname(rel_path))
                    target_file_dir = target_file_dir.replace('\\', '/')
                    
                    # 创建目标文件所在目录
                    self._create_dir_on_device(target_file_dir)
                    
                    # 传输文件
                    adb_cmd = self._build_adb_cmd(['push', file_path, target_file_dir])
                    result = subprocess.run(adb_cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        file_count += 1
                        logger.info(f"[{file_count}/{len(all_files)}] 传输成功: {rel_path}")
                    else:
                        logger.error(f"传输失败: {rel_path}, 错误: {result.stderr}")
                        success = False
                        break
            
            if success:
                logger.info(f"文件传输成功，共传输 {file_count} 个文件")
                
                # 发送媒体扫描广播，让相册能显示新传输的图片
                logger.info("开始发送媒体扫描广播...")
                
                if os.path.isfile(computer_dir):
                    filename = os.path.basename(computer_dir)
                    target_file_path = f"{phone_dir}/{filename}"
                    self._send_media_scanner_broadcast(target_file_path)
                else:
                    dir_name = os.path.basename(computer_dir)
                    target_dir_path = f"{phone_dir}/{dir_name}"
                    
                    if self._check_path_exists_on_device(target_dir_path):
                        self._scan_directory_media(target_dir_path)
                    else:
                        self._scan_directory_media(phone_dir)
                
                return {
                    "success": True, 
                    "message": f"文件传输成功，共 {file_count} 个文件",
                    "file_count": file_count
                }
            else:
                return {"success": False, "error": "部分文件传输失败"}
                
        except Exception as e:
            logger.error(f"传输文件时发生错误: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _count_files(self, directory: str) -> int:
        """统计目录中的文件/文件夹数量"""
        try:
            if os.path.isfile(directory):
                return 1
            count = 0
            for root, dirs, files in os.walk(directory):
                count += len(dirs) + len(files)
            return max(count, 1)  # 至少返回1（目录本身）
        except:
            return 0
    
    def clear_computer_directory(self, computer_dir: str) -> Dict:
        """
        清空电脑上的传输目录
        
        参数:
            computer_dir: 电脑上的源目录路径
            
        返回:
            Dict: 包含操作结果的字典
        """
        try:
            logger.info(f"开始清空电脑传输目录: {computer_dir}")
            
            # 检查目录是否存在
            if not os.path.exists(computer_dir):
                return {"success": False, "error": f"目录不存在: {computer_dir}"}
            
            # 遍历并删除所有内容
            deleted_count = 0
            for filename in os.listdir(computer_dir):
                file_path = os.path.join(computer_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"已删除文件: {file_path}")
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        deleted_count += 1
                        logger.info(f"已删除目录: {file_path}")
                except Exception as e:
                    logger.error(f"删除 {file_path} 时发生错误: {str(e)}")
            
            logger.info(f"电脑传输目录清空成功，共删除 {deleted_count} 个项目")
            return {
                "success": True, 
                "message": f"清空成功，共删除 {deleted_count} 个项目",
                "deleted_count": deleted_count
            }
            
        except Exception as e:
            logger.error(f"清空电脑传输目录时发生错误: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def execute_full_transfer(self, computer_dir: str, phone_dir: str) -> Dict:
        """
        执行完整的传输流程：
        1. 清理手机传输目录
        2. 传输文件到手机
        3. 清空电脑传输目录
        
        参数:
            computer_dir: 电脑上的源目录路径
            phone_dir: 手机上的目标目录路径
            
        返回:
            Dict: 包含所有步骤结果的字典
        """
        results = {
            "success": True,
            "steps": {}
        }
        
        # 步骤1: 清理手机传输目录
        step1_result = self.clear_phone_directory(phone_dir)
        results["steps"]["clear_phone"] = step1_result
        
        if not step1_result["success"]:
            results["success"] = False
            results["message"] = "清理手机目录失败，流程终止"
            return results
        
        # 步骤2: 传输文件到手机
        step2_result = self.transfer_files_to_phone(computer_dir, phone_dir)
        results["steps"]["transfer"] = step2_result
        
        if not step2_result["success"]:
            results["success"] = False
            results["message"] = "文件传输失败"
            return results
        
        # 步骤3: 清空电脑传输目录
        step3_result = self.clear_computer_directory(computer_dir)
        results["steps"]["clear_computer"] = step3_result
        
        if not step3_result["success"]:
            results["success"] = False
            results["message"] = "清空电脑目录失败"
            return results
        
        results["message"] = "文件传输流程执行成功"
        return results


# 全局文件传输管理器实例
file_transfer_manager = FileTransferManager()
