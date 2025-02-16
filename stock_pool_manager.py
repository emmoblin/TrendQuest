from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
from utils.log_init import get_logger

logger = get_logger(__name__)

class StockPoolManager:
    """股票池管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self.current_time = datetime.strptime("2025-02-16 16:50:38", "%Y-%m-%d %H:%M:%S")
        self.current_user = "emmoblin"
        self._pools = self._initialize_pools()
    
    def _initialize_pools(self) -> Dict[str, Dict[str, Any]]:
        """初始化股票池数据
        
        Returns:
            股票池数据字典
        """
        try:
            # 这里后续可以从数据库或文件加载
            return {
                "沪深300": {
                    "description": "沪深300指数成分股",
                    "created_at": self.current_time,
                    "created_by": self.current_user,
                    "updated_at": self.current_time,
                    "updated_by": self.current_user,
                    "symbols": {
                        "600519": {
                            "name": "贵州茅台",
                            "industry": "食品饮料",
                            "added_at": self.current_time,
                            "added_by": self.current_user
                        },
                        "601318": {
                            "name": "中国平安",
                            "industry": "金融保险",
                            "added_at": self.current_time,
                            "added_by": self.current_user
                        }
                    }
                },
                "中证500": {
                    "description": "中证500指数成分股",
                    "created_at": self.current_time,
                    "created_by": self.current_user,
                    "updated_at": self.current_time,
                    "updated_by": self.current_user,
                    "symbols": {
                        "000661": {
                            "name": "长春高新",
                            "industry": "医药生物",
                            "added_at": self.current_time,
                            "added_by": self.current_user
                        },
                        "002475": {
                            "name": "立讯精密",
                            "industry": "电子",
                            "added_at": self.current_time,
                            "added_by": self.current_user
                        }
                    }
                }
            }
        except Exception as e:
            logger.error("Failed to initialize stock pools", exc_info=True)
            return {}
    
    def get_all_pools(self) -> Dict[str, Dict[str, Any]]:
        """获取所有股票池"""
        return self._pools
    
    def get_pool_symbols(self, pool_name: str) -> Dict[str, Dict[str, Any]]:
        """获取指定股票池中的股票
        
        Args:
            pool_name: 股票池名称
            
        Returns:
            股票信息字典
        """
        if pool_name not in self._pools:
            logger.warning(f"Stock pool '{pool_name}' not found")
            return {}
        return self._pools[pool_name]["symbols"]
    
    def create_pool(self, name: str, description: str = "") -> bool:
        """创建新的股票池
        
        Args:
            name: 股票池名称
            description: 股票池描述
            
        Returns:
            是否创建成功
        """
        try:
            if name in self._pools:
                logger.warning(f"Stock pool '{name}' already exists")
                return False
            
            self._pools[name] = {
                "description": description,
                "created_at": self.current_time,
                "created_by": self.current_user,
                "updated_at": self.current_time,
                "updated_by": self.current_user,
                "symbols": {}
            }
            
            logger.info(f"Created stock pool: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create stock pool: {name}", exc_info=True)
            return False
    
    def add_symbol(self, pool_name: str, symbol: str, name: str, industry: str) -> bool:
        """向股票池添加股票
        
        Args:
            pool_name: 股票池名称
            symbol: 股票代码
            name: 股票名称
            industry: 行业分类
            
        Returns:
            是否添加成功
        """
        try:
            if pool_name not in self._pools:
                logger.warning(f"Stock pool '{pool_name}' not found")
                return False
            
            self._pools[pool_name]["symbols"][symbol] = {
                "name": name,
                "industry": industry,
                "added_at": self.current_time,
                "added_by": self.current_user
            }
            
            # 更新股票池信息
            self._pools[pool_name]["updated_at"] = self.current_time
            self._pools[pool_name]["updated_by"] = self.current_user
            
            logger.info(f"Added symbol {symbol} to pool {pool_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add symbol {symbol} to pool {pool_name}", exc_info=True)
            return False
    
    def remove_symbol(self, pool_name: str, symbol: str) -> bool:
        """从股票池移除股票
        
        Args:
            pool_name: 股票池名称
            symbol: 股票代码
            
        Returns:
            是否移除成功
        """
        try:
            if pool_name not in self._pools:
                logger.warning(f"Stock pool '{pool_name}' not found")
                return False
            
            if symbol not in self._pools[pool_name]["symbols"]:
                logger.warning(f"Symbol {symbol} not found in pool {pool_name}")
                return False
            
            del self._pools[pool_name]["symbols"][symbol]
            
            # 更新股票池信息
            self._pools[pool_name]["updated_at"] = self.current_time
            self._pools[pool_name]["updated_by"] = self.current_user
            
            logger.info(f"Removed symbol {symbol} from pool {pool_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove symbol {symbol} from pool {pool_name}", exc_info=True)
            return False
    
    def delete_pool(self, pool_name: str) -> bool:
        """删除股票池
        
        Args:
            pool_name: 股票池名称
            
        Returns:
            是否删除成功
        """
        try:
            if pool_name not in self._pools:
                logger.warning(f"Stock pool '{pool_name}' not found")
                return False
            
            del self._pools[pool_name]
            logger.info(f"Deleted stock pool: {pool_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete stock pool: {pool_name}", exc_info=True)
            return False
    
    def get_pool_info(self, pool_name: str) -> Optional[Dict[str, Any]]:
        """获取股票池信息
        
        Args:
            pool_name: 股票池名称
            
        Returns:
            股票池信息字典，不存在时返回None
        """
        try:
            if pool_name not in self._pools:
                logger.warning(f"Stock pool '{pool_name}' not found")
                return None
            
            pool_info = self._pools[pool_name].copy()
            pool_info["symbol_count"] = len(pool_info["symbols"])
            return pool_info
            
        except Exception as e:
            logger.error(f"Failed to get pool info: {pool_name}", exc_info=True)
            return None