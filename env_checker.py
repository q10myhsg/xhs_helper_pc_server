#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境检查模块
功能：检查系统环境依赖是否满足
"""

import os
import sys
import subprocess
import platform
import shutil
from typing import Dict, List, Optional, Tuple


class EnvChecker:
    """环境检查器"""
    
    def __init__(self):
        self.system = platform.system()
        self.architecture = platform.machine()
        self.python_version = platform.python_version()
        self.results = {}
        
    def check_all(self) -> Dict:
        """检查所有依赖项"""
        self.results = {
            'python': self.check_python(),
            'adb': self.check_adb(),
            'poppler': self.check_poppler(),
            'git': self.check_git()
        }
        return self.results
    
    def check_python(self) -> Dict:
        """检查 Python 环境"""
        result = {
            'available': False,
            'version': None,
            'message': '',
            'path': sys.executable
        }
        
        try:
            result['version'] = platform.python_version()
            major, minor = map(int, result['version'].split('.')[:2])
            
            if major >= 3 and minor >= 7:
                result['available'] = True
                result['message'] = f'Python {result["version"]} (符合要求)'
            else:
                result['message'] = f'Python 版本过低，需要 Python 3.7+，当前版本: {result["version"]}'
        except Exception as e:
            result['message'] = f'检查 Python 时出错: {str(e)}'
        
        return result
    
    def check_adb(self) -> Dict:
        """检查 ADB 是否可用"""
        result = {
            'available': False,
            'version': None,
            'message': '',
            'path': None
        }
        
        adb_path = self._find_command('adb')
        if adb_path:
            result['path'] = adb_path
            try:
                cmd_output = subprocess.run(
                    [adb_path, 'version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if cmd_output.returncode == 0:
                    result['available'] = True
                    result['message'] = 'ADB 可用'
                    # 提取版本信息
                    for line in cmd_output.stdout.split('\n'):
                        if 'version' in line.lower():
                            result['version'] = line.strip()
                            break
            except Exception as e:
                result['message'] = f'ADB 命令执行失败: {str(e)}'
        else:
            result['message'] = '未找到 ADB，请安装 Android SDK 或 Android Studio'
        
        return result
    
    def check_poppler(self) -> Dict:
        """检查 Poppler (PDF 处理所需)"""
        result = {
            'available': False,
            'version': None,
            'message': '',
            'path': None
        }
        
        pdftoppm = self._find_command('pdftoppm')
        if pdftoppm:
            result['path'] = pdftoppm
            try:
                cmd_output = subprocess.run(
                    [pdftoppm, '-v'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if cmd_output.returncode == 0:
                    result['available'] = True
                    result['message'] = 'Poppler 可用'
                    # 从 stderr 获取版本信息
                    if cmd_output.stderr:
                        result['version'] = cmd_output.stderr.strip()
            except Exception as e:
                result['message'] = f'Poppler 命令执行失败: {str(e)}'
        else:
            if self.system == 'Windows':
                result['message'] = '未找到 Poppler，请从 https://github.com/oschwartz10612/poppler-windows 下载'
            elif self.system == 'Darwin':
                result['message'] = '未找到 Poppler，请运行: brew install poppler'
            else:
                result['message'] = '未找到 Poppler，请安装 poppler-utils'
        
        return result
    
    def check_git(self) -> Dict:
        """检查 Git 是否可用"""
        result = {
            'available': False,
            'version': None,
            'message': '',
            'path': None
        }
        
        git_path = self._find_command('git')
        if git_path:
            result['path'] = git_path
            try:
                cmd_output = subprocess.run(
                    [git_path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if cmd_output.returncode == 0:
                    result['available'] = True
                    result['message'] = 'Git 可用'
                    result['version'] = cmd_output.stdout.strip()
            except Exception as e:
                result['message'] = f'Git 命令执行失败: {str(e)}'
        else:
            result['message'] = '未找到 Git，请安装 Git'
        
        return result
    
    def _find_command(self, cmd: str) -> Optional[str]:
        """查找命令的完整路径"""
        return shutil.which(cmd)
    
    def get_summary(self) -> str:
        """获取检查摘要"""
        if not self.results:
            self.check_all()
        
        summary_lines = [
            '=' * 60,
            '环境检查摘要',
            '=' * 60,
            f'系统: {self.system} {self.architecture}',
            ''
        ]
        
        for name, result in self.results.items():
            status = '✓' if result['available'] else '✗'
            line = f'{status} {name.upper()}: {result["message"]}'
            summary_lines.append(line)
        
        summary_lines.extend([
            '',
            '=' * 60
        ])
        
        return '\n'.join(summary_lines)
    
    def get_missing_dependencies(self) -> List[str]:
        """获取缺失的依赖项列表"""
        if not self.results:
            self.check_all()
        
        missing = []
        for name, result in self.results.items():
            if not result['available'] and name != 'git':
                missing.append(name)
        
        return missing


def main():
    """测试环境检查"""
    checker = EnvChecker()
    results = checker.check_all()
    print(checker.get_summary())
    
    missing = checker.get_missing_dependencies()
    if missing:
        print(f'\n缺失的依赖项: {", ".join(missing)}')
    else:
        print('\n所有核心依赖项已满足!')


if __name__ == '__main__':
    main()
