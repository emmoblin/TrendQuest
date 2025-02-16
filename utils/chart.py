import plotly.graph_objects as go
import pandas as pd
from typing import Dict, Any

def create_summary_chart(summary_df: pd.DataFrame) -> go.Figure:
    """创建汇总分析图表
    
    Args:
        summary_df: 包含汇总数据的DataFrame
    
    Returns:
        plotly图表对象
    """
    fig = go.Figure()
    
    # 添加收益率柱状图
    fig.add_trace(go.Bar(
        name='总收益率',
        x=summary_df['股票代码'],
        y=summary_df['总收益率'],
        text=summary_df['总收益率'].apply(lambda x: f"{x*100:.2f}%"),
        textposition='auto',
    ))
    
    # 添加最大回撤折线图
    fig.add_trace(go.Scatter(
        name='最大回撤',
        x=summary_df['股票代码'],
        y=summary_df['最大回撤'],
        mode='lines+markers',
        yaxis='y2'
    ))
    
    # 更新布局
    fig.update_layout(
        title='收益与风险分析',
        xaxis_title='交易标的',
        yaxis_title='收益率',
        yaxis2=dict(
            title='最大回撤',
            overlaying='y',
            side='right'
        ),
        barmode='group'
    )
    
    return fig