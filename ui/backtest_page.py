import streamlit as st
from datetime import datetime
from typing import Dict, Any
from ui.backtest_form import render_backtest_form
from ui.backtest_results import display_results
from ui.backtest_help import display_backtest_help
from stock_pool_manager import StockPoolManager
from utils.log_init import get_logger
from backtest_engine import BacktestEngine

logger = get_logger(__name__)

class BacktestPage:
    """回测页面类"""
    
    def __init__(self):
        self.current_time = datetime.strptime("2025-02-16 14:50:20", "%Y-%m-%d %H:%M:%S")
        self.current_user = "emmoblin"
        self.pool_manager = StockPoolManager()
    
    def render(self):
        """渲染回测页面"""
        try:
            st.title("策略回测")
            
            # 检查标的池
            pools = self.pool_manager.get_all_pools()
            if not pools:
                st.warning("请先在标的池管理中创建并添加标的")
                return
            
            # 渲染回测表单
            submitted, params = render_backtest_form()
            
            # 处理回测请求
            if submitted:
                self._handle_backtest(params)
            
            # 显示帮助信息
            display_backtest_help()
                
        except Exception as e:
            st.error(f"页面加载失败: {str(e)}")
            logger.error("页面加载失败", exc_info=True)
    
    def _handle_backtest(self, params: Dict[str, Any]):
        """处理回测请求"""
        try:
            # 参数验证
            if not self._validate_params(params):
                return
            
            # 获取标的池数据
            pool_symbols = self.pool_manager.get_pool_symbols(params['pool'])
            if not pool_symbols:
                st.warning(f"标的池 '{params['pool']}' 中没有标的")
                return
            
            # 执行回测
            with st.spinner("正在进行回测..."):
                results = self._run_backtest(params, pool_symbols)
                if results:
                    display_results(results, pool_symbols, params)
                    logger.info(
                        f"Backtest completed for {params['strategy_code']} "
                        f"by {self.current_user}"
                    )
        
        except Exception as e:
            st.error(f"回测过程中出现错误: {str(e)}")
            logger.exception("回测失败")
    
    def _validate_params(self, params: Dict[str, Any]) -> bool:
        """验证回测参数"""
        if not params.get('strategy_code'):
            st.error("请选择交易策略")
            return False
        
        if params['start_date'] >= params['end_date']:
            st.error("结束日期必须晚于开始日期")
            return False
        
        return True
    
    def _run_backtest(self, params: Dict[str, Any], pool_symbols: Dict[str, Dict]) -> Dict[str, Any]:
        """运行回测"""
        try:
            # 创建进度条
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
            
            # 定义进度回调
            def update_progress(progress: float, status: str):
                progress_bar.progress(progress)
                status_text.text(status)
            
            # 设置进度回调
            engine.progress_callback = update_progress
            
            # 运行回测
            return engine.run()
            
        except Exception as e:
            logger.error("回测执行失败", exc_info=True)
            return None