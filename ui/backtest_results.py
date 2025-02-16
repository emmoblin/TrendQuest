import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
from typing import Dict, Any
import json

def display_results(results: Dict[str, Any], symbols: Dict[str, Dict], params: Dict[str, Any]):
    """显示回测结果
    
    Args:
        results: 回测结果字典
        symbols: 交易标的信息
        params: 回测参数
    """
    try:
        # 显示回测信息
        st.subheader("回测信息")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**策略:** {params['strategy_code']}")
            st.markdown(f"**初始资金:** {params['initial_cash']:,.2f}")
            
        with col2:
            st.markdown(f"**开始日期:** {params['start_date']}")
            st.markdown(f"**结束日期:** {params['end_date']}")
            
        with col3:
            st.markdown(f"**交易标的:** {len(symbols)}个")
            st.markdown(f"**交易次数:** {results['summary']['trade_count']}")
        
        # 显示关键指标
        st.subheader("策略绩效")
        col4, col5, col6, col7 = st.columns(4)
        
        with col4:
            st.metric(
                "总收益率",
                f"{results['summary']['total_return']*100:.2f}%",
                delta=f"{(results['summary']['total_return'] - results.get('benchmark_return', 0))*100:.2f}%"
            )
            
        with col5:
            st.metric(
                "夏普比率",
                f"{results['summary']['sharpe_ratio']:.2f}"
            )
            
        with col6:
            st.metric(
                "最大回撤",
                f"{results['summary']['max_drawdown']*100:.2f}%"
            )
            
        with col7:
            st.metric(
                "胜率",
                f"{results['summary']['win_rate']*100:.2f}%"
            )
        
        # 创建多子图
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=('累计收益', '回撤', '每日交易量'),
            row_heights=[0.5, 0.25, 0.25]
        )
        
        # 转换收益数据为DataFrame
        returns_df = pd.DataFrame.from_dict(results['returns'], orient='index')
        
        # 1. 累计收益曲线
        fig.add_trace(
            go.Scatter(
                x=returns_df.index,
                y=returns_df['strategy_cum_returns'],
                name='策略收益',
                line=dict(color='rgb(49,130,189)')
            ),
            row=1, col=1
        )
        
        if 'benchmark_cum_returns' in returns_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=returns_df.index,
                    y=returns_df['benchmark_cum_returns'],
                    name='沪深300',
                    line=dict(color='rgb(189,189,189)')
                ),
                row=1, col=1
            )
        
        # 2. 回撤曲线
        drawdown = (returns_df['strategy_cum_returns'].cummax() - returns_df['strategy_cum_returns'])
        fig.add_trace(
            go.Scatter(
                x=returns_df.index,
                y=-drawdown*100,
                name='回撤',
                fill='tonexty',
                line=dict(color='rgb(255,73,73)')
            ),
            row=2, col=1
        )
        
        # 3. 交易量
        if 'trades' in results:
            trades_df = pd.DataFrame(results['trades'])
            daily_volume = trades_df.groupby(pd.to_datetime(trades_df['datetime']).dt.date)['size'].sum()
            fig.add_trace(
                go.Bar(
                    x=daily_volume.index,
                    y=daily_volume.values,
                    name='交易量',
                    marker_color='rgb(49,130,189)'
                ),
                row=3, col=1
            )
        
        # 更新布局
        fig.update_layout(
            height=800,
            showlegend=True,
            title_text="回测详细分析",
            xaxis3_title="日期",
            yaxis_title="累计收益",
            yaxis2_title="回撤(%)",
            yaxis3_title="交易量(股)",
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 显示交易日志
        if results.get('trades'):
            st.subheader("交易日志")
            trades_df = pd.DataFrame(results['trades'])
            trades_df['datetime'] = pd.to_datetime(trades_df['datetime'])
            trades_df['profit'] = trades_df['pnl'].apply(lambda x: f"{x:,.2f}")
            trades_df['return'] = trades_df['return'].apply(lambda x: f"{x*100:.2f}%")
            
            st.dataframe(
                trades_df[[
                    'datetime', 'symbol', 'type',
                    'size', 'price', 'profit', 'return'
                ]].sort_values('datetime', ascending=False),
                hide_index=True
            )
        
        # 显示持仓信息
        if results.get('positions'):
            st.subheader("当前持仓")
            positions_df = pd.DataFrame(results['positions'])
            positions_df['value'] = positions_df['value'].apply(lambda x: f"{x:,.2f}")
            st.dataframe(positions_df, hide_index=True)
        
        # 显示详细统计
        st.subheader("详细统计")
        col8, col9 = st.columns(2)
        
        with col8:
            st.markdown("**收益指标**")
            stats_df = pd.DataFrame({
                '指标': [
                    '总收益率',
                    '年化收益率',
                    '夏普比率',
                    '最大回撤',
                    '最大回撤持续期',
                    '收益波动率'
                ],
                '策略': [
                    f"{results['summary']['total_return']*100:.2f}%",
                    f"{(1+results['summary']['total_return'])**(365/len(returns_df))-1:.2f}%",
                    f"{results['summary']['sharpe_ratio']:.2f}",
                    f"{results['summary']['max_drawdown']*100:.2f}%",
                    f"{results['summary']['max_drawdown_period']}天",
                    f"{np.std(returns_df['strategy_returns'])*np.sqrt(252)*100:.2f}%"
                ]
            })
            st.dataframe(stats_df, hide_index=True)
        
        with col9:
            st.markdown("**交易指标**")
            trade_df = pd.DataFrame({
                '指标': [
                    '交易次数',
                    '胜率',
                    '盈亏比',
                    '平均收益',
                    '最大单笔收益',
                    '最大单笔亏损'
                ],
                '数值': [
                    results['summary']['trade_count'],
                    f"{results['summary']['win_rate']*100:.2f}%",
                    f"{results['summary']['profit_factor']:.2f}",
                    f"{results['summary']['avg_trade_return']*100:.2f}%",
                    f"{max([t['return'] for t in results['trades']], default=0)*100:.2f}%",
                    f"{min([t['return'] for t in results['trades']], default=0)*100:.2f}%"
                ]
            })
            st.dataframe(trade_df, hide_index=True)
        
        # 显示日志文件链接
        if 'log_file' in results:
            with open(results['log_file'], 'r', encoding='utf-8') as f:
                log_data = json.load(f)
                
            st.subheader("策略执行日志")
            for log in log_data['logs']:
                if log['level'] == 'ERROR':
                    st.error(f"{log['time']} - {log['message']}")
                elif log['level'] == 'WARNING':
                    st.warning(f"{log['time']} - {log['message']}")
                else:
                    st.info(f"{log['time']} - {log['message']}")
        
    except Exception as e:
        st.error(f"结果显示失败: {str(e)}")