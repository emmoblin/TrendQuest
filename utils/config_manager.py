import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
# config_manager.py
from .log_init import get_logger

logger = get_logger(__name__)

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = 'config'):
        self.current_time = datetime.strptime("2025-02-15 18:54:58", "%Y-%m-%d %H:%M:%S")
        self.current_user = "emmoblin"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 默认配置
        self.default_config = {
            'system': {
                'version': '1.0.0',
                'debug': False,
                'log_level': 'INFO',
                'data_cache_days': 7
            },
            'trading': {
                'commission_rate': 0.0003,
                'slippage': 0.0002,
                'min_trade_unit': 100,
                'max_position_size': 0.2
            },
            'backtest': {
                'default_initial_cash': 1000000,
                'default_strategy': 'DualMA',
                'risk_free_rate': 0.03,
                'performance_benchmark': '000300'
            },
            'display': {
                'theme': 'light',
                'chart_style': 'default',
                'date_format': '%Y-%m-%d'
            }
        }
        
        # 加载配置
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_file = self.config_dir / 'config.yaml'
        
        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    if user_config is None:
                        user_config = {}
                    
                    # 递归更新配置
                    return self._deep_update(self.default_config.copy(), user_config)
            
            # 如果配置文件不存在，保存默认配置
            self.save_config(self.default_config)
            return self.default_config.copy()
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置文件"""
        config_file = self.config_dir / 'config.yaml'
        
        try:
            # 添加元数据
            config['_metadata'] = {
                'last_modified': self.current_time.strftime("%Y-%m-%d %H:%M:%S"),
                'modified_by': self.current_user
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, sort_keys=False)
            
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")
            return False
    
    def get_config(self, section: str = None) -> Dict[str, Any]:
        """获取配置"""
        if section:
            return self.config.get(section, {})
        return self.config
    
    def update_config(self, updates: Dict[str, Any], section: str = None) -> bool:
        """更新配置"""
        try:
            if section:
                if section not in self.config:
                    self.config[section] = {}
                self.config[section] = self._deep_update(
                    self.config[section],
                    updates
                )
            else:
                self.config = self._deep_update(self.config, updates)
            
            return self.save_config(self.config)
            
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            return False
    
    def _deep_update(self, base: Dict, update: Dict) -> Dict:
        """递归更新字典"""
        for key, value in update.items():
            if isinstance(value, dict) and key in base:
                base[key] = self._deep_update(base[key], value)
            else:
                base[key] = value
        return base