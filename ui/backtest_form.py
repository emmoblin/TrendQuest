import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from strategies.strategy_factory import get_strategy, list_strategies, get_display_names
from utils.log_init import get_logger
from stock_pool_manager import StockPoolManager

logger = get_logger(__name__)

def render_backtest_form() -> Tuple[bool, Dict[str, Any]]:
    """渲染回测表单
    
    Returns:
        (submitted, params) 元组:
            submitted: 表单是否提交
            params: 回测参数字典
    """
    try:
        with st.form("backtest_form"):
            # 获取当前时间
            current_time = datetime.strptime("2025-02-16 16:40:16", "%Y-%m-%d %H:%M:%S")
            
            # 获取股票池
            pool_manager = StockPoolManager()
            pools = pool_manager.get_all_pools()
            
            # 基本参数
            col1, col2, col3 = st.columns(3)
            
            with col1:
                pool = st.selectbox(
                    "选择股票池",
                    options=list(pools.keys()),
                    help="选择要回测的股票池"
                )
            
            with col2:
                start_date = st.date_input(
                    "开始日期",
                    value=current_time.date() - timedelta(days=365),
                    help="回测起始日期"
                )
            
            with col3:
                end_date = st.date_input(
                    "结束日期",
                    value=current_time.date(),
                    help="回测结束日期"
                )
            
            # 策略参数
            strategy_params = render_strategy_section()
            
            # 资金参数
            col4, col5 = st.columns(2)
            
            with col4:
                initial_cash = st.number_input(
                    "初始资金",
                    min_value=1000,
                    max_value=10000000,
                    value=100000,
                    step=1000,
                    help="回测初始资金"
                )
            
            submitted = st.form_submit_button("开始回测")
            
            params = {
                "pool": pool,
                "start_date": start_date,
                "end_date": end_date,
                "initial_cash": initial_cash,
                **strategy_params
            }
            
            return submitted, params
            
    except Exception as e:
        logger.error("Failed to render backtest form", exc_info=True)
        st.error(f"表单加载失败: {str(e)}")
        return False, {}

def render_strategy_section() -> Dict[str, Any]:
    """渲染策略选择和参数部分
    
    Returns:
        策略参数字典
    """
    try:
        # 获取可用策略
        available_strategies = list_strategies()
        strategy_names = {info["name"]: code for code, info in available_strategies.items()}
        
        # 策略选择
        strategy_name = st.selectbox(
            "选择策略",
            options=list(strategy_names.keys()),
            help="选择要使用的交易策略"
        )
        
        # 获取策略代码
        strategy_code = strategy_names[strategy_name]
        strategy_info = available_strategies[strategy_code]
        
        # 显示策略说明
        st.markdown(f"**策略说明:** {strategy_info['description']}")
        
        # 获取策略类
        strategy_class = get_strategy(strategy_code)
        
        try:
            # 获取默认参数
            default_params = strategy_class.get_default_params()
            
            # 创建参数输入
            st.subheader("策略参数")
            param_values = {}
            
            # 根据参数类型创建不同的输入控件
            for param_name, param_info in default_params.items():
                param_type = param_info["type"]
                
                if param_type == "float":
                    value = st.number_input(
                        param_info["display_name"],
                        min_value=float(param_info["min"]),
                        max_value=float(param_info["max"]),
                        value=float(param_info["default"]),
                        step=float(param_info["step"]),
                        help=param_info["description"]
                    )
                elif param_type == "int":
                    value = st.number_input(
                        param_info["display_name"],
                        min_value=int(param_info["min"]),
                        max_value=int(param_info["max"]),
                        value=int(param_info["default"]),
                        step=int(param_info["step"]),
                        help=param_info["description"]
                    )
                else:  # string
                    value = st.text_input(
                        param_info["display_name"],
                        value=str(param_info["default"]),
                        help=param_info["description"]
                    )
                
                param_values[param_name] = value
            
            return {
                "strategy_code": strategy_code,
                "strategy_params": param_values
            }
            
        except Exception as e:
            logger.error("Failed to load strategy parameters", exc_info=True)
            st.error(f"策略参数加载失败: {str(e)}")
            return {
                "strategy_code": strategy_code,
                "strategy_params": {}
            }
            
    except Exception as e:
        logger.error("Failed to render strategy section", exc_info=True)
        st.error(f"策略选择加载失败: {str(e)}")
        return {}