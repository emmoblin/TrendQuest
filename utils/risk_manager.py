import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime

class RiskManager:
    """风险管理器"""
    
    def __init__(
        self,
        max_positions: int = 5,
        position_size: float = 0.2,
        max_drawdown: float = 0.2,
        stop_loss: float = 0.1,
        profit_target: float = 0.3
    ):
        self.max_positions = max_positions
        self.position_size = position_size
        self.max_drawdown = max_drawdown
        self.stop_loss = stop_loss
        self.profit_target = profit_target
        
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.portfolio_value = 0.0
        self.peak_value = 0.0
        self.current_drawdown = 0.0
    
    def can_open_position(self, symbol: str, price: float, cash: float) -> bool:
        """检查是否可以开仓"""
        # 检查持仓数量限制
        if len(self.positions) >= self.max_positions:
            return False
        
        # 检查是否已有持仓
        if symbol in self.positions:
            return False
        
        # 检查资金是否足够
        position_value = cash * self.position_size
        if position_value < price * 100:  # 假设最小交易单位为100股
            return False
        
        # 检查当前回撤
        if self.current_drawdown > self.max_drawdown:
            return False
        
        return True
    
    def should_close_position(
        self,
        symbol: str,
        current_price: float,
        position_info: Dict[str, Any]
    ) -> bool:
        """检查是否应该平仓"""
        if symbol not in self.positions:
            return False
        
        entry_price = position_info['entry_price']
        
        # 计算浮动盈亏
        pnl_rate = (current_price - entry_price) / entry_price
        
        # 止损检查
        if pnl_rate <= -self.stop_loss:
            return True
        
        # 止盈检查
        if pnl_rate >= self.profit_target:
            return True
        
        return False
    
    def update_portfolio_value(self, new_value: float):
        """更新组合价值"""
        self.portfolio_value = new_value
        self.peak_value = max(self.peak_value, new_value)
        
        # 更新当前回撤
        if self.peak_value > 0:
            self.current_drawdown = (self.peak_value - self.portfolio_value) / self.peak_value
    
    def add_position(
        self,
        symbol: str,
        entry_price: float,
        size: int,
        timestamp: datetime
    ):
        """添加新持仓"""
        self.positions[symbol] = {
            'entry_price': entry_price,
            'size': size,
            'entry_time': timestamp,
            'cost': entry_price * size
        }
    
    def remove_position(self, symbol: str):
        """移除持仓"""
        if symbol in self.positions:
            del self.positions[symbol]
    
    def get_position_size(self, cash: float, price: float) -> int:
        """计算开仓数量"""
        position_value = cash * self.position_size
        size = int(position_value / (price * 100)) * 100  # 向下取整到100的倍数
        return size
    
    def get_risk_metrics(self) -> Dict[str, float]:
        """获取风险指标"""
        return {
            'current_drawdown': self.current_drawdown,
            'peak_value': self.peak_value,
            'portfolio_value': self.portfolio_value,
            'position_count': len(self.positions),
            'total_exposure': sum(p['cost'] for p in self.positions.values())
        }