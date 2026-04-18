#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
虚拟环境管理模块
功能：创建和管理 Python 虚拟环境
"""

import os
import sys
import subprocess
import platform
import venv
from pathlib import Path
from typing import Dict, Optional, List


class VenvManager:
    """虚拟环境管理器"""
    
    def __init__(self, base_dir: Optional[str] = None):
        self.system = platform.system()
        self.is_windows = self.system == 'Windows'
        self.is_mac = self.system == 'Darwin'
        
        if base_dir is None:
            if self.is_windows:
                app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
                self.base_dir = os.path.join(app_data, 'xhs_helper', 'venvs')
            else:
                self.base_dir = os.path.join(os.path.expanduser('~'), '.xhs_helper', 'venvs')
        else:
            self.base_dir = base_dir
        
        os.makedirs(self.base_dir, exist_ok=True)
    
    def create_venv(self, name: str = 'xhs_helper_env', python_path: Optional[str] = None) -> Dict:
        """
        创建虚拟环境
        
        参数:
            name: 虚拟环境名称
            python_path: 指定 Python 解释器路径，默认使用当前 Python
            
        返回:
            操作结果字典
        """
        try:
            venv_path = os.path.join(self.base_dir, name)
            
            # 如果环境已存在，询问是否删除
            if os.path.exists(venv_path):
                return {
                    'success': False,
                    'message': f'虚拟环境已存在: {venv_path}\n请先删除或使用其他名称'
                }
            
            print(f'正在创建虚拟环境: {venv_path}')
            
            # 使用 venv 模块创建
            if python_path is None:
                python_path = sys.executable
            
            venv.create(venv_path, with_pip=True, symlinks=False)
            
            print('虚拟环境创建成功')
            
            # 升级 pip
            pip_path = self._get_pip_path(venv_path)
            if pip_path:
                print('正在升级 pip...')
                subprocess.run([pip_path, 'install', '--upgrade', 'pip'], capture_output=True)
            
            return {
                'success': True,
                'message': f'虚拟环境创建成功: {venv_path}',
                'venv_path': venv_path,
                'python_path': self._get_python_path(venv_path),
                'pip_path': pip_path
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'创建虚拟环境失败: {str(e)}'
            }
    
    def delete_venv(self, name: str = 'xhs_helper_env') -> Dict:
        """删除虚拟环境"""
        try:
            import shutil
            
            venv_path = os.path.join(self.base_dir, name)
            
            if not os.path.exists(venv_path):
                return {
                    'success': False,
                    'message': f'虚拟环境不存在: {venv_path}'
                }
            
            print(f'正在删除虚拟环境: {venv_path}')
            shutil.rmtree(venv_path)
            
            return {
                'success': True,
                'message': f'虚拟环境删除成功: {venv_path}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'删除虚拟环境失败: {str(e)}'
            }
    
    def install_requirements(self, venv_name: str, requirements_path: str) -> Dict:
        """在虚拟环境中安装依赖"""
        try:
            venv_path = os.path.join(self.base_dir, venv_name)
            
            if not os.path.exists(venv_path):
                return {
                    'success': False,
                    'message': f'虚拟环境不存在: {venv_path}'
                }
            
            if not os.path.exists(requirements_path):
                return {
                    'success': False,
                    'message': f'requirements.txt 不存在: {requirements_path}'
                }
            
            pip_path = self._get_pip_path(venv_path)
            if not pip_path:
                return {
                    'success': False,
                    'message': '未找到 pip'
                }
            
            print(f'正在安装依赖到虚拟环境...')
            result = subprocess.run(
                [pip_path, 'install', '-r', requirements_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': '依赖安装成功'
                }
            else:
                return {
                    'success': False,
                    'message': f'依赖安装失败: {result.stderr}'
                }
        except Exception as e:
            return {
                'success': False,
                'message': f'安装依赖时出错: {str(e)}'
            }
    
    def get_venv_python(self, venv_name: str = 'xhs_helper_env') -> Optional[str]:
        """获取虚拟环境的 Python 解释器路径"""
        venv_path = os.path.join(self.base_dir, venv_name)
        return self._get_python_path(venv_path)
    
    def list_venvs(self) -> List[str]:
        """列出所有虚拟环境"""
        try:
            venvs = []
            if os.path.exists(self.base_dir):
                for name in os.listdir(self.base_dir):
                    venv_path = os.path.join(self.base_dir, name)
                    if os.path.isdir(venv_path):
                        # 检查是否是有效的虚拟环境
                        py_path = self._get_python_path(venv_path)
                        if py_path and os.path.exists(py_path):
                            venvs.append(name)
            return venvs
        except Exception:
            return []
    
    def venv_exists(self, name: str = 'xhs_helper_env') -> bool:
        """检查虚拟环境是否存在"""
        venv_path = os.path.join(self.base_dir, name)
        if not os.path.exists(venv_path):
            return False
        py_path = self._get_python_path(venv_path)
        return py_path is not None and os.path.exists(py_path)
    
    def _get_python_path(self, venv_path: str) -> Optional[str]:
        """获取虚拟环境的 Python 解释器路径"""
        if self.is_windows:
            paths = [
                os.path.join(venv_path, 'Scripts', 'python.exe'),
                os.path.join(venv_path, 'Scripts', 'pythonw.exe')
            ]
        else:
            paths = [
                os.path.join(venv_path, 'bin', 'python'),
                os.path.join(venv_path, 'bin', 'python3')
            ]
        
        for path in paths:
            if os.path.exists(path):
                return path
        return None
    
    def _get_pip_path(self, venv_path: str) -> Optional[str]:
        """获取虚拟环境的 pip 路径"""
        if self.is_windows:
            paths = [
                os.path.join(venv_path, 'Scripts', 'pip.exe'),
                os.path.join(venv_path, 'Scripts', 'pip3.exe')
            ]
        else:
            paths = [
                os.path.join(venv_path, 'bin', 'pip'),
                os.path.join(venv_path, 'bin', 'pip3')
            ]
        
        for path in paths:
            if os.path.exists(path):
                return path
        return None
    
    def get_base_dir(self) -> str:
        """获取虚拟环境基目录"""
        return self.base_dir


def main():
    """测试虚拟环境管理器"""
    manager = VenvManager()
    print(f'虚拟环境基目录: {manager.get_base_dir()}')
    print(f'现有虚拟环境: {manager.list_venvs()}')
    print(f'默认虚拟环境存在: {manager.venv_exists()}')


if __name__ == '__main__':
    main()
