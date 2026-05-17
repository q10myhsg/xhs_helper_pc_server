"""
subprocess 工具封装：Windows 上自动添加 CREATE_NO_WINDOW，
避免每次调用子进程时弹出黑色控制台窗口。
其他平台行为与标准 subprocess.run / Popen 完全一致。
"""
import subprocess
import sys


def run(*args, **kwargs):
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.run(*args, **kwargs)


def Popen(*args, **kwargs):
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.Popen(*args, **kwargs)
