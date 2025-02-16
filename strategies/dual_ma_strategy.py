from .base_strategy import BaseStrategy
import backtrader as bt

class DualMAStrategy(BaseStrategy):
    """双均线策略"""
    
    params = (
        ('fast_period', 20),  # 短期均线周期
        ('slow_period', 60),  # 长期均线周期
        ('position_size', 0.1),  # 仓位比例
    )
    
    def setup_indicators(self):
        """设置技术指标"""
        # 计算移动平均线
        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.data.close,
            period=self.params.fast_period
        )
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.data.close,
            period=self.params.slow_period
        )
        
        # 计算金叉死叉信号
        self.crossover = bt.indicators.CrossOver(
            self.fast_ma,
            self.slow_ma
        )
    
    def next(self):
        """策略逻辑"""
        # 检查是否已有持仓
        if not self.position:
            # 金叉买入
            if self.crossover > 0:
                size = self.get_position_size(self.data.close[0])
                self.buy(size=size)
        
        else:
            # 死叉卖出
            if self.crossover < 0:
                self.close()