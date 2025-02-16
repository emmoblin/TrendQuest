import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List
from utils.formatter import format_number
from utils.chart import create_summary_chart
from utils.log_init import get_logger

logger = get_logger(__name__)

def display_results(results: Dict[str, Any], pool_symbols: Dict[str, Dict], backtest_config: Dict[str, Any]):
    """显示回测结果"""
    if not results:
        st.error("回测执行失败，请查看日志获取详细信息")
        return
    
    st.subheader("回测结果分析")
    
    # 创建汇总数据
    summary_data = []
    
    # 显示每个交易标的的结果
    for symbol in pool_symbols:
        if symbol in results:
            display_symbol_result(symbol, results[symbol], pool_symbols[symbol], summary_data)
    
    # 显示汇总分析
    if summary_data:
        display_portfolio_analysis(summary_data, backtest_config)

def display_symbol_result(symbol: str, result: Dict[str, Any], symbol_info: Dict[str, Any], summary_data: List[Dict[str, Any]]):
    """显示单个交易标的的结果"""
    with st.expander(f"📊 {symbol} ({symbol_info['name']})", expanded=False):
        # 显示主要指标
        display_metrics(result)
        
        # 显示交易图表和记录
        display_trades(result)
        
        # 添加到汇总数据
        summary_data.append(create_summary_entry(symbol, symbol_info, result))

def display_metrics(result: Dict[str, Any]):
    """显示指标数据"""
    # 主要指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总收益率", format_number(result['return_rate'], True))
    
    with col2:
        st.metric("年化收益率", format_number(result['annual_return'], True))
    
    with col3:
        st.metric("最大回撤", format_number(result['max_drawdown'], True))
    
    with col4:
        st.metric("夏普比率", format_number(result['sharpe_ratio'], False))
    
    # 交易统计
    col5, col6, col7, col8 = st.columns(4)
    
    with col5:
        st.metric("交易次数", str(result['total_trades']))
    
    with col6:
        st.metric("胜率", format_number(result['win_rate'], True))
    
    with col7:
        st.metric("平均盈利", format_number(result.get('avg_win', 0), True))
    
    with col8:
        st.metric("平均亏损", format_number(result.get('avg_loss', 0), True))

def display_trades(result: Dict[str, Any]):
    """显示交易图表和记录"""
    if result.get('chart'):
        st.plotly_chart(result['chart'], use_container_width=True)
    
    if result.get('trades'):
        st.subheader("交易记录")
        trades_df = pd.DataFrame(result['trades'])
        st.dataframe(trades_df, use_container_width=True)

def display_portfolio_analysis(summary_data: List[Dict[str, Any]], backtest_config: Dict[str, Any]):
    """显示投资组合分析"""
    st.subheader("投资组合汇总分析")
    
    # 创建汇总DataFrame
    summary_df = pd.DataFrame(summary_data)
    
    # 显示组合指标
    display_portfolio_metrics(summary_df)
    
    # 显示汇总图表
    st.plotly_chart(create_summary_chart(summary_df), use_container_width=True)
    
    # 提供数据下载
    provide_data_download(summary_df, backtest_config)

def create_summary_entry(symbol: str, symbol_info: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """创建汇总数据条目"""
    return {
        '股票代码': symbol,
        '股票名称': symbol_info['name'],
        '总收益率': result['return_rate'],
        '年化收益率': result['annual_return'],
        '最大回撤': result['max_drawdown'],
        '夏普比率': result['sharpe_ratio'],
        '交易次数': result['total_trades'],
        '胜率': result['win_rate']
    }

def display_portfolio_metrics(summary_df: pd.DataFrame):
    """显示组合指标"""
    portfolio_metrics = calculate_portfolio_metrics(summary_df)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("组合总收益率", format_number(portfolio_metrics['总收益率'], True))
        st.metric("组合最大回撤", format_number(portfolio_metrics['最大回撤'], True))
    
    with col2:
        st.metric("组合年化收益率", format_number(portfolio_metrics['年化收益率'], True))
        st.metric("平均夏普比率", format_number(portfolio_metrics['平均夏普比率'], False))
    
    with col3:
        st.metric("总交易次数", str(portfolio_metrics['总交易次数']))
        st.metric("平均胜率", format_number(portfolio_metrics['平均胜率'], True))

def calculate_portfolio_metrics(summary_df: pd.DataFrame) -> Dict[str, float]:
    """计算组合指标"""
    return {
        '总收益率': summary_df['总收益率'].mean(),
        '年化收益率': summary_df['年化收益率'].mean(),
        '最大回撤': summary_df['最大回撤'].max(),
        '平均夏普比率': summary_df['夏普比率'].mean(),
        '总交易次数': summary_df['交易次数'].sum(),
        '平均胜率': summary_df['胜率'].mean()
    }

def provide_data_download(summary_df: pd.DataFrame, backtest_config: Dict[str, Any]):
    """提供数据下载功能"""
    col1, col2 = st.columns(2)
    
    with col1:
        # 导出CSV
        csv = summary_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="下载CSV格式结果",
            data=csv,
            file_name=f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        try:
            # 导出Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # 写入汇总数据
                summary_df.to_excel(writer, sheet_name='汇总数据', index=False)
                
                # 写入策略参数
                pd.DataFrame([backtest_config['strategy_params']]).to_excel(
                    writer,
                    sheet_name='策略参数',
                    index=False
                )
                
                # 写入回测配置
                config_data = {
                    '配置项': ['回测开始日期', '回测结束日期', '初始资金', '选择策略', '标的池'],
                    '配置值': [
                        backtest_config['start_date'].strftime('%Y-%m-%d'),
                        backtest_config['end_date'].strftime('%Y-%m-%d'),
                        format_number(backtest_config['initial_cash'], False),
                        backtest_config['strategy_code'],
                        backtest_config['pool']
                    ]
                }
                pd.DataFrame(config_data).to_excel(
                    writer,
                    sheet_name='回测配置',
                    index=False
                )
            
            excel_data = output.getvalue()
            st.download_button(
                label="下载Excel格式结果",
                data=excel_data,
                file_name=f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.warning(f"Excel导出失败: {str(e)}")