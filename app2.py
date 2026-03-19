from flask import Flask, request, jsonify, make_response, send_from_directory, Response, stream_with_context, render_template
import requests
import os
import json
import uuid
from openai import OpenAI
from utils import generate_doubao_chat_word, generate_doubao_chat_html, generate_doubao_chat_image

# 初始化Flask应用
app = Flask(__name__)

# 对话存储结构，用于保存不同对话的历史
conversations = {}

# 生成唯一对话ID
def generate_conversation_id():
    return str(uuid.uuid4())

# 创建新对话
def create_new_conversation():
    conversation_id = generate_conversation_id()
    # 初始化对话历史，包含系统消息
    conversations[conversation_id] = [
        {"role": "assistant", "content": "您好！我是大模型，很高兴为您服务～ 您可以发送消息开始对话，也可以生成Word/HTML/图像文件保存对话记录！"}
    ]
    return conversation_id, conversations[conversation_id]

# 加载配置文件
config_path = os.path.join(os.path.dirname(__file__), 'config', 'llm_config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    LLM_CONFIG = json.load(f)

# 获取默认配置
default_provider = LLM_CONFIG.get('default_provider', 'doubao')
default_model = LLM_CONFIG.get('default_model', '')

# 获取当前提供商的配置
current_provider_config = LLM_CONFIG.get('models', {}).get(default_provider, {})
current_api_key = current_provider_config.get('api_key', '')
current_api_url = current_provider_config.get('api_url', '')
current_support_models = current_provider_config.get('supported_models', [])

# 确保有默认模型
if not default_model and current_support_models:
    default_model = current_support_models[0]

# 生成文件存储目录（自动创建，与utils.py一致）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATE_DIR = os.path.join(BASE_DIR, "static/generate_files")
WORD_DIR = os.path.join(GENERATE_DIR, "word")
HTML_DIR = os.path.join(GENERATE_DIR, "html")
IMAGE_DIR = os.path.join(GENERATE_DIR, "image")
UPLOAD_DIR = os.path.join(GENERATE_DIR, "upload")
# 自动创建所有目录，避免文件保存失败
for dir_path in [GENERATE_DIR, WORD_DIR, HTML_DIR, IMAGE_DIR, UPLOAD_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# 首页路由：渲染WebUI界面
@app.route("/", methods=["GET"])
def index():
    return render_template("index2.html", models=current_support_models)

# 创建新对话的API接口
@app.route("/api/new_conversation", methods=["POST"])
def new_conversation():
    try:
        # 创建新对话
        conversation_id, conversation_history = create_new_conversation()
        print(f"创建新对话，ID: {conversation_id}")
        return jsonify({
            "code": 200,
            "conversation_id": conversation_id,
            "messages": conversation_history
        })
    except Exception as e:
        print(f"创建新对话失败: {e}")
        return jsonify({"code": 500, "msg": f"创建新对话失败：{str(e)}"}), 500

# 大模型API调用路由（流式输出，WebUI打字机效果核心）
@app.route("/api/chat", methods=["POST"])
def llm_chat():
    try:
        # 获取前端传参
        data = request.get_json()
        messages = data.get("messages", [])
        stream = data.get("stream", True)
        temperature = float(data.get("temperature", 0.7))
        top_p = float(data.get("top_p", 0.9))
        model = data.get("model", default_model)
        conversation_id = data.get("conversation_id")

        # 校验参数
        if not current_api_key or current_api_key.startswith("your-"):
            return jsonify({"code": 400, "msg": f"请先在配置文件中配置真实的{default_provider} API Key！"}), 400
        if not messages:
            return jsonify({"code": 400, "msg": "无对话内容，请先发送消息！"}), 400
        if model not in current_support_models:
            return jsonify({"code": 400, "msg": f"不支持的模型，仅支持：{','.join(current_support_models)}"}), 400

        # 处理对话管理
        if conversation_id:
            # 检查对话是否存在
            if conversation_id not in conversations:
                return jsonify({"code": 404, "msg": "对话不存在，请先创建新对话！"}), 404
            # 获取现有对话历史
            conversation_history = conversations[conversation_id]
        else:
            # 如果没有提供对话ID，创建新对话
            conversation_id, conversation_history = create_new_conversation()

        # 更新对话历史，添加用户消息
        user_message = messages[-1]  # 假设最后一条消息是用户消息
        if user_message["role"] == "user":
            conversation_history.append(user_message)

        # 创建OpenAI客户端
        client = OpenAI(
            base_url=current_api_url,
            api_key=current_api_key,
        )

        # 流式响应（WebUI首选，打字机效果核心）
        if stream:
            # 调用API，开启流式请求
            print(f"调用{default_provider} API: {current_api_url}")
            print(f"模型: {model}")
            print(f"消息: {conversation_history}")
            print(f"对话ID: {conversation_id}")
            
            # 使用OpenAI SDK的流式调用
            response = client.chat.completions.create(
                model=model,
                messages=conversation_history,
                stream=stream,
                temperature=temperature,
                top_p=top_p
            )
            
            # 用于存储模型的完整回复
            assistant_response = ""
            
            # 封装为Flask流式响应，适配前端解析
            def generate():
                nonlocal assistant_response
                for chunk in response:
                    # 转换为前端期望的格式
                    if chunk.choices and chunk.choices[0].delta:
                        content = chunk.choices[0].delta.content or ""
                        finish_reason = chunk.choices[0].finish_reason
                        
                        # 累积模型回复
                        assistant_response += content
                        
                        # 构造响应数据
                        data = {
                            "id": chunk.id,
                            "object": "chat.completion.chunk",
                            "created": chunk.created,
                            "model": chunk.model,
                            "conversation_id": conversation_id,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "content": content
                                    },
                                    "finish_reason": finish_reason
                                }
                            ]
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                        
                        # 如果完成，发送结束信号
                        if finish_reason:
                            # 更新对话历史，添加模型回复
                            conversation_history.append({"role": "assistant", "content": assistant_response})
                            yield "data: [DONE]\n\n"
            
            return Response(
                generate(),
                mimetype="text/event-stream; charset=utf-8"
            )
        # 非流式响应（备用）
        else:
            print(f"调用{default_provider} API: {current_api_url}")
            print(f"模型: {model}")
            print(f"消息: {conversation_history}")
            print(f"对话ID: {conversation_id}")
            
            # 使用OpenAI SDK的非流式调用
            response = client.chat.completions.create(
                model=model,
                messages=conversation_history,
                stream=stream,
                temperature=temperature,
                top_p=top_p
            )
            
            print(f"API响应: {response}")
            
            # 构造响应数据
            content = response.choices[0].message.content
            
            # 更新对话历史，添加模型回复
            conversation_history.append({"role": "assistant", "content": content})
            
            return jsonify({
                "code": 200,
                "content": content,
                "conversation_id": conversation_id
            })
    except Exception as e:
        print(f"API调用失败: {e}")
        return jsonify({"code": 500, "msg": f"{default_provider} API调用失败：{str(e)}"}), 500

