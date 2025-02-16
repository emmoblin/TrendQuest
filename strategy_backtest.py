import streamlit as st
from datetime import datetime
from typing import Dict, Any
from ui.backtest_form import render_backtest_form
from ui.backtest_results import display_results
from utils.stock_pool import StockPoolManager
from utils.log_init import get_logger
from backtest_engine import BacktestEngine

logger = get_logger(__name__)

def show_strategy_backtest():
    """显示策略回测界面"""
    try:
        current_time = datetime.strptime("2025-02-16 13:31:57", "%Y-%m-%d %H:%M:%S")
        current_user = "emmoblin"
        logger.info(f"Strategy backtest page accessed by {current_user}")
        
        st.title("策略回测")
        
        # 加载标的池管理器
        pool_manager = StockPoolManager()
        pools = pool_manager.get_all_pools()
        
        if not pools:
            st.warning("请先在标的池管理中创建并添加标的")
            return
        
        # 渲染回测设置表单并获取参数
        submitted, params = render_backtest_form()
        
        # 处理回测请求
        if submitted:
            if not params.get('strategy_code'):
                st.error("请选择交易策略")
                return
            
            if params['start_date'] >= params['end_date']:
                st.error("结束日期必须晚于开始日期")
                return
            
            # 获取选中标的池中的标的
            pool_symbols = pool_manager.get_pool_symbols(params['pool'])
            if not pool_symbols:
                st.warning(f"标的池 '{params['pool']}' 中没有标的")
                return
            
            try:
                with st.spinner("正在进行回测..."):
                    # 显示进度
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # 创建回测引擎
                    engine = BacktestEngine(
                        strategy_name=params['strategy_code'],
                        symbols=list(pool_symbols.keys()),
                        start_date=datetime.combine(params['start_date'], datetime.min.time()),
                        end_date=datetime.combine(params['end_date'], datetime.max.time()),
                        initial_cash=params['initial_cash'],
                        commission=0.0003  # 默认手续费率
                    )
                    
                    # 设置策略参数
                    engine.set_strategy_params(params['strategy_params'])
                    
                    # 运行回测
                    results = engine.run()
                    
                    # 显示回测结果
                    display_results(results, pool_symbols, params)
                    
                    # 记录回测完成
                    logger.info(
                        f"Backtest completed for {params['strategy_code']} "
                        f"by {current_user}"
                    )
            
            except Exception as e:
                st.error(f"回测过程中出现错误: {str(e)}")
                logger.exception("回测失败")
    
    except Exception as e:
        st.error(f"页面加载失败: {str(e)}")
        logger.error("页面加载失败", exc_info=True)

def display_backtest_help():
    """显示回测帮助信息"""
    with st.expander("回测说明", expanded=False):
        st.markdown("""
        ### 回测指标说明
        
        1. **收益指标**
           - 总收益率：策略整体收益表现
           - 年化收益率：将总收益率转化为年度收益率
           - 超额收益：相对于基准的超额收益部分
        
        2. **风险指标**
           - 最大回撤：策略最大的回撤幅度
           - 夏普比率：年化超额收益与波动率的比值
           - 信息比率：超额收益与跟踪误差的比值
        
        3. **交易统计**
           - 交易次数：策略总共进行的交易次数
           - 胜率：盈利交易占总交易的比例
           - 平均盈利/亏损：每笔交易的平均盈亏
        
        ### 策略说明
        
        1. **资金管理**
           - 单个持仓的资金比例限制
           - 最大持仓数量限制
           - 考虑交易成本（手续费）
        
        2. **选股逻辑**
           - 基于技术指标的动态选股
           - 股票池轮动机制
           - 风险控制措施
        
        3. **注意事项**
           - 回测结果仅供参考，实盘交易可能存在滑点
           - 建议结合基本面分析
           - 注意风险控制和仓位管理
        """)

if __name__ == "__main__":
    show_strategy_backtest()