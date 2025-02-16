import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime

class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.current_time = datetime.strptime("2025-02-15 18:49:36", "%Y-%m-%d %H:%M:%S")
    
    def analyze_trades(
        self,
        trades_list: List[Dict[str, Any]],
        equity_curve: pd.DataFrame
    ) -> Dict[str, Any]:
        """分析交易表现"""
        if not trades_list or equity_curve.empty:
            return {}
        
        # 计算基础指标
        total_trades = len([t for t in trades_list if t['type'] == 'sell'])
        won_trades = len([t for t in trades_list if t['type'] == 'sell' and t['pnl'] > 0])
        lost_trades = len([t for t in trades_list if t['type'] == 'sell' and t['pnl'] <= 0])
        
        # 计算收益指标
        total_pnl = sum(t['pnl'] for t in trades_list if t['type'] == 'sell')
        win_rate = won_trades / total_trades if total_trades > 0 else 0
        
        # 计算回撤
        equity = equity_curve['value']
        max_drawdown = self._calculate_max_drawdown(equity)
        
        # 计算夏普比率
        returns = equity.pct_change().dropna()
        sharpe = self._calculate_sharpe_ratio(returns)
        
        return {
            'total_trades': total_trades,
            'won_trades': won_trades,
            'lost_trades': lost_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'avg_trade_pnl': total_pnl / total_trades if total_trades > 0 else 0,
            'profit_factor': self._calculate_profit_factor(trades_list)
        }
    
    def _calculate_max_drawdown(self, equity: pd.Series) -> float:
        """计算最大回撤"""
        rolling_max = equity.expanding().max()
        drawdowns = (equity - rolling_max) / rolling_max
        return abs(drawdowns.min())
    
    def _calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.03,
        periods: int = 252
    ) -> float:
        """计算夏普比率"""
        excess_returns = returns - risk_free_rate/periods
        return np.sqrt(periods) * (excess_returns.mean() / excess_returns.std())
    
    def _calculate_profit_factor(self, trades_list: List[Dict[str, Any]]) -> float:
        """计算盈亏比"""
        gross_profit = sum(t['pnl'] for t in trades_list if t['type'] == 'sell' and t['pnl'] > 0)
        gross_loss = abs(sum(t['pnl'] for t in trades_list if t['type'] == 'sell' and t['pnl'] <= 0))
        return gross_profit / gross_loss if gross_loss > 0 else float('inf')