#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境安装模块
功能：自动安装缺失的环境依赖
"""

import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import tarfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Callable
import tempfile


class EnvInstaller:
    """环境安装器"""
    
    # 国内镜像源列表（优先使用，依次尝试）
    ADB_MIRRORS = [
        # 腾讯云镜像
        'https://mirrors.cloud.tencent.com/android/repository/',
        # 阿里云镜像
        'https://mirrors.aliyun.com/android/repository/',
        # 华为云镜像
        'https://mirrors.huaweicloud.com/android/repository/',
        # 官方源（最后备选）
        'https://dl.google.com/android/repository/'
    ]
    
    def __init__(self):
        self.system = platform.system()
        self.is_windows = self.system == 'Windows'
        self.is_mac = self.system == 'Darwin'
        self.is_linux = self.system == 'Linux'
        
        # 安装目录
        self.install_dir = self._get_install_dir()
        self.bin_dir = os.path.join(self.install_dir, 'bin')
        os.makedirs(self.bin_dir, exist_ok=True)
    
    def _get_install_dir(self) -> str:
        """获取安装目录"""
        if self.is_windows:
            app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
            return os.path.join(app_data, 'xhs_helper', 'tools')
        else:
            return os.path.join(os.path.expanduser('~'), '.xhs_helper', 'tools')
    
    def install_all(self, components: List[str], progress_callback: Optional[Callable] = None) -> Dict:
        """
        安装多个组件
        
        参数:
            components: 要安装的组件列表 ['adb', 'poppler', ...]
            progress_callback: 进度回调函数，签名 (component, status, message)
            
        返回:
            安装结果字典
        """
        results = {}
        
        for component in components:
            if progress_callback:
                progress_callback(component, 'installing', f'正在安装 {component}...')
            
            try:
                if component == 'adb':
                    result = self.install_adb()
                elif component == 'poppler':
                    result = self.install_popper()
                else:
                    result = {
                        'success': False,
                        'message': f'不支持的组件: {component}'
                    }
                
                results[component] = result
                
                if progress_callback:
                    if result['success']:
                        progress_callback(component, 'success', result['message'])
                    else:
                        progress_callback(component, 'error', result['message'])
            except Exception as e:
                error_msg = f'安装 {component} 时出错: {str(e)}'
                results[component] = {
                    'success': False,
                    'message': error_msg
                }
                if progress_callback:
                    progress_callback(component, 'error', error_msg)
        
        return results
    
    def install_adb(self) -> Dict:
        """安装 ADB"""
        if self.is_windows:
            return self._install_adb_windows()
        elif self.is_mac:
            return self._install_adb_mac()
        else:
            return self._install_adb_linux()
    
    def _download_with_mirrors(self, filename: str) -> Optional[str]:
        """
        使用多个镜像源下载文件
        
        参数:
            filename: 要下载的文件名
            
        返回:
            下载成功的文件路径，失败返回 None
        """
        zip_path = os.path.join(tempfile.gettempdir(), filename)
        
        for i, mirror in enumerate(self.ADB_MIRRORS):
            try:
                url = mirror + filename
                print(f'尝试从镜像源 {i+1}/{len(self.ADB_MIRRORS)} 下载: {url}')
                urllib.request.urlretrieve(url, zip_path)
                print(f'下载成功！')
                return zip_path
            except Exception as e:
                print(f'镜像源 {i+1} 下载失败: {str(e)}')
                continue
        
        print('所有镜像源都下载失败')
        return None
    
    def _install_adb_windows(self) -> Dict:
        """Windows 下安装 ADB"""
        try:
            print(f'下载 ADB 工具...')
            zip_path = self._download_with_mirrors('platform-tools-latest-windows.zip')
            
            if not zip_path:
                return {
                    'success': False,
                    'message': 'ADB 下载失败，请检查网络连接\n或手动安装: https://developer.android.com/studio/releases/platform-tools'
                }
            
            print(f'解压 ADB 工具...')
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tempfile.gettempdir())
            
            # 复制需要的文件
            platform_tools_dir = os.path.join(tempfile.gettempdir(), 'platform-tools')
            adb_files = ['adb.exe', 'AdbWinApi.dll', 'AdbWinUsbApi.dll']
            
            for filename in adb_files:
                src = os.path.join(platform_tools_dir, filename)
                dst = os.path.join(self.bin_dir, filename)
                if os.path.exists(src):
                    shutil.copy2(src, dst)
            
            # 清理
            os.remove(zip_path)
            shutil.rmtree(platform_tools_dir, ignore_errors=True)
            
            # 添加到 PATH 环境变量（当前会话）
            self._add_to_path()
            
            return {
                'success': True,
                'message': f'ADB 安装成功到: {self.bin_dir}',
                'path': self.bin_dir
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'安装 ADB 失败: {str(e)}\n请手动安装: https://developer.android.com/studio/releases/platform-tools'
            }
    
    def _install_adb_mac(self) -> Dict:
        """macOS 下安装 ADB"""
        try:
            # 检查是否有 Homebrew
            if shutil.which('brew'):
                print('使用 Homebrew 安装 ADB...')
                result = subprocess.run(
                    ['brew', 'install', '--cask', 'android-platform-tools'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return {
                        'success': True,
                        'message': 'ADB 安装成功'
                    }
            
            # 直接下载 Platform Tools（使用镜像源）
            print(f'下载 ADB 工具...')
            zip_path = self._download_with_mirrors('platform-tools-latest-darwin.zip')
            
            if not zip_path:
                return {
                    'success': False,
                    'message': 'ADB 下载失败，请检查网络连接\n或手动运行: brew install --cask android-platform-tools'
                }
            
            print(f'解压 ADB 工具...')
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tempfile.gettempdir())
            
            # 复制 adb
            platform_tools_dir = os.path.join(tempfile.gettempdir(), 'platform-tools')
            adb_src = os.path.join(platform_tools_dir, 'adb')
            adb_dst = os.path.join(self.bin_dir, 'adb')
            
            if os.path.exists(adb_src):
                shutil.copy2(adb_src, adb_dst)
                os.chmod(adb_dst, 0o755)
            
            # 清理
            os.remove(zip_path)
            shutil.rmtree(platform_tools_dir, ignore_errors=True)
            
            self._add_to_path()
            
            return {
                'success': True,
                'message': f'ADB 安装成功到: {self.bin_dir}',
                'path': self.bin_dir
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'安装 ADB 失败: {str(e)}\n请手动运行: brew install --cask android-platform-tools'
            }
    
    def _install_adb_linux(self) -> Dict:
        """Linux 下安装 ADB"""
        try:
            # 尝试使用系统包管理器
            for pkg_manager in ['apt-get', 'apt', 'dnf', 'yum', 'pacman']:
                if shutil.which(pkg_manager):
                    if pkg_manager in ['apt-get', 'apt']:
                        cmd = ['sudo', pkg_manager, 'install', '-y', 'android-tools-adb']
                    elif pkg_manager in ['dnf', 'yum']:
                        cmd = ['sudo', pkg_manager, 'install', '-y', 'android-tools']
                    elif pkg_manager == 'pacman':
                        cmd = ['sudo', pkg_manager, '-S', '--noconfirm', 'android-tools']
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        return {
                            'success': True,
                            'message': 'ADB 安装成功'
                        }
                    break
            
            return {
                'success': False,
                'message': '请使用系统包管理器安装 android-tools 或 android-tools-adb'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'安装 ADB 失败: {str(e)}'
            }
    
    def install_popper(self) -> Dict:
        """安装 Poppler"""
        if self.is_windows:
            return self._install_popper_windows()
        elif self.is_mac:
            return self._install_popper_mac()
        else:
            return self._install_popper_linux()
    
    def _install_popper_windows(self) -> Dict:
        """Windows 下安装 Poppler"""
        try:
            # 从 GitHub 下载 Poppler for Windows
            url = 'https://github.com/oschwartz10612/poppler-windows/releases/download/v24.02.0-0/Release-24.02.0-0.zip'
            zip_path = os.path.join(tempfile.gettempdir(), 'poppler.zip')
            
            print(f'下载 Poppler...')
            urllib.request.urlretrieve(url, zip_path)
            
            print(f'解压 Poppler...')
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tempfile.gettempdir())
            
            # 查找 bin 目录
            poppler_dir = None
            for item in os.listdir(tempfile.gettempdir()):
                if item.startswith('Release-'):
                    poppler_dir = os.path.join(tempfile.gettempdir(), item)
                    break
            
            if poppler_dir:
                bin_src = os.path.join(poppler_dir, 'Library', 'bin')
                if os.path.exists(bin_src):
                    # 复制所有 exe 和 dll
                    for filename in os.listdir(bin_src):
                        src = os.path.join(bin_src, filename)
                        dst = os.path.join(self.bin_dir, filename)
                        if os.path.isfile(src):
                            shutil.copy2(src, dst)
            
            # 清理
            os.remove(zip_path)
            if poppler_dir:
                shutil.rmtree(poppler_dir, ignore_errors=True)
            
            self._add_to_path()
            
            return {
                'success': True,
                'message': f'Poppler 安装成功到: {self.bin_dir}',
                'path': self.bin_dir
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'安装 Poppler 失败: {str(e)}\n请手动下载: https://github.com/oschwartz10612/poppler-windows'
            }
    
    def _install_popper_mac(self) -> Dict:
        """macOS 下安装 Poppler"""
        try:
            if shutil.which('brew'):
                print('使用 Homebrew 安装 Poppler...')
                result = subprocess.run(
                    ['brew', 'install', 'poppler'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return {
                        'success': True,
                        'message': 'Poppler 安装成功'
                    }
            
            return {
                'success': False,
                'message': '请手动运行: brew install poppler'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'安装 Poppler 失败: {str(e)}\n请手动运行: brew install poppler'
            }
    
    def _install_popper_linux(self) -> Dict:
        """Linux 下安装 Poppler"""
        try:
            for pkg_manager in ['apt-get', 'apt', 'dnf', 'yum', 'pacman']:
                if shutil.which(pkg_manager):
                    if pkg_manager in ['apt-get', 'apt']:
                        cmd = ['sudo', pkg_manager, 'install', '-y', 'poppler-utils']
                    elif pkg_manager in ['dnf', 'yum']:
                        cmd = ['sudo', pkg_manager, 'install', '-y', 'poppler-utils']
                    elif pkg_manager == 'pacman':
                        cmd = ['sudo', pkg_manager, '-S', '--noconfirm', 'poppler']
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        return {
                            'success': True,
                            'message': 'Poppler 安装成功'
                        }
                    break
            
            return {
                'success': False,
                'message': '请使用系统包管理器安装 poppler-utils'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'安装 Poppler 失败: {str(e)}'
            }
    
    def _add_to_path(self):
        """将安装目录添加到 PATH 环境变量"""
        if self.bin_dir not in os.environ['PATH']:
            os.environ['PATH'] = self.bin_dir + os.pathsep + os.environ['PATH']
    
    def get_install_dir(self) -> str:
        """获取安装目录"""
        return self.install_dir
    
    def get_bin_dir(self) -> str:
        """获取二进制文件目录"""
        return self.bin_dir


def main():
    """测试安装器"""
    installer = EnvInstaller()
    print(f'安装目录: {installer.get_install_dir()}')
    print(f'二进制目录: {installer.get_bin_dir()}')
    print('\n可用的安装组件: adb, poppler')


if __name__ == '__main__':
    main()
