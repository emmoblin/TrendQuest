import backtrader as bt
from typing import Dict, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod
from utils.log_init import get_logger

logger = get_logger(__name__)

class BaseStrategy(bt.Strategy):
    """策略基类"""
    
    def __init__(self):
        """初始化策略"""
        super().__init__()  # 必须先调用父类初始化
        
        # 记录持仓信息
        self._positions = {}  # 使用_positions而不是positions
        
        # 记录交易记录
        self._trades = []
        
        # 记录当前时间
        self._current_time = None
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Completed]:
            if order.isbuy():
                self._positions[order.data._name] = {
                    'size': order.size,
                    'price': order.executed.price,
                    'time': self._current_time
                }
            else:  # Sell
                if order.data._name in self._positions:
                    del self._positions[order.data._name]
            
            # 记录交易
            self._trades.append({
                'symbol': order.data._name,
                'datetime': self._current_time,
                'type': 'BUY' if order.isbuy() else 'SELL',
                'size': order.size,
                'price': order.executed.price,
                'commission': order.executed.comm
            })
    
    def next(self):
        """K线更新"""
        self._current_time = self.data0.datetime.datetime(0)
        self._update_indicators()
        self._process_signals()
    
    def _update_indicators(self):
        """更新指标"""
        pass
    
    @abstractmethod
    def _process_signals(self):
        """处理交易信号"""
        raise NotImplementedError("子类必须实现_process_signals方法")
    
    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """获取当前持仓"""
        return self._positions.copy()
    
    def get_trades(self) -> list:
        """获取交易记录"""
        return self._trades.copy()
    
    @classmethod
    def get_default_params(cls) -> Dict[str, Dict[str, Any]]:
        """获取默认参数
        
        Returns:
            参数配置字典
        """
        raise NotImplementedError("子类必须实现get_default_params方法")