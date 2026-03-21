import hashlib
import platform
import uuid
import logging

logger = logging.getLogger(__name__)


def get_machine_code() -> str:
    """
    生成本机唯一机器码
    :return: 机器码字符串
    """
    try:
        machine_info = []
        
        try:
            machine_info.append(platform.machine())
        except:
            pass
        
        try:
            machine_info.append(platform.system())
        except:
            pass
        
        try:
            machine_info.append(platform.processor())
        except:
            pass
        
        try:
            machine_info.append(str(uuid.getnode()))
        except:
            pass
        
        try:
            import socket
            hostname = socket.gethostname()
            machine_info.append(hostname)
        except:
            pass
        
        combined = "|".join(machine_info)
        machine_code = hashlib.md5(combined.encode('utf-8')).hexdigest()
        logger.info(f"生成机器码: {machine_code}")
        return machine_code
    except Exception as e:
        logger.error(f"生成机器码失败: {e}")
        fallback_code = hashlib.md5(str(uuid.uuid4()).encode('utf-8')).hexdigest()
        logger.warning(f"使用随机 fallback 机器码: {fallback_code}")
        return fallback_code
