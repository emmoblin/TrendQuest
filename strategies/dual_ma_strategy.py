import backtrader as bt
from typing import Dict, Any
from .base_strategy import BaseStrategy
from utils.log_init import get_logger
import numpy as np

logger = get_logger(__name__)

class DualMAStrategy(BaseStrategy):
    """双均线策略"""
    
    params = (
        ('fast_period', 10),     # 快线周期
        ('slow_period', 30),     # 慢线周期
        ('atr_period', 14),      # ATR周期
        ('risk_ratio', 0.02),    # 风险系数
        ('stop_loss', 0.05),     # 止损比例
        ('take_profit', 0.15),   # 止盈比例
        ('trailing_stop', 0.03), # 移动止损比例
        ('min_volume', 100),     # 最小成交量
        ('warmup_period', 30),   # 预热期
    )
    
    def __init__(self):
        """初始化策略"""
        super().__init__()
        logger.info("="*50)
        logger.info("初始化双均线策略")
        logger.info(f"策略参数：")
        logger.info(f"快线周期: {self.params.fast_period}")
        logger.info(f"慢线周期: {self.params.slow_period}")
        logger.info(f"ATR周期: {self.params.atr_period}")
        logger.info(f"风险系数: {self.params.risk_ratio}")
        logger.info(f"止损比例: {self.params.stop_loss}")
        logger.info(f"止盈比例: {self.params.take_profit}")
        logger.info(f"移动止损比例: {self.params.trailing_stop}")
        logger.info(f"最小成交量: {self.params.min_volume}")
        logger.info("="*50)
        
        # 计算指标
        for data in self.datas:
            logger.info(f"初始化{data._name}的技术指标")
            # 双均线
            self.fast_ma = bt.indicators.SMA(
                data,
                period=self.params.fast_period,
                plotname=f'FastMA_{self.params.fast_period}'
            )
            self.slow_ma = bt.indicators.SMA(
                data,
                period=self.params.slow_period,
                plotname=f'SlowMA_{self.params.slow_period}'
            )
            
            # 交叉信号
            self.crossover = bt.indicators.CrossOver(
                self.fast_ma,
                self.slow_ma,
                plotname='CrossOver'
            )
            
            # ATR
            self.atr = bt.indicators.ATR(
                data,
                period=self.params.atr_period,
                plotname='ATR'
            )
            
            # 成交量
            self.volume_ma = bt.indicators.SMA(
                data.volume,
                period=20,
                plotname='VolMA'
            )
    
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            logger.info(f'订单已提交/已接受 - {order.data._name}')
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                logger.info(
                    f'买入成交 - {order.data._name}\n'
                    f'价格: {order.executed.price:.2f}\n'
                    f'数量: {order.executed.size}\n'
                    f'金额: {order.executed.value:.2f}\n'
                    f'手续费: {order.executed.comm:.2f}'
                )
            else:
                logger.info(
                    f'卖出成交 - {order.data._name}\n'
                    f'价格: {order.executed.price:.2f}\n'
                    f'数量: {order.executed.size}\n'
                    f'金额: {order.executed.value:.2f}\n'
                    f'手续费: {order.executed.comm:.2f}'
                )
        elif order.status in [order.Canceled]:
            logger.warning(f'订单取消 - {order.data._name}')
        elif order.status in [order.Margin]:
            logger.warning(f'保证金不足 - {order.data._name}')
        elif order.status in [order.Rejected]:
            logger.warning(f'订单被拒绝 - {order.data._name}')
    
    def notify_trade(self, trade):
        """交易状态通知"""
        if trade.isclosed:
            logger.info(
                f'交易结束 - {trade.data._name}\n'
                f'毛利润: {trade.pnl:.2f}\n'
                f'净利润: {trade.pnlcomm:.2f}\n'
                f'收益率: {(trade.pnlcomm/trade.price)*100:.2f}%'
            )
    
    def _process_signals(self):
        """处理交易信号"""
        for data in self.datas:
            current_datetime = data.datetime.datetime(0)
            logger.info("-"*30)
            logger.info(f"处理 {data._name} 在 {current_datetime} 的信号")
            
            # 检查是否有足够的数据
            if len(data) < self.params.warmup_period:
                logger.info(f"数据预热中 ({len(data)}/{self.params.warmup_period})")
                return
                
            # 检查指标是否准备就绪
            if (np.isnan(self.fast_ma[0]) or 
                np.isnan(self.slow_ma[0]) or 
                np.isnan(self.atr[0])):
                logger.warning(f"{data._name} 指标未就绪")
                return
            
            # 打印当前市场状态
            logger.info(
                f"市场状态:\n"
                f"价格: {data.close[0]:.2f}\n"
                f"成交量: {data.volume[0]}\n"
                f"快线: {self.fast_ma[0]:.2f}\n"
                f"慢线: {self.slow_ma[0]:.2f}\n"
                f"ATR: {self.atr[0]:.2f}\n"
                f"交叉信号: {self.crossover[0]}"
            )
            
            # 获取当前持仓
            position = self.getposition(data)
            
            if position:
                logger.info(
                    f"当前持仓:\n"
                    f"数量: {position.size}\n"
                    f"成本: {position.price:.2f}\n"
                    f"市值: {position.size * data.close[0]:.2f}\n"
                    f"浮动盈亏: {((data.close[0]/position.price)-1)*100:.2f}%"
                )
            
            # 检查成交量
            if data.volume[0] < self.params.min_volume:
                if position:
                    logger.info(f"成交量不足 {data.volume[0]} < {self.params.min_volume}，执行平仓")
                    self.close(data=data)
                return
            
            # 无持仓时，检查买入信号
            if not position:
                if self.crossover > 0:  # 金叉
                    size = self._calculate_size(data)
                    if size > 0:
                        logger.info(
                            f"买入信号触发:\n"
                            f"原因: 快线上穿慢线\n"
                            f"买入数量: {size}\n"
                            f"当前价格: {data.close[0]:.2f}\n"
                            f"账户余额: {self.broker.getcash():.2f}"
                        )
                        self.buy(data=data, size=size)
            
            # 有持仓时，检查卖出信号
            else:
                # 死叉卖出
                if self.crossover < 0:
                    logger.info(f"死叉信号触发，执行平仓")
                    self.close(data=data)
                    return
                
                # 止损检查
                elif self._check_stop_loss(data, position):
                    logger.info(
                        f"止损信号触发:\n"
                        f"持仓成本: {position.price:.2f}\n"
                        f"当前价格: {data.close[0]:.2f}\n"
                        f"亏损比例: {((data.close[0]/position.price)-1)*100:.2f}%"
                    )
                    self.close(data=data)
                    return
                
                # 止盈检查
                elif self._check_take_profit(data, position):
                    logger.info(
                        f"止盈信号触发:\n"
                        f"持仓成本: {position.price:.2f}\n"
                        f"当前价格: {data.close[0]:.2f}\n"
                        f"盈利比例: {((data.close[0]/position.price)-1)*100:.2f}%"
                    )
                    self.close(data=data)
                    return
                
                # 移动止损检查
                elif self._check_trailing_stop(data, position):
                    highest = self._positions[data._name].get('highest', data.close[0])
                    logger.info(
                        f"移动止损触发:\n"
                        f"最高价: {highest:.2f}\n"
                        f"当前价格: {data.close[0]:.2f}\n"
                        f"回撤比例: {((data.close[0]/highest)-1)*100:.2f}%"
                    )
                    self.close(data=data)
                    return
    @classmethod
    def get_default_params(cls) -> Dict[str, Dict[str, Any]]:
        """获取默认参数
        
        Returns:
            dict: 参数配置字典
        """
        return {
            "fast_period": {
                "display_name": "快线周期",
                "type": "int",
                "min": 5,
                "max": 20,
                "default": 10,
                "step": 1,
                "description": "短期移动平均线周期"
            },
            "slow_period": {
                "display_name": "慢线周期",
                "type": "int",
                "min": 20,
                "max": 60,
                "default": 30,
                "step": 1,
                "description": "长期移动平均线周期"
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
            "risk_ratio": {
                "display_name": "风险系数",
                "type": "float",
                "min": 0.01,
                "max": 0.05,
                "default": 0.02,
                "step": 0.01,
                "description": "单次交易风险系数"
            },
            "stop_loss": {
                "display_name": "止损比例",
                "type": "float",
                "min": 0.02,
                "max": 0.1,
                "default": 0.05,
                "step": 0.01,
                "description": "固定止损触发比例"
            },
            "take_profit": {
                "display_name": "止盈比例",
                "type": "float",
                "min": 0.05,
                "max": 0.3,
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
            },
            "min_volume": {
                "display_name": "最小成交量",
                "type": "int",
                "min": 100,
                "max": 10000,
                "default": 1000,
                "step": 100,
                "description": "最小成交量要求"
            },
            "warmup_period": {
                "display_name": "预热期",
                "type": "int",
                "min": 20,
                "max": 60,
                "default": 30,
                "step": 5,
                "description": "策略预热期，需要大于慢线周期"
            }
        }                