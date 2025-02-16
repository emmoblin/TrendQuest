from typing import Dict, Type, Any
from .base_strategy import BaseStrategy
from .dual_ma_strategy import DualMAStrategy
from .macd_strategy import MACDStrategy

class StrategyFactory:
    """策略工厂类"""
    
    _strategies: Dict[str, Dict[str, Any]] = {
        "DualMA": {
            "name": "双均线策略",
            "class": DualMAStrategy,
            "description": "使用快慢两条移动平均线产生交易信号的经典策略。当快线上穿慢线时买入，当快线下穿慢线时卖出，同时包含止盈止损机制。"
        },
        "MACD": {
            "name": "MACD策略",
            "class": MACDStrategy,
            "description": "使用MACD指标进行交易，结合RSI过滤虚假信号。包含移动止损、波动率过滤等机制，适合趋势型交易。"
        }
    }

def get_strategy(strategy_code: str) -> Type[BaseStrategy]:
    """获取策略类
    
    Args:
        strategy_code: 策略代码
        
    Returns:
        策略类
    
    Raises:
        ValueError: 策略不存在
    """
    if strategy_code not in StrategyFactory._strategies:
        raise ValueError(f"Strategy '{strategy_code}' not found")
    return StrategyFactory._strategies[strategy_code]["class"]

def list_strategies() -> Dict[str, Dict[str, Any]]:
    """获取所有可用策略"""
    return StrategyFactory._strategies

def get_display_names() -> Dict[str, str]:
    """获取策略显示名称映射"""
    return {
        code: info["name"]
        for code, info in StrategyFactory._strategies.items()
    }

__all__ = [
    'StrategyFactory',
    'get_strategy',
    'list_strategies',
    'get_display_names'
]