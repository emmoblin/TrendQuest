import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from functools import lru_cache

class LogManager:
    """日志管理器"""
    
    def __init__(
        self,
        log_dir: str = 'logs',
        log_level: str = 'INFO',
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5
    ):
        self.current_time = datetime.strptime("2025-02-16 03:44:49", "%Y-%m-%d %H:%M:%S")
        self.current_user = "emmoblin"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.log_level = getattr(logging, log_level.upper())
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # 设置根日志器
        self._setup_root_logger()
        
        # 日志器缓存
        self._loggers: Dict[str, logging.Logger] = {}
    
    def _setup_root_logger(self):
        """配置根日志器"""
        root_logger = logging.getLogger()
        
        # 清除现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 设置格式化器
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s'
        )
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 添加文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'app.log',
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # 添加错误日志处理器
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / 'error.log',
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
        
        root_logger.setLevel(self.log_level)
    
    @lru_cache(maxsize=None)
    def get_logger(self, name: str) -> logging.Logger:
        """获取日志器"""
        logger = logging.getLogger(name)
        
        if name not in self._loggers:
            # 添加模块特定的文件处理器
            handler = logging.handlers.RotatingFileHandler(
                self.log_dir / f"{name.split('.')[-1]}.log",
                maxBytes=self.max_bytes,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            handler.setFormatter(logging.Formatter(
                '[%(asctime)s] [%(levelname)s] - %(message)s'
            ))
            logger.addHandler(handler)
            
            # 记录创建信息
            logger.info(
                f"Logger created by {self.current_user} at {self.current_time}"
            )
            
            self._loggers[name] = logger
        
        return logger
    
    def set_level(self, level: str):
        """设置日志级别"""
        level_value = getattr(logging, level.upper())
        self.log_level = level_value
        
        # 更新所有日志器的级别
        for logger in self._loggers.values():
            logger.setLevel(level_value)

# 创建全局日志管理器实例
log_manager = LogManager()

def get_logger(name: str) -> logging.Logger:
    """获取日志器的统一接口"""
    return log_manager.get_logger(name)