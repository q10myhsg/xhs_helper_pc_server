import json
import os
from db_manager import DBManager

def migrate_keywords_to_db():
    """将config.json中的关键词迁移到数据库"""
    config_path = "config/config.json"
    if not os.path.exists(config_path):
        print(f"配置文件 {config_path} 不存在")
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    db_manager = DBManager()
    
    for device_id, device_config in config.items():
        if device_id == "_default":
            continue
        
        keywords = device_config.get("keywords", [])
        if keywords:
            print(f"迁移设备 {device_id} 的关键词，共 {len(keywords)} 个...")
            db_manager.save_keywords(device_id, keywords)
            
            # 从config中删除keywords字段
            if "keywords" in device_config:
                del device_config["keywords"]
    
    # 保存更新后的config
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("关键词迁移完成！")

if __name__ == "__main__":
    migrate_keywords_to_db()