from flask import Flask, request, jsonify, render_template, send_file
import json
import threading
import os
import uuid
from werkzeug.utils import secure_filename
from xhs_nurturing import NurturingManager
from license_manager import LicenseManager
from machine_code import get_machine_code
from pdf_converter import pdf_converter
from file_transfer import file_transfer_manager

app = Flask(__name__, template_folder='templates', static_folder='static')

# 初始化管理器
nurturing_manager = NurturingManager()
license_manager = LicenseManager()
current_device = {"device_id": None}

# ==================== 页面路由 ====================
@app. route("/")
def index():
    """主页仪表板"""
    return render_template("index.html")

@app.route("/device")
def device_page():
    """设备管理页面"""
    return render_template("device.html")

@app.route("/keyword")
def keyword_page():
    """关键词管理页面"""
    return render_template("keyword. html")

@app.route("/param")
def param_page():
    """核心参数页面"""
    return render_template("param.html")

@app.route("/visit")
def visit_page():
    """访问控制页面"""
    return render_template("visit.html")

@app.route("/interact")
def interact_page():
    """互动配置页面"""
    return render_template("interact.html")

@app.route("/status")
def status_page():
    """状态监控页面"""
    return render_template("status.html")

@app.route("/activation")
def activation_page():
    """激活页面"""
    return render_template("activation.html")

# ==================== API 接口 ====================

@app.route("/api/devices", methods=["GET"])
def api_devices():
    """获取已连接设备列表"""
    try:
        devices = nurturing_manager.get_all_devices()
        return jsonify({"success": True, "data": devices})
    except Exception as e:
        return jsonify({"success": False, "error":  str(e)})

