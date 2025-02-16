import backtrader as bt
from typing import Dict, Any
from datetime import datetime
from utils import utils_manager
from utils.log_init import get_logger

logger = get_logger(__name__)

class BaseStrategy(bt.Strategy):
    """策略基类"""
    
    def __init__(self):
        super().__init__()
        self.current_time = datetime.strptime("2025-02-16 01:43:56", "%Y-%m-%d %H:%M:%S")
        self.current_user = "emmoblin"
        
        # 获取配置
        strategy_config = utils_manager.config.get_config().get('trading', {})
        
        # 设置风险参数
        self.max_position_size = strategy_config.get('max_position_size', 0.2)
        self.max_drawdown = strategy_config.get('max_drawdown', 0.1)
        self.stop_loss = strategy_config.get('stop_loss', 0.05)
        self.trailing_stop = strategy_config.get('trailing_stop', 0.02)
        
        # 记录交易和持仓
        self.trades = []
        self.positions = {}
        
        # 设置技术指标
        self.setup_indicators()
    
    def setup_indicators(self):
        """设置技术指标"""
        pass
    
    def log(self, txt: str, dt=None):
        """记录日志"""
        dt = dt or self.datas[0].datetime.date(0)
        logger.info(f'{dt.isoformat()} {txt}')
    
    def notify_order(self, order):
        """订单状态更新通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'买入执行 价格: {order.executed.price:.2f}, '
                    f'数量: {order.executed.size}, '
                    f'手续费: {order.executed.comm:.2f}'
                )
            else:
                self.log(
                    f'卖出执行 价格: {order.executed.price:.2f}, '
                    f'数量: {order.executed.size}, '
                    f'手续费: {order.executed.comm:.2f}'
                )
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单取消/保证金不足/拒绝')
    
    def notify_trade(self, trade):
        """交易状态更新通知"""
        if not trade.isclosed:
            return
        
        self.log(f'交易利润, 总额: {trade.pnl:.2f}, 净额: {trade.pnlcomm:.2f}')
        
        # 记录交易
        self.trades.append({
            'date': self.data.datetime.date(0).strftime('%Y-%m-%d'),
            'type': 'sell',
            'price': trade.price,
            'size': trade.size,
            'pnl': trade.pnl,
            'pnlcomm': trade.pnlcomm,
            'commission': trade.commission
        })
    
    def get_position_size(self, price: float) -> int:
        """计算开仓数量"""
        cash = self.broker.getcash()
        size = int(cash * 0.1 / price)  # 默认使用10%资金开仓
        return size - (size % 100)  # 向下取整到100的倍数
    
    def get_trading_stats(self) -> Dict[str, Any]:
        """获取交易统计数据"""
        return {
            'total_trades': len(self.trades),
            'winning_trades': len([t for t in self.trades if t['pnl'] > 0]),
            'losing_trades': len([t for t in self.trades if t['pnl'] <= 0]),
            'total_pnl': sum(t['pnl'] for t in self.trades),
            'total_commission': sum(t['commission'] for t in self.trades)
        }