from .base_strategy import BaseStrategy
from .dual_ma_strategy import DualMAStrategy
from .macd_strategy import MACDStrategy
from .strategy_factory import get_strategy, register_strategy, list_strategies

# 导出工厂方法而不是实例
__all__ = [
    'BaseStrategy',
    'DualMAStrategy',
    'MACDStrategy',
    'get_strategy',
    'register_strategy',
    'list_strategies'
]