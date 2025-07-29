from pydantic import BaseModel


class Config(BaseModel):
    """NSFW检测器配置"""
    
    # API配置
    nsfw_api_url: str = "https://nsfwpy.cn/analyze"
    nsfw_model: str = "mobilenet_v2"
    request_timeout: int = 30
    
    # 默认群组配置
    default_enabled: bool = True
    default_threshold: float = 0.7
    default_ban_time: int = 60
    default_warning_limit: int = 3
    default_kick_enabled: bool = True
    
    # 消息撤回配置
    auto_recall_enabled: bool = True
    recall_delay: int = 5  # 撤回延迟时间(秒)
    
    # 调试配置
    debug_mode: bool = False  # 是否启用调试模式
    
    # 数据存储配置
    data_dir: str = "data/nsfw_detector"
    
    class Config:
        extra = "ignore" 