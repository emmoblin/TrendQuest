from typing import Dict, Any
import backtrader as bt
from .base_strategy import BaseStrategy

class DualMAStrategy(BaseStrategy):
    """双均线策略"""
    
    params = (
        ('fast_period', 5),  # 快线周期
        ('slow_period', 20),  # 慢线周期
        ('order_percentage', 0.95),  # 订单资金比例
        ('stop_loss', 0.05),  # 止损比例
        ('take_profit', 0.15),  # 止盈比例
    )
    
    @classmethod
    def get_default_params(cls) -> Dict[str, Dict[str, Any]]:
        """获取策略默认参数"""
        return {
            "fast_period": {
                "display_name": "快线周期",
                "type": "int",
                "min": 2,
                "max": 100,
                "default": 5,
                "step": 1,
                "description": "快速移动平均线的周期"
            },
            "slow_period": {
                "display_name": "慢线周期",
                "type": "int",
                "min": 5,
                "max": 200,
                "default": 20,
                "step": 1,
                "description": "慢速移动平均线的周期"
            },
            "order_percentage": {
                "display_name": "订单资金比例",
                "type": "float",
                "min": 0.1,
                "max": 1.0,
                "default": 0.95,
                "step": 0.05,
                "description": "每次交易使用的资金比例"
            },
            "stop_loss": {
                "display_name": "止损比例",
                "type": "float",
                "min": 0.01,
                "max": 0.2,
                "default": 0.05,
                "step": 0.01,
                "description": "止损触发比例"
            },
            "take_profit": {
                "display_name": "止盈比例",
                "type": "float",
                "min": 0.05,
                "max": 0.5,
                "default": 0.15,
                "step": 0.05,
                "description": "止盈触发比例"
            }
        }
    
    def __init__(self):
        super().__init__()
        
        # 计算移动平均线
        self.fast_ma = bt.indicators.SMA(
            self.data.close,
            period=self.params.fast_period,
            plotname=f'SMA{self.params.fast_period}'
        )
        
        self.slow_ma = bt.indicators.SMA(
            self.data.close,
            period=self.params.slow_period,
            plotname=f'SMA{self.params.slow_period}'
        )
        
        # 交叉信号
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
        # 跟踪订单和持仓价格
        self.order = None
        self.entry_price = None
    
    def next(self):
        """策略核心逻辑"""
        # 如果有待处理订单，不执行新操作
        if self.order:
            return
        
        # 检查是否持仓
        if not self.position:
            # 金叉买入信号
            if self.crossover > 0:
                size = self.get_position_size()
                if size > 0:
                    self.order = self.buy(size=size)
                    self.entry_price = self.data.close[0]
                    
        else:
            # 判断是否需要止损或止盈
            if self.should_stop_loss() or self.should_take_profit():
                self.order = self.close()
            
            # 死叉卖出信号
            elif self.crossover < 0:
                self.order = self.close()
    
    def get_position_size(self) -> int:
        """计算开仓数量"""
        available_cash = self.broker.get_cash() * self.params.order_percentage
        return int(available_cash / self.data.close[0])
    
    def should_stop_loss(self) -> bool:
        """判断是否触发止损"""
        if not self.entry_price:
            return False
        return (self.data.close[0] - self.entry_price) / self.entry_price <= -self.params.stop_loss
    
    def should_take_profit(self) -> bool:
        """判断是否触发止盈"""
        if not self.entry_price:
            return False
        return (self.data.close[0] - self.entry_price) / self.entry_price >= self.params.take_profit