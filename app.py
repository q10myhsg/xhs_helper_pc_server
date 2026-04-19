from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
import json
import threading
import os
import uuid
from werkzeug.utils import secure_filename
from xhs_nurturing import NurturingManager
from license_manager import get_license_manager
from machine_code import get_machine_code
from pdf_converter import PDFConverter
from file_transfer import file_transfer_manager

# 初始化PDF转换器
pdf_converter = PDFConverter()

app = Flask(__name__, template_folder='templates', static_folder='static')

# 初始化管理器
nurturing_manager = NurturingManager()
license_manager = get_license_manager()
current_device = {"device_id": None}

# ==================== 页面路由 ====================
@app.route("/")
def index():
    """主页仪表板"""
    return render_template("dashboard.html", active_page="dashboard")

@app.route("/dashboard")
def dashboard_page():
    """仪表板页面"""
    return render_template("dashboard.html", active_page="dashboard")

@app.route("/device")
def device_page():
    """设备管理页面"""
    return render_template("device.html", active_page="device")

@app.route("/keyword")
def keyword_page():
    """关键词管理页面"""
    return render_template("keyword.html", active_page="keyword")

@app.route("/nurturing")
def nurturing_page():
    """养号配置页面"""
    return render_template("nurturing.html", active_page="nurturing")

@app.route("/config")
def config_page():
    """参数配置页面"""
    return render_template("config.html", active_page="config")

@app.route("/pdf")
def pdf_page():
    """PDF转图片页面"""
    return render_template("pdf.html", active_page="pdf")

@app.route("/file-transfer")
def file_transfer_page():
    """文件传输页面"""
    return render_template("file-transfer.html", active_page="file-transfer")

@app.route("/activation")
def activation_page():
    """激活页面"""
    return render_template("activation.html", active_page="activation")

@app.route("/cover-generator")
def cover_generator_page():
    """小红书封面生成器页面"""
    return render_template("cover_generator.html", active_page="cover-generator")



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
    """保存设备配置（部分更新）"""
    try:
        config = request.json

        # 先获取现有配置
        existing_config = nurturing_manager.get_device_config(device_id)

        # 合并配置：现有配置 + 新配置（新配置覆盖现有配置）
        merged_config = {**existing_config, **config}

        success = nurturing_manager.update_device_config(device_id, merged_config)
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
            keywords = nurturing_manager.config_manager.get_keywords(device_id)
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
    import logging
    logger = logging.getLogger(__name__)
    try: 
        device_id = request.json.get("device_id") or current_device["device_id"]
        if not device_id:
            logger.error("启动养号失败: 未选择设备")
            return jsonify({"success": False, "error": "未选择设备"})
        
        logger.info(f"尝试启动设备 {device_id} 的养号")
        
        # 获取设备配置
        config = nurturing_manager.config_manager.get_device_config(device_id)
        
        # 检查是否可以启动（使用新的授权管理）
        duration_minutes = config.get("duration_minutes", 20)
        can_start, msg, actual_duration = license_manager.check_can_start(device_id, duration_minutes, is_create=False)
        if not can_start:
            logger.error(f"启动检查失败: {msg}")
            return jsonify({"success": False, "error": f"启动失败: {msg}"})
        
        # 如果有提示信息，记录日志
        if msg:
            logger.info(msg)
        
        # 连接设备
        if not nurturing_manager.device_manager.connect_device(device_id):
            logger.error(f"无法连接设备 {device_id}")
            return jsonify({"success": False, "error": f"启动失败: 无法连接设备 {device_id}"})
        
        # 验证配置
        if not nurturing_manager.config_manager.validate_config(config):
            logger.error(f"设备 {device_id} 的配置无效")
            return jsonify({"success": False, "error": f"启动失败: 设备配置无效"})
        
        # 从数据库获取关键词
        keywords = nurturing_manager.config_manager.get_keywords(device_id)
        config["keywords"] = keywords
        
        # 验证关键词
        from xhs_nurturing.utils import validate_keywords
        if not validate_keywords(config.get("keywords", [])):
            logger.error(f"设备 {device_id} 的关键词配置无效")
            return jsonify({"success": False, "error": f"启动失败: 关键词配置无效"})
        
        # 启动养号
        success = nurturing_manager.start_nurturing(device_id)
        if success:
            logger.info(f"设备 {device_id} 养号启动成功")
            return jsonify({"success": True, "message": "养号已启动"})
        else:
            logger.error(f"设备 {device_id} 养号启动失败")
            return jsonify({"success": False, "error": "启动养号失败，请查看后台日志"})
    except Exception as e:
        logger.error(f"启动养号异常: {e}", exc_info=True)
        return jsonify({"success": False, "error": f"启动失败: {str(e)}"})

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

