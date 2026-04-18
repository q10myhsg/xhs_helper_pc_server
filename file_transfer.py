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
import time
import urllib.parse

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
            subprocess.run(['adb', 'version'], check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
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
            # 使用简单的 test 命令，不使用 shell 操作符
            adb_cmd = self._build_adb_cmd(['shell', 'test', '-e', path])
            result = subprocess.run(adb_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            # 如果返回码是 0，表示路径存在
            return result.returncode == 0
        except KeyboardInterrupt:
            # 捕获用户中断信号，不记录错误
            raise
        except Exception as e:
            logger.error(f"检查设备路径时发生错误: {str(e)}")
            return False
    
    def _create_dir_on_device(self, path: str) -> bool:
        """在手机上创建目录"""
        try:
            # 直接传递路径参数，不需要引号（因为我们传递的是参数列表）
            adb_cmd = self._build_adb_cmd(['shell', 'mkdir', '-p', path])
            result = subprocess.run(adb_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', check=True)
            logger.info(f"已创建手机目录: {path}")
            return True
        except KeyboardInterrupt:
            # 捕获用户中断信号，不记录错误
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"ADB创建目录命令执行失败: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"创建设备目录失败: {str(e)}")
            return False
    
    def _delete_dir_on_device(self, path: str) -> bool:
        """删除手机上的目录"""
        try:
            if not self._check_path_exists_on_device(path):
                logger.info(f"目录不存在，无需删除: {path}")
                return True
            
            # 执行ADB删除目录命令（直接传递路径参数）
            logger.info(f"正在删除手机目录: {path}")
            adb_cmd = self._build_adb_cmd(['shell', 'rm', '-rf', path])
            result = subprocess.run(adb_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', check=True)
            
            # 验证目录是否已删除
            if not self._check_path_exists_on_device(path):
                logger.info(f"手机目录删除成功: {path}")
                return True
            else:
                logger.error(f"手机目录删除失败，目录仍然存在: {path}")
                return False
        except KeyboardInterrupt:
            # 捕获用户中断信号，不记录错误
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"ADB删除命令执行失败: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"删除设备目录失败: {str(e)}")
            return False
    
    def _send_media_scanner_broadcast(self, path: str) -> bool:
        """
        发送媒体扫描广播，让系统识别新传输的文件或文件夹
        参考 adb_file.py 的实现方式
        
        参数:
            path: 手机上的文件或目录路径
            
        返回:
            bool: 发送成功返回True，失败返回False
        """
        try:
            # 执行ADB广播命令，支持多设备
            logger.info(f"正在发送媒体扫描广播: {path}")
            # 对路径进行 URL 编码，确保特殊字符正确处理
            encoded_path = urllib.parse.quote(path)
            adb_cmd = self._build_adb_cmd([
                'shell', 'am', 'broadcast', 
                '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE', 
                '-d', f'file://{encoded_path}'
            ])
            
            result = subprocess.run(adb_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', check=True)
            
            logger.info(f"媒体扫描广播发送成功: {result.stdout.strip()}")
            return True
            
        except KeyboardInterrupt:
            # 捕获用户中断信号，不记录错误
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"ADB广播命令执行失败: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"发送媒体扫描广播时发生错误: {str(e)}")
            return False
    
    def _trigger_media_store_scan(self, path: str) -> bool:
        """
        使用 MediaStore 触发媒体扫描 (适用于 Android 10+)
        
        参数:
            path: 要扫描的路径
            
        返回:
            bool: 成功返回True
        """
        try:
            # 使用 am start 启动媒体扫描
            # 对路径进行 URL 编码，确保特殊字符正确处理
            encoded_path = urllib.parse.quote(path)
            adb_cmd = self._build_adb_cmd([
                'shell', 'am', 'startservice',
                '-a', 'android.intent.action.MEDIA_SCANNER_SCAN_FILE',
                '-d', f'file://{encoded_path}'
            ])
            
            result = subprocess.run(adb_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            logger.info(f"MediaStore 扫描触发结果: {result.returncode}")
            
            # 等待一下让系统处理
            time.sleep(0.5)
            
            return True
        except KeyboardInterrupt:
            # 捕获用户中断信号，不记录错误
            raise
        except Exception as e:
            logger.warning(f"MediaStore 扫描触发失败: {str(e)}")
            return False
    
    def _scan_directory_media(self, dir_path: str) -> bool:
        """
        扫描目录中的所有图片/视频/PDF文件，发送媒体扫描广播
        
        参数:
            dir_path: 手机上的目录路径
            
        返回:
            bool: 扫描成功返回True
        """
        try:
            logger.info(f"开始扫描目录媒体文件: {dir_path}")
            
            # 先扫描目录本身
            self._send_media_scanner_broadcast(dir_path)
            
            # 使用 ls -1 命令只列出文件名，避免空格解析问题
            adb_cmd = self._build_adb_cmd(['shell', 'ls', '-1', dir_path])
            result = subprocess.run(adb_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode == 0 and result.stdout:
                filenames = result.stdout.strip().split('\n')
                media_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.pdf', '.mp4', '.mov', '.avi'}
                
                for filename in filenames:
                    if not filename:
                        continue
                    filename = filename.strip()
                    if not filename or filename in ['.', '..']:
                        continue
                        
                    # 检查是否是媒体文件
                    file_lower = filename.lower()
                    if any(file_lower.endswith(ext) for ext in media_extensions):
                        file_path = f"{dir_path}/{filename}"
                        logger.info(f"扫描媒体文件: {file_path}")
                        self._send_media_scanner_broadcast(file_path)
                        # 稍微延迟避免广播过于频繁
                        time.sleep(0.1)
            
            # 额外触发一次全面的媒体扫描
            self._trigger_full_media_scan()
            
            return True
        except Exception as e:
            logger.error(f"扫描目录媒体时发生错误: {str(e)}")
            return False
    
    def _trigger_full_media_scan(self) -> bool:
        """
        触发全面的媒体库扫描
        
        返回:
            bool: 成功返回True
        """
        try:
            # 使用广播触发系统媒体扫描
            adb_cmd = self._build_adb_cmd([
                'shell', 'am', 'broadcast',
                '-a', 'android.intent.action.MEDIA_MOUNTED',
                '-d', 'file:///storage/emulated/0'
            ])
            
            result = subprocess.run(adb_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            logger.info(f"全面媒体扫描触发结果: {result.returncode}")
            
            return True
        except KeyboardInterrupt:
            # 捕获用户中断信号，不记录错误
            raise
        except Exception as e:
            logger.warning(f"全面媒体扫描触发失败: {str(e)}")
            return False
    
    def _modify_file_timestamp(self, file_path: str, sequence: int = 0) -> bool:
        """
        修改手机上文件的时间戳，让图片按顺序显示
        通过设置递增的时间戳，确保相册按文件名顺序排列
        
        参数:
            file_path: 手机上的文件路径
            sequence: 文件序号，用于生成递增的时间戳
            
        返回:
            bool: 修改成功返回True
        """
        try:
            import datetime
            # 基于当前时间，加上序号偏移，确保按顺序排列
            # 每个文件间隔1秒
            base_time = datetime.datetime.now()
            file_time = base_time + datetime.timedelta(seconds=sequence)
            time_str = file_time.strftime("%Y%m%d%H%M.%S")
            
            logger.info(f"正在修改文件时间戳: {file_path} -> {time_str}")
            adb_cmd = self._build_adb_cmd([
                'shell', 'touch', '-a', '-m', '-t', time_str, file_path
            ])
            
            result = subprocess.run(adb_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', check=True)
            logger.info(f"文件时间戳修改成功: {file_path}")
            return True
        except KeyboardInterrupt:
            # 捕获用户中断信号，不记录错误
            raise
        except subprocess.CalledProcessError as e:
            logger.warning(f"修改文件时间戳失败: {e.stderr}")
            return False
        except Exception as e:
            logger.warning(f"修改文件时间戳时发生错误: {str(e)}")
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
            transferred_files = []  # 记录传输的文件路径
            
            # 如果是单个文件，直接传输
            if os.path.isfile(computer_dir):
                # 构建完整的目标文件路径
                filename = os.path.basename(computer_dir)
                target_file_path = f"{phone_dir}/{filename}"
                
                adb_cmd = self._build_adb_cmd(['push', computer_dir, target_file_path])
                logger.info(f"执行命令: {' '.join(adb_cmd)}")
                result = subprocess.run(adb_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                
                # 打印详细的输出信息，方便调试
                logger.info(f"adb 返回码: {result.returncode}")
                if result.stdout:
                    logger.info(f"adb stdout: {result.stdout.strip()}")
                if result.stderr:
                    logger.info(f"adb stderr: {result.stderr.strip()}")
                
                # 合并 stdout 和 stderr 进行检查
                combined_output = (result.stdout or '') + (result.stderr or '')
                
                # 检查是否传输成功 - 有时 adb 会返回非零错误码但实际上文件已传输成功
                transfer_success = result.returncode == 0 or "1 file pushed" in combined_output or "file pushed" in combined_output
                
                if transfer_success:
                    file_count = 1
                    transferred_files.append(target_file_path)
                    logger.info(f"文件传输成功: {filename}")
                    # 检查是否有 "1 file pushed" 的成功提示，即使返回码非零也没问题
                    if "1 file pushed" in combined_output:
                        logger.info(f"  文件已成功传输（adb 返回码可忽略）")
                else:
                    logger.error(f"文件传输失败: {result.stderr or result.stdout}")
                    return {"success": False, "error": result.stderr or result.stdout}
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
                    
                    # 构建完整的目标文件路径
                    target_file_path = f"{target_file_dir}/{os.path.basename(file_path)}"
                    target_file_path = target_file_path.replace('//', '/')
                    
                    # 创建目标文件所在目录
                    dir_created = self._create_dir_on_device(target_file_dir)
                    if not dir_created:
                        logger.error(f"创建目录失败，跳过文件: {rel_path}")
                        success = False
                        break
                    
                    # 传输文件 - 直接指定完整目标文件路径
                    adb_cmd = self._build_adb_cmd(['push', file_path, target_file_path])
                    logger.info(f"执行命令: {' '.join(adb_cmd)}")
                    result = subprocess.run(adb_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                    
                    # 打印详细的输出信息，方便调试
                    logger.info(f"adb 返回码: {result.returncode}")
                    if result.stdout:
                        logger.info(f"adb stdout: {result.stdout.strip()}")
                    if result.stderr:
                        logger.info(f"adb stderr: {result.stderr.strip()}")
                    
                    # 合并 stdout 和 stderr 进行检查
                    combined_output = (result.stdout or '') + (result.stderr or '')
                    
                    # 检查是否传输成功 - 有时 adb 会返回非零错误码但实际上文件已传输成功
                    transfer_success = result.returncode == 0 or "1 file pushed" in combined_output or "file pushed" in combined_output
                    
                    if transfer_success:
                        file_count += 1
                        # 记录传输的文件路径
                        transferred_files.append(target_file_path)
                        # 暂时禁用时间戳修改，测试是否导致文件 0KB
                        # self._modify_file_timestamp(target_file_path, file_count)
                        logger.info(f"[{file_count}/{len(all_files)}] 传输成功: {rel_path}")
                        # 检查是否有 "1 file pushed" 的成功提示，即使返回码非零也没问题
                        if "1 file pushed" in combined_output:
                            logger.info(f"  文件已成功传输（adb 返回码可忽略）")
                    else:
                        logger.error(f"传输失败: {rel_path}, 错误: {result.stderr or result.stdout}")
                        success = False
                        break
            
            if success:
                logger.info(f"文件传输成功，共传输 {file_count} 个文件")
                
                # 发送媒体扫描广播，让相册能显示新传输的图片
                logger.info("开始发送媒体扫描广播...")
                
                if os.path.isfile(computer_dir):
                    filename = os.path.basename(computer_dir)
                    target_file_path = f"{phone_dir}/{filename}"
                    self._send_media_scanner_broadcast(f"file://{target_file_path}")
                else:
                    dir_name = os.path.basename(computer_dir)
                    target_dir_path = f"{phone_dir}/{dir_name}"
                    
                    if self._check_path_exists_on_device(target_dir_path):
                        self._scan_directory_media(target_dir_path)
                    else:
                        self._scan_directory_media(phone_dir)
                
                # 等待媒体扫描完成
                logger.info("等待媒体扫描完成...")
                time.sleep(2)
                
                return {
                    "success": True, 
                    "message": f"文件传输成功，共 {file_count} 个文件",
                    "file_count": file_count,
                    "transferred_files": transferred_files
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

    def transfer_files_from_phone(self, phone_dir: str, computer_dir: str) -> Dict:
        """
        将手机上的文件/文件夹传输到电脑
        
        参数:
            phone_dir: 手机上的源目录路径
            computer_dir: 电脑上的目标目录路径
            
        返回:
            Dict: 包含操作结果的字典
        """
        try:
            logger.info(f"开始从手机传输文件: {phone_dir} -> {computer_dir}")
            
            # 检查手机源目录是否存在
            if not self._check_path_exists_on_device(phone_dir):
                return {"success": False, "error": f"手机源目录不存在: {phone_dir}"}
            
            # 确保电脑目标目录存在
            os.makedirs(computer_dir, exist_ok=True)
            
            file_count = 0
            success = True
            transferred_files = []
            
            # 检查是否是单个文件
            adb_cmd = self._build_adb_cmd(['shell', 'test', '-f', phone_dir, '&&', 'echo', 'file', '||', 'echo', 'dir'])
            result = subprocess.run(adb_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            is_file = 'file' in result.stdout
            
            if is_file:
                # 单个文件，直接拉取
                filename = os.path.basename(phone_dir)
                target_path = os.path.join(computer_dir, filename)
                
                adb_cmd = self._build_adb_cmd(['pull', phone_dir, target_path])
                result = subprocess.run(adb_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                
                if result.returncode == 0:
                    file_count = 1
                    transferred_files.append(target_path)
                    logger.info(f"文件拉取成功: {filename}")
                else:
                    logger.error(f"文件拉取失败: {result.stderr}")
                    return {"success": False, "error": result.stderr}
            else:
                # 目录，需要递归拉取
                # 先获取目录结构
                adb_cmd = self._build_adb_cmd(['shell', 'find', phone_dir, '-type', 'f'])
                result = subprocess.run(adb_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                
                if result.returncode != 0:
                    return {"success": False, "error": f"获取手机文件列表失败: {result.stderr}"}
                
                phone_files = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                
                logger.info(f"准备从手机拉取 {len(phone_files)} 个文件...")
                
                for phone_file_path in phone_files:
                    # 计算相对路径
                    rel_path = phone_file_path[len(phone_dir):].lstrip('/')
                    target_file_path = os.path.join(computer_dir, rel_path)
                    
                    # 创建目标目录
                    target_file_dir = os.path.dirname(target_file_path)
                    os.makedirs(target_file_dir, exist_ok=True)
                    
                    # 拉取文件
                    adb_cmd = self._build_adb_cmd(['pull', phone_file_path, target_file_path])
                    result = subprocess.run(adb_cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                    
                    if result.returncode == 0:
                        file_count += 1
                        transferred_files.append(target_file_path)
                        logger.info(f"[{file_count}/{len(phone_files)}] 拉取成功: {rel_path}")
                    else:
                        logger.error(f"拉取失败: {rel_path}, 错误: {result.stderr}")
                        success = False
                        break
            
            if success:
                logger.info(f"文件从手机传输成功，共 {file_count} 个文件")
                return {
                    "success": True,
                    "message": f"文件从手机传输成功，共 {file_count} 个文件",
                    "file_count": file_count,
                    "transferred_files": transferred_files
                }
            else:
                return {"success": False, "error": "部分文件拉取失败"}
                
        except Exception as e:
            logger.error(f"从手机传输文件时发生错误: {str(e)}")
            return {"success": False, "error": str(e)}


# 全局文件传输管理器实例
file_transfer_manager = FileTransferManager()
