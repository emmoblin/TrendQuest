import streamlit as st
import pandas as pd
import datetime
import logging
import yaml
from pathlib import Path
from stock_pool_manager import show_pool_management
from strategy_backtest import show_strategy_backtest
from utils import utils_manager, UtilsFactory
from utils.log_init import get_logger, log_manager
import atexit


# 初始化工具管理器
utils_manager = UtilsFactory.get_instance(
    config_dir="config",
    log_dir="logs",
    cache_dir="cache",
    log_level="INFO"
)

# 注册清理函数
atexit.register(utils_manager.cleanup)

# 获取日志器
logger = get_logger(__name__)

# 系统配置
SYSTEM_CONFIG = {
    'version': '1.0.0',
    'current_time': datetime.datetime.strptime("2025-02-15 18:13:27", "%Y-%m-%d %H:%M:%S"),
    'current_user': 'emmoblin',
    'system_name': '量化交易回测系统',
    'data_dir': 'data',
    'config_dir': 'config',
    'logs_dir': 'logs',
    'default_settings': {
        'theme': '默认',
        'data_cache_days': 7,
        'commission_rate': 0.0003,
        'slippage': 0.0002,
        'max_positions': 5,
        'position_size': 0.2
    }
}

def ensure_directories():
    """确保必要的目录结构存在"""
    directories = [
        Path(SYSTEM_CONFIG['data_dir']) / 'stock_data',
        Path(SYSTEM_CONFIG['config_dir']),
        Path(SYSTEM_CONFIG['logs_dir'])
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        if directory.name == 'stock_data':
            # 添加 .gitkeep 文件以保持目录结构
            (directory / '.gitkeep').touch(exist_ok=True)

def load_config():
    """加载配置文件"""
    config_file = Path(SYSTEM_CONFIG['config_dir']) / 'config.yaml'
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                if user_config is None:
                    user_config = {}
                return {**SYSTEM_CONFIG['default_settings'], **user_config}
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return SYSTEM_CONFIG['default_settings']
    return SYSTEM_CONFIG['default_settings']

def save_config(config):
    """保存配置文件"""
    config_file = Path(SYSTEM_CONFIG['config_dir']) / 'config.yaml'
    
    try:
        # 添加更新信息
        config['last_modified'] = SYSTEM_CONFIG['current_time'].strftime("%Y-%m-%d %H:%M:%S")
        config['modified_by'] = SYSTEM_CONFIG['current_user']
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)
        return True
    except Exception as e:
        logger.error(f"保存配置文件失败: {str(e)}")
        return False

def init_session_state():
    """初始化会话状态"""
    if 'initialized' not in st.session_state:
        st.session_state.update({
            'initialized': True,
            'user': SYSTEM_CONFIG['current_user'],
            'current_time': SYSTEM_CONFIG['current_time'],
            'config': load_config(),
            'last_action': None,
            'last_error': None
        })

def show_header():
    """显示页面头部"""
    st.sidebar.title(SYSTEM_CONFIG['system_name'])
    st.sidebar.markdown("---")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.markdown(f"**用户:** {st.session_state.user}")
    with col2:
        st.markdown(f"**时间:** {st.session_state.current_time.strftime('%H:%M:%S')}")
    
    st.sidebar.markdown(f"**日期:** {st.session_state.current_time.strftime('%Y-%m-%d')}")
    
    # 显示系统信息
    with st.sidebar.expander("系统信息", expanded=False):
        st.markdown(f"**版本:** {SYSTEM_CONFIG['version']}")
        st.markdown(f"**运行环境:** Streamlit")
        st.markdown(f"**开发者:** {SYSTEM_CONFIG['current_user']}")

def show_settings():
    """显示设置页面"""
    st.title("系统设置")
    
    config = st.session_state.config
    
    with st.form("settings_form"):
        # 基本设置
        st.subheader("基本设置")
        col1, col2 = st.columns(2)
        
        with col1:
            theme = st.selectbox(
                "界面主题",
                options=["默认", "暗色", "浅色"],
                index=["默认", "暗色", "浅色"].index(config.get('theme', '默认')),
                help="选择界面显示主题"
            )
            
            data_cache = st.number_input(
                "数据缓存天数",
                min_value=1,
                max_value=30,
                value=config.get('data_cache_days', 7),
                help="历史数据缓存保存天数"
            )
        
        with col2:
            commission_rate = st.number_input(
                "默认手续费率",
                min_value=0.0,
                max_value=0.01,
                value=config.get('commission_rate', 0.0003),
                format="%.4f",
                help="交易手续费率"
            )
            
            slippage = st.number_input(
                "默认滑点",
                min_value=0.0,
                max_value=0.01,
                value=config.get('slippage', 0.0002),
                format="%.4f",
                help="交易滑点设置"
            )
        
        # 策略设置
        st.subheader("策略默认设置")
        col3, col4 = st.columns(2)
        
        with col3:
            max_positions = st.number_input(
                "最大持仓数",
                min_value=1,
                max_value=10,
                value=config.get('max_positions', 5),
                help="策略默认最大持仓数量"
            )
        
        with col4:
            position_size = st.number_input(
                "默认持仓比例",
                min_value=0.1,
                max_value=1.0,
                value=config.get('position_size', 0.2),
                format="%.2f",
                help="单个持仓的默认资金比例"
            )
        
        # 保存按钮
        submitted = st.form_submit_button("保存设置", type="primary")
        
        if submitted:
            new_config = {
                'theme': theme,
                'data_cache_days': data_cache,
                'commission_rate': commission_rate,
                'slippage': slippage,
                'max_positions': max_positions,
                'position_size': position_size
            }
            
            if save_config(new_config):
                st.session_state.config = new_config
                st.success("设置已更新！")
                st.rerun()
            else:
                st.error("保存设置失败！")
    
    # 显示当前配置
    with st.expander("当前配置", expanded=False):
        st.json(config)

def main():
    """主函数"""
    try:
        # 确保目录结构
        ensure_directories()
        
        # 设置页面
        st.set_page_config(
            page_title=SYSTEM_CONFIG['system_name'],
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://github.com/emmoblin/quant-trading-system',
                'Report a bug': "https://github.com/emmoblin/quant-trading-system/issues",
                'About': f"""
                # {SYSTEM_CONFIG['system_name']}
                
                Version: {SYSTEM_CONFIG['version']}
                
                Developer: {SYSTEM_CONFIG['current_user']}
                
                Last Updated: {SYSTEM_CONFIG['current_time'].strftime('%Y-%m-%d %H:%M:%S')}
                """
            }
        )
        
        # 初始化会话状态
        init_session_state()
        
        # 显示头部信息
        show_header()
        
        # 侧边栏导航
        nav_selection = st.sidebar.radio(
            "功能导航",
            ["策略回测", "标的池管理", "系统设置"]
        )
        
        # 显示版权信息
        st.sidebar.markdown("---")
        st.sidebar.markdown(
            f"© 2024-{SYSTEM_CONFIG['current_time'].year} {SYSTEM_CONFIG['system_name']}. "
            f"All rights reserved."
        )
        
        # 根据导航选择显示页面
        if nav_selection == "策略回测":
            show_strategy_backtest()
        elif nav_selection == "标的池管理":
            show_pool_management()
        else:
            show_settings()
        
    except Exception as e:
        logger.exception("系统运行错误")
        st.error(f"系统错误: {str(e)}")
        
        with st.expander("错误详情", expanded=False):
            st.code(f"{type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    main()