@app.route("/api/device/switch", methods=["POST"])
def api_device_switch():
    """切换设备"""
    try: 
        device_id = request.json.get("device_id")
        if not device_id: 
            return jsonify({"success":  False, "error": "设备ID不能为空"})
        
        # 如果有其他设备在运行，先停止
        if current_device["device_id"]:
            nurturing_manager.stop_nurturing(current_device["device_id"])
        
        result = nurturing_manager.device_manager.connect_device(device_id)
        if result: 
            current_device["device_id"] = device_id
            # 初始化新设备配置（如无则使用默认配置）
            config = nurturing_manager.get_device_config(device_id)
            return jsonify({"success": True, "message": f"已切换到设备:  {device_id}"})
        else:
            return jsonify({"success": False, "error":  "设备连接失败"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/device/alias", methods=["POST", "GET"])
def api_device_alias():
    """设置或获取设备别名"""
    try:
        if request.method == "POST":
            # 设置设备别名
            device_id = request.json.get("device_id")
            alias = request.json.get("alias")
            if not device_id:
                return jsonify({"success": False, "error": "设备ID不能为空"})
            
            nurturing_manager.device_manager.set_device_alias(device_id, alias)
            return jsonify({"success": True, "message": f"已为设备 {device_id} 设置别名: {alias}"})
        else:
            # 获取设备别名
            device_id = request.args.get("device_id")
            if not device_id:
                return jsonify({"success": False, "error": "设备ID不能为空"})
            
            alias = nurturing_manager.device_manager.get_device_alias(device_id)
            return jsonify({"success": True, "data": {"device_id": device_id, "alias": alias}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/device/alias/<device_id>", methods=["DELETE"])
def api_remove_device_alias(device_id):
    """移除设备别名"""
    try:
        nurturing_manager.device_manager.remove_device_alias(device_id)
        return jsonify({"success": True, "message": f"已移除设备 {device_id} 的别名"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/device/<device_id>", methods=["DELETE"])
def api_delete_device(device_id):
    """删除设备"""
    try:
        # 检查设备是否离线
        devices = nurturing_manager.get_all_devices()
        device = next((d for d in devices if d['id'] == device_id), None)
        if not device:
            return jsonify({"success": False, "error": "设备不存在"})
        
        if device['status'] == 'online':
            return jsonify({"success": False, "error": "只能删除离线设备"})
        
        # 从配置中删除设备
        nurturing_manager.config_manager.remove_device_config(device_id)
        # 移除设备别名
        nurturing_manager.device_manager.remove_device_alias(device_id)
        
        return jsonify({"success": True, "message": f"设备 {device_id} 已删除"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/config/<device_id>", methods=["GET"])
def api_get_config(device_id):
    """获取设备配置"""
    try:
        config = nurturing_manager.get_device_config(device_id)
        return jsonify({"success":  True, "data": config})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/config/<device_id>", methods=["PUT"])
def api_save_config(device_id):
    """保存设备配置"""
    try:
        config = request.json
        success = nurturing_manager.update_device_config(device_id, config)
        if success:
            return jsonify({"success": True, "message": "配置已保存"})
        else:
            return jsonify({"success": False, "error": "配置更新失败"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/config/keywords/<device_id>", methods=["GET", "PUT"])
def api_keywords(device_id):
    """管理关键词"""
    try:
        if request.method == "GET": 
            config = nurturing_manager.get_device_config(device_id)
            keywords = config.get("keywords", [])
            return jsonify({"success": True, "data": keywords})
        else:
            keywords = request.json.get("keywords", [])
            success = nurturing_manager.update_keywords(device_id, keywords)
            if success:
                return jsonify({"success": True, "message": "关键词已更新"})
            else:
                return jsonify({"success": False, "error": "关键词更新失败"})
    except Exception as e:
        return jsonify({"success": False, "error":  str(e)})

# ==================== 养号控制 ====================

@app.route("/api/yanghao/start", methods=["POST"])
def api_start_yanghao():
    """启动养号"""
    try: 
        device_id = request. json.get("device_id") or current_device["device_id"]
        if not device_id:
            return jsonify({"success": False, "error": "未选择设备"})
        
        success = nurturing_manager.start_nurturing(device_id)
        if success:
            return jsonify({"success": True, "message": "养号已启动"})
        else:
            return jsonify({"success": False, "error": "启动养号失败"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/yanghao/stop", methods=["POST"])
def api_stop_yanghao():
    """停止养号"""
    try: 
        device_id = request.json.get("device_id") or current_device["device_id"]
        if not device_id: 
            return jsonify({"success": False, "error": "未选择设备"})
        
        nurturing_manager.stop_nurturing(device_id)
        return jsonify({"success": True, "message": "已停止养号"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/yanghao/status/<device_id>")
def api_status(device_id):
    """获取养号状态"""
    try:
        status = nurturing_manager.get_nurturing_status(device_id)
        return jsonify({"success": True, "data": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/yanghao/close-xhs/<device_id>")
def api_close_xhs(device_id):
    """关闭小红书"""
    try:
        # 调用NurturingManager中的方法关闭小红书
        device = nurturing_manager.device_manager.get_device(device_id)
        if not device:
            # 尝试连接设备
            if not nurturing_manager.device_manager.connect_device(device_id):
                return jsonify({"success": False, "error": "设备未连接"})
            device = nurturing_manager.device_manager.get_device(device_id)
        
        if device:
            device.app_stop("com.xingin.xhs")
            return jsonify({"success": True, "message": "小红书已关闭"})
        else:
            return jsonify({"success": False, "error": "设备未连接"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/config/default", methods=["GET", "PUT"])
def api_default_config():
    """管理默认配置模板"""
    try:
        if request.method == "GET": 
            default_cfg = nurturing_manager.config_manager.get_default_template()
            return jsonify({"success": True, "data": default_cfg})
        else:
            cfg = request.json
            nurturing_manager.config_manager.set_default_template(cfg)
            return jsonify({"success":  True, "message": "默认模板已更新"})
    except Exception as e:
        return jsonify({"success": False, "error":  str(e)})

# ==================== 激活相关 API ====================

@app.route("/api/activation/verify", methods=["POST"])
def api_verify_activation():
    """验证激活码"""
    try:
        auth_code = request.json.get("auth_code", "")
        if not auth_code:
            return jsonify({"success": False, "error": "激活码不能为空"})
        
        success, message, data = license_manager.verify_activation_code(auth_code)
        if success:
            return jsonify({"success": True, "message": message, "data": data})
        else:
            return jsonify({"success": False, "error": message})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/license/info", methods=["GET"])
def api_get_license_info():
    """获取当前授权信息"""
    try:
        license_info = license_manager.get_license_info()
        machine_code = get_machine_code()
        
        # 获取今日所有设备使用情况
        devices_usage = license_manager.get_all_devices_usage_today()
        
        return jsonify({
            "success": True,
            "data": {
                "license": license_info,
                "machine_code": machine_code,
                "devices_usage": devices_usage
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/device/usage/<device_id>", methods=["GET"])
def api_get_device_usage(device_id):
    """获取设备今日使用情况"""
    try:
        usage = license_manager.get_device_usage_today(device_id)
        return jsonify({"success": True, "data": usage})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/permission/check", methods=["GET"])
def api_check_permission():
    """检查启动权限"""
    try:
        allowed, message = license_manager.check_launch_permission()
        return jsonify({
            "success": True,
            "data": {
                "allowed": allowed,
                "message": message
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ==================== 错误处理 ====================

# ==================== PDF转换 API ====================

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/api/pdf/upload", methods=["POST"])
def api_pdf_upload():
    """上传PDF文件"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "没有文件"})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "没有选择文件"})
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # 生成唯一文件名
            unique_id = str(uuid.uuid4())
            filename = f"{unique_id}_{filename}"
            filepath = os.path.join(pdf_converter.upload_folder, filename)
            file.save(filepath)
            
            return jsonify({
                "success": True, 
                "message": "文件上传成功",
                "data": {
                    "filename": filename,
                    "original_name": file.filename,
                    "filepath": filepath
                }
            })
        else:
            return jsonify({"success": False, "error": "只允许上传PDF文件"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/pdf/convert", methods=["POST"])
def api_pdf_convert():
    """转换PDF为图片"""
    try:
        data = request.json
        filename = data.get('filename')
        dpi = data.get('dpi', 300)
        fmt = data.get('format', 'png')
        add_watermark = data.get('add_watermark', True)
        generate_simple_pdf = data.get('generate_simple_pdf', True)
        start_page = data.get('start_page', 1)
        end_page = data.get('end_page')
        add_header = data.get('add_header', False)
        add_footer = data.get('add_footer', False)
        
        if not filename:
            return jsonify({"success": False, "error": "文件名不能为空"})
        
        filepath = os.path.join(pdf_converter.upload_folder, filename)
        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "文件不存在"})
        
        # 执行转换
        result = pdf_converter.convert_pdf_to_images(
            filepath, 
            dpi=dpi, 
            fmt=fmt, 
            add_watermark=add_watermark,
            generate_simple_pdf=generate_simple_pdf,
            start_page=start_page,
            end_page=end_page,
            add_header=add_header,
            add_footer=add_footer
        )
        
        # 获取相对路径用于前端显示
        images_urls = []
        for img_path in result['images']:
            # 转换为URL路径
            rel_path = os.path.relpath(img_path, 'static')
            images_urls.append(f"/static/{rel_path}")
        
        simple_pdf_url = None
        if result['simple_pdf']:
            rel_path = os.path.relpath(result['simple_pdf'], 'static')
            simple_pdf_url = f"/static/{rel_path}"
        
        return jsonify({
            "success": True,
            "message": "转换完成",
            "data": {
                "images": images_urls,
                "simple_pdf": simple_pdf_url,
                "total_pages": len(result['images'])
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/pdf/download/<path:filename>")
def api_pdf_download(filename):
    """下载转换后的文件"""
    try:
        filepath = os.path.join('static', filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({"success": False, "error": "文件不存在"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/pdf/cleanup", methods=["POST"])
def api_pdf_cleanup():
    """清理旧的PDF转换文件"""
    try:
        pdf_converter.cleanup_old_files(max_age_hours=24)
        return jsonify({"success": True, "message": "清理完成"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ==================== PDF批量处理 API ====================

# PDF路径配置存储文件
PDF_PATHS_CONFIG_FILE = "config/pdf_paths_config.json"

def load_pdf_paths_config():
    """加载PDF路径配置"""
    if os.path.exists(PDF_PATHS_CONFIG_FILE):
        with open(PDF_PATHS_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "source_path": "",
        "output_path": ""
    }

def save_pdf_paths_config(config):
    """保存PDF路径配置"""
    os.makedirs("config", exist_ok=True)
    with open(PDF_PATHS_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

@app.route("/api/pdf/paths/config", methods=["GET"])
def api_get_pdf_paths_config():
    """获取PDF路径配置"""
    try:
        config = load_pdf_paths_config()
        return jsonify({"success": True, "data": config})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/pdf/paths/config", methods=["POST"])
def api_save_pdf_paths_config():
    """保存PDF路径配置"""
    try:
        config = request.json
        save_pdf_paths_config(config)
        return jsonify({"success": True, "message": "配置已保存"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/pdf/batch/upload", methods=["POST"])
def api_pdf_batch_upload():
    """批量上传PDF文件"""
    try:
        if 'files' not in request.files:
            return jsonify({"success": False, "error": "没有文件"})
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({"success": False, "error": "没有选择文件"})
        
        uploaded_files = []
        for file in files:
            if file and file.filename.endswith('.pdf'):
                filename = secure_filename(file.filename)
                unique_id = str(uuid.uuid4())
                saved_filename = f"{unique_id}_{filename}"
                filepath = os.path.join(pdf_converter.upload_folder, saved_filename)
                file.save(filepath)
                
                uploaded_files.append({
                    "original_name": filename,
                    "saved_name": saved_filename,
                    "filepath": filepath,
                    "size": os.path.getsize(filepath)
                })
        
        return jsonify({
            "success": True,
            "message": f"成功上传 {len(uploaded_files)} 个文件",
            "data": {
                "files": uploaded_files,
                "count": len(uploaded_files)
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/pdf/batch/convert", methods=["POST"])
def api_pdf_batch_convert():
    """批量转换PDF文件"""
    try:
        data = request.json
        files = data.get('files', [])
        settings = data.get('settings', {})
        
        if not files:
            return jsonify({"success": False, "error": "没有选择文件"})
        
        results = []
        total_files = len(files)
        
        for index, file_info in enumerate(files):
            try:
                filename = file_info.get('saved_name')
                filepath = os.path.join(pdf_converter.upload_folder, filename)
                
                if not os.path.exists(filepath):
                    results.append({
                        "original_name": file_info.get('original_name'),
                        "success": False,
                        "error": "文件不存在"
                    })
                    continue
                
                # 加载用户配置的图片路径
                config = load_pdf_images_config()
                from pdf_converter import PDFConverter
                converter = PDFConverter(
                    watermark_path=config.get('watermark') or None,
                    header_path=config.get('header') or None,
                    footer_path=config.get('footer') or None
                )
                
                # 执行转换
                result = converter.convert_pdf_to_images(
                    filepath,
                    dpi=settings.get('dpi', 300),
                    fmt=settings.get('format', 'png'),
                    add_watermark=settings.get('add_watermark', True),
                    generate_simple_pdf=settings.get('generate_simple_pdf', True),
                    start_page=settings.get('start_page', 1),
                    end_page=settings.get('end_page'),
                    add_header=settings.get('add_header', False),
                    add_footer=settings.get('add_footer', False)
                )
                
                # 获取相对路径
                images_urls = []
                for img_path in result['images']:
                    rel_path = os.path.relpath(img_path, 'static')
                    images_urls.append(f"/static/{rel_path}")
                
                simple_pdf_url = None
                if result['simple_pdf']:
                    rel_path = os.path.relpath(result['simple_pdf'], 'static')
                    simple_pdf_url = f"/static/{rel_path}"
                
                results.append({
                    "original_name": file_info.get('original_name'),
                    "saved_name": filename,
                    "success": True,
                    "images": images_urls,
                    "simple_pdf": simple_pdf_url,
                    "total_pages": len(result['images']),
                    "progress": {
                        "current": index + 1,
                        "total": total_files
                    }
                })
                
            except Exception as e:
                results.append({
                    "original_name": file_info.get('original_name'),
                    "success": False,
                    "error": str(e)
                })
        
        return jsonify({
            "success": True,
            "message": "批量转换完成",
            "data": {
                "results": results,
                "total": total_files,
                "success_count": sum(1 for r in results if r['success']),
                "failed_count": sum(1 for r in results if not r['success'])
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ==================== PDF图片配置 API ====================

# 用户图片配置存储文件
PDF_IMAGES_CONFIG_FILE = "config/pdf_images_config.json"

def load_pdf_images_config():
    """加载PDF图片配置"""
    if os.path.exists(PDF_IMAGES_CONFIG_FILE):
        with open(PDF_IMAGES_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "watermark": None,
        "header": None,
        "footer": None
    }

def save_pdf_images_config(config):
    """保存PDF图片配置"""
    os.makedirs("config", exist_ok=True)
    with open(PDF_IMAGES_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

@app.route("/api/pdf/images/config", methods=["GET"])
def api_get_pdf_images_config():
    """获取PDF图片配置"""
    try:
        config = load_pdf_images_config()
        return jsonify({"success": True, "data": config})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/pdf/images/config", methods=["POST"])
def api_save_pdf_images_config():
    """保存PDF图片配置"""
    try:
        config = request.json
        save_pdf_images_config(config)
        return jsonify({"success": True, "message": "配置已保存"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/pdf/images/upload", methods=["POST"])
def api_upload_pdf_image():
    """上传PDF图片（水印/页眉/页脚）"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "没有文件"})
        
        file = request.files['file']
        image_type = request.form.get('type', 'watermark')  # watermark, header, footer
        
        if file.filename == '':
            return jsonify({"success": False, "error": "没有选择文件"})
        
        # 检查文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
        if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            return jsonify({"success": False, "error": "只允许上传图片文件(PNG, JPG, JPEG, GIF, BMP)"})
        
        # 保存文件
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}_{filename}"
        
        # 按类型分类存储
        upload_dir = os.path.join('static', 'pdf_images', image_type)
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # 更新配置
        config = load_pdf_images_config()
        config[image_type] = f"/static/pdf_images/{image_type}/{filename}"
        save_pdf_images_config(config)
        
        return jsonify({
            "success": True,
            "message": "图片上传成功",
            "data": {
                "type": image_type,
                "path": config[image_type],
                "filename": filename
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/pdf/preview", methods=["POST"])
def api_pdf_preview():
    """生成PDF预览（第一页带水印/页眉/页脚效果）"""
    try:
        data = request.json
        filename = data.get('filename')
        add_watermark = data.get('add_watermark', True)
        add_header = data.get('add_header', False)
        add_footer = data.get('add_footer', False)
        
        if not filename:
            return jsonify({"success": False, "error": "文件名不能为空"})
        
        filepath = os.path.join(pdf_converter.upload_folder, filename)
        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "文件不存在"})
        
        # 加载用户配置的图片路径
        config = load_pdf_images_config()
        
        # 创建临时转换器，使用用户配置的图片
        from pdf_converter import PDFConverter
        preview_converter = PDFConverter(
            watermark_path=config.get('watermark') or None,
            header_path=config.get('header') or None,
            footer_path=config.get('footer') or None
        )
        
        # 只转换第一页作为预览
        result = preview_converter.convert_pdf_to_images(
            filepath,
            dpi=150,  # 预览用较低DPI，加快速度
            fmt='png',
            add_watermark=add_watermark,
            generate_simple_pdf=False,
            start_page=1,
            end_page=1,
            add_header=add_header,
            add_footer=add_footer
        )
        
        if result['images']:
            # 返回预览图片URL
            rel_path = os.path.relpath(result['images'][0], 'static')
            preview_url = f"/static/{rel_path}"
            return jsonify({
                "success": True,
                "data": {
                    "preview_url": preview_url
                }
            })
        else:
            return jsonify({"success": False, "error": "预览生成失败"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ==================== 文件传输 API ====================

# 文件传输配置存储文件
FILE_TRANSFER_CONFIG_FILE = "config/file_transfer_config.json"

def load_file_transfer_config():
    """加载文件传输配置"""
    if os.path.exists(FILE_TRANSFER_CONFIG_FILE):
        with open(FILE_TRANSFER_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "computer_dir": "/Users/wenyangzang/Desktop/1/传输专用目录",
        "phone_dir": "/sdcard/Download/传输专用目录"
    }

def save_file_transfer_config(config):
    """保存文件传输配置"""
    os.makedirs("config", exist_ok=True)
    with open(FILE_TRANSFER_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

@app.route("/api/file-transfer/config", methods=["GET"])
def api_get_file_transfer_config():
    """获取文件传输配置"""
    try:
        config = load_file_transfer_config()
        return jsonify({"success": True, "data": config})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/file-transfer/config", methods=["POST"])
def api_save_file_transfer_config():
    """保存文件传输配置"""
    try:
        config = request.json
        save_file_transfer_config(config)
        return jsonify({"success": True, "message": "配置已保存"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/file-transfer/clear-phone", methods=["POST"])
def api_clear_phone_directory():
    """清理手机传输目录"""
    try:
        data = request.json
        phone_dir = data.get('phone_dir')
        device_id = data.get('device_id')
        
        if not phone_dir:
            return jsonify({"success": False, "error": "手机目录路径不能为空"})
        
        if not device_id:
            return jsonify({"success": False, "error": "请先选择目标设备"})
        
        # 创建设备特定的传输管理器
        from file_transfer import FileTransferManager
        ft_manager = FileTransferManager(device_id=device_id)
        
        result = ft_manager.clear_phone_directory(phone_dir)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/file-transfer/transfer", methods=["POST"])
def api_transfer_files():
    """传输文件到手机（支持文件上传）"""
    try:
        phone_dir = request.form.get('phone_dir')
        device_id = request.form.get('device_id')
        
        if not phone_dir:
            return jsonify({"success": False, "error": "手机目录路径不能为空"})
        
        if not device_id:
            return jsonify({"success": False, "error": "请先选择目标设备"})
        
        # 检查是否有上传的文件
        if 'files' not in request.files:
            return jsonify({"success": False, "error": "没有选择文件"})
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({"success": False, "error": "没有选择文件"})
        
        # 创建临时目录存储上传的文件
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix='file_transfer_')
        
        try:
            # 保存上传的文件到临时目录
            file_count = 0
            for file in files:
                if file.filename:
                    # 保持相对路径结构
                    rel_path = file.filename
                    file_path = os.path.join(temp_dir, rel_path)
                    
                    # 确保父目录存在
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path)
                    file_count += 1
            
            # 创建设备特定的传输管理器
            from file_transfer import FileTransferManager
            ft_manager = FileTransferManager(device_id=device_id)
            
            # 传输文件到手机
            result = ft_manager.transfer_files_to_phone(temp_dir, phone_dir)
            result['file_count'] = file_count
            
            return jsonify(result)
            
        finally:
            # 清理临时目录
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/file-transfer/clear-computer", methods=["POST"])
def api_clear_computer_directory():
    """清空电脑传输目录（前端处理，后端只需返回成功）"""
    try:
        # 由于文件是通过上传方式传输，电脑端不需要清理实际目录
        # 浏览器会自动释放内存中的文件引用
        return jsonify({"success": True, "message": "已清除选择的文件"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/file-transfer/full-transfer", methods=["POST"])
def api_full_transfer():
    """执行完整的传输流程"""
    try:
        phone_dir = request.form.get('phone_dir')
        device_id = request.form.get('device_id')
        
        if not phone_dir:
            return jsonify({"success": False, "error": "手机目录路径不能为空"})
        
        if not device_id:
            return jsonify({"success": False, "error": "请先选择目标设备"})
        
        # 检查是否有上传的文件
        if 'files' not in request.files:
            return jsonify({"success": False, "error": "没有选择文件"})
        
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({"success": False, "error": "没有选择文件"})
        
        # 创建设备特定的传输管理器
        from file_transfer import FileTransferManager
        ft_manager = FileTransferManager(device_id=device_id)
        
        results = {
            "success": True,
            "steps": {}
        }
        
        # 步骤1: 清理手机传输目录
        step1_result = ft_manager.clear_phone_directory(phone_dir)
        results["steps"]["clear_phone"] = step1_result
        
        if not step1_result["success"]:
            results["success"] = False
            results["message"] = "清理手机目录失败，流程终止"
            return jsonify(results)
        
        # 步骤2: 创建临时目录并保存上传的文件
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp(prefix='file_transfer_')
        
        try:
            file_count = 0
            for file in files:
                if file.filename:
                    rel_path = file.filename
                    file_path = os.path.join(temp_dir, rel_path)
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    file.save(file_path)
                    file_count += 1
            
            # 传输文件到手机
            step2_result = ft_manager.transfer_files_to_phone(temp_dir, phone_dir)
            step2_result['file_count'] = file_count
            results["steps"]["transfer"] = step2_result
            
            if not step2_result["success"]:
                results["success"] = False
                results["message"] = "文件传输失败"
                return jsonify(results)
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        # 步骤3: 清空电脑目录（前端已处理）
        results["steps"]["clear_computer"] = {
            "success": True,
            "message": "已清除选择的文件"
        }
        
        results["message"] = "文件传输流程执行成功"
        return jsonify(results)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "请求不存在"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"success": False, "error": "服务器错误"}), 500

if __name__ == '__main__':
    # 确保配置文件存在
    os.makedirs("config", exist_ok=True)
    if not os.path.exists("config/config.json"):
        with open("config/config.json", "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2, ensure_ascii=False)
    
    app.run(host="0.0.0.0", port=5002, debug=True, threaded=True)