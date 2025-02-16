from typing import Dict, Any
import backtrader as bt
from .base_strategy import BaseStrategy

class MACDStrategy(BaseStrategy):
    """MACD策略
    
    使用MACD指标进行交易，结合RSI过滤虚假信号，并包含止盈止损机制。
    主要规则：
    1. MACD金叉且RSI不超买时买入
    2. MACD死叉或RSI超卖时卖出
    3. 设置波动率过滤，避免剧烈波动时期
    4. 包含止盈止损和移动止损
    """
    
    params = (
        # MACD参数
        ('macd_fast', 12),      # MACD快线周期
        ('macd_slow', 26),      # MACD慢线周期
        ('macd_signal', 9),     # MACD信号线周期
        # RSI参数
        ('rsi_period', 14),     # RSI周期
        ('rsi_overbought', 70), # RSI超买阈值
        ('rsi_oversold', 30),   # RSI超卖阈值
        # 波动率参数
        ('atr_period', 14),     # ATR周期
        ('volatility_mult', 2),  # 波动率倍数
        # 交易参数
        ('order_percentage', 0.95),  # 订单资金比例
        ('stop_loss', 0.05),     # 止损比例
        ('take_profit', 0.15),   # 止盈比例
        ('trailing_stop', 0.03),  # 移动止损比例
    )
    
    @classmethod
    def get_default_params(cls) -> Dict[str, Dict[str, Any]]:
        """获取策略默认参数"""
        return {
            "macd_fast": {
                "display_name": "MACD快线周期",
                "type": "int",
                "min": 8,
                "max": 24,
                "default": 12,
                "step": 1,
                "description": "MACD快速移动平均线周期"
            },
            "macd_slow": {
                "display_name": "MACD慢线周期",
                "type": "int",
                "min": 16,
                "max": 52,
                "default": 26,
                "step": 1,
                "description": "MACD慢速移动平均线周期"
            },
            "macd_signal": {
                "display_name": "MACD信号线周期",
                "type": "int",
                "min": 5,
                "max": 15,
                "default": 9,
                "step": 1,
                "description": "MACD信号线平滑周期"
            },
            "rsi_period": {
                "display_name": "RSI周期",
                "type": "int",
                "min": 7,
                "max": 28,
                "default": 14,
                "step": 1,
                "description": "相对强弱指标周期"
            },
            "rsi_overbought": {
                "display_name": "RSI超买阈值",
                "type": "int",
                "min": 65,
                "max": 85,
                "default": 70,
                "step": 1,
                "description": "RSI超买判断阈值"
            },
            "rsi_oversold": {
                "display_name": "RSI超卖阈值",
                "type": "int",
                "min": 15,
                "max": 35,
                "default": 30,
                "step": 1,
                "description": "RSI超卖判断阈值"
            },
            "atr_period": {
                "display_name": "ATR周期",
                "type": "int",
                "min": 7,
                "max": 28,
                "default": 14,
                "step": 1,
                "description": "平均真实波幅周期"
            },
            "volatility_mult": {
                "display_name": "波动率倍数",
                "type": "float",
                "min": 1.0,
                "max": 5.0,
                "default": 2.0,
                "step": 0.1,
                "description": "ATR波动率过滤倍数"
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
                "min": 0.02,
                "max": 0.15,
                "default": 0.05,
                "step": 0.01,
                "description": "固定止损触发比例"
            },
            "take_profit": {
                "display_name": "止盈比例",
                "type": "float",
                "min": 0.05,
                "max": 0.5,
                "default": 0.15,
                "step": 0.05,
                "description": "固定止盈触发比例"
            },
            "trailing_stop": {
                "display_name": "移动止损比例",
                "type": "float",
                "min": 0.02,
                "max": 0.1,
                "default": 0.03,
                "step": 0.01,
                "description": "移动止损触发比例"
            }
        }
    
    def __init__(self):
        super().__init__()
        
        # 计算指标
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.macd_fast,
            period_me2=self.params.macd_slow,
            period_signal=self.params.macd_signal
        )
        
        self.rsi = bt.indicators.RSI(
            self.data.close,
            period=self.params.rsi_period
        )
        
        self.atr = bt.indicators.ATR(
            self.data,
            period=self.params.atr_period
        )
        
        # 交叉信号
        self.macd_cross = bt.indicators.CrossOver(
            self.macd.macd,
            self.macd.signal
        )
        
        # 跟踪订单和持仓
        self.order = None
        self.entry_price = None
        self.highest_price = None
    
    def next(self):
        """策略核心逻辑"""
        # 如果有待处理订单，不执行新操作
        if self.order:
            return
        
        # 检查是否持仓
        if not self.position:
            # 买入条件：MACD金叉 + RSI不超买 + 波动率适中
            if (self.macd_cross > 0 and 
                self.rsi < self.params.rsi_overbought and
                self.is_volatility_acceptable()):
                
                size = self.get_position_size()
                if size > 0:
                    self.order = self.buy(size=size)
                    self.entry_price = self.data.close[0]
                    self.highest_price = self.data.close[0]
                    
        else:
            # 更新最高价
            if self.data.close[0] > self.highest_price:
                self.highest_price = self.data.close[0]
            
            # 卖出条件检查
            should_sell = (
                # MACD死叉
                self.macd_cross < 0 or
                # RSI超买
                self.rsi > self.params.rsi_overbought or
                # 止损
                self.should_stop_loss() or
                # 止盈
                self.should_take_profit() or
                # 移动止损
                self.should_trailing_stop()
            )
            
            if should_sell:
                self.order = self.close()
    
    def get_position_size(self) -> int:
        """计算开仓数量"""
        available_cash = self.broker.get_cash() * self.params.order_percentage
        return int(available_cash / self.data.close[0])
    
    def is_volatility_acceptable(self) -> bool:
        """检查波动率是否在可接受范围内"""
        current_volatility = self.atr[0]
        avg_price = (self.data.high[0] + self.data.low[0]) / 2
        return current_volatility <= (avg_price * self.params.volatility_mult / 100)
    
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
    
    def should_trailing_stop(self) -> bool:
        """判断是否触发移动止损"""
        if not self.highest_price:
            return False
        return (self.data.close[0] - self.highest_price) / self.highest_price <= -self.params.trailing_stop