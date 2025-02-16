import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional
from ui.backtest_page import BacktestPage
from utils.log_init import get_logger
import sys
import os

# 设置日志记录器
logger = get_logger(__name__)

class TrendQuestApp:
    """TrendQuest量化交易系统"""
    
    def __init__(self):
        """初始化应用"""
        self.current_time = datetime.strptime("2025-02-16 15:24:11", "%Y-%m-%d %H:%M:%S")
        self.current_user = "emmoblin"
        self._configure_app()
        self._init_session_state()
    
    def _configure_app(self):
        """配置Streamlit应用"""
        st.set_page_config(
            page_title="TrendQuest量化交易系统",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # 设置主题
        st.markdown("""
        <style>
        .main {
            max-width: 1200px;
            padding: 1rem;
        }
        .stButton>button {
            width: 100%;
        }
        .app-header {
            text-align: center;
            color: #1f77b4;
            padding: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _init_session_state(self):
        """初始化会话状态"""
        if 'user' not in st.session_state:
            st.session_state.user = self.current_user
        if 'last_access' not in st.session_state:
            st.session_state.last_access = self.current_time
        if 'page' not in st.session_state:
            st.session_state.page = "回测"
    
    def render_sidebar(self):
        """渲染侧边栏"""
        with st.sidebar:
            # 使用标题和图标代替logo图片
            st.markdown("""
            <div class="app-header">
                <h1>📈 TrendQuest</h1>
                <p>量化交易系统</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 显示用户信息
            st.markdown(f"**当前用户:** {st.session_state.user}")
            st.markdown(f"**最后访问:** {st.session_state.last_access.strftime('%Y-%m-%d %H:%M')}")
            
            # 导航菜单
            st.header("功能导航")
            pages = {
                "回测": "📊 策略回测",
                "实盘": "💹 实盘交易",
                "数据": "📈 数据中心",
                "策略": "🔧 策略管理",
                "设置": "⚙️ 系统设置"
            }
            
            for page_id, page_name in pages.items():
                if st.button(page_name, key=f"nav_{page_id}"):
                    st.session_state.page = page_id
                    st.experimental_rerun()
            
            # 系统信息
            st.markdown("---")
            st.markdown("### 系统信息")
            st.markdown(f"版本: v1.0.0")
            st.markdown(f"运行环境: Python {sys.version.split()[0]}")
            
            # 帮助链接
            st.markdown("---")
            st.markdown("### 帮助")
            st.markdown("[📘 使用文档](https://github.com/emmoblin/TrendQuest/wiki)")
            st.markdown("[🐛 问题反馈](https://github.com/emmoblin/TrendQuest/issues)")
            st.markdown("[💡 功能建议](https://github.com/emmoblin/TrendQuest/discussions)")
    
    def render_main_content(self):
        """渲染主要内容"""
        try:
            if st.session_state.page == "回测":
                backtest_page = BacktestPage()
                backtest_page.render()
                
            elif st.session_state.page == "实盘":
                self._show_coming_soon("实盘交易功能开发中...")
                
            elif st.session_state.page == "数据":
                self._show_coming_soon("数据中心功能开发中...")
                
            elif st.session_state.page == "策略":
                self._show_coming_soon("策略管理功能开发中...")
                
            elif st.session_state.page == "设置":
                self._render_settings()
                
        except Exception as e:
            st.error(f"页面渲染失败: {str(e)}")
            logger.error("页面渲染失败", exc_info=True)
    
    def _show_coming_soon(self, message: str):
        """显示开发中提示"""
        st.info(
            f"🚧 {message}\n\n"
            "预计发布时间: 2025年Q2"
        )
    
    def _render_settings(self):
        """渲染设置页面"""
        st.title("系统设置")
        
        # 基本设置
        st.subheader("基本设置")
        col1, col2 = st.columns(2)
        
        with col1:
            theme = st.selectbox(
                "界面主题",
                options=["默认", "暗色", "亮色"],
                help="选择界面显示主题"
            )
            
        with col2:
            language = st.selectbox(
                "界面语言",
                options=["中文", "English"],
                help="选择界面显示语言"
            )
        
        # 回测设置
        st.subheader("回测设置")
        col3, col4 = st.columns(2)
        
        with col3:
            cache_dir = st.text_input(
                "缓存目录",
                value="cache",
                help="数据缓存目录路径"
            )
            
        with col4:
            max_workers = st.number_input(
                "最大并行数",
                min_value=1,
                max_value=16,
                value=4,
                help="最大并行处理线程数"
            )
        
        # 实盘设置
        st.subheader("实盘设置")
        api_key = st.text_input(
            "API密钥",
            type="password",
            help="交易API密钥"
        )
        
        # 保存按钮
        if st.button("保存设置", type="primary"):
            try:
                # 保存设置
                settings = {
                    "theme": theme,
                    "language": language,
                    "cache_dir": cache_dir,
                    "max_workers": max_workers,
                    "api_key": api_key
                }
                self._save_settings(settings)
                st.success("设置已保存")
                
            except Exception as e:
                st.error(f"保存设置失败: {str(e)}")
                logger.error("保存设置失败", exc_info=True)
    
    def _save_settings(self, settings: Dict[str, Any]):
        """保存系统设置"""
        # 这里实现设置保存逻辑
        pass
    
    def run(self):
        """运行应用"""
        try:
            # 渲染侧边栏
            self.render_sidebar()
            
            # 渲染主要内容
            self.render_main_content()
            
            # 更新最后访问时间
            st.session_state.last_access = self.current_time
            
        except Exception as e:
            st.error(f"应用运行失败: {str(e)}")
            logger.error("应用运行失败", exc_info=True)
            
def main():
    """主函数"""
    try:
        # 创建并运行应用
        app = TrendQuestApp()
        app.run()
        
    except Exception as e:
        st.error(f"程序启动失败: {str(e)}")
        logger.error("程序启动失败", exc_info=True)

if __name__ == "__main__":
    main()