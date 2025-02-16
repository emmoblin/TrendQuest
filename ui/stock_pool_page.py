import streamlit as st
from datetime import datetime
from typing import Dict, Any
from stock_pool_manager import StockPoolManager
from utils.log_init import get_logger

logger = get_logger(__name__)

class StockPoolPage:
    """股票池管理页面"""
    
    def __init__(self):
        self.current_time = datetime.strptime("2025-02-16 15:59:57", "%Y-%m-%d %H:%M:%S")
        self.current_user = "emmoblin"
        self.pool_manager = StockPoolManager()
    
    def render(self):
        """渲染股票池管理页面"""
        try:
            st.title("股票池管理")
            
            # 添加新股票池表单
            with st.expander("➕ 创建新股票池", expanded=False):
                self._render_create_pool_form()
            
            # 显示现有股票池
            self._render_existing_pools()
            
        except Exception as e:
            st.error(f"页面加载失败: {str(e)}")
            logger.error("页面加载失败", exc_info=True)
    
    def _render_create_pool_form(self):
        """渲染创建股票池表单"""
        with st.form("create_pool_form"):
            pool_name = st.text_input(
                "股票池名称",
                help="输入新股票池的名称"
            )
            
            description = st.text_area(
                "描述",
                help="输入股票池的描述信息"
            )
            
            submitted = st.form_submit_button("创建")
            
            if submitted and pool_name:
                if self.pool_manager.create_pool(pool_name, description):
                    st.success(f"股票池 '{pool_name}' 创建成功")
                else:
                    st.error(f"股票池 '{pool_name}' 创建失败")
    
    def _render_existing_pools(self):
        """渲染现有股票池列表"""
        pools = self.pool_manager.get_all_pools()
        
        if not pools:
            st.warning("暂无股票池，请先创建")
            return
        
        # 显示所有股票池
        for pool_name, pool_info in pools.items():
            with st.expander(f"📁 {pool_name}", expanded=False):
                # 显示股票池信息
                st.markdown(f"**描述:** {pool_info['description']}")
                st.markdown(f"**创建时间:** {pool_info['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                st.markdown(f"**创建者:** {pool_info['created_by']}")
                
                # 显示股票列表
                symbols = pool_info['symbols']
                if symbols:
                    st.subheader("股票列表")
                    symbol_data = []
                    for symbol, info in symbols.items():
                        symbol_data.append({
                            "代码": symbol,
                            "名称": info['name'],
                            "行业": info['industry']
                        })
                    
                    st.dataframe(symbol_data)
                else:
                    st.info("暂无股票")
                
                # 添加股票表单
                with st.form(f"add_symbol_form_{pool_name}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        symbol = st.text_input("股票代码", key=f"symbol_{pool_name}")
                    
                    with col2:
                        name = st.text_input("股票名称", key=f"name_{pool_name}")
                    
                    with col3:
                        industry = st.text_input("所属行业", key=f"industry_{pool_name}")
                    
                    submitted = st.form_submit_button("添加股票")
                    
                    if submitted and symbol and name:
                        if self.pool_manager.add_symbol(pool_name, symbol, name, industry):
                            st.success(f"股票 {symbol} 添加成功")
                        else:
                            st.error(f"股票 {symbol} 添加失败")
                
                # 删除股票池按钮
                if st.button("🗑️ 删除股票池", key=f"delete_{pool_name}"):
                    if st.warning(f"确定要删除股票池 '{pool_name}' 吗？"):
                        if self.pool_manager.delete_pool(pool_name):
                            st.success(f"股票池 '{pool_name}' 删除成功")
                            st.rerun()
                        else:
                            st.error(f"股票池 '{pool_name}' 删除失败")