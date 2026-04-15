
from flask import Flask, request, jsonify, render_template
import json
import threading
import os
from xhs_nurturing import NurturingManager
from license_manager import get_license_manager

app = Flask(__name__, template_folder='templates', static_folder='static')

# 初始化养号管理器和授权管理器
nurturing_manager = NurturingManager()
license_manager = get_license_manager()
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

@app.route("/license")
def license_page():
    """授权管理页面"""
    return render_template("license.html")

@app.route("/status")
def status_page():
    """状态监控页面"""
    return render_template("status.html")

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

@app.route("/api/device/alias/&lt;device_id&gt;", methods=["DELETE"])
def api_remove_device_alias(device_id):
    """移除设备别名"""
    try:
        nurturing_manager.device_manager.remove_device_alias(device_id)
        return jsonify({"success": True, "message": f"已移除设备 {device_id} 的别名"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/device/&lt;device_id&gt;", methods=["DELETE"])
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

@app.route("/api/config/&lt;device_id&gt;", methods=["GET"])
def api_get_config(device_id):
    """获取设备配置"""
    try:
        config = nurturing_manager.get_device_config(device_id)
        return jsonify({"success":  True, "data": config})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/config/&lt;device_id&gt;", methods=["PUT"])
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

@app.route("/api/config/keywords/&lt;device_id&gt;", methods=["GET", "PUT"])
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

# ==================== 授权管理 API ====================

@app.route("/api/license/info", methods=["GET"])
def api_license_info():
    """获取当前授权信息和使用统计"""
    try:
        stats = license_manager.get_usage_stats()
        return jsonify({"success": True, "data": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/license/activate", methods=["POST"])
def api_license_activate():
    """激活授权"""
    try:
        activation_code = request.json.get("activation_code")
        machine_code = request.json.get("machine_code")
        
        if not activation_code:
            return jsonify({"success": False, "error": "激活码不能为空"})
        if not machine_code:
            return jsonify({"success": False, "error": "机器码不能为空"})
        
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

# ==================== 养号控制 ====================

@app.route("/api/yanghao/start", methods=["POST"])
def api_start_yanghao():
    """启动养号"""
    try: 
        device_id = request.json.get("device_id") or current_device["device_id"]
        if not device_id:
            return jsonify({"success": False, "error": "未选择设备"})
        
        # 获取用户配置的计划养号时长
        planned_duration = 0
        config = nurturing_manager.get_device_config(device_id)
        if config and "duration_minutes" in config:
            planned_duration = int(config["duration_minutes"])
        
        # 权限检查 - 检查配额和获取提示信息
        can_start, message, actual_duration = license_manager.check_can_start(device_id, planned_duration)
        if not can_start:
            return jsonify({"success": False, "error": message})
        
        # 如果实际时长和计划不同，更新配置里的时长
        if actual_duration != planned_duration:
            config["duration_minutes"] = actual_duration
            nurturing_manager.update_device_config(device_id, config)
        
        # 记录开始时间，用于统计（同时增加养号次数）
        license_manager.on_start(device_id)
        
        success = nurturing_manager.start_nurturing(device_id)
        if success:
            # 获取当前授权信息，用于提示用户
            license_info = license_manager.get_current_license()
            package_type = license_info.get("package_type", "free")
            package_names = {
                "free": "免费版",
                "basic": "基础版",
                "advanced": "高级版",
                "premium": "高级版"
            }
            package_name = package_names.get(package_type, package_type)
            
            # 构建提示消息
            license_message = f"您是{package_name}用户"
            if package_type == "free":
                max_single = license_info.get("max_single_yanghao_minutes", 20)
                license_message += f"，每次养号最长{max_single}分钟"
            
            full_message = f"{license_message}\n{message}" if message else license_message
            
            return jsonify({
                "success": True, 
                "message": full_message,
                "actual_duration": actual_duration,
                "license_info": license_info
            })
        else:
            # 启动失败，回滚统计
            license_manager.on_stop(device_id)
            # 恢复原来的时长
            if actual_duration != planned_duration:
                config["duration_minutes"] = planned_duration
                nurturing_manager.update_device_config(device_id, config)
            return jsonify({"success": False, "error": "启动养号失败"})
    except Exception as e:
        # 异常也要回滚统计
        license_manager.on_stop(device_id)
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/yanghao/stop", methods=["POST"])
def api_stop_yanghao():
    """停止养号"""
    try: 
        device_id = request.json.get("device_id") or current_device["device_id"]
        if not device_id: 
            return jsonify({"success": False, "error": "未选择设备"})
        
        nurturing_manager.stop_nurturing(device_id)
        # 统计时长
        license_manager.on_stop(device_id)
        return jsonify({"success": True, "message": "已停止养号"})
    except Exception as e:
        # 异常也要统计
        license_manager.on_stop(device_id)
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/yanghao/status/&lt;device_id&gt;")
def api_status(device_id):
    """获取养号状态"""
    try:
        status = nurturing_manager.get_nurturing_status(device_id)
        return jsonify({"success": True, "data": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/yanghao/close-xhs/&lt;device_id&gt;")
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
    
    # 程序启动时刷新授权
    license_manager.refresh_license()
    
    app.run(host="0.0.0.0", port=5002, debug=True, threaded=True)

