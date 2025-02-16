import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime

class Visualizer:
    """可视化组件"""
    
    def __init__(self):
        self.current_time = datetime.strptime("2025-02-15 18:49:36", "%Y-%m-%d %H:%M:%S")
    
    def create_equity_curve_chart(
        self,
        equity_curve: pd.DataFrame,
        trades_list: List[Dict[str, Any]]
    ) -> go.Figure:
        """创建权益曲线图"""
        fig = go.Figure()
        
        # 添加收盘价
        fig.add_trace(
            go.Scatter(
                x=equity_curve.index,
                y=equity_curve['close'],
                name='价格',
                line=dict(color='blue', width=1)
            )
        )
        
        # 添加账户价值
        fig.add_trace(
            go.Scatter(
                x=equity_curve.index,
                y=equity_curve['value'],
                name='账户价值',
                line=dict(color='green', width=1)
            )
        )
        
        # 添加交易点
        self._add_trade_markers(fig, trades_list)
        
        # 更新布局
        fig.update_layout(
            title='策略回测分析',
            xaxis_title='日期',
            yaxis_title='价格/价值',
            showlegend=True,
            hovermode='x unified'
        )
        
        return fig
    
    def create_pnl_distribution_chart(
        self,
        trades_list: List[Dict[str, Any]]
    ) -> go.Figure:
        """创建收益分布图"""
        pnls = [t['pnl'] for t in trades_list if t['type'] == 'sell']
        
        fig = go.Figure()
        fig.add_trace(
            go.Histogram(
                x=pnls,
                nbinsx=30,
                name='收益分布'
            )
        )
        
        fig.update_layout(
            title='收益分布',
            xaxis_title='收益',
            yaxis_title='频次'
        )
        
        return fig
    
    def _add_trade_markers(
        self,
        fig: go.Figure,
        trades_list: List[Dict[str, Any]]
    ):
        """添加交易标记"""
        buy_trades = [t for t in trades_list if t['type'] == 'buy']
        sell_trades = [t for t in trades_list if t['type'] == 'sell']
        
        if buy_trades:
            fig.add_trace(
                go.Scatter(
                    x=[datetime.strptime(t['date'], '%Y-%m-%d') for t in buy_trades],
                    y=[t['price'] for t in buy_trades],
                    mode='markers',
                    name='买入',
                    marker=dict(
                        symbol='triangle-up',
                        size=10,
                        color='red'
                    )
                )
            )
        
        if sell_trades:
            fig.add_trace(
                go.Scatter(
                    x=[datetime.strptime(t['date'], '%Y-%m-%d') for t in sell_trades],
                    y=[t['price'] for t in sell_trades],
                    mode='markers',
                    name='卖出',
                    marker=dict(
                        symbol='triangle-down',
                        size=10,
                        color='green'
                    )
                )
            )