from datetime import datetime
from typing import Dict, Any
from .config_manager import ConfigManager
from .log_manager import LogManager
from .cache_manager import CacheManager
from .event_system import EventSystem, Event
from .log_init import get_logger

logger = get_logger(__name__)

class UtilsManager:
    """工具管理器，统一管理所有工具类实例"""
    
    def __init__(
        self,
        config_dir: str = 'config',
        log_dir: str = 'logs',
        cache_dir: str = 'cache',
        log_level: str = 'INFO'
    ):
        self.current_time = datetime.strptime("2025-02-16 01:39:31", "%Y-%m-%d %H:%M:%S")
        self.current_user = "emmoblin"
        
        # 初始化各个管理器
        self.config = ConfigManager(config_dir=config_dir)
        self.logger = LogManager(log_dir=log_dir, log_level=log_level)
        self.cache = CacheManager(cache_dir=cache_dir)
        self.event = EventSystem()
        
        # 配置日志
        self.logger.setup_logging()
        
        # 记录初始化信息
        logger.info(
            f"Utils Manager initialized by {self.current_user} at {self.current_time}"
        )
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        try:
            return {
                'initialized_time': self.current_time,
                'initialized_by': self.current_user,
                'config_version': self.config.get_config().get('system', {}).get('version'),
                'cache_status': {
                    'size': self.cache.get_cache_size(),
                    'items': len(self.cache.index)
                },
                'logger_status': {
                    'level': self.logger.get_logger(__name__).getEffectiveLevel(),
                    'handlers': len(self.logger.get_logger(__name__).handlers)
                },
                'event_subscribers': len(self.event.handlers)
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {str(e)}")
            return {}
    
    def cleanup(self):
        """清理资源"""
        try:
            # 保存配置
            self.config.save_config(self.config.get_config())
            
            # 清理过期缓存
            self.cache.clean_expired_cache()
            
            # 清理事件订阅
            self.event.clear()
            
            # 记录清理信息
            logger.info("Utils Manager cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")