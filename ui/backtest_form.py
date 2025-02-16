import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from strategies.strategy_factory import get_strategy, list_strategies, get_display_names
from utils.log_init import get_logger
from stock_pool_manager import StockPoolManager

logger = get_logger(__name__)

def render_backtest_form() -> Tuple[bool, Dict[str, Any]]:
    """渲染回测设置表单
    
    Returns:
        Tuple[bool, Dict[str, Any]]: (是否提交, 回测参数)
    """
    # 获取当前信息
    current_time = datetime.strptime("2025-02-16 13:28:26", "%Y-%m-%d %H:%M:%S")
    
    # 加载标的池
    pool_manager = StockPoolManager()
    pools = pool_manager.get_all_pools()
    
    with st.form("backtest_settings"):
        # === 基本设置 ===
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_pool = st.selectbox(
                "选择标的池",
                options=list(pools.keys()),
                help="选择要进行回测的标的池"
            )
        
        with col2:
            start_date = st.date_input(
                "回测开始日期",
                value=(current_time - timedelta(days=365)).date(),
                min_value=datetime(2010, 1, 1).date(),
                max_value=current_time.date(),
                help="回测起始日期"
            )
        
        with col3:
            end_date = st.date_input(
                "回测结束日期",
                value=current_time.date(),
                min_value=start_date,
                max_value=current_time.date(),
                help="回测结束日期"
            )
        
        # === 策略配置 ===
        st.subheader("策略配置")
        strategy_params = render_strategy_section()
        
        # === 资金配置 ===
        st.subheader("资金配置")
        initial_cash = st.number_input(
            "初始资金（元）",
            min_value=10000,
            max_value=10000000,
            value=1000000,
            step=10000,
            help="回测使用的初始资金金额"
        )
        
        # 提交按钮
        submitted = st.form_submit_button(
            "开始回测",
            type="primary",
            help="点击开始运行回测"
        )
        
        # 收集参数
        params = {
            "pool": selected_pool,
            "start_date": start_date,
            "end_date": end_date,
            "initial_cash": initial_cash,
            **strategy_params
        }
        
        return submitted, params

def render_strategy_section() -> Dict[str, Any]:
    """渲染策略选择和参数设置部分"""
    # 获取策略显示名称映射
    display_names = get_display_names()
    available_strategies = list_strategies()
    
    selected_strategy_name = st.selectbox(
        "选择策略",
        options=list(display_names.keys()),
        help="选择要使用的交易策略"
    )
    
    strategy_params = {}
    
    if selected_strategy_name:
        strategy_code = display_names[selected_strategy_name]
        strategy_info = available_strategies[strategy_code]
        
        # 显示策略描述
        st.info(strategy_info.description)
        
        try:
            # 获取策略类并获取默认参数
            strategy_class = get_strategy(strategy_code)
            default_params = strategy_class.get_default_params()
            
            # 创建参数设置界面
            params = {}
            param_cols = st.columns(len(default_params))
            
            for (param_name, param_info), col in zip(default_params.items(), param_cols):
                with col:
                    if param_info['type'] == 'float':
                        params[param_name] = st.number_input(
                            param_info['display_name'],
                            min_value=float(param_info['min']),
                            max_value=float(param_info['max']),
                            value=float(param_info['default']),
                            step=float(param_info['step']),
                            help=param_info['description']
                        )
                    elif param_info['type'] == 'int':
                        params[param_name] = st.number_input(
                            param_info['display_name'],
                            min_value=int(param_info['min']),
                            max_value=int(param_info['max']),
                            value=int(param_info['default']),
                            step=int(param_info['step']),
                            help=param_info['description']
                        )
                    else:
                        params[param_name] = st.text_input(
                            param_info['display_name'],
                            value=str(param_info['default']),
                            help=param_info['description']
                        )
            
            strategy_params = {
                "strategy_code": strategy_code,
                "strategy_params": params
            }
            
        except Exception as e:
            st.error(f"加载策略参数失败: {str(e)}")
            logger.error("Failed to load strategy parameters", exc_info=True)
            
    return strategy_params