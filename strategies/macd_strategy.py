from .base_strategy import BaseStrategy
import backtrader as bt

class MACDStrategy(BaseStrategy):
    """MACD策略"""
    
    params = (
        ('fast_period', 12),   # 快速EMA周期
        ('slow_period', 26),   # 慢速EMA周期
        ('signal_period', 9),  # 信号线周期
        ('position_size', 0.1),  # 仓位比例
    )
    
    def setup_indicators(self):
        """设置技术指标"""
        # 计算MACD
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period
        )
        
        # 设置信号线穿越
        self.crossover = bt.indicators.CrossOver(
            self.macd.macd,
            self.macd.signal
        )
    
    def next(self):
        """策略逻辑"""
        if not self.position:
            # MACD金叉且柱状图为正
            if self.crossover > 0 and self.macd.macd[0] > 0:
                size = self.get_position_size(self.data.close[0])
                self.buy(size=size)
        
        else:
            # MACD死叉或柱状图转负
            if self.crossover < 0 or self.macd.macd[0] < 0:
                self.close()