@app.route("/api/yanghao/close-xhs/<device_id>", methods=["POST"])
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
    """验证激活码（兼容旧接口）"""
    try:
        auth_code = request.json.get("auth_code", "")
        if not auth_code:
            return jsonify({"success": False, "error": "激活码不能为空"})
        
        success, message = license_manager.activate_license(auth_code, license_manager.machine_code)
        if success:
            stats = license_manager.get_usage_stats()
            return jsonify({"success": True, "message": message, "data": stats})
        else:
            return jsonify({"success": False, "error": message})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/license/activate", methods=["POST"])
def api_license_activate():
    """激活授权（新接口）"""
    try:
        activation_code = request.json.get("activation_code")
        machine_code = request.json.get("machine_code") or license_manager.machine_code
        
        if not activation_code:
            return jsonify({"success": False, "error": "激活码不能为空"})
        
        success, message = license_manager.activate_license(activation_code, machine_code)
        if success:
            stats = license_manager.get_usage_stats()
            return jsonify({"success": True, "message": message, "data": stats})
        else:
            return jsonify({"success": False, "error": message})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/license/refresh", methods=["POST"])
def api_license_refresh():
    """刷新授权"""
    try:
        success, message = license_manager.refresh_license()
        stats = license_manager.get_usage_stats()
        return jsonify({"success": success, "message": message, "data": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/license/info", methods=["GET"])
def api_get_license_info():
    """获取当前授权信息"""
    try:
        stats = license_manager.get_usage_stats()
        return jsonify({"success": True, "data": stats})
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
        # 使用新的授权检查逻辑
        license = license_manager.get_current_license()
        if license.get("package_type") == "free":
            return jsonify({
                "success": True,
                "data": {
                    "allowed": False,
                    "message": "未激活，请先输入激活码"
                }
            })
        # 检查是否过期
        expire_date = license.get("expire_date")
        if expire_date:
            try:
                from datetime import datetime
                expire_dt = datetime.strptime(expire_date, "%Y-%m-%d")
                if datetime.now() > expire_dt:
                    return jsonify({
                        "success": True,
                        "data": {
                            "allowed": False,
                            "message": "授权已过期"
                        }
                    })
            except:
                pass
        return jsonify({
            "success": True,
            "data": {
                "allowed": True,
                "message": "权限检查通过"
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
        
        # 水印相关参数
        watermark_page_range = data.get('watermark_page_range', 'even')
        watermark_position = data.get('watermark_position', None)
        header_position = data.get('header_position', None)
        footer_position = data.get('footer_position', None)
        
        # 图片边框和背景色参数
        border_width = data.get('border_width', 0)
        border_color = data.get('border_color', '#000000')
        background_color = data.get('background_color', '#ffffff')
        
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
            add_footer=add_footer,
            watermark_page_range=watermark_page_range,
            watermark_position=watermark_position,
            header_position=header_position,
            footer_position=footer_position,
            border_width=border_width,
            border_color=border_color,
            background_color=background_color
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

@app.route("/api/pdf/preview", methods=["POST"])
def api_pdf_preview():
    """预览PDF转换效果（仅转换第一页）"""
    try:
        data = request.json
        filename = data.get('filename')
        dpi = data.get('dpi', 200)  # 预览使用较低DPI加快速度
        fmt = data.get('format', 'png')
        add_watermark = data.get('add_watermark', True)
        add_header = data.get('add_header', False)
        add_footer = data.get('add_footer', False)
        
        # 水印相关参数
        watermark_page_range = data.get('watermark_page_range', 'even')
        watermark_position = data.get('watermark_position', None)
        header_position = data.get('header_position', None)
        footer_position = data.get('footer_position', None)
        
        # 图片边框和背景色参数
        border_width = data.get('border_width', 0)
        border_color = data.get('border_color', '#000000')
        background_color = data.get('background_color', '#ffffff')
        
        if not filename:
            return jsonify({"success": False, "error": "文件名不能为空"})
        
        filepath = os.path.join(pdf_converter.upload_folder, filename)
        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "文件不存在"})
        
        # 执行转换（仅第一页）
        result = pdf_converter.convert_pdf_to_images(
            filepath, 
            dpi=dpi, 
            fmt=fmt, 
            add_watermark=add_watermark,
            generate_simple_pdf=False,  # 预览不生成simple PDF
            start_page=1,
            end_page=1,  # 仅第一页
            add_header=add_header,
            add_footer=add_footer,
            watermark_page_range=watermark_page_range,
            watermark_position=watermark_position,
            header_position=header_position,
            footer_position=footer_position,
            border_width=border_width,
            border_color=border_color,
            background_color=background_color
        )
        
        # 获取相对路径用于前端显示
        images_urls = []
        for img_path in result['images']:
            rel_path = os.path.relpath(img_path, 'static')
            images_urls.append(f"/static/{rel_path}")
        
        return jsonify({
            "success": True,
            "message": "预览生成完成",
            "data": {
                "images": images_urls,
                "total_pages": len(result['images'])
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/pdf/preview-multi", methods=["POST"])
def api_pdf_preview_multi():
    """预览PDF转换效果（多页预览，最多5页）"""
    try:
        data = request.json
        filename = data.get('filename')
        dpi = data.get('dpi', 150)  # 预览使用较低DPI加快速度
        fmt = data.get('format', 'png')
        add_watermark = data.get('add_watermark', True)
        add_header = data.get('add_header', False)
        add_footer = data.get('add_footer', False)
        max_pages = data.get('max_pages', 5)  # 最多预览页数
        
        # 水印相关参数
        watermark_page_range = data.get('watermark_page_range', 'even')
        watermark_position = data.get('watermark_position', None)
        header_position = data.get('header_position', None)
        footer_position = data.get('footer_position', None)
        
        # 图片边框和背景色参数
        border_width = data.get('border_width', 0)
        border_color = data.get('border_color', '#000000')
        background_color = data.get('background_color', '#ffffff')
        
        if not filename:
            return jsonify({"success": False, "error": "文件名不能为空"})
        
        filepath = os.path.join(pdf_converter.upload_folder, filename)
        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "文件不存在"})
        
        # 获取PDF总页数
        import fitz
        doc = fitz.open(filepath)
        total_pages = len(doc)
        doc.close()
        
        # 计算要预览的页数
        preview_pages = min(max_pages, total_pages)
        
        # 执行转换（多页）
        result = pdf_converter.convert_pdf_to_images(
            filepath, 
            dpi=dpi, 
            fmt=fmt, 
            add_watermark=add_watermark,
            generate_simple_pdf=False,  # 预览不生成simple PDF
            start_page=1,
            end_page=preview_pages,  # 预览多页
            add_header=add_header,
            add_footer=add_footer,
            watermark_page_range=watermark_page_range,
            watermark_position=watermark_position,
            header_position=header_position,
            footer_position=footer_position,
            border_width=border_width,
            border_color=border_color,
            background_color=background_color
        )
        
        # 获取相对路径用于前端显示
        images_urls = []
        for img_path in result['images']:
            rel_path = os.path.relpath(img_path, 'static')
            images_urls.append(f"/static/{rel_path}")
        
        return jsonify({
            "success": True,
            "message": "预览生成完成",
            "data": {
                "images": images_urls,
                "total_pages": total_pages,
                "preview_pages": preview_pages
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
        base_dir = data.get('base_dir', '')

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
                    footer_path=config.get('footer') or None,
                    watermark_scale=settings.get('watermark_scale', 100)
                )

                # 执行转换 - 输出到工作区目录
                target_dir = file_info.get('target_dir', base_dir)
                if not target_dir:
                    target_dir = os.path.expanduser("~/Downloads/xhs_helper_workspace")
                output_dir = os.path.join(target_dir, 'output_images', os.path.splitext(file_info.get('original_name', ''))[0])
                result = converter.convert_pdf_to_images(
                    filepath,
                    dpi=settings.get('dpi', 300),
                    fmt=settings.get('format', 'png'),
                    add_watermark=settings.get('add_watermark', True),
                    generate_simple_pdf=settings.get('generate_simple_pdf', True),
                    start_page=settings.get('start_page', 1),
                    end_page=settings.get('end_page'),
                    add_header=settings.get('add_header', False),
                    add_footer=settings.get('add_footer', False),
                    watermark_page_range=settings.get('watermark_page_range', 'even'),
                    watermark_position=settings.get('watermark_position'),
                    header_position=settings.get('header_position'),
                    footer_position=settings.get('footer_position'),
                    output_dir=output_dir,
                    border_width=settings.get('border_width', 0),
                    border_color=settings.get('border_color', '#000000'),
                    background_color=settings.get('background_color', '#ffffff'),
                    add_random_icon=settings.get('add_random_icon', False),
                    icon_size=settings.get('icon_size')
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


@app.route("/api/pdf/batch/upload-to-dir", methods=["POST"])
def api_pdf_batch_upload_to_dir():
    """批量上传PDF文件到服务器uploads目录，记录目标目录信息用于后续转换"""
    try:
        base_dir = request.form.get('base_dir', '')
        relative_paths = request.form.getlist('relative_paths')

        # 如果未指定工作区，使用默认工作区
        if not base_dir:
            base_dir = os.path.expanduser("~/Downloads/xhs_helper_workspace")

        if 'files' not in request.files:
            return jsonify({"success": False, "error": "没有文件"})

        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            return jsonify({"success": False, "error": "没有选择文件"})

        uploaded_files = []

        for index, file in enumerate(files):
            if file and file.filename.endswith('.pdf'):
                # 获取相对路径
                relative_path = relative_paths[index] if index < len(relative_paths) else file.filename
                filename = os.path.basename(relative_path)

                # 生成唯一文件名，保存到服务器uploads目录
                unique_id = str(uuid.uuid4())
                saved_filename = f"{unique_id}_{filename}"
                filepath = os.path.join(pdf_converter.upload_folder, saved_filename)

                # 保存文件到服务器uploads目录
                file.save(filepath)

                uploaded_files.append({
                    "original_name": filename,
                    "saved_name": saved_filename,
                    "saved_path": filepath,
                    "target_dir": base_dir,  # 用户指定的目标目录（用于输出）
                    "relative_path": relative_path
                })

        return jsonify({
            "success": True,
            "message": f"成功上传 {len(uploaded_files)} 个文件",
            "data": {
                "files": uploaded_files,
                "base_dir": base_dir
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
@app.route("/api/pdf/batch/convert-local", methods=["POST"])
def api_pdf_batch_convert_local():
    """批量转换本地PDF文件（不经过上传，直接读取本地路径）"""
    try:
        data = request.json
        files = data.get('files', [])
        settings = data.get('settings', {})
        base_dir = data.get('base_dir', '')
        if not files:
            return jsonify({"success": False, "error": "没有选择文件"})

        # 如果未指定工作区，使用默认工作区
        if not base_dir:
            base_dir = os.path.expanduser("~/Downloads/xhs_helper_workspace")

        # 验证基础目录是否存在
        if not os.path.exists(base_dir):
            return jsonify({"success": False, "error": f"工作区不存在: {base_dir}"})

        # 列出工作区中的PDF文件，帮助调试
        print(f"[PDF转换] 工作区: {base_dir}")
        workspace_files = []
        if os.path.exists(base_dir):
            for f in os.listdir(base_dir):
                if f.lower().endswith('.pdf'):
                    workspace_files.append(f)
            print(f"[PDF转换] 工作区中的PDF文件: {workspace_files}")

        results = []
        total_files = len(files)

        # 加载用户配置的图片路径
        config = load_pdf_images_config()
        from pdf_converter import PDFConverter
        converter = PDFConverter(
            watermark_path=config.get('watermark') or None,
            header_path=config.get('header') or None,
            footer_path=config.get('footer') or None,
            watermark_scale=settings.get('watermark_scale', 100)
        )

        for index, file_info in enumerate(files):
            try:
                # 从文件信息中获取路径
                relative_path = file_info.get('relative_path', '')
                folder_path = file_info.get('folder_path', '')
                original_name = file_info.get('original_name', '')

                print(f"[PDF转换] 处理文件: {original_name}")
                print(f"[PDF转换]   - relative_path: {relative_path}")
                print(f"[PDF转换]   - folder_path: {folder_path}")

                filepath = None
                tried_paths = []

                # 方式1: 直接在base_dir中查找文件名匹配的PDF文件
                # 因为浏览器不会透露真实路径，我们直接在工作区中查找匹配的文件名
                if workspace_files:
                    # 精确匹配文件名
                    if original_name in workspace_files:
                        test_path = os.path.join(base_dir, original_name)
                        tried_paths.append(test_path)
                        if os.path.exists(test_path):
                            filepath = test_path
                            print(f"[PDF转换]   ✓ 方式1成功: {filepath}")

                # 方式2: base_dir + filename（简单拼接）
                if filepath is None:
                    test_path = os.path.join(base_dir, original_name)
                    tried_paths.append(test_path)
                    if os.path.exists(test_path):
                        filepath = test_path
                        print(f"[PDF转换]   ✓ 方式2成功: {filepath}")

                # 方式3: 如果有relative_path，尝试去掉前面的路径部分，只保留文件名
                if filepath is None and relative_path and '/' in relative_path:
                    filename_only = relative_path.split('/')[-1]
                    test_path = os.path.join(base_dir, filename_only)
                    tried_paths.append(test_path)
                    if os.path.exists(test_path):
                        filepath = test_path
                        print(f"[PDF转换]   ✓ 方式3成功: {filepath}")

                # 方式4: 扫描工作区，找文件名相似的文件
                if filepath is None:
                    for f in workspace_files:
                        if f.lower() == original_name.lower():
                            test_path = os.path.join(base_dir, f)
                            tried_paths.append(test_path)
                            if os.path.exists(test_path):
                                filepath = test_path
                                print(f"[PDF转换]   ✓ 方式4成功（大小写不敏感）: {filepath}")
                                break

                # 方式5: 尝试从base_dir的父目录查找（用户可能输入了图片目录而不是PDF目录）
                if filepath is None:
                    parent_dir = os.path.dirname(base_dir)
                    if parent_dir != base_dir:  # 确保不是根目录
                        print(f"[PDF转换]   尝试从父目录查找: {parent_dir}")
                        parent_files = []
                        if os.path.exists(parent_dir):
                            for f in os.listdir(parent_dir):
                                if f.lower().endswith('.pdf'):
                                    parent_files.append(f)
                            print(f"[PDF转换]   父目录中的PDF文件: {parent_files}")
                            
                            # 查找匹配的文件
                            for f in parent_files:
                                if f.lower() == original_name.lower():
                                    test_path = os.path.join(parent_dir, f)
                                    tried_paths.append(test_path)
                                    if os.path.exists(test_path):
                                        filepath = test_path
                                        print(f"[PDF转换]   ✓ 方式5成功（从父目录）: {filepath}")
                                        base_dir = parent_dir  # 更新base_dir用于输出
                                        break

                if filepath is None or not os.path.exists(filepath):
                    print(f"[PDF转换]   ✗ 未找到文件，尝试过的路径: {tried_paths}")
                    results.append({
                        "original_name": original_name,
                        "success": False,
                        "error": f"找不到文件，请确认文件在工作区中: {base_dir}\n工作区中的PDF文件: {', '.join(workspace_files[:5])}{'...' if len(workspace_files) > 5 else ''}"
                    })
                    continue

                # 执行转换 - 输出到工作区目录
                output_dir = os.path.join(base_dir, 'output_images', os.path.splitext(original_name)[0])
                
                # 处理页码范围
                start_page = settings.get('start_page', 1)
                end_page = settings.get('end_page')
                print(f"[PDF转换] 页码范围: {start_page} - {end_page}")
                
                result = converter.convert_pdf_to_images(
                    filepath,
                    dpi=settings.get('dpi', 300),
                    fmt=settings.get('format', 'png'),
                    add_watermark=settings.get('add_watermark', True),
                    generate_simple_pdf=settings.get('generate_simple_pdf', True),
                    start_page=start_page,
                    end_page=end_page,
                    add_header=settings.get('add_header', False),
                    add_footer=settings.get('add_footer', False),
                    watermark_page_range=settings.get('watermark_page_range', 'even'),
                    watermark_position=settings.get('watermark_position'),
                    header_position=settings.get('header_position'),
                    footer_position=settings.get('footer_position'),
                    output_dir=output_dir,
                    border_width=settings.get('border_width', 0),
                    border_color=settings.get('border_color', '#000000'),
                    background_color=settings.get('background_color', '#ffffff'),
                    add_random_icon=settings.get('add_random_icon', False),
                    icon_size=settings.get('icon_size')
                )

                # 将本地路径转换为URL
                import time
                images_urls = [f"{local_path_to_url(img_path)}?t={int(time.time())}" for img_path in result['images']]
                simple_pdf_url = f"{local_path_to_url(result['simple_pdf'])}?t={int(time.time())}"
                
                results.append({
                    "original_name": original_name,
                    "success": True,
                    "images": images_urls,
                    "simple_pdf": simple_pdf_url,
                    "output_dir": result['output_dir'],
                    "total_pages": len(result['images']),
                    "progress": {
                        "current": index + 1,
                        "total": total_files
                    }
                })

            except Exception as e:
                results.append({
                    "original_name": file_info.get('original_name', 'unknown'),
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

@app.route("/api/pdf/images/delete", methods=["POST"])
def api_delete_pdf_image():
    """删除PDF图片（水印/页眉/页脚）"""
    try:
        data = request.json
        image_type = data.get('type')
        
        if not image_type or image_type not in ['watermark', 'header', 'footer']:
            return jsonify({"success": False, "error": "无效的图片类型"})
        
        # 加载当前配置
        config = load_pdf_images_config()
        image_path = config.get(image_type)
        
        # 如果配置中有图片路径，删除实际文件
        if image_path:
            # 将URL路径转换为文件系统路径
            if image_path.startswith('/static/'):
                # 移除开头的/，转换为相对路径
                relative_path = image_path[1:]  # 去掉开头的/
                full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)
                
                # 删除文件（如果存在）
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                    except Exception as e:
                        print(f"删除文件失败: {full_path}, 错误: {e}")
        
        # 更新配置，移除该类型的图片
        config[image_type] = None
        save_pdf_images_config(config)
        
        return jsonify({
            "success": True,
            "message": f"{image_type} 图片已删除"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/pdf/clear-output-dir", methods=["POST"])
def api_clear_output_directory():
    """清空PDF输出目录"""
    try:
        data = request.json
        output_dir = data.get('output_dir')
        
        if not output_dir:
            return jsonify({"success": False, "error": "输出目录路径不能为空"})
        
        # 安全检查：确保目录在允许的范围内
        # 只允许删除 output_images 目录下的内容
        if 'output_images' not in output_dir:
            return jsonify({"success": False, "error": "只能清空 output_images 目录下的文件夹"})
        
        # 检查目录是否存在
        if not os.path.exists(output_dir):
            return jsonify({"success": False, "error": f"目录不存在: {output_dir}"})
        
        # 确保是目录而不是文件
        if not os.path.isdir(output_dir):
            return jsonify({"success": False, "error": "指定的路径不是目录"})
        
        # 清空目录中的所有文件和子目录
        deleted_count = 0
        for item in os.listdir(output_dir):
            item_path = os.path.join(output_dir, item)
            try:
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    deleted_count += 1
                elif os.path.isdir(item_path):
                    import shutil
                    shutil.rmtree(item_path)
                    deleted_count += 1
            except Exception as e:
                print(f"删除失败 {item_path}: {e}")
        
        return jsonify({
            "success": True,
            "message": f"目录已清空，共删除 {deleted_count} 个项目",
            "deleted_count": deleted_count
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/check-directory", methods=["POST"])
def api_check_directory():
    """检查目录是否存在"""
    try:
        data = request.json
        directory = data.get('directory')
        
        if not directory:
            return jsonify({"success": False, "error": "目录路径不能为空"})
        
        # 检查目录是否存在
        exists = os.path.exists(directory) and os.path.isdir(directory)
        
        return jsonify({
            "success": True,
            "exists": exists,
            "message": "目录存在" if exists else "目录不存在"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/pdf/batch/convert-full-path", methods=["POST"])
def api_pdf_batch_convert_full_path():
    """批量转换PDF文件（使用完整路径）"""
    try:
        data = request.json
        file_paths = data.get('file_paths', [])  # 完整文件路径列表
        settings = data.get('settings', {})
        
        if not file_paths:
            return jsonify({"success": False, "error": "没有选择文件"})
        
        results = []
        total_files = len(file_paths)
        
        # 加载用户配置的图片路径
        config = load_pdf_images_config()
        from pdf_converter import PDFConverter
        converter = PDFConverter(
            watermark_path=config.get('watermark') or None,
            header_path=config.get('header') or None,
            footer_path=config.get('footer') or None,
            watermark_scale=settings.get('watermark_scale', 100)
        )
        
        for index, file_path in enumerate(file_paths):
            try:
                if not os.path.exists(file_path):
                    results.append({
                        "file_path": file_path,
                        "original_name": os.path.basename(file_path),
                        "success": False,
                        "error": "文件不存在"
                    })
                    continue
                
                # 确定输出目录：在PDF所在目录下创建output文件夹
                pdf_dir = os.path.dirname(file_path)
                pdf_name = os.path.splitext(os.path.basename(file_path))[0]
                
                # 输出目录：优先使用用户指定的，否则在PDF所在目录创建output
                output_base_dir = settings.get('output_dir')
                if output_base_dir and os.path.exists(output_base_dir):
                    output_dir = os.path.join(output_base_dir, pdf_name)
                else:
                    output_dir = os.path.join(pdf_dir, 'output', pdf_name)
                
                print(f"[PDF转换] 处理文件: {file_path}")
                print(f"[PDF转换] 输出目录: {output_dir}")
                
                # 处理页码范围
                start_page = settings.get('start_page', 1)
                end_page = settings.get('end_page')
                print(f"[PDF转换] 页码范围: {start_page} - {end_page}")
                
                result = converter.convert_pdf_to_images(
                    file_path,
                    dpi=settings.get('dpi', 300),
                    fmt=settings.get('format', 'png'),
                    add_watermark=settings.get('add_watermark', True),
                    generate_simple_pdf=settings.get('generate_simple_pdf', True),
                    start_page=start_page,
                    end_page=end_page,
                    add_header=settings.get('add_header', False),
                    add_footer=settings.get('add_footer', False),
                    watermark_page_range=settings.get('watermark_page_range', 'even'),
                    watermark_position=settings.get('watermark_position'),
                    header_position=settings.get('header_position'),
                    footer_position=settings.get('footer_position'),
                    output_dir=output_dir,
                    border_width=settings.get('border_width', 0),
                    border_color=settings.get('border_color', '#000000'),
                    background_color=settings.get('background_color', '#ffffff'),
                    add_random_icon=settings.get('add_random_icon', False),
                    icon_size=settings.get('icon_size')
                )
                
                # 将本地路径转换为URL
                import time
                images_urls = [f"{local_path_to_url(img_path)}?t={int(time.time())}" for img_path in result['images']]
                simple_pdf_url = f"{local_path_to_url(result['simple_pdf'])}?t={int(time.time())}"
                
                results.append({
                    "file_path": file_path,
                    "original_name": os.path.basename(file_path),
                    "success": True,
                    "images": images_urls,
                    "simple_pdf": simple_pdf_url,
                    "output_dir": result['output_dir'],
                    "total_pages": len(result['images']),
                    "progress": {
                        "current": index + 1,
                        "total": total_files
                    }
                })
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                results.append({
                    "file_path": file_path,
                    "original_name": os.path.basename(file_path) if file_path else 'unknown',
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
        import traceback
        traceback.print_exc()
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
    """传输文件到手机（通过路径）"""
    try:
        data = request.json
        computer_dir = data.get('computer_dir')
        phone_dir = data.get('phone_dir')
        device_id = data.get('device_id')
        
        if not computer_dir:
            return jsonify({"success": False, "error": "电脑源目录路径不能为空"})
        
        if not phone_dir:
            return jsonify({"success": False, "error": "手机目录路径不能为空"})
        
        if not device_id:
            return jsonify({"success": False, "error": "请先选择目标设备"})
        
        # 检查电脑源目录是否存在
        if not os.path.exists(computer_dir):
            return jsonify({"success": False, "error": f"电脑源目录不存在: {computer_dir}"})
        
        # 创建设备特定的传输管理器
        from file_transfer import FileTransferManager
        ft_manager = FileTransferManager(device_id=device_id)
        
        # 传输文件到手机
        result = ft_manager.transfer_files_to_phone(computer_dir, phone_dir)
        
        return jsonify(result)
            
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
        data = request.json
        computer_dir = data.get('computer_dir')
        phone_dir = data.get('phone_dir')
        device_id = data.get('device_id')
        
        if not computer_dir:
            return jsonify({"success": False, "error": "电脑源目录路径不能为空"})
        
        if not phone_dir:
            return jsonify({"success": False, "error": "手机目录路径不能为空"})
        
        if not device_id:
            return jsonify({"success": False, "error": "请先选择目标设备"})
        
        # 检查电脑源目录是否存在
        if not os.path.exists(computer_dir):
            return jsonify({"success": False, "error": f"电脑源目录不存在: {computer_dir}"})
        
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
        
        # 步骤2: 传输文件到手机
        step2_result = ft_manager.transfer_files_to_phone(computer_dir, phone_dir)
        results["steps"]["transfer"] = step2_result
        
        if not step2_result["success"]:
            results["success"] = False
            results["message"] = "文件传输失败"
            return jsonify(results)
        
        # 步骤3: 清空电脑目录
        step3_result = ft_manager.clear_computer_directory(computer_dir)
        results["steps"]["clear_computer"] = step3_result
        
        results["message"] = "完整传输流程执行成功"
        return jsonify(results)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/file-transfer/transfer-from-phone", methods=["POST"])
def api_transfer_from_phone():
    """将手机文件传输到电脑"""
    try:
        data = request.json
        phone_dir = data.get('phone_dir')
        computer_dir = data.get('computer_dir')
        device_id = data.get('device_id')
        
        if not phone_dir:
            return jsonify({"success": False, "error": "手机源目录路径不能为空"})
        
        if not computer_dir:
            return jsonify({"success": False, "error": "电脑目标目录路径不能为空"})
        
        if not device_id:
            return jsonify({"success": False, "error": "请先选择目标设备"})
        
        # 创建设备特定的传输管理器
        from file_transfer import FileTransferManager
        ft_manager = FileTransferManager(device_id=device_id)
        
        # 执行从手机到电脑的传输
        result = ft_manager.transfer_files_from_phone(phone_dir, computer_dir)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "请求不存在"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"success": False, "error": "服务器错误"}), 500


# ==================== 辅助函数 ====================

def local_path_to_url(path):
    """
    将本地文件路径转换为可通过服务器访问的URL
    """
    if not path:
        return None
    
    # 如果已经是URL格式，直接返回
    if path.startswith('/static/'):
        return path
    if path.startswith('http://') or path.startswith('https://'):
        return path
    
    # 将本地路径转换为 /local-file?path=xxx URL
    # 对路径进行URL编码
    from urllib.parse import quote
    encoded_path = quote(path, safe='')
    return f"/local-file?path={encoded_path}"


# ==================== 本地文件访问路由 ====================

@app.route('/local-file')
def serve_local_file():
    """
    提供本地文件访问服务
    用于访问生成的PDF图片（位于用户本地目录）
    使用查询参数: ?path=xxx
    """
    try:
        from urllib.parse import unquote
        import logging
        
        # 从查询参数获取路径
        encoded_path = request.args.get('path', '')
        
        if not encoded_path:
            return jsonify({"success": False, "error": "缺少path参数"}), 400
        
        # 解码路径 - 只解码一次，避免过度解码
        decoded_path = unquote(encoded_path)
        
        # 去除时间戳参数（如果有的话）
        if '?' in decoded_path:
            decoded_path = decoded_path.split('?')[0]
        
        logging.info(f"Local file request: decoded={decoded_path}")
        
        # 安全检查：确保路径是允许的目录之一
        allowed_prefixes = [
            '/Users/',
            '/home/',
            'C:/',
            'D:/',
        ]
        
        is_allowed = any(decoded_path.startswith(prefix) for prefix in allowed_prefixes)
        if not is_allowed:
            return jsonify({"success": False, "error": "访问被拒绝"}), 403
        
        # 检查文件是否存在
        if not os.path.exists(decoded_path):
            logging.warning(f"File not found: {decoded_path}")
            return jsonify({"success": False, "error": "文件不存在"}), 404
        
        # 检查是否是文件（不是目录）
        if not os.path.isfile(decoded_path):
            return jsonify({"success": False, "error": "不是文件"}), 400
        
        # 发送文件
        directory = os.path.dirname(decoded_path)
        filename = os.path.basename(decoded_path)
        return send_from_directory(directory, filename)
        
    except Exception as e:
        import logging
        logging.error(f"Error serving local file: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ==================== 封面生成器 API ====================

@app.route("/api/cover-generator/save", methods=["POST"])
def api_save_cover_image():
    """保存生成的封面图片"""
    try:
        if 'image' not in request.files:
            return jsonify({"success": False, "error": "没有图片文件"})
        
        file = request.files['image']
        output_dir = request.form.get('output_dir', '')
        
        if file.filename == '':
            return jsonify({"success": False, "error": "没有选择文件"})
        
        # 如果未指定输出目录，使用默认目录
        if not output_dir:
            output_dir = os.path.expanduser("~/Desktop/小红书封面")
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名
        filename = secure_filename(file.filename)
        filepath = os.path.join(output_dir, filename)
        
        # 保存文件
        file.save(filepath)
        
        return jsonify({
            "success": True,
            "message": "封面保存成功",
            "file_path": filepath,
            "filename": filename
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == '__main__':
    # 确保配置文件存在
    os.makedirs("config", exist_ok=True)
    if not os.path.exists("config/config.json"):
        with open("config/config.json", "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2, ensure_ascii=False)
    
    app.run(host="0.0.0.0", port=5002, debug=True, threaded=True)