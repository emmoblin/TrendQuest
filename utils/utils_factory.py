from typing import Optional
from .utils_manager import UtilsManager

class UtilsFactory:
    """工具工厂类，管理UtilsManager的单例"""
    
    _instance: Optional[UtilsManager] = None
    
    @classmethod
    def get_instance(
        cls,
        config_dir: str = 'config',
        log_dir: str = 'logs',
        cache_dir: str = 'cache',
        log_level: str = 'INFO'
    ) -> UtilsManager:
        """
        获取或创建UtilsManager实例
        
        Args:
            config_dir: 配置目录
            log_dir: 日志目录
            cache_dir: 缓存目录
            log_level: 日志级别
        
        Returns:
            UtilsManager实例
        """
        if cls._instance is None:
            cls._instance = UtilsManager(
                config_dir=config_dir,
                log_dir=log_dir,
                cache_dir=cache_dir,
                log_level=log_level
            )
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """重置实例"""
        if cls._instance is not None:
            cls._instance.cleanup()
            cls._instance = None