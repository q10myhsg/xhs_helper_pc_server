
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import base64
import os
import subprocess

# ---------------------- 核心配置（需替换为你的大模型API） ----------------------
LLM_API_URL = "http://localhost:8000/v1/chat/completions"  # 你的多模态大模型API地址
LLM_API_KEY = "your-api-key"  # 本地部署模型可填任意值
ADB_PATH = "adb"  # ADB路径（已配置环境变量则直接填adb）

# ---------------------- 轻量GUI核心逻辑 ----------------------
class LLMDrivenDesktopAgent:
    def __init__(self, root):
        self.root = root
        self.root.title("轻量桌面Agent（大模型驱动）")
        self.root.geometry("800x600")  # 界面大小
        
        # 存储对话记录
        self.chat_history = []
        # 存储选中的文件路径
        self.selected_file = None
        
        # 构建界面
        self._build_ui()
    
    def _build_ui(self):
        # 1. 对话展示区（核心）
        chat_frame = ttk.Frame(self.root)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 对话文本框（只读，展示记录）
        self.chat_text = tk.Text(chat_frame, state=tk.DISABLED, wrap=tk.WORD)
        self.chat_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 滚动条
        chat_scroll = ttk.Scrollbar(chat_frame, command=self.chat_text.yview)
        chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_text.config(yscrollcommand=chat_scroll.set)
        
        # 2. 文件上传区
        file_frame = ttk.Frame(self.root)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(file_frame, text="上传文件：").pack(side=tk.LEFT)
        self.file_label = ttk.Label(file_frame, text="未选择文件")
        self.file_label.pack(side=tk.LEFT, padx=10)
        ttk.Button(file_frame, text="选择PDF/图片", command=self._select_file).pack(side=tk.LEFT)
        
        # 3. 输入与操作区
        input_frame = ttk.Frame(self.root)
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 指令输入框
        self.input_entry = ttk.Entry(input_frame)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 发送按钮
        ttk.Button(input_frame, text="发送", command=self._send_message).pack(side=tk.LEFT, padx=5)
        
        # 辅助操作按钮
        ttk.Button(input_frame, text="保存结果", command=self._save_result).pack(side=tk.LEFT, padx=5)
        ttk.Button(input_frame, text="执行设备指令", command=self._execute_device_cmd).pack(side=tk.LEFT, padx=5)
    
    def _select_file(self):
        """选择PDF/图片文件（本地只选文件，不解析）"""
        file_path = filedialog.askopenfilename(
            filetypes=[("支持的文件", "*.pdf *.png *.jpg *.jpeg")]
        )
        if file_path:
            self.selected_file = file_path
            self.file_label.config(text=os.path.basename(file_path))
    
    def _send_message(self):
        """发送指令给大模型（核心交互）"""
        user_prompt = self.input_entry.get().strip()
        if not user_prompt:
            messagebox.showwarning("提示", "请输入指令！")
            return
        
        # 1. 更新对话记录（用户消息）
        self._update_chat(f"你：{user_prompt}", "user")
        self.input_entry.delete(0, tk.END)
        
        # 2. 调用大模型（本地只做API调用，无任何解析/生成逻辑）
        try:
            self.root.config(cursor="wait")  # 加载中光标
            response = self._call_llm(user_prompt)
            # 3. 更新对话记录（模型回复）
            self._update_chat(f"模型：{response}", "model")
            # 保存最新回复，用于后续保存/执行
            self.latest_response = response
        except Exception as e:
            self._update_chat(f"错误：{str(e)}", "error")
        finally:
            self.root.config(cursor="")  # 恢复光标
    
    def _call_llm(self, prompt):
        """调用大模型API（本地唯一的核心调用逻辑）"""
        # 构建请求参数（适配多模态模型）
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 基础对话消息
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        # 如果有上传文件，传给模型（本地只传路径/二进制，不解析）
        if self.selected_file:
            # 读取文件并转base64（交给模型解析）
            with open(self.selected_file, "rb") as f:
                file_base64 = base64.b64encode(f.read()).decode("utf-8")
            # 多模态消息格式（适配主流大模型API）
            messages[0]["content"] = [
                {"type": "text", "text": prompt},
                {"type": "image_url" if self.selected_file.endswith(("png", "jpg", "jpeg")) else "file",
                 "image_url": {"url": f"data:image/jpeg;base64,{file_base64}"}}
            ]
        
        # 调用大模型API
        data = {
            "model": "your-model-name",  # 你的多模态模型名称
            "messages": messages,
            "temperature": 0.7
        }
        resp = requests.post(LLM_API_URL, headers=headers, json=data)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    
    def _update_chat(self, content, msg_type):
        """更新对话界面"""
        self.chat_text.config(state=tk.NORMAL)
        # 不同类型消息加颜色标记
        if msg_type == "user":
            self.chat_text.insert(tk.END, content + "\n\n", "user")
        elif msg_type == "model":
            self.chat_text.insert(tk.END, content + "\n\n", "model")
        else:
            self.chat_text.insert(tk.END, content + "\n\n", "error")
        # 设置颜色标签
        self.chat_text.tag_config("user", foreground="#2196F3")
        self.chat_text.tag_config("model", foreground="#4CAF50")
        self.chat_text.tag_config("error", foreground="#F44336")
        # 滚动到最底部
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)
    
    def _save_result(self):
        """保存大模型返回的结果（本地只做保存，不处理内容）"""
        if not hasattr(self, "latest_response"):
            messagebox.showwarning("提示", "暂无可保存的结果！")
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("HTML文件", "*.html"), ("Word文件", "*.docx")]
        )
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(self.latest_response)
            messagebox.showinfo("成功", f"结果已保存到：{save_path}")
    
    def _execute_device_cmd(self):
        """执行大模型生成的跨设备指令（本地只执行，不生成逻辑）"""
        if not hasattr(self, "latest_response"):
            messagebox.showwarning("提示", "暂无设备指令！")
            return
        # 假设模型返回的是ADB指令，本地直接执行
        try:
            # 提取指令（可让模型按固定格式返回，比如【ADB指令：xxx】）
            cmd_start = self.latest_response.find("【ADB指令：") + len("【ADB指令：")
            cmd_end = self.latest_response.find("】", cmd_start)
            adb_cmd = self.latest_response[cmd_start:cmd_end].strip()
            
            # 执行ADB指令（本地只做执行，无逻辑）
            result = subprocess.run(
                f"{ADB_PATH} {adb_cmd}",
                shell=True,
                capture_output=True,
                encoding="utf-8"
            )
            if result.returncode == 0:
                self._update_chat(f"执行结果：{result.stdout}", "model")
            else:
                self._update_chat(f"执行失败：{result.stderr}", "error")
        except Exception as e:
            self._update_chat(f"解析/执行指令失败：{str(e)}", "error")

# ---------------------- 启动界面 ----------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = LLMDrivenDesktopAgent(root)
    root.mainloop()