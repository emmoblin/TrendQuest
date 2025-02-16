import streamlit as st
import pandas as pd
import json
import logging
from pathlib import Path
from datetime import datetime

# 配置日志
logger = logging.getLogger(__name__)

class StockPoolManager:
    """标的池管理类"""
    
    def __init__(self, config_path="config/stock_pools.json"):
        """
        初始化标的池管理器
        
        Args:
            config_path (str): 标的池配置文件路径
        """
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.pools = self.load_pools()

    def load_pools(self):
        """加载标的池配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"加载标的池配置失败: {str(e)}")
            return {}

    def save_pools(self):
        """保存标的池配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.pools, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logger.error(f"保存标的池配置失败: {str(e)}")
            return False

    def create_pool(self, pool_name):
        """
        创建新的标的池
        
        Args:
            pool_name (str): 标的池名称
            
        Returns:
            bool: 是否创建成功
        """
        if not pool_name:
            return False, "标的池名称不能为空"
        
        if pool_name in self.pools:
            return False, f"标的池 '{pool_name}' 已存在"
        
        self.pools[pool_name] = {}
        if self.save_pools():
            return True, f"成功创建标的池: {pool_name}"
        return False, "创建标的池失败"

    def delete_pool(self, pool_name):
        """
        删除标的池
        
        Args:
            pool_name (str): 标的池名称
            
        Returns:
            bool: 是否删除成功
        """
        if pool_name in self.pools:
            del self.pools[pool_name]
            if self.save_pools():
                return True, f"成功删除标的池: {pool_name}"
        return False, f"删除标的池失败: {pool_name}"

    def add_symbol(self, pool_name, symbol, name, symbol_type):
        """
        向标的池添加新标的
        
        Args:
            pool_name (str): 标的池名称
            symbol (str): 标的代码
            name (str): 标的名称
            symbol_type (str): 标的类型
            
        Returns:
            tuple: (bool, str) 是否添加成功及消息
        """
        if pool_name not in self.pools:
            return False, f"标的池 '{pool_name}' 不存在"
        
        if symbol in self.pools[pool_name]:
            return False, f"标的 {symbol} 已存在于标的池中"
        
        self.pools[pool_name][symbol] = {
            "name": name,
            "type": symbol_type,
            "added_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if self.save_pools():
            return True, f"成功添加标的: {symbol} ({name})"
        return False, "添加标的失败"

    def delete_symbols(self, pool_name, symbols):
        """
        从标的池删除标的
        
        Args:
            pool_name (str): 标的池名称
            symbols (list): 要删除的标的代码列表
            
        Returns:
            tuple: (bool, str) 是否删除成功及消息
        """
        if pool_name not in self.pools:
            return False, f"标的池 '{pool_name}' 不存在"
        
        deleted_count = 0
        for symbol in symbols:
            if symbol in self.pools[pool_name]:
                del self.pools[pool_name][symbol]
                deleted_count += 1
        
        if deleted_count > 0 and self.save_pools():
            return True, f"成功删除 {deleted_count} 个标的"
        return False, "删除标的失败"

    def get_pool_symbols(self, pool_name):
        """
        获取标的池中的所有标的
        
        Args:
            pool_name (str): 标的池名称
            
        Returns:
            dict: 标的池中的标的信息
        """
        return self.pools.get(pool_name, {})

    def get_all_pools(self):
        """
        获取所有标的池
        
        Returns:
            dict: 所有标的池的信息
        """
        return self.pools

def show_pool_management():
    """显示标的池管理界面"""
    st.header("标的池管理")
    
    # 初始化标的池管理器
    pool_manager = StockPoolManager()
    
    # 创建新标的池
    col1, col2 = st.columns([3, 1])
    with col1:
        new_pool_name = st.text_input(
            "输入新标的池名称",
            key="new_pool_name"
        )
    with col2:
        if st.button("创建标的池", key="create_pool"):
            success, message = pool_manager.create_pool(new_pool_name)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.warning(message)

    # 现有标的池管理
    pools = pool_manager.get_all_pools()
    if pools:
        st.subheader("现有标的池")
        selected_pool = st.selectbox(
            "选择要管理的标的池",
            options=list(pools.keys()),
            key="manage_pool"
        )

        if selected_pool:
            st.markdown(f"### 管理 '{selected_pool}' 标的池")
            
            # 添加新标的
            with st.form(key="add_symbol_form"):
                st.subheader("添加新标的")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    symbol = st.text_input("标的代码", help="输入股票或ETF代码")
                with col2:
                    name = st.text_input("标的名称")
                with col3:
                    symbol_type = st.selectbox(
                        "标的类型",
                        options=["股票", "ETF"]
                    )

                if st.form_submit_button("添加标的"):
                    success, message = pool_manager.add_symbol(
                        selected_pool, symbol, name, symbol_type
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.warning(message)

            # 显示现有标的
            pool_symbols = pool_manager.get_pool_symbols(selected_pool)
            if pool_symbols:
                st.subheader("标的池内容")
                
                # 创建DataFrame显示标的信息
                df = pd.DataFrame([
                    {
                        "代码": code,
                        "名称": info["name"],
                        "类型": info["type"],
                        "添加时间": info.get("added_time", "未知")
                    }
                    for code, info in pool_symbols.items()
                ])
                
                # 显示标的列表
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                # 删除标的
                symbols_to_delete = st.multiselect(
                    "选择要删除的标的",
                    options=df["代码"].tolist(),
                    format_func=lambda x: f"{x} ({pool_symbols[x]['name']})"
                )

                if symbols_to_delete and st.button("删除所选标的", key="delete_symbols"):
                    success, message = pool_manager.delete_symbols(
                        selected_pool, symbols_to_delete
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.warning(message)

            # 删除标的池
            if st.button("删除此标的池", key="delete_pool"):
                if st.session_state.get("confirm_delete_pool") is None:
                    st.session_state.confirm_delete_pool = False
                    
                if not st.session_state.confirm_delete_pool:
                    st.warning(f"确定要删除标的池 '{selected_pool}' 吗？此操作不可恢复。")
                    if st.button("确认删除"):
                        st.session_state.confirm_delete_pool = True
                        
                if st.session_state.confirm_delete_pool:
                    success, message = pool_manager.delete_pool(selected_pool)
                    if success:
                        st.success(message)
                        st.session_state.confirm_delete_pool = False
                        st.rerun()
                    else:
                        st.error(message)

    else:
        st.info("当前没有标的池，请创建新的标的池")