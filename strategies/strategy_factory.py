from datetime import datetime
from typing import Dict, Type, NamedTuple
from .base_strategy import BaseStrategy
from .dual_ma_strategy import DualMAStrategy
from .macd_strategy import MACDStrategy
from utils.log_init import get_logger

logger = get_logger(__name__)

class StrategyInfo(NamedTuple):
    """策略信息"""
    class_type: Type[BaseStrategy]  # 策略类
    display_name: str  # 显示名称
    description: str  # 策略描述

class StrategyFactory:
    """策略工厂类"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
        return cls._instance
    
    def __init__(self):
        if self.initialized:
            return
            
        self.current_time = datetime.strptime("2025-02-16 12:28:46", "%Y-%m-%d %H:%M:%S")
        self.current_user = "emmoblin"
        
        # 初始化策略映射表
        self._strategy_map: Dict[str, StrategyInfo] = {}
        
        # 注册内置策略
        self._register_built_in_strategies()
        
        self.initialized = True
        logger.info(f"StrategyFactory initialized by {self.current_user}")
    
    def _register_built_in_strategies(self):
        """注册内置策略"""
        strategies = {
            'DualMA': StrategyInfo(
                class_type=DualMAStrategy,
                display_name='双均线策略',
                description='使用快慢双均线进行交易'
            ),
            'MACD': StrategyInfo(
                class_type=MACDStrategy,
                display_name='MACD策略',
                description='使用MACD指标进行交易'
            )
        }
        
        for name, info in strategies.items():
            self.register_strategy(name, info)
    
    def get_strategy(self, name_or_display: str) -> Type[BaseStrategy]:
        """
        获取策略类
        
        Args:
            name_or_display: 策略代码或显示名称
        
        Returns:
            策略类
        """
        # 先尝试直接查找
        if name_or_display in self._strategy_map:
            return self._strategy_map[name_or_display].class_type
        
        # 尝试通过显示名称查找
        for strategy_info in self._strategy_map.values():
            if strategy_info.display_name == name_or_display:
                return strategy_info.class_type
        
        # 未找到策略
        available = [
            f"{info.display_name} ({name})"
            for name, info in self._strategy_map.items()
        ]
        error_msg = (
            f"Strategy '{name_or_display}' not found. "
            f"Available: {available}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    def register_strategy(self, name: str, info: StrategyInfo):
        """
        注册新策略
        
        Args:
            name: 策略代码
            info: 策略信息
        """
        if not issubclass(info.class_type, BaseStrategy):
            error_msg = f"Strategy class must inherit from BaseStrategy"
            logger.error(error_msg)
            raise TypeError(error_msg)
        
        self._strategy_map[name] = info
        logger.info(f"Registered strategy: {name} ({info.display_name})")
    
    def list_strategies(self) -> Dict[str, StrategyInfo]:
        """
        列出所有可用策略
        
        Returns:
            策略映射表
        """
        return self._strategy_map.copy()
    
    def get_display_names(self) -> Dict[str, str]:
        """
        获取策略显示名称映射
        
        Returns:
            显示名称映射表 {显示名称: 策略代码}
        """
        return {
            info.display_name: name
            for name, info in self._strategy_map.items()
        }

# 创建全局单例实例
_factory = StrategyFactory()

# 导出工厂方法
def get_strategy(name_or_display: str) -> Type[BaseStrategy]:
    """获取策略类的全局方法"""
    return _factory.get_strategy(name_or_display)

def register_strategy(name: str, info: StrategyInfo):
    """注册策略的全局方法"""
    return _factory.register_strategy(name, info)

def list_strategies() -> Dict[str, StrategyInfo]:
    """列出策略的全局方法"""
    return _factory.list_strategies()

def get_display_names() -> Dict[str, str]:
    """获取显示名称映射的全局方法"""
    return _factory.get_display_names()