# Word生成路由
@app.route("/api/generate/word", methods=["POST"])
def generate_word():
    try:
        data = request.get_json()
        messages = data.get("messages", [])
        if not messages:
            return jsonify({"code": 400, "msg": "无对话内容，无法生成Word！"}), 400
        # 调用工具函数生成Word
        file_path, file_name = generate_doubao_chat_word(messages)
        return jsonify({
            "code": 200,
            "msg": "Word生成成功！",
            "file_name": file_name,
            "download_url": f"/api/download?type=word&filename={file_name}"
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": f"Word生成失败：{str(e)}"}), 500

# HTML生成路由（含预览代码）
@app.route("/api/generate/html", methods=["POST"])
def generate_html():
    try:
        data = request.get_json()
        messages = data.get("messages", [])
        if not messages:
            return jsonify({"code": 400, "msg": "无对话内容，无法生成HTML！"}), 400
        # 调用工具函数生成HTML
        file_path, file_name, full_html = generate_doubao_chat_html(messages)
        return jsonify({
            "code": 200,
            "msg": "HTML生成成功！",
            "file_name": file_name,
            "download_url": f"/api/download?type=html&filename={file_name}",
            "html_code": full_html  # 返回纯HTML代码，供前端预览
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": f"HTML生成失败：{str(e)}"}), 500

# 图像生成路由
@app.route("/api/generate/image", methods=["POST"])
def generate_image():
    try:
        data = request.get_json()
        messages = data.get("messages", [])
        img_size = tuple(data.get("img_size", [1200, 800]))  # 前端自定义尺寸
        img_format = data.get("img_format", "PNG")          # 前端自定义格式
        if not messages:
            return jsonify({"code": 400, "msg": "无对话内容，无法生成图像！"}), 400
        # 调用工具函数生成图像
        file_path, file_name = generate_doubao_chat_image(messages, img_size=img_size, img_format=img_format)
        return jsonify({
            "code": 200,
            "msg": "图像生成成功！",
            "file_name": file_name,
            "download_url": f"/api/download?type=image&filename={file_name}"
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": f"图像生成失败：{str(e)}"}), 500

# 文件上传路由
@app.route("/api/upload", methods=["POST"])
def upload_file():
    try:
        # 检查是否有文件部分
        if "file" not in request.files:
            return jsonify({"code": 400, "msg": "请选择要上传的文件！"}), 400
        
        file = request.files["file"]
        # 检查文件是否为空
        if file.filename == "":
            return jsonify({"code": 400, "msg": "请选择要上传的文件！"}), 400
        
        # 为文件生成唯一文件名
        import uuid
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # 保存文件
        file.save(file_path)
        
        # 生成文件URL
        file_url = f"/static/generate_files/upload/{unique_filename}"
        
        return jsonify({
            "code": 200,
            "msg": "文件上传成功！",
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_url": file_url,
            "file_path": file_path
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": f"文件上传失败：{str(e)}"}), 500

# 统一下载路由（支持Word/HTML/图像/上传文件，解决中文乱码）
@app.route("/api/download", methods=["GET"])
def unified_download():
    try:
        # 获取请求参数
        file_type = request.args.get("type")
        file_name = request.args.get("filename")
        # 映射文件类型到对应目录
        type2dir = {"word": WORD_DIR, "html": HTML_DIR, "image": IMAGE_DIR, "upload": UPLOAD_DIR}
        # 校验参数
        if not file_type or not file_name or file_type not in type2dir:
            return jsonify({"code": 400, "msg": "参数错误！请指定正确的文件类型和文件名"}), 400
        file_dir = type2dir[file_type]
        file_full_path = os.path.join(file_dir, file_name)
        if not os.path.exists(file_full_path):
            return jsonify({"code": 404, "msg": "文件不存在！可能已被清理"}), 404

        # 构造下载响应，解决中文文件名乱码
        response = make_response(
            send_from_directory(file_dir, file_name, as_attachment=True)
        )
        response.headers["Content-Disposition"] = f"attachment; filename*=utf-8''{file_name}"
        # 配置对应Content-Type，适配不同文件
        if file_type == "html":
            response.headers["Content-Type"] = "text/html; charset=utf-8"
        elif file_type == "image":
            response.headers["Content-Type"] = "image/png" if file_name.endswith((".png", ".PNG")) else "image/jpeg"
        elif file_type == "upload":
            # 根据文件扩展名设置Content-Type
            if file_name.endswith((".png", ".PNG")):
                response.headers["Content-Type"] = "image/png"
            elif file_name.endswith((".jpg", ".jpeg", ".JPG", ".JPEG")):
                response.headers["Content-Type"] = "image/jpeg"
            elif file_name.endswith((".pdf", ".PDF")):
                response.headers["Content-Type"] = "application/pdf"
            elif file_name.endswith((".txt", ".TXT")):
                response.headers["Content-Type"] = "text/plain; charset=utf-8"
            elif file_name.endswith((".doc", ".docx", ".DOC", ".DOCX")):
                response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif file_name.endswith((".xls", ".xlsx", ".XLS", ".XLSX")):
                response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                response.headers["Content-Type"] = "application/octet-stream"
        else:
            response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return response
    except Exception as e:
        return jsonify({"code": 500, "msg": f"文件下载失败：{str(e)}"}), 500

# OpenAI风格的API接口（兼容OpenAI客户端和库）
@app.route("/v1/chat/completions", methods=["POST"])
def openai_chat_completions():
    try:
        # 获取请求数据（OpenAI格式）
        data = request.get_json()
        
        # 提取OpenAI格式的参数
        model = data.get("model", default_model)
        messages = data.get("messages", [])
        stream = data.get("stream", True)
        temperature = float(data.get("temperature", 0.7))
        top_p = float(data.get("top_p", 0.9))
        max_tokens = data.get("max_tokens", 2048)
        conversation_id = data.get("conversation_id")
        
        # 打印调试信息
        print(f"OpenAI风格API请求：")
        print(f"模型：{model}")
        print(f"消息：{messages}")
        print(f"流式：{stream}")
        print(f"温度：{temperature}")
        print(f"Top P：{top_p}")
        print(f"对话ID：{conversation_id}")
        
        # 校验参数
        if not messages:
            return jsonify({
                "error": {
                    "message": "无对话内容，请先发送消息！",
                    "type": "invalid_request_error",
                    "param": None,
                    "code": None
                }
            }), 400
        
        # 确定使用哪个提供商
        provider = default_provider
        # 获取当前支持的模型列表
        current_support_models_list = current_support_models
        # 检查模型是否在当前提供商的支持列表中
        if model not in current_support_models_list:
            # 尝试在所有提供商中查找该模型
            found = False
            for p, p_config in LLM_CONFIG.get('models', {}).items():
                if model in p_config.get('supported_models', []):
                    provider = p
                    current_provider_config = p_config
                    api_key = p_config.get('api_key', '')
                    api_url = p_config.get('api_url', '')
                    current_support_models_list = p_config.get('supported_models', [])
                    found = True
                    break
            if not found:
                return jsonify({
                    "error": {
                        "message": f"不支持的模型：{model}，请在配置文件中添加该模型",
                        "type": "invalid_request_error",
                        "param": "model",
                        "code": "model_not_supported"
                    }
                }), 400
        else:
            # 使用默认提供商的配置
            api_key = current_api_key
            api_url = current_api_url
        
        # 检查API Key
        if not api_key or api_key.startswith("your-"):
            return jsonify({
                "error": {
                    "message": f"请在配置文件中配置真实的{provider} API Key！",
                    "type": "invalid_request_error",
                    "param": None,
                    "code": None
                }
            }), 400
        
        # 创建OpenAI客户端
        client = OpenAI(
            base_url=api_url,
            api_key=api_key,
        )
        
        # 打印API调用信息
        print(f"调用{provider} API：{api_url}")
        print(f"模型：{model}")
        
        # 流式响应（OpenAI风格）
        if stream:
            # 使用OpenAI SDK的流式调用
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens
            )
            
            # 封装为OpenAI风格的流式响应
            def generate():
                for chunk in response:
                    # 构造OpenAI格式的响应
                    openai_response = {
                        "id": chunk.id,
                        "object": "chat.completion.chunk",
                        "created": chunk.created,
                        "model": chunk.model,
                        "system_fingerprint": None,
                        "conversation_id": conversation_id,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {
                                    "role": "assistant" if chunk.choices[0].delta.content else {},
                                    "content": chunk.choices[0].delta.content or None
                                },
                                "finish_reason": chunk.choices[0].finish_reason
                            }
                        ]
                    }
                    yield f"data: {json.dumps(openai_response)}\n\n"
                    
                    # 如果完成，发送结束信号
                    if chunk.choices[0].finish_reason:
                        yield "data: [DONE]\n\n"
            
            return Response(generate(), mimetype="text/event-stream; charset=utf-8")
        # 非流式响应（OpenAI风格）
        else:
            # 使用OpenAI SDK的非流式调用
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens
            )
            
            # 构造OpenAI格式的响应
            openai_response = {
                "id": response.id,
                "object": "chat.completion",
                "created": response.created,
                "model": response.model,
                "system_fingerprint": None,
                "conversation_id": conversation_id,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response.choices[0].message.content
                        },
                        "finish_reason": response.choices[0].finish_reason
                    }
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            print(f"转换后的OpenAI响应：{openai_response}")
            return jsonify(openai_response)
    except Exception as e:
        print(f"异常：{e}")
        return jsonify({
            "error": {
                "message": f"API调用失败：{str(e)}",
                "type": "internal_error",
                "param": None,
                "code": "internal_server_error"
            }
        }), 500

# 项目启动入口
if __name__ == "__main__":
    # 启动Flask服务，host=0.0.0.0允许局域网访问，debug=True方便开发调试
    app.run(debug=True, host="0.0.0.0", port=